"""
Blueprint para API v1 com Versionamento
遵循 RESTful API best practices para AgroKongo
"""
from flask import Blueprint, jsonify, request, current_app
from app.extensions import cache, db
from app.models import Usuario, Transacao, Safra, Produto
from flask_login import login_required, current_user
from datetime import datetime, timezone
import hashlib

api_v1_bp = Blueprint('api_v1', __name__, url_prefix='/api/v1')


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def api_response(data=None, message=None, status=200, meta=None):
    """Resposta padronizada para API v1"""
    response = {
        'success': 200 <= status < 300,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'version': '1.0',
    }
    
    if message:
        response['message'] = message
    
    if data is not None:
        response['data'] = data
        
    if meta:
        response['meta'] = meta
    
    return jsonify(response), status


def api_error(message, status=400, error_code=None):
    """Resposta de erro padronizada para API v1"""
    response = {
        'success': False,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'version': '1.0',
        'error': {
            'message': message,
            'code': error_code or f'ERR_{status}'
        }
    }
    return jsonify(response), status


# =============================================================================
# HEALTH & INFO ENDPOINTS
# =============================================================================

@api_v1_bp.route('/health', methods=['GET'])
@cache.cached(timeout=60)
def health_check():
    """Health check da API v1"""
    return api_response({
        'status': 'healthy',
        'api_version': '1.0',
        'database': 'connected'
    })


@api_v1_bp.route('/info', methods=['GET'])
def api_info():
    """Informação sobre a API"""
    from app.models.base import TransactionStatus
    
    return api_response({
        'name': 'AgroKongo API',
        'version': '1.0',
        'description': 'API para marketplace agrícola angolano',
        'endpoints': {
            'auth': '/api/v1/auth',
            'produtores': '/api/v1/produtores',
            'produtos': '/api/v1/produtos',
            'transacoes': '/api/v1/transacoes',
            'safras': '/api/v1/safras',
        },
        'status_options': {
            'transacao': list(TransactionStatus.__dict__.keys())
        }
    })


# =============================================================================
# PRODUTOS
# =============================================================================

