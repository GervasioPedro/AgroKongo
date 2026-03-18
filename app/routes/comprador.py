import hashlib
import base64
import qrcode
from io import BytesIO
from datetime import datetime, timezone
from decimal import Decimal

from flask import (
    Blueprint, render_template, redirect, url_for,
    flash, request, current_app, abort, make_response
)
from flask_login import login_required, current_user
from sqlalchemy import func

from app.extensions import db
from app.models import (
    Transacao, Safra, Usuario, LogAuditoria,
    HistoricoStatus, Notificacao, Avaliacao, TransactionStatus
)
from app.utils.helpers import salvar_ficheiro
from app.utils.status_helper import status_to_value

comprador_bp = Blueprint('comprador', __name__)


# --- DASHBOARD CENTRALIZADO ---
@comprador_bp.route('/dashboard')
@login_required
def dashboard():
    """Painel do Comprador com métricas reais."""
    
    if current_user.tipo != 'comprador':
        flash("Acesso restrito a compradores.", "danger")
        return redirect(url_for('main.index'))

    # 1. Consultas Base (Filtradas pelo utilizador atual)
    query = Transacao.query.filter_by(comprador_id=current_user.id)

    # 2. Categorização para as Tabs
    # Tab 1: Aguardando Ações (Pendente de aceite ou Pagamento)
    pendentes = query.filter(Transacao.status.in_([
        status_to_value(TransactionStatus.PENDENTE),
        status_to_value(TransactionStatus.AGUARDANDO_PAGAMENTO)
    ])).all()

    # Tab 2: Em Trânsito (Pago, Em Análise ou Enviado)
    em_transito = query.filter(Transacao.status.in_([
        status_to_value(TransactionStatus.ANALISE),
        status_to_value(TransactionStatus.ESCROW),
        status_to_value(TransactionStatus.ENVIADO)
    ])).order_by(Transacao.data_envio.desc()).all()

    # Tab 3: Histórico (Entregue, Finalizada ou Cancelada)
    historico = query.filter(Transacao.status.in_([
        status_to_value(TransactionStatus.ENTREGUE),
        status_to_value(TransactionStatus.FINALIZADO),
        status_to_value(TransactionStatus.CANCELADO),
        status_to_value(TransactionStatus.DISPUTA)
    ])).order_by(Transacao.data_entrega.desc()).all()

    # 3. KPIs do Comprador
    # Total Gasto: Inclui tudo que já foi pago (ESCROW, ENVIADO, ENTREGUE, FINALIZADO)
    total_gasto = db.session.query(func.sum(Transacao.valor_total_pago)).filter(
        Transacao.comprador_id == current_user.id,
        Transacao.status.in_([
            status_to_value(TransactionStatus.ESCROW),
            status_to_value(TransactionStatus.ENVIADO),
            status_to_value(TransactionStatus.ENTREGUE),
            status_to_value(TransactionStatus.FINALIZADO)
        ])
    ).scalar() or 0

    compras_ativas = query.filter(Transacao.status != status_to_value(TransactionStatus.FINALIZADO)).count()

    return render_template('painel/comprador.html',
                           pendentes=pendentes,
                           em_transito=em_transito,
                           historico=historico,
                           total_gasto=total_gasto,
                           compras_ativas=compras_ativas)


# --- GESTÃO DE RESERVAS (ANTES DO PAGAMENTO) ---
@comprador_bp.route('/minhas-reservas')
@login_required
def minhas_reservas():
    """Lista apenas o que precisa de ação imediata (confirmar stock ou pagar)."""
    transacoes = Transacao.query.filter(
        Transacao.comprador_id == current_user.id,
        Transacao.status.in_([status_to_value(TransactionStatus.PENDENTE), status_to_value(TransactionStatus.AGUARDANDO_PAGAMENTO)])
    ).order_by(Transacao.data_criacao.desc()).all()
    return render_template('comprador/minhas_reservas.html', transacoes=transacoes)


