from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from extensions import db
from core.models import Usuario, Safra, Transacao, Interesse
from functools import wraps
from datetime import datetime

# Importamos a função de notificação
try:
    from modules.perfil.routes import enviar_notificacao
except ImportError:
    def enviar_notificacao(*args, **kwargs):
        pass

admin_bp = Blueprint('admin', __name__)


# --- DECORATOR DE SEGURANÇA ---
def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash("Acesso restrito a administradores.", "danger")
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)

    return decorated_function


# --- DASHBOARD PRINCIPAL ---
@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    # Estatísticas
    total_valor = db.session.query(db.func.sum(Transacao.preco_total)).scalar() or 0
    total_produtores = Usuario.query.filter_by(tipo='produtor').count()
    total_compradores = Usuario.query.filter_by(tipo='comprador').count()
    safras_ativas = Safra.query.filter_by(status='disponivel').count()
    pendentes_verificacao = Transacao.query.filter_by(status='aguardando_validacao').count()

    # Listagens
    interesses = Interesse.query.order_by(Interesse.data_criacao.desc()).limit(10).all()
    novos_usuarios = Usuario.query.order_by(Usuario.id.desc()).limit(5).all()

    return render_template('admin/dashboard.html',
                           total_valor=total_valor,
                           total_produtores=total_produtores,
                           total_compradores=total_compradores,
                           safras_ativas=safras_ativas,
                           pendentes_verificacao=pendentes_verificacao,
                           interesses=interesses,
                           novos_usuarios=novos_usuarios)


# --- LISTAGEM DE PAGAMENTOS ---
@admin_bp.route('/validar-pagamentos')
@admin_required
def validar_pagamentos():
    # Busca transações nos estados específicos do fluxo de Angola
    pendentes = Transacao.query.filter_by(status='aguardando_validacao').order_by(Transacao.data_criacao.desc()).all()
    custodia = Transacao.query.filter_by(status='pago_custodia').order_by(Transacao.data_criacao.desc()).all()

    return render_template('admin/validar_pagamentos.html',
                           pendentes=pendentes,
                           custodia=custodia)


# --- AÇÃO: VALIDAR COMPROVATIVO ---
@admin_bp.route('/pagamento/validar/<int:transacao_id>', methods=['POST'])
@admin_required
def validar_comprovativo(transacao_id):
    transacao = Transacao.query.get_or_404(transacao_id)

    # Atualiza Status para Custódia
    transacao.status = 'pago_custodia'

    # 1. Notificar o PRODUTOR (Autorizar entrega)
    enviar_notificacao(
        usuario_id=transacao.safra.produtor_id,
        titulo="✅ Pagamento Validado!",
        mensagem=f"O pagamento da Ref: {transacao.fatura_ref} foi confirmado. Pode avançar com a entrega.",
        tipo="success"
    )

    # 2. Notificar o COMPRADOR (Confirmação de segurança)
    enviar_notificacao(
        usuario_id=transacao.comprador_id,
        titulo="Comprovativo Aprovado",
        mensagem=f"O seu comprovativo (Ref: {transacao.fatura_ref}) foi validado. O valor está seguro em custódia.",
        tipo="info"
    )

    db.session.commit()
    flash(f'Pagamento {transacao.fatura_ref} validado. Fundo em custódia!', 'success')
    return redirect(url_for('admin.validar_pagamentos'))


# --- AÇÃO: REJEITAR COMPROVATIVO ---
@admin_bp.route('/pagamento/rejeitar/<int:transacao_id>', methods=['POST'])
@admin_required
def rejeitar_comprovativo(transacao_id):
    transacao = Transacao.query.get_or_404(transacao_id)
    motivo = request.form.get('motivo', 'Comprovativo inválido ou ilegível.')

    try:
        # 1. Resetar status para o valor exato do seu modelo ('pendente_pagamento')
        # Isso reativa o botão de pagar no painel do comprador
        transacao.status = 'pendente_pagamento'

        # 2. Limpar o rastro do ficheiro errado para forçar novo upload
        transacao.comprovativo_path = None

        # 3. Notificar o COMPRADOR
        enviar_notificacao(
            usuario_id=transacao.comprador_id,
            titulo="❌ Pagamento Rejeitado",
            mensagem=f"O comprovativo da Ref: {transacao.fatura_ref} foi rejeitado. Motivo: {motivo}",
            tipo="danger"
        )

        db.session.commit()
        flash(f"Pagamento {transacao.fatura_ref} rejeitado. O comprador poderá tentar novamente.", "info")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao processar rejeição: {str(e)}", "danger")

    return redirect(url_for('admin.validar_pagamentos'))

@admin_bp.route('/atividades-sistema')
@login_required
def atividades_admin():
    if not current_user.is_admin:
        abort(403)
    atividades = Transacao.query.order_by(Transacao.data_criacao.desc()).all()
    return render_template('admin/atividades.html', atividades=atividades)