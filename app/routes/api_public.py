from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from app.models import Provincia, Municipio, Produto, Transacao

api_public_bp = Blueprint('api_public', __name__)

@api_public_bp.route('/api/transacao/<int:id>', methods=['GET'])
@login_required
def get_transacao_details(id):
    """Retorna os detalhes de uma transação se o user tiver permissão."""
    transacao = Transacao.query.get_or_404(id)
    
    # Verificação de permissão
    if current_user.id not in [transacao.comprador_id, transacao.vendedor_id] and current_user.tipo != 'admin':
        return jsonify({'ok': False, 'message': 'Acesso negado.'}), 403
        
    return jsonify({'ok': True, 'transacao': transacao.to_dict()})

@api_public_bp.route('/api/localizacao/provincias', methods=['GET'])
def get_provincias():
    provincias = Provincia.query.order_by(Provincia.nome).all()
    return jsonify({'ok': True, 'provincias': [p.to_dict() for p in provincias]})

@api_public_bp.route('/api/localizacao/municipios', methods=['GET'])
def get_municipios():
    from flask import request
    provincia_id = request.args.get('provincia_id')
    query = Municipio.query
    if provincia_id:
        query = query.filter_by(provincia_id=provincia_id)
    municipios = query.order_by(Municipio.nome).all()
    return jsonify({'ok': True, 'municipios': [m.to_dict() for m in municipios]})

@api_public_bp.route('/api/produtos/categorias', methods=['GET'])
def get_categorias():
    # Assumindo que Produto tem um campo categoria ou que Produto é a categoria
    produtos = Produto.query.order_by(Produto.nome).all()
    return jsonify({'ok': True, 'categorias': [p.to_dict() for p in produtos]})
