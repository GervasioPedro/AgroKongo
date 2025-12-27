from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import current_user, login_required
from extensions import db
from core.models import Usuario, Safra, Produto, Provincia, Interesse
from datetime import datetime

# Definimos o blueprint
mercado_bp = Blueprint('mercado', __name__)

@mercado_bp.route('/explorar')
def explorar():
    """
    Página principal do mercado para explorar safras disponíveis com filtros inteligentes.
    """
    # 1. Captura de Filtros e Pesquisa
    produto_id = request.args.get('produto', type=int)
    provincia_id = request.args.get('provincia', type=int)
    termo_pesquisa = request.args.get('q', '')

    # 2. Query Base
    # Usamos joinedload para carregar produto e produtor numa única consulta (mais rápido)
    query = Safra.query.filter_by(status='disponivel')

    # Filtro por Nome de Produto ou Categoria
    if termo_pesquisa:
        # Importante: Garantir que o join é feito corretamente
        query = query.join(Safra.produto).filter(Produto.nome.ilike(f'%{termo_pesquisa}%'))

    # Filtro por ID do Produto (Select de categorias)
    if produto_id:
        query = query.filter(Safra.produto_id == produto_id)

    # Filtro por Província
    if provincia_id:
        # Se já fizemos join com Usuario antes, o SQLAlchemy resolve,
        # mas aqui garantimos que filtramos pelo produtor da safra
        query = query.join(Safra.produtor).filter(Usuario.provincia_id == provincia_id)

    # 3. Execução
    # distinct() evita duplicados caso os joins se cruzem
    safras = query.order_by(Safra.data_publicacao.desc()).distinct().all()

    # 4. Dados para os Selects
    todos_produtos = Produto.query.order_by(Produto.nome).all()
    todas_provincias = Provincia.query.order_by(Provincia.nome).all()

    return render_template('mercado/explorar.html',
                           safras=safras,
                           produtos=todos_produtos,
                           provincias=todas_provincias,
                           termo=termo_pesquisa)


@mercado_bp.route('/manifestar-interesse/<int:safra_id>', methods=['POST'])
@login_required
def fazer_match(safra_id):
    # 1. Validação de Papel (Role)
    if current_user.tipo != 'comprador':
        flash('Apenas compradores podem negociar safras.', 'warning')
        return redirect(url_for('mercado.explorar'))

    # 2. Busca Segura
    safra = Safra.query.get_or_404(safra_id)

    try:
        # 3. Captura e Validação de Input
        quantidade_str = request.form.get('quantidade_pretendida', '').replace(',', '.')
        quantidade = float(quantidade_str)

        if quantidade <= 0:
            flash('A quantidade deve ser superior a zero.', 'warning')
            return redirect(url_for('mercado.detalhes_safra', safra_id=safra_id))

        if quantidade > safra.quantidade_kg:
            flash(f'Quantidade indisponível. Stock atual: {safra.quantidade_kg} kg.', 'danger')
            return redirect(url_for('mercado.detalhes_safra', safra_id=safra_id))

        # 4. Operação na Base de Dados com Proteção
        existente = Interesse.query.filter_by(
            comprador_id=current_user.id,
            safra_id=safra_id,
            status='pendente'
        ).first()

        if existente:
            existente.quantidade_pretendida = quantidade
            existente.data_criacao = datetime.utcnow()
            flash('O seu pedido de interesse foi atualizado.', 'info')
        else:
            novo_interesse = Interesse(
                comprador_id=current_user.id,
                safra_id=safra_id,
                quantidade_pretendida=quantidade,
                status='pendente'
            )
            db.session.add(novo_interesse)

        db.session.commit()
        flash(f'Pedido de {quantidade}kg enviado com sucesso!', 'success')
        return redirect(url_for('perfil.meu_perfil_comprador'))

    except ValueError:
        # Se o utilizador digitar letras em vez de números
        flash('Por favor, insira um número válido para a quantidade.', 'danger')
        return redirect(url_for('mercado.detalhes_safra', safra_id=safra_id))

    except Exception as e:
        # Erro genérico de base de dados ou sistema
        db.session.rollback()
        print(f"Erro Crítico: {e}")  # Log para si
        flash('Não foi possível processar o seu pedido agora. Tente novamente mais tarde.', 'danger')
        return redirect(url_for('mercado.detalhes_safra', safra_id=safra_id))

@mercado_bp.route('/safra/<int:safra_id>')
def detalhes_safra(safra_id):
    """Renderiza a página de detalhes de uma colheita específica."""
    safra = Safra.query.get_or_404(safra_id)
    # Note que agora usamos 'mercado/...' para coincidir com a pasta
    return render_template('mercado/detalhes_safra.html', safra=safra)