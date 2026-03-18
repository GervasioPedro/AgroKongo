"""
Blueprint para gestão de disputas do Admin.
Responsável por mediação e resolução de conflitos.
"""
from decimal import Decimal
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Transacao, Notificacao, LogAuditoria, TransactionStatus
from functools import wraps

from app.utils.status_helper import status_to_value

admin_disputas_bp = Blueprint('admin_disputas', __name__)


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.tipo != 'admin':
            flash("Acesso restrito a administradores.", "danger")
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


@admin_disputas_bp.route('/disputas')
@login_required
@admin_required
def painel_disputas():
    disputas = Transacao.query.filter_by(status='em_disputa').order_by(Transacao.data_criacao.asc()).all()
    return render_template('admin/painel_disputas.html', disputas=disputas)


@admin_disputas_bp.route('/resolver-disputa/<int:trans_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def resolver_disputa(trans_id):
    """Juiz do Mercado: Decide se devolve o dinheiro ao comprador ou paga ao produtor."""
    venda = Transacao.query.get_or_404(trans_id)

    if request.method == 'POST':
        try:
            decisao = request.form.get('decisao')  # 'libertar' ou 'reembolsar'

            if decisao == 'libertar':
                venda.mudar_status(status_to_value(TransactionStatus.ENTREGUE), "Disputa resolvida a favor do Produtor")
                produtor = venda.vendedor
                valor_liquido = Decimal(str(venda.valor_liquido_vendedor))
                produtor.saldo_disponivel = (produtor.saldo_disponivel or Decimal('0.00')) + valor_liquido
                
                msg = "Disputa resolvida a favor do Produtor."
                
                db.session.add(Notificacao(usuario_id=venda.vendedor_id, mensagem="✅ Disputa ganha! Fundos libertados."))
                db.session.add(Notificacao(usuario_id=venda.comprador_id, mensagem="❌ Disputa fechada a favor do vendedor."))

            elif decisao == 'reembolsar':
                venda.mudar_status(status_to_value(TransactionStatus.CANCELADO), "Disputa resolvida com Reembolso")
                if venda.safra:
                    venda.safra.quantidade_disponivel += venda.quantidade_comprada
                
                msg = "Disputa resolvida com Reembolso ao Comprador."
                
                db.session.add(Notificacao(usuario_id=venda.comprador_id, mensagem="✅ Disputa ganha! Reembolso aprovado."))
                db.session.add(Notificacao(usuario_id=venda.vendedor_id, mensagem="❌ Disputa fechada a favor do comprador."))

            db.session.add(LogAuditoria(
                usuario_id=current_user.id,
                acao="RESOLUCAO_DISPUTA",
                detalhes=f"Ref {venda.fatura_ref}: {msg}",
                ip=request.remote_addr
            ))
            db.session.commit()
            flash("Disputa encerrada.", "success")
            return redirect(url_for('admin_dashboard.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro disputa: {e}")
            flash("Erro ao resolver disputa.", "danger")

    return render_template('admin/detalhe_disputa.html', venda=venda)


@admin_disputas_bp.route('/abrir-disputa-admin/<int:trans_id>', methods=['POST'])
@login_required
@admin_required
def abrir_disputa_admin(trans_id):
    """Admin pode abrir disputa manualmente se detectar irregularidades."""
    try:
        venda = Transacao.query.with_for_update().get_or_404(trans_id)
        
        if venda.status not in [status_to_value(TransactionStatus.CANCELADO), status_to_value(TransactionStatus.FINALIZADO)]:
            venda.mudar_status(status_to_value(TransactionStatus.DISPUTA), "Disputa aberta pelo Admin")
            
            db.session.add(LogAuditoria(
                usuario_id=current_user.id,
                acao="DISPUTA_ABERTA_ADMIN",
                detalhes=f"Ref: {venda.fatura_ref}",
                ip=request.remote_addr
            ))
            
            db.session.add(Notificacao(
                usuario_id=venda.vendedor_id,
                mensagem=f"⚠️ O Admin abriu uma disputa na venda {venda.fatura_ref}.",
                link=url_for('produtor.vendas')
            ))
            
            db.session.add(Notificacao(
                usuario_id=venda.comprador_id,
                mensagem=f"⚠️ O Admin abriu uma disputa na compra {venda.fatura_ref}.",
                link=url_for('comprador.dashboard')
            ))
            
            db.session.commit()
            flash("Disputa aberta. Analise o caso.", "warning")
        else:
             flash("Não é possível abrir disputa para uma transação finalizada ou cancelada.", "danger")
             
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao abrir disputa: {e}")
        flash("Erro ao processar pedido de disputa.", "danger")

    return redirect(url_for('admin_disputas.painel_disputas'))
