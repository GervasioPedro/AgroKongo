import uuid
from decimal import Decimal, InvalidOperation
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from sqlalchemy import func, or_
from app.extensions import db
from app.models import (
    Safra, Produto, Provincia, Transacao,
    Usuario, TransactionStatus, LogAuditoria
)
from app.utils.status_helper import status_to_value

mercado_bp = Blueprint('mercado', __name__)


# --- 1. VITRINE PÚBLICA ---
@mercado_bp.route('/')
@mercado_bp.route('/explorar')
def explorar():
    """Vitrine com filtros geográficos e de categoria."""
    prov_id = request.args.get('provincia', type=int)
    cat_id = request.args.get('categoria', type=int)
    termo = request.args.get('q', '').strip()

    # Eager loading para evitar o problema de N+1 consultas no banco
    query = Safra.query.options(
        joinedload(Safra.produto),
        joinedload(Safra.produtor).joinedload(Usuario.provincia)
    ).filter(Safra.status == 'disponivel', Safra.quantidade_disponivel > 0)

    if prov_id:
        query = query.join(Usuario).filter(Usuario.provincia_id == prov_id)
    if cat_id:
        query = query.filter(Safra.produto_id == cat_id)
    if termo:
        # Busca por nome do produto ou nome do produtor
        query = query.join(Produto).filter(
            or_(
                Produto.nome.ilike(f'%{termo}%'),
                Usuario.nome.ilike(f'%{termo}%')
            )
        )

    # Paginação para não carregar tudo de uma vez
    page = request.args.get('page', 1, type=int)
    per_page = 12
    pagination = query.order_by(Safra.data_criacao.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    safras = pagination.items

    return render_template('mercado/explorar.html',
                           safras=safras,
                           pagination=pagination,
                           provincias=Provincia.query.all(),
                           categorias=Produto.query.all(),
                           termo=termo,
                           selected_prov=prov_id,
                           selected_cat=cat_id)


# --- 2. DETALHES E PERFIL ---
@mercado_bp.route('/safra/<int:id>')
def detalhes_safra(id):
    """Visualização detalhada de um lote específico."""
    safra = Safra.query.options(
        joinedload(Safra.produtor), 
        joinedload(Safra.produto)
    ).get_or_404(id)

    # Adicionamos a média de preço da região para ajudar o comprador
    media_regiao = db.session.query(func.avg(Safra.preco_por_unidade)).filter(
        Safra.produto_id == safra.produto_id,
        Safra.status == 'disponivel',
        Safra.id != safra.id # Excluir o próprio da média
    ).scalar()
    
    if media_regiao is None:
        media_regiao = safra.preco_por_unidade

    return render_template('mercado/detalhes.html',
                           safra=safra,
                           media_regiao=media_regiao)


@mercado_bp.route('/produtor/<int:user_id>')
def perfil_produtor(user_id):
    """Página pública do produtor com reputação e outros produtos."""
    produtor = Usuario.query.get_or_404(user_id)
    if produtor.tipo != 'produtor':
        abort(404)

    safras_ativas = Safra.query.filter_by(produtor_id=user_id, status='disponivel').all()

    return render_template('mercado/perfil_produtor.html',
                           produtor=produtor,
                           safras=safras_ativas)


# --- 3. INÍCIO DO FLUXO DE COMPRA ---
@mercado_bp.route('/safra/<int:id>/encomendar', methods=['POST'])
@login_required
def iniciar_encomenda(id):
    """Cria a reserva inicial e bloqueia o stock."""
    
    # 1. Validações Prévias
    if current_user.tipo == 'produtor':
        flash('Produtores não podem comprar safras. Registe uma conta de Comprador.', 'warning')
        return redirect(url_for('mercado.detalhes_safra', id=id))

    if not current_user.conta_validada and not current_user.perfil_completo:
        flash('⚠️ Complete o seu perfil para realizar compras.', 'warning')
        return redirect(url_for('main.perfil'))

    try:
        # Uso de transação explícita para garantir integridade
        with db.session.begin_nested():
            # Lock de linha (FOR UPDATE) para evitar race conditions no stock
            safra = Safra.query.with_for_update().get_or_404(id)

            # Auto-compra não permitida (redundante com verificação de tipo, mas seguro)
            if safra.produtor_id == current_user.id:
                flash('Não pode comprar a sua própria safra.', 'danger')
                return redirect(url_for('mercado.detalhes_safra', id=id))

            raw_qtd = request.form.get('quantidade', '0').replace(',', '.')
            try:
                quantidade = Decimal(raw_qtd)
            except InvalidOperation:
                flash("Quantidade inválida.", "danger")
                return redirect(url_for('mercado.detalhes_safra', id=id))

            if quantidade <= 0:
                flash("A quantidade deve ser maior que zero.", "danger")
                return redirect(url_for('mercado.detalhes_safra', id=id))

            if quantidade > safra.quantidade_disponivel:
                flash(f"Quantidade indisponível. Máximo: {safra.quantidade_disponivel}kg", "danger")
                return redirect(url_for('mercado.detalhes_safra', id=id))

            valor_total = (quantidade * safra.preco_por_unidade).quantize(Decimal('0.01'))

            # Criação da Transação
            nova_reserva = Transacao(
                safra_id=safra.id,
                comprador_id=current_user.id,
                vendedor_id=safra.produtor_id,
                quantidade_comprada=quantidade,
                valor_total_pago=valor_total,
                status=status_to_value(TransactionStatus.PENDENTE)
            )
            # O __init__ da Transacao já gera a fatura_ref e calcula comissões

            # Abate do stock imediato
            safra.quantidade_disponivel -= quantidade
            if safra.quantidade_disponivel <= 0:
                safra.status = 'esgotado'

            db.session.add(nova_reserva)
            
            # Registo de Histórico
            nova_reserva.mudar_status(status_to_value(TransactionStatus.PENDENTE), "Reserva criada pelo comprador.")
            
            # Log de Auditoria
            db.session.add(LogAuditoria(
                usuario_id=current_user.id,
                acao="COMPRA_INICIADA",
                detalhes=f"Ref: {nova_reserva.fatura_ref} | Qtd: {quantidade} | Safra: {safra.id}",
                ip=request.remote_addr
            ))

        # Commit é feito automaticamente ao sair do bloco with se não houver erro
        db.session.commit()

        flash(f"✅ Reserva {nova_reserva.fatura_ref} efetuada! Aguarde a confirmação do produtor.", "success")
        # Redirecionar para detalhes da encomenda (assumindo rota existente ou usando lista)
        return redirect(url_for('comprador.encomenda_detalhe', id=nova_reserva.id)) 
        # Nota: Se 'comprador.encomenda_detalhe' não existir, usar 'comprador.minhas_reservas'

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"ERRO COMPRA: {str(e)}")
        flash("Ocorreu um erro ao processar a encomenda. Tente novamente.", "danger")
        return redirect(url_for('mercado.detalhes_safra', id=id))


# --- 4. VALIDAÇÃO DE DOCUMENTOS (PÚBLICO) ---
@mercado_bp.route('/validar-fatura/<code>')
def validar_fatura(code):
    """Verifica a autenticidade de uma fatura via QR Code."""
    # Procura pela referência da fatura (case insensitive para melhor UX)
    venda = Transacao.query.filter(func.lower(Transacao.fatura_ref) == func.lower(code)).first()

    if not venda:
        return render_template('mercado/validar_fatura.html', erro="Fatura não encontrada ou código inválido.")

    return render_template('mercado/validar_fatura.html', venda=venda)