@comprador_bp.route('/pagar-reserva/<int:trans_id>')
@login_required
def pagar_reserva(trans_id):
    """Página com o IBAN da AgroKongo e formulário de upload."""
    venda = Transacao.query.get_or_404(trans_id)

    if venda.comprador_id != current_user.id:
        abort(403)

    if venda.status == status_to_value(TransactionStatus.PENDENTE):
        flash("Aguarde a confirmação de stock pelo produtor antes de pagar.", "warning")
        return redirect(url_for('comprador.minhas_reservas'))

    if venda.status != status_to_value(TransactionStatus.AGUARDANDO_PAGAMENTO):
        flash("Esta transação já não se encontra em fase de pagamento.", "info")
        return redirect(url_for('comprador.minhas_compras'))

    return render_template('comprador/pagar_reserva.html', transacao=venda)


@comprador_bp.route('/submeter-comprovativo/<int:trans_id>', methods=['POST'])
@login_required
def submeter_comprovativo(trans_id):
    """Único ponto de entrada para talões bancários."""
    try:
        venda = Transacao.query.with_for_update().get_or_404(trans_id)

        if venda.comprador_id != current_user.id:
            abort(403)
            
        if venda.status != status_to_value(TransactionStatus.AGUARDANDO_PAGAMENTO):
             flash("O estado desta encomenda não permite envio de comprovativo.", "warning")
             return redirect(url_for('comprador.dashboard'))

        ficheiro = request.files.get('comprovativo')
        if not ficheiro:
            flash("Por favor, selecione o ficheiro do comprovativo.", "warning")
            return redirect(url_for('comprador.pagar_reserva', trans_id=trans_id))

        nome_foto = salvar_ficheiro(ficheiro, subpasta='comprovativos', privado=True)

        if nome_foto:
            venda.comprovativo_path = nome_foto
            venda.mudar_status(status_to_value(TransactionStatus.ANALISE), "Comprovativo enviado pelo comprador")

            db.session.add(LogAuditoria(
                usuario_id=current_user.id,
                acao="COMPROVATIVO_UPLOAD",
                detalhes=f"Ref: {venda.fatura_ref} | File: {nome_foto}",
                ip=request.remote_addr
            ))

            db.session.commit()
            flash("Talão enviado! O Admin validará o pagamento em breve.", "success")
            return redirect(url_for('comprador.dashboard')) # Redirecionar para dashboard é melhor UX
        else:
            flash("Formato de ficheiro inválido.", "danger")
            return redirect(url_for('comprador.pagar_reserva', trans_id=trans_id))

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro no upload comprovativo {trans_id}: {e}")
        flash("Erro técnico ao processar ficheiro.", "danger")
        return redirect(url_for('comprador.pagar_reserva', trans_id=trans_id))


# --- GESTÃO DE COMPRAS ATIVAS (PÓS-PAGAMENTO) ---
@comprador_bp.route('/minhas-compras')
@login_required
def minhas_compras():
    """Acompanhamento de logística e entregas."""
    status_compras = [
        status_to_value(TransactionStatus.ANALISE), status_to_value(TransactionStatus.ESCROW),
        status_to_value(TransactionStatus.ENVIADO), status_to_value(TransactionStatus.ENTREGUE),
        status_to_value(TransactionStatus.FINALIZADO), status_to_value(TransactionStatus.DISPUTA)
    ]
    compras = Transacao.query.filter(
        Transacao.comprador_id == current_user.id,
        Transacao.status.in_(status_compras)
    ).order_by(Transacao.data_criacao.desc()).all()

    return render_template('comprador/minhas_compras.html', compras=compras)


@comprador_bp.route('/confirmar-recebimento/<int:trans_id>', methods=['POST'])
@login_required
def confirmar_recebimento(trans_id):
    """O comprador confirma a chegada da mercadoria. Saldo fica em custódia até o admin liberar."""
    
    try:
        # Locking para evitar cliques duplos
        transacao = Transacao.query.with_for_update().get_or_404(trans_id)

        # Segurança: Apenas o comprador dono da transação pode confirmar
        if transacao.comprador_id != current_user.id:
            abort(403)

        # Só se pode confirmar o que foi enviado
        if transacao.status != status_to_value(TransactionStatus.ENVIADO):
            flash("Esta encomenda não está em estado de receção (deve estar 'Enviada').", "warning")
            return redirect(url_for('comprador.dashboard'))

        # Muda para ENTREGUE (ainda NÃO libera saldo!)
        transacao.mudar_status(status_to_value(TransactionStatus.ENTREGUE), "Entrega confirmada pelo comprador")
        transacao.data_entrega = datetime.now(timezone.utc)
        # NOTA: data_liquidacao será definida apenas quando o admin aprovar a transferência

        db.session.add(LogAuditoria(
            usuario_id=current_user.id,
            acao="ENTREGA_CONFIRMADA",
            detalhes=f"Ref: {transacao.fatura_ref}",
            ip=request.remote_addr
        ))
        
        # Notificar Admin para aprovar transferência
        db.session.add(Notificacao(
            usuario_id=current_user.id,  # Admin será notificado
            mensagem=f"📦 Entrega confirmada na fatura {transacao.fatura_ref}. Aguarde aprovação para liberação do saldo.",
            link=url_for('admin_dashboard.dashboard')
        ))

        db.session.commit()
        flash("Recebimento confirmado! O administrador irá liberar o saldo ao produtor.", "success")

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"ERRO_RECEBIMENTO: {e}")
        flash("Erro ao processar a confirmação.", "danger")

    return redirect(url_for('comprador.dashboard'))