@api_v1_bp.route('/produtos', methods=['GET'])
@cache.cached(timeout=300)
def listar_produtos():
    """Lista produtos disponíveis"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)
    categoria = request.args.get('categoria')
    
    query = Produto.query.filter_by(ativo=True)
    
    if categoria:
        query = query.filter_by(categoria=categoria)
    
    pagination = query.order_by(Produto.data_criacao.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return api_response(
        data=[p.to_dict() for p in pagination.items],
        meta={
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    )


@api_v1_bp.route('/produtos/<int:produto_id>', methods=['GET'])
@cache.cached(timeout=300)
def detalhes_produto(produto_id):
    """Detalhes de um produto"""
    produto = Produto.query.get_or_404(produto_id)
    return api_response(data=produto.to_dict())


# =============================================================================
# SAFRAS
# =============================================================================

@api_v1_bp.route('/safras', methods=['GET'])
@cache.cached(timeout=300)
def listar_safras():
    """Lista safras disponíveis no mercado"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)
    provincia_id = request.args.get('provincia', type=int)
    produto_id = request.args.get('produto', type=int)
    
    query = Safra.query.filter_by(ativa=True)
    
    if provincia_id:
        query = query.filter_by(provincia_id=provincia_id)
    if produto_id:
        query = query.filter_by(produto_id=produto_id)
    
    pagination = query.order_by(Safra.data_criacao.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return api_response(
        data=[s.to_dict() for s in pagination.items],
        meta={
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages
        }
    )


@api_v1_bp.route('/safras/<int:safra_id>', methods=['GET'])
def detalhes_safra(safra_id):
    """Detalhes de uma safra"""
    safra = Safra.query.get_or_404(safra_id)
    return api_response(data=safra.to_dict())


# =============================================================================
# PRODUTORES
# =============================================================================

@api_v1_bp.route('/produtores', methods=['GET'])
def listar_produtores():
    """Lista produtores disponíveis"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)
    
    query = Usuario.query.filter_by(tipo='produtor', ativo=True, conta_validada=True)
    
    pagination = query.order_by(Usuario.vendas_concluidas.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Dados públicos do produtor
    produtores = [{
        'id': p.id,
        'nome': p.nome,
        'provincia': p.provincia.nome if p.provincia else None,
        'municipio': p.municipio.nome if p.municipio else None,
        'foto_perfil': p.foto_perfil,
        'vendas_concluidas': p.vendas_concluidas,
        'principal_cultura': p.principal_cultura,
    } for p in pagination.items]
    
    return api_response(
        data=produtores,
        meta={
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages
        }
    )


@api_v1_bp.route('/produtores/<int:produtor_id>', methods=['GET'])
def detalhes_produtor(produtor_id):
    """Perfil público de um produtor"""
    produtor = Usuario.query.filter_by(
        id=produtor_id, 
        tipo='produtor', 
        ativo=True
    ).first_or_404()
    
    return api_response(data={
        'id': produtor.id,
        'nome': produtor.nome,
        'provincia': produtor.provincia.nome if produtor.provincia else None,
        'municipio': produtor.municipio.nome if produtor.municipio else None,
        'foto_perfil': produtor.foto_perfil,
        'vendas_concluidas': produtor.vendas_concluidas,
        'principal_cultura': produtor.principal_cultura,
        'experiencia_anos': produtor.experiencia_anos,
        'certificacoes': produtor.certificacoes,
    })


# =============================================================================
# TRANSAÇÕES (protegidas)
# =============================================================================

@api_v1_bp.route('/transacoes', methods=['GET'])
@login_required
def listar_transacoes():
    """Lista transações do utilizador atual"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    
    # Usuário pode ver suas transações como comprador ou vendedor
    query = Transacao.query.filter(
        (Transacao.comprador_id == current_user.id) | 
        (Transacao.vendedor_id == current_user.id)
    )
    
    if status:
        query = query.filter_by(status=status)
    
    pagination = query.order_by(Transacao.data_criacao.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return api_response(
        data=[t.to_dict() for t in pagination.items],
        meta={
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages
        }
    )


@api_v1_bp.route('/transacoes/<int:transacao_id>', methods=['GET'])
@login_required
def detalhes_transacao(transacao_id):
    """Detalhes de uma transação"""
    transacao = Transacao.query.get_or_404(transacao_id)
    
    # Verificar acesso
    if transacao.comprador_id != current_user.id and transacao.vendedor_id != current_user.id:
        if not current_user.is_admin:
            return api_error('Acesso negado', 403, 'ERR_ACCESS_DENIED')
    
    return api_response(data=transacao.to_dict())


# =============================================================================
# ESTATÍSTICAS PÚBLICAS
# =============================================================================

@api_v1_bp.route('/estatisticas', methods=['GET'])
@cache.cached(timeout=600)
def estatisticas():
    """Estatísticas públicas do marketplace"""
    
    # Usar cache para evitar queries frequentes
    stats_cache = cache.get('marketplace_stats')
    
    if stats_cache:
        return api_response(data=stats_cache)
    
    # Calcular estatísticas
    from sqlalchemy import func
    from app.models import Transacao, Safra, Usuario
    
    total_produtores = Usuario.query.filter_by(
        tipo='produtor', 
        ativo=True, 
        conta_validada=True
    ).count()
    
    total_safras = Safra.query.filter_by(ativa=True).count()
    
    total_transacoes = Transacao.query.filter_by(
        status='finalizada'
    ).count()
    
    # Valor total transacionado
    valor_total = db.session.query(func.sum(Transacao.valor_total)).filter_by(
        status='finalizada'
    ).scalar() or 0
    
    stats = {
        'produtores_ativos': total_produtores,
        'safras_disponiveis': total_safras,
        'transacoes_concluidas': total_transacoes,
        'valor_total_transacionado': float(valor_total),
    }
    
    # Cache por 10 minutos
    cache.set('marketplace_stats', stats, timeout=600)
    
    return api_response(data=stats)


# =============================================================================
# PREÇOS MÉDIOS
# =============================================================================

@api_v1_bp.route('/precos-medios', methods=['GET'])
@cache.cached(timeout=3600)
def precos_medios():
    """Preços médios por produto"""
    from sqlalchemy import func
    from app.models import Transacao, Safra
    
    # Calcular preço médio por produto em transações finalizadas
    precos = db.session.query(
        Safra.produto_id,
        Produto.nome.label('produto_nome'),
        func.avg(Transacao.valor_total / Transacao.quantidade).label('preco_medio'),
        func.count(Transacao.id).label('total_transacoes')
    ).join(
        Transacao, Safra.id == Transacao.safra_id
    ).join(
        Produto, Safra.produto_id == Produto.id
    ).filter(
        Transacao.status == 'finalizada'
    ).group_by(
        Safra.produto_id, Produto.nome
    ).all()
    
    return api_response(data=[{
        'produto_id': p.produto_id,
        'produto': p.produto_nome,
        'preco_medio_kg': float(p.preco_medio or 0),
        'total_transacoes': p.total_transacoes
    } for p in precos])
