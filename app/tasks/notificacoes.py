# app/tasks/notificacoes.py - Versão auditada, resiliente e unificada
# Versão Corrigida - 22/02/2026
from celery import shared_task
import requests
from requests.exceptions import Timeout, RequestException
from flask import url_for  # ← Import adicionado
from flask import current_app
from app.extensions import db
from app.tasks.base import AgroKongoTask, AgroKongoTaskBase  # ← Import adicionado
from app.models import Notificacao, Usuario, LogAuditoria
from app.models.base import aware_utcnow
import bleach


@shared_task(bind=True, base=AgroKongoTaskBase, max_retries=5, rate_limit='50/m')
def enviar_notificacao_externa(self, usuario_id: int, mensagem: str, link: str = None, tipo: str = 'whatsapp'):
    """
    Envio async notificação externa (WhatsApp/SMS futuro) com fallback interna.
    Segurança: sanitização, PII mask log, timeout rede.
    UX: mensagem curta/mobile, link clicável.
    Resiliência: retry transient, notificação admin falhas.
    """
    try:
        user = _validar_usuario(usuario_id)
        mensagem_safe, link_safe = _sanitizar_mensagem(mensagem, link)
        _criar_notificacao_interna(usuario_id, mensagem_safe, link_safe)
        
        if tipo == 'whatsapp':
            _enviar_whatsapp(user, mensagem_safe, link_safe)
        
        _registrar_auditoria_notificacao(usuario_id, tipo, mensagem_safe, user.telemovel, self.request.id)
        db.session.commit()

    except ValueError as ve:
        current_app.logger.warning(f"Erro lógico notificação {usuario_id}: {ve}")

    except (Timeout, RequestException) as re:
        db.session.rollback()
        current_app.logger.error(f"Erro rede notificação {usuario_id} (task {self.request.id}): {re}")
        raise self.retry(exc=re, countdown=min(60 * 2 ** self.request.retries, 300))

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro task notificação {usuario_id} (ID: {self.request.id}): {e}", exc_info=True)
        _notificar_admin_erro(self.request.id, e)
        raise self.retry(exc=e)

    return "Notificação enviada"


def _validar_usuario(usuario_id):
    """Valida se usuário existe, está ativo e tem telemóvel."""
    user = db.session.query(Usuario).get(usuario_id)
    if not user or not user.is_active or not user.telemovel:
        raise ValueError(f"Usuário {usuario_id} inválido/inativo/sem telemóvel.")
    return user


def _sanitizar_mensagem(mensagem, link):
    """Sanitiza mensagem e link para segurança."""
    mensagem_safe = bleach.clean(mensagem, tags=['b', 'i', 'u'], strip=True)
    link_safe = bleach.linkify(bleach.clean(link or '', tags=[], strip=True)) if link else None
    return mensagem_safe, link_safe


def _criar_notificacao_interna(usuario_id, mensagem_safe, link_safe):
    """Cria notificação interna como fallback."""
    db.session.add(Notificacao(
        usuario_id=usuario_id,
        mensagem=mensagem_safe,
        link=link_safe,
        categoria='notificacao_externa',
        data_criacao=aware_utcnow()
    ))


def _enviar_whatsapp(user, mensagem_safe, link_safe):
    """Envia notificação via WhatsApp API."""
    api_url = current_app.config.get('WHATSAPP_API_URL')
    token = current_app.config.get('WHATSAPP_TOKEN')

    if not api_url or not token:
        raise RuntimeError("Config WhatsApp ausente.")

    mensagem_full = mensagem_safe + (f"\nLink: {link_safe}" if link_safe else "")
    payload = {
        'to': user.telemovel,
        'type': 'text',
        'text': {'body': mensagem_full}
    }
    headers = {'Authorization': f"Bearer {token}"}

    response = requests.post(api_url, json=payload, headers=headers, timeout=10)

    if response.status_code != 200:
        raise RuntimeError(f"Falha WhatsApp ({response.status_code}): {response.text[:200]}")


def _registrar_auditoria_notificacao(usuario_id, tipo, mensagem_safe, telemovel, task_id):
    """Registra auditoria da notificação com PII mascarado."""
    db.session.add(LogAuditoria(
        usuario_id=usuario_id,
        acao=f"ENVIO_NOTIFICACAO_{tipo.upper()}",
        detalhes=f"Tipo: {tipo} | Mensagem: {mensagem_safe[:100]}... | Telemóvel: ...{telemovel[-4:]} (task {task_id})"
    ))


def _notificar_admin_erro(task_id, erro):
    """Notifica administrador sobre erro no envio."""
    admin = db.session.query(Usuario).filter_by(tipo='admin').first()
    if admin:
        db.session.add(Notificacao(
            usuario_id=admin.id,
            mensagem=f"Falha envio notificação externa (task {task_id}): {str(erro)[:100]}...",
            categoria='erro_notificacao'
        ))
        db.session.commit()