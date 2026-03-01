import uuid
from decimal import Decimal, InvalidOperation
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from sqlalchemy import func, or_
from app.extensions import db
from app.models import (
    Safra, Produto, Provincia, Transacao,
    Usuario, TransactionStatus
)

mercado_bp = Blueprint('mercado', __name__)


# --- 1. VITRINE PÚBLICA ---
@mercado_bp.route('/')
@mercado_bp.route('/explorar')
def explorar():
    """Vitrine com filtros geográficos e de categoria."""
    prov_id = request.args.get('provincia', type=int)
    cat_id = request.args.get('categoria', type=int)

    # Eager loading para evitar o problema de N+1 consultas no banco
    # Autorização: apenas safras de produtores validados são exibidas publicamente
    query = Safra.query.options(
        joinedload(Safra.produto),
        joinedload(Safra.produtor).joinedload(Usuario.provincia)
    ).join(Usuario).filter(
        Safra.status == 'disponivel',
        Safra.quantidade_disponivel > 0,
        Usuario.conta_validada == True  # Filtro de autorização
    )

    if prov_id:
        query = query.filter(Usuario.provincia_id == prov_id)
    if cat_id:
        query = query.filter(Safra.produto_id == cat_id)

    safras = query.order_by(Safra.id.desc()).all()

    return render_template('mercado/explorar.html',
                           safras=safras,
                           provincias=Provincia.query.all(),
                           categorias=Produto.query.all())


# --- 2. DETALHES E PERFIL ---
@mercado_bp.route('/safra/<int:id>')
def detalhes_safra(id):
    """Visualização detalhada de um lote específico."""
    safra = Safra.query.options(joinedload(Safra.produtor)).get_or_404(id)
    
    # Verificação de autorização: apenas safras de produtores validados são públicas
    if not safra.produtor.conta_validada:
        abort(404)
    
    # Verificação adicional: safra deve estar em estado visível
    if safra.status not in ['disponivel', 'esgotado']:
        abort(404)

    # Adicionamos a média de preço da região para ajudar o comprador
    media_regiao = db.session.query(func.avg(Safra.preco_por_unidade)).join(Usuario).filter(
        Safra.produto_id == safra.produto_id,
        Safra.status == 'disponivel',
        Usuario.conta_validada == True
    ).scalar() or safra.preco_por_unidade

    return render_template('mercado/detalhes.html',
                           safra=safra,
                           media_regiao=media_regiao)


@mercado_bp.route('/produtor/<int:user_id>')
def perfil_produtor(user_id):
    """Página pública do produtor com reputação e outros produtos."""
    produtor = Usuario.query.get_or_404(user_id)
    if produtor.tipo != 'produtor' or not produtor.conta_validada:
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
    if not current_user.conta_validada:
        flash('⚠️ A sua conta precisa de validação para realizar compras.', 'warning')
        return redirect(url_for('mercado.detalhes_safra', id=id))

    # Lock de linha para garantir que ninguém compra o mesmo quilo ao mesmo tempo
    safra = Safra.query.with_for_update().get_or_404(id)

    try:
        raw_qtd = request.form.get('quantidade', '0').replace(',', '.')
        quantidade = Decimal(raw_qtd)

        if quantidade <= 0 or quantidade > safra.quantidade_disponivel:
            flash(f"Quantidade indisponível (Máx: {safra.quantidade_disponivel}kg)", "danger")
            return redirect(url_for('mercado.detalhes_safra', id=id))

        # Criar referência única (AK-XXXXXX)
        ref = f"AK-{uuid.uuid4().hex[:6].upper()}"

        nova_reserva = Transacao(
            fatura_ref=ref,
            safra_id=safra.id,
            comprador_id=current_user.id,
            vendedor_id=safra.produtor_id,
            quantidade_comprada=quantidade,
            valor_total_pago=(quantidade * safra.preco_por_unidade).quantize(Decimal('0.01')),
            status=TransactionStatus.PENDENTE  # Aguarda confirmação do produtor
        )

        # Abate do stock imediato
        safra.quantidade_disponivel -= quantidade
        if safra.quantidade_disponivel <= 0:
            safra.status = 'esgotado'

        db.session.add(nova_reserva)
        db.session.commit()

        flash("✅ Reserva efetuada com sucesso!", "success")
        return redirect(url_for('comprador.minhas_reservas'))

    except (InvalidOperation, ValueError):
        db.session.rollback()
        flash("Erro: Introduza um número válido.", "danger")
        return redirect(url_for('mercado.detalhes_safra', id=id))


# --- 4. VALIDAÇÃO DE DOCUMENTOS (PÚBLICO) ---
@mercado_bp.route('/validar-fatura/<code>')
def validar_fatura(code):
    """Verifica a autenticidade de uma fatura via QR Code."""
    # Procura pela referência da fatura
    venda = Transacao.query.filter(Transacao.fatura_ref == code).first()

    if not venda:
        return render_template('mercado/validar_fatura.html', erro="Fatura não encontrada.")

    # Verificação de autorização: determinar nível de acesso ANTES de processar dados
    acesso_completo = False
    if current_user.is_authenticated:
        # Usuário autenticado: verifica se é parte da transação ou admin
        if current_user.id in [venda.comprador_id, venda.vendedor_id] or current_user.tipo == 'admin':
            acesso_completo = True
    
    if acesso_completo:
        # Acesso completo aos detalhes
        return render_template('mercado/validar_fatura.html', venda=venda, acesso_completo=True)
    
    # Acesso público: apenas validação básica (sem dados sensíveis)
    dados_publicos = {
        'fatura_ref': venda.fatura_ref,
        'status': venda.status,
        'data_criacao': venda.data_criacao,
        'valida': True
    }
    return render_template('mercado/validar_fatura.html', dados_publicos=dados_publicos, acesso_completo=False)