@comprador_bp.route('/avaliar/<int:trans_id>', methods=['POST'])
@login_required
def avaliar_venda(trans_id):
    venda = Transacao.query.get_or_404(trans_id)
    if venda.comprador_id != current_user.id:
        flash("Ação não permitida.", "danger")
        return redirect(url_for('comprador.minhas_compras'))
        
    if venda.avaliacao:
        flash("Já avaliou esta compra.", "warning")
        return redirect(url_for('comprador.minhas_compras'))

    try:
        estrelas = int(request.form.get('estrelas', 5))
        nova_av = Avaliacao(
            transacao_id=venda.id,
            nota=estrelas, # Corrigido para corresponder ao modelo (nota vs estrelas)
            comentario=request.form.get('comentario')
        )
        db.session.add(nova_av)
        
        # Atualizar rating do vendedor (Média simples)
        vendedor = venda.vendedor
        # Recalcular média (simplificado, idealmente seria uma query agregada)
        # Assumindo que queremos atualizar o rating no user
        # ... Lógica de calculo de rating pode ser complexa, para já apenas notificamos
        
        db.session.add(Notificacao(
            usuario_id=venda.vendedor_id,
            mensagem=f"⭐ Recebeste {estrelas} estrelas na venda {venda.fatura_ref}!",
            link=url_for('produtor.vendas')
        ))
        db.session.commit()
        flash("Obrigado pela sua avaliação!", "success")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao avaliar: {e}")
        flash("Erro ao submeter avaliação.", "danger")

    return redirect(url_for('comprador.minhas_compras'))


@comprador_bp.route('/abrir-disputa/<int:trans_id>', methods=['POST'])
@login_required
def abrir_disputa(trans_id):
    try:
        venda = Transacao.query.with_for_update().get_or_404(trans_id)
        if venda.comprador_id != current_user.id: abort(403)

        # Só pode abrir disputa se não estiver finalizada (dinheiro já entregue)
        if venda.status not in [status_to_value(TransactionStatus.FINALIZADO), status_to_value(TransactionStatus.CANCELADO)]:
            venda.mudar_status(status_to_value(TransactionStatus.DISPUTA), "Disputa aberta pelo comprador")
            
            db.session.add(LogAuditoria(
                usuario_id=current_user.id,
                acao="DISPUTA_ABERTA",
                detalhes=f"Ref: {venda.fatura_ref}",
                ip=request.remote_addr
            ))
            
            # Notificar Admin e Produtor
            db.session.add(Notificacao(
                usuario_id=venda.vendedor_id,
                mensagem=f"⚠️ O comprador abriu uma disputa na venda {venda.fatura_ref}.",
                link=url_for('produtor.vendas')
            ))
            
            db.session.commit()
            flash("Disputa aberta. A equipa de suporte entrará em contacto.", "warning")
        else:
             flash("Não é possível abrir disputa para uma transação finalizada ou cancelada.", "danger")
             
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao abrir disputa: {e}")
        flash("Erro ao processar pedido de disputa.", "danger")

    return redirect(url_for('comprador.dashboard'))

@comprador_bp.route('/encomenda/<int:id>')
@login_required
def encomenda_detalhe(id):
    """Detalhes de uma encomenda específica (Rota para redirecionamento do mercado)."""
    compra = Transacao.query.get_or_404(id)
    if compra.comprador_id != current_user.id:
        abort(403)
    return render_template('comprador/detalhes_compra.html', compra=compra)