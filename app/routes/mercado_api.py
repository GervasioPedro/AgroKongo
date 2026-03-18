from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Safra, Produto, Usuario
from app.services.transaction_service import TransactionService
from app.utils.decorators import kyc_required
from sqlalchemy.orm import joinedload

# Blueprint para a API do Mercado
mercado_api_bp = Blueprint('mercado_api', __name__)

@mercado_api_bp.route('/safras', methods=['GET'])
def get_safras():
    """
    Endpoint para listar todas as safras disponíveis, com filtros.
    Rota: GET /api/market/safras
    """
    try:
        # Extrair query params
        q = request.args.get('q', '', type=str)
        provincia_id = request.args.get('provincia_id', type=int)
        categoria_id = request.args.get('categoria_id', type=int)
        page = request.args.get('page', 1, type=int)
        per_page = 12 

        query = Safra.query.options(
            joinedload(Safra.produto),
            joinedload(Safra.produtor).joinedload(Usuario.provincia),
            joinedload(Safra.produtor).joinedload(Usuario.municipio)
        ).filter(
            Safra.status == 'disponivel',
            Safra.quantidade_disponivel > 0
        )

        if q:
            query = query.join(Produto).join(Usuario).filter(
                (Produto.nome.ilike(f'%{q}%')) |
                (Usuario.nome.ilike(f'%{q}%'))
            )
        if provincia_id:
            query = query.join(Usuario).filter(Usuario.provincia_id == provincia_id)
        if categoria_id:
            query = query.filter(Safra.produto_id == categoria_id)

        pagination = query.order_by(Safra.data_criacao.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        safras = pagination.items
        safras_dict = [safra.to_dict() for safra in safras]

        return jsonify({
            "success": True,
            "data": safras_dict,
            "meta": {
                "page": pagination.page,
                "per_page": pagination.per_page,
                "total_pages": pagination.pages,
                "total_items": pagination.total
            }
        }), 200

    except Exception as e:
        return jsonify({"success": False, "errors": [str(e)]}), 500


@mercado_api_bp.route('/safras/<int:id>', methods=['GET'])
def get_safra_detalhe(id):
    """
    Endpoint para detalhes de uma safra.
    Rota: GET /api/market/safras/<id>
    """
    try:
        safra = Safra.query.options(
            joinedload(Safra.produto),
            joinedload(Safra.produtor).joinedload(Usuario.provincia)
        ).get(id)

        if not safra:
            return jsonify({"success": False, "errors": ["Safra não encontrada"]}), 404

        return jsonify({
            "success": True,
            "data": safra.to_dict()
        }), 200

    except Exception as e:
        return jsonify({"success": False, "errors": [str(e)]}), 500


@mercado_api_bp.route('/buy', methods=['POST', 'OPTIONS'])
@jwt_required() # Requer Token JWT válido
@kyc_required() # Requer conta validada pelo Admin
def buy_safra():
    """
    Endpoint para comprar uma safra.
    Rota: POST /api/market/buy
    Body: { "safra_id": 1, "quantidade": 10 }
    """
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "errors": ["JSON inválido"]}), 400

        safra_id = data.get('safra_id')
        quantidade = data.get('quantidade')

        if not safra_id or not quantidade:
            return jsonify({"success": False, "errors": ["safra_id e quantidade são obrigatórios"]}), 400

        # Obter ID do utilizador autenticado via JWT
        comprador_id = get_jwt_identity()

        # Chamar Serviço de Transação
        sucesso, resultado = TransactionService.criar_reserva(safra_id, comprador_id, quantidade)

        if sucesso:
            return jsonify({
                "success": True,
                "message": "Reserva efetuada com sucesso!",
                "data": resultado.to_dict()
            }), 201
        else:
            return jsonify({
                "success": False,
                "errors": [resultado] # resultado contém a mensagem de erro
            }), 400

    except Exception as e:
        return jsonify({"success": False, "errors": [str(e)]}), 500