from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_required, current_user
from flask_wtf.csrf import validate_csrf
from wtforms import ValidationError
from markupsafe import escape
from app.extensions import db
from app.models import Transacao, TransactionStatus, Notificacao, LogAuditoria
from app.models import Disputa
from app.utils.helpers import salvar_ficheiro
from app.tasks.notificacoes import enviar_notificacao_disputa_async
from datetime import datetime, timezone

disputas_bp = Blueprint('disputas', __name__)


def _validar_acesso_disputa(transacao, usuario_id):
    if transacao.comprador_id != usuario_id:
        return False, "Acesso negado."
    
    if hasattr(transacao, 'disputa') and transacao.disputa:
        return False, "Esta transacao ja possui uma disputa aberta."
    
    return True, None


def _validar_prazo_disputa(transacao, usuario_id):
    disputa_temp = Disputa(transacao_id=transacao.id, comprador_id=usuario_id)
    return disputa_temp.pode_abrir_disputa()


def _criar_disputa_from_form(transacao_id, comprador_id):
    motivo = escape(request.form.get('motivo', '').strip())
    
    if not motivo or len(motivo) < 20:
        raise ValueError("Por favor, descreva o motivo da disputa com detalhes (minimo 20 caracteres).")
    
    nova_disputa = Disputa(
        transacao_id=transacao_id,
        comprador_id=comprador_id,
        motivo=motivo
    )
    
    evidencia_file = request.files.get('evidencia')
    if evidencia_file and evidencia_file.filename != '':
        nova_disputa.evidencia_path = salvar_ficheiro(evidencia_file, subpasta='evidencias_disputas', privado=True)
    
    return nova_disputa


def _validar_justificativa_decisao():
    justificativa = escape(request.form.get('justificativa', '').strip())
    if not justificativa or len(justificativa) < 30:
        raise ValueError("Por favor, forneca uma justificativa detalhada para sua decisao (minimo 30 caracteres).")
    return justificativa


def _processar_decisao_disputa(disputa, decisao, admin_id, justificativa):
    ip_address = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')
    
    if decisao == 'comprador':
        disputa.resolver_favor_comprador(admin_id, justificativa, ip_address, user_agent)
        return "Disputa resolvida a favor do comprador. Reembolso processado."
    elif decisao == 'produtor':
        disputa.resolver_favor_produtor(admin_id, justificativa, ip_address, user_agent)
        return "Disputa resolvida a favor do produtor. Pagamento liberado."
    else:
        raise ValueError("Decisao invalida.")


@disputas_bp.route('/abrir-disputa/<string:trans_uuid>', methods=['GET', 'POST'])
@login_required
def abrir_disputa(trans_uuid):
    transacao = Transacao.query.filter_by(uuid=trans_uuid).first_or_404()
    
    pode_acessar, mensagem_erro = _validar_acesso_disputa(transacao, current_user.id)
    if not pode_acessar:
        if mensagem_erro == "Acesso negado.":
            abort(403)
        flash(mensagem_erro, "warning")
        return redirect(url_for('comprador.minhas_compras'))
    
    pode_abrir, mensagem = _validar_prazo_disputa(transacao, current_user.id)
    if not pode_abrir:
        flash(mensagem, "warning")
        return redirect(url_for('comprador.minhas_compras'))
    
    if request.method == 'POST':
        try:
            validate_csrf(request.form.get('csrf_token'))
        except ValidationError:
            abort(403)
        
        try:
            nova_disputa = _criar_disputa_from_form(transacao.id, current_user.id)
            transacao.status = TransactionStatus.DISPUTA
            
            db.session.add(nova_disputa)
            db.session.add(LogAuditoria(
                usuario_id=current_user.id,
                acao="ABERTURA_DISPUTA",
                detalhes=f"Comprador abriu disputa para transacao {escape(transacao.fatura_ref)}. Motivo: {escape(nova_disputa.motivo[:100])}...",
                ip=request.remote_addr
            ))
            
            db.session.commit()
            
            enviar_notificacao_disputa_async.delay(
                disputa_id=nova_disputa.id,
                tipo_notificacao='abertura'
            )
            
            flash("Disputa aberta com sucesso! Um administrador ira analisar seu caso.", "success")
            return redirect(url_for('comprador.minhas_compras'))
            
        except ValueError as ve:
            flash(str(ve), "warning")
            return render_template('disputas/abrir_disputa.html', transacao=transacao)
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro ao abrir disputa: {e}")
            flash("Erro ao processar sua solicitacao. Tente novamente.", "danger")
    
    return render_template('disputas/abrir_disputa.html', transacao=transacao)


@disputas_bp.route('/admin/painel-disputas')
@login_required
def painel_disputas():
    from app.utils.decorators import admin_required
    
    if not admin_required(current_user):
        abort(403)
    
    disputas_abertas = Disputa.query.filter_by(status='aberta').order_by(Disputa.data_abertura.asc()).all()
    
    return render_template('admin/painel_disputas.html', disputas=disputas_abertas)


@disputas_bp.route('/admin/disputa/<int:disputa_id>', methods=['GET', 'POST'])
@login_required
def detalhe_disputa(disputa_id):
    from app.utils.decorators import admin_required
    
    if not admin_required(current_user):
        abort(403)
    
    disputa = Disputa.query.with_for_update().get_or_404(disputa_id)
    
    if request.method == 'POST':
        try:
            validate_csrf(request.form.get('csrf_token'))
        except ValidationError:
            abort(403)
        
        try:
            decisao = request.form.get('decisao')
            justificativa = _validar_justificativa_decisao()
            mensagem = _processar_decisao_disputa(disputa, decisao, current_user.id, justificativa)
            
            db.session.commit()
            
            enviar_notificacao_disputa_async.delay(
                disputa_id=disputa.id,
                tipo_notificacao='resolucao',
                decisao=decisao,
                admin_nome=current_user.nome
            )
            
            flash(mensagem, "success")
            return redirect(url_for('disputas.painel_disputas'))
            
        except ValueError as ve:
            flash(str(ve), "warning")
            return render_template('admin/detalhe_disputa.html', disputa=disputa)
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro ao resolver disputa {disputa_id}: {e}")
            flash("Erro ao processar sua decisao. Tente novamente.", "danger")
    
    return render_template('admin/detalhe_disputa.html', disputa=disputa)


@disputas_bp.route('/admin/chat/<int:disputa_id>')
@login_required
def chat_disputa(disputa_id):
    from app.utils.decorators import admin_required
    
    if not admin_required(current_user):
        abort(403)
    
    disputa = Disputa.query.get_or_404(disputa_id)
    
    from app.models import Mensagem
    mensagens = Mensagem.query.filter_by(transacao_id=disputa.transacao_id).order_by(Mensagem.data_envio.asc()).all()
    
    return render_template('admin/chat_disputa.html', disputa=disputa, mensagens=mensagens)


def register_disputas_routes(app):
    app.register_blueprint(disputas_bp)
