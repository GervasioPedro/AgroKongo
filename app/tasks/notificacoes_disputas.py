# app/tasks/notificacoes_disputas.py - Task assíncrona para notificações de disputas
# Implementação RN08 - Processamento assíncrono para performance

from celery import shared_task
from flask import url_for
from markupsafe import escape
from app.tasks.base import AgroKongoTask
from app.extensions import db, current_app
from app.models import Notificacao, Usuario
from app.models import Disputa
from datetime import datetime, timezone


@shared_task(bind=True, base=AgroKongoTask, max_retries=3, rate_limit='10/m')
def enviar_notificacao_disputa_async(self, disputa_id, tipo_notificacao, decisao=None, admin_nome=None):
    """
    Task assíncrona para enviar notificações de disputas
    Performance: Não bloqueia interface do Admin
    Segurança: Processamento em background com retry
    """
    try:
        with current_app.app_context():
            disputa = _buscar_disputa(disputa_id)
            if not disputa:
                return f"Disputa {disputa_id} não encontrada"
            
            if tipo_notificacao == 'abertura':
                _notificar_abertura_disputa(disputa)
            elif tipo_notificacao == 'resolucao':
                _notificar_resolucao_disputa(disputa, decisao, admin_nome)
            
            db.session.commit()
            # Proteção XSS: escapar tipo_notificacao em logs
            current_app.logger.info(f"Notificações {escape(tipo_notificacao)} enviadas para disputa {disputa_id}")
            return f"Notificações {escape(tipo_notificacao)} enviadas para disputa {disputa_id}"
            
    except Exception as e:
        current_app.logger.error(f"Erro task notificação disputa {disputa_id}: {e}", exc_info=True)
        db.session.rollback()
        raise self.retry(exc=e)


def _buscar_disputa(disputa_id):
    """Busca disputa com relacionamentos necessários."""
    from sqlalchemy.orm import joinedload
    
    disputa = Disputa.query.options(
        joinedload(Disputa.transacao).joinedload(Disputa.comprador),
        joinedload(Disputa.transacao).joinedload(Disputa.transacao).property.mapper.class_.vendedor
    ).get(disputa_id)
    
    if not disputa:
        current_app.logger.error(f"Disputa {disputa_id} não encontrada")
    
    return disputa


def _notificar_abertura_disputa(disputa):
    """Envia notificações de abertura de disputa."""
    _notificar_admins_nova_disputa(disputa)
    _notificar_produtor_disputa(disputa)
    _notificar_comprador_confirmacao(disputa)


def _notificar_admins_nova_disputa(disputa):
    """Notifica administradores sobre nova disputa."""
    admins = Usuario.query.filter_by(tipo='admin').all()
    for admin in admins:
        db.session.add(Notificacao(
            usuario_id=admin.id,
            mensagem=f"🚨 Nova disputa aberta: {escape(disputa.transacao.fatura_ref)}. Análise necessária.",
            link=url_for('disputas.detalhe_disputa', disputa_id=disputa.id)
        ))


def _notificar_produtor_disputa(disputa):
    """Notifica produtor sobre disputa aberta."""
    db.session.add(Notificacao(
        usuario_id=disputa.transacao.vendedor_id,
        mensagem=f"⚠️ Disputa aberta para {escape(disputa.transacao.fatura_ref)}. Aguardando análise.",
        link=url_for('produtor.vendas')
    ))


def _notificar_comprador_confirmacao(disputa):
    """Confirma ao comprador que disputa foi registrada."""
    db.session.add(Notificacao(
        usuario_id=disputa.comprador_id,
        mensagem=f"✅ Disputa #{escape(str(disputa.id))} registrada. Admin irá analisar seu caso.",
        link=url_for('comprador.minhas_compras')
    ))


