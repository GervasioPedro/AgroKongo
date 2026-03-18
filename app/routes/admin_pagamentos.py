"""
Blueprint para gestão de pagamentos do Admin.
Responsável por validação de talões, liquidação e conferência bancária.
"""
from decimal import Decimal
from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_file
from flask_login import login_required, current_user

from app import scheduler
from app.extensions import db
from app.models import Transacao, Notificacao, LogAuditoria, TransactionStatus
from functools import wraps

from app.utils.status_helper import status_to_value

admin_pagamentos_bp = Blueprint('admin_pagamentos', __name__)


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.tipo != 'admin':
            flash("Acesso restrito a administradores.", "danger")
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


@admin_pagamentos_bp.route('/validar-pagamento/<int:id>', methods=['POST'])
@login_required
@admin_required
def validar_pagamento(id):
    try:
        venda = Transacao.query.with_for_update().get_or_404(id)

        if venda.status != status_to_value(TransactionStatus.ANALISE):
            flash('Esta transação já foi processada ou não está em análise.', 'warning')
            return redirect(url_for('admin_dashboard.dashboard'))

        venda.mudar_status(status_to_value(TransactionStatus.ESCROW), "Pagamento validado pelo Admin")

        db.session.add(LogAuditoria(
            usuario_id=current_user.id,
            acao="VALIDACAO_PAGAMENTO",
            detalhes=f"Ref {venda.fatura_ref} aprovada.",
            ip=request.remote_addr
        ))
        
        db.session.add(Notificacao(
            usuario_id=venda.vendedor_id,
            mensagem=f"💰 Pagamento confirmado para {venda.fatura_ref}! Pode enviar a mercadoria.",
            link=url_for('produtor.vendas')
        ))

        db.session.commit()

        # Disparo assíncrono de email (se configurado)
        try:
            if scheduler.running:
                from app.tasks import enviar_fatura_email
                scheduler.add_job(
                    id=f'envio_fatura_{venda.id}',
                    func=enviar_fatura_email,
                    args=[venda.id],
                    trigger='date',
                    run_date=None
                )
        except Exception as e:
            current_app.logger.warning(f"Falha ao agendar email: {e}")

        flash(f'Pagamento {venda.fatura_ref} validado! O produtor foi notificado.', 'success')

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"ERRO_ADMIN_VALIDACAO (ID: {id}): {e}")
        flash('Erro técnico ao processar a validação.', 'danger')

    return redirect(url_for('admin_dashboard.dashboard'))


@admin_pagamentos_bp.route('/confirmar-transferencia/<int:id>', methods=['POST'])
@login_required
@admin_required
def confirmar_transferencia(id):
    """O Admin confirma que já fez a transferência bancária para o IBAN do produtor."""
    try:
        venda = Transacao.query.with_for_update().get_or_404(id)

        if venda.status == status_to_value(TransactionStatus.ENTREGUE) and not venda.transferencia_concluida:
            venda.transferencia_concluida = True
            venda.status = status_to_value(TransactionStatus.FINALIZADO)
            venda.data_liquidacao = datetime.now(timezone.utc)
            
            db.session.add(LogAuditoria(
                usuario_id=current_user.id,
                acao="LIQUIDACAO_PRODUTOR",
                detalhes=f"Ref {venda.fatura_ref} liquidada.",
                ip=request.remote_addr
            ))

            db.session.add(Notificacao(
                usuario_id=venda.vendedor_id,
                mensagem=f"💵 Pagamento enviado para o seu IBAN (Ref: {venda.fatura_ref}).",
                link=url_for('produtor.dashboard')
            ))

            db.session.commit()
            flash("Liquidação concluída com sucesso!", "success")
        else:
            flash("Esta transação não está pronta para liquidação.", "warning")
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"ERRO LIQUIDACAO: {e}")
        flash("Erro ao processar liquidação.", "danger")

    return redirect(url_for('admin_dashboard.dashboard'))


@admin_pagamentos_bp.route('/rejeitar-pagamento/<int:id>', methods=['POST'])
@login_required
@admin_required
def rejeitar_pagamento(id):
    try:
        venda = Transacao.query.get_or_404(id)
        motivo = request.form.get('motivo', 'Não especificado')

        db.session.add(LogAuditoria(
            usuario_id=current_user.id,
            acao="REJEICAO_PAGAMENTO",
            detalhes=f"Rejeitou pagamento da Ref: {venda.fatura_ref}. Motivo: {motivo}",
            ip=request.remote_addr
        ))

        venda.status = status_to_value(TransactionStatus.AGUARDANDO_PAGAMENTO)
        venda.comprovativo_path = None

        db.session.add(Notificacao(
            usuario_id=venda.comprador_id,
            mensagem=f"❌ Pagamento Rejeitado ({venda.fatura_ref}). Motivo: {motivo}. Envie novo comprovativo.",
            link=url_for('comprador.dashboard')
        ))

        db.session.commit()
        flash('Pagamento rejeitado e log registado.', 'info')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro rejeitar pagamento: {e}")
        flash("Erro ao rejeitar pagamento.", "danger")

    return redirect(url_for('admin_dashboard.dashboard'))


@admin_pagamentos_bp.route('/gerir-taloes')
@login_required
@admin_required
def gerir_taloes():
    pendentes = Transacao.query.filter_by(status=status_to_value(TransactionStatus.ANALISE)).all()

    validados = Transacao.query.filter(
        Transacao.status.in_([
            status_to_value(TransactionStatus.ESCROW),
            status_to_value(TransactionStatus.ENVIADO),
            status_to_value(TransactionStatus.ENTREGUE),
            status_to_value(TransactionStatus.FINALIZADO)
        ])
    ).order_by(Transacao.data_criacao.desc()).all()

    return render_template('admin/gerir_taloes.html', pendentes=pendentes, validados=validados)


@admin_pagamentos_bp.route('/analisar-pagamento/<int:id>', methods=['GET'])
@login_required
@admin_required
def analisar_pagamento(id):
    venda = Transacao.query.get_or_404(id)
    comissao = venda.valor_total_pago * Decimal('0.05')
    valor_produtor = venda.valor_total_pago - comissao

    return render_template('admin/analisar.html',
                           venda=venda,
                           comissao=comissao,
                           valor_produtor=valor_produtor)


@admin_pagamentos_bp.route('/painel-pagamentos')
@login_required
@admin_required
def painel_pagamentos():
    pendentes_liquidacao = Transacao.query.filter_by(
        status=TransactionStatus.ENTREGUE,
        transferencia_concluida=False
    ).all()

    return render_template('admin/painel_pagamentos.html', pendentes=pendentes_liquidacao)


@admin_pagamentos_bp.route('/tesouraria')
@login_required
@admin_required
def painel_liquidacoes():
    vendas_pendentes = Transacao.query.filter_by(
        status=TransactionStatus.ENTREGUE,
        transferencia_concluida=False
    ).all()

    return render_template('admin/pagamentos.html', vendas=vendas_pendentes)


@admin_pagamentos_bp.route('/historico-financeiro')
@login_required
@admin_required
def historico_financeiro():
    taloes_validados = Transacao.query.filter(
        Transacao.status.in_([status_to_value(TransactionStatus.ESCROW), status_to_value(TransactionStatus.ENVIADO),
                             status_to_value(TransactionStatus.ENTREGUE), status_to_value(TransactionStatus.FINALIZADO)])
    ).order_by(Transacao.data_criacao.desc()).all()

    liquidacoes_concluidas = Transacao.query.filter_by(transferencia_concluida=True)\
        .order_by(Transacao.data_criacao.desc()).all()

    return render_template('admin/historico_financeiro.html',
                           taloes=taloes_validados,
                           liquidacoes=liquidacoes_concluidas)


@admin_pagamentos_bp.route('/pagamentos-pendentes')
@login_required
@admin_required
def pagamentos_pendentes():
    vendas_a_pagar = Transacao.query.filter_by(
        status=status_to_value(TransactionStatus.ENTREGUE),
        transferencia_concluida=False
    ).all()
    return render_template('admin/pagamentos.html', vendas=vendas_a_pagar)