def _notificar_resolucao_disputa(disputa, decisao, admin_nome):
    """Envia notificações de resolução de disputa."""
    # Proteção XSS: validar decisao antes de usar
    if decisao not in ['comprador', 'produtor']:
        current_app.logger.error(f"Decisão inválida: {escape(decisao)}")
        return
    
    if decisao == 'comprador':
        _notificar_decisao_favor_comprador(disputa)
    elif decisao == 'produtor':
        _notificar_decisao_favor_produtor(disputa)
    
    _notificar_outros_admins_resolucao(disputa, decisao, admin_nome)


def _notificar_decisao_favor_comprador(disputa):
    """Notifica sobre decisão favorável ao comprador."""
    db.session.add(Notificacao(
        usuario_id=disputa.comprador_id,
        mensagem=f"✅ Disputa resolvida! Reembolso processado para {escape(disputa.transacao.fatura_ref)}.",
        link=url_for('comprador.minhas_compras')
    ))
    
    db.session.add(Notificacao(
        usuario_id=disputa.transacao.vendedor_id,
        mensagem=f"⚠️ Disputa resolvida contra você. Taxa admin: {escape(str(disputa.taxa_administrativa))} Kz.",
        link=url_for('produtor.vendas')
    ))


def _notificar_decisao_favor_produtor(disputa):
    """Notifica sobre decisão favorável ao produtor."""
    db.session.add(Notificacao(
        usuario_id=disputa.transacao.vendedor_id,
        mensagem=f"✅ Disputa resolvida a seu favor! Pagamento liberado.",
        link=url_for('produtor.vendas')
    ))
    
    db.session.add(Notificacao(
        usuario_id=disputa.comprador_id,
        mensagem=f"❌ Disputa resolvida. Decisão favorável ao produtor.",
        link=url_for('comprador.minhas_compras')
    ))


def _notificar_outros_admins_resolucao(disputa, decisao, admin_nome):
    """Notifica outros administradores sobre resolução."""
    from flask_login import current_user
    
    outros_admins = Usuario.query.filter(
        Usuario.tipo == 'admin',
        Usuario.id != current_user.id
    ).all()
    
    for admin in outros_admins:
        db.session.add(Notificacao(
            usuario_id=admin.id,
            mensagem=f"📋 Disputa {escape(str(disputa.id))} resolvida por {escape(admin_nome)}. Decisão: {escape(decisao)}.",
            link=url_for('disputas.detalhe_disputa', disputa_id=disputa.id)
        ))


@shared_task(bind=True, base=AgroKongoTask, max_retries=2, rate_limit='5/d')
def enviar_lembrete_disputa_pendente(self):
    """
    Task diária para lembrar admins sobre disputas pendentes > 48h
    Performance: Executa uma vez por dia
    """
    try:
        with current_app.app_context():
            # Buscar disputas abertas há mais de 48h
            from datetime import timedelta
            limite = datetime.now(timezone.utc) - timedelta(hours=48)
            
            disputas_antigas = Disputa.query.filter(
                Disputa.status == 'aberta',
                Disputa.data_abertura <= limite
            ).all()
            
            if not disputas_antigas:
                return "Nenhuma disputa pendente > 48h"
            
            # Notificar todos os admins
            admins = Usuario.query.filter_by(tipo='admin').all()
            for admin in admins:
                db.session.add(Notificacao(
                    usuario_id=admin.id,
                    mensagem=f"⏰ {escape(str(len(disputas_antigas)))} disputas pendentes há mais de 48h. Ação necessária!",
                    link=url_for('disputas.painel_disputas')
                ))
            
            db.session.commit()
            current_app.logger.warning(f"Lembrete enviado: {escape(str(len(disputas_antigas)))} disputas pendentes > 48h")
            return f"Lembrete enviado para {escape(str(len(admins)))} admins"
            
    except Exception as e:
        current_app.logger.error(f"Erro task lembrete disputas: {e}", exc_info=True)
        raise self.retry(exc=e)


# Import necessário para joinedload (movido para o topo)
from sqlalchemy.orm import joinedload
