from flask import Blueprint, jsonify, request, current_app
from app.extensions import db

mercado_api_bp = Blueprint('mercado_api', __name__, url_prefix='/api/mercado')


def _safra_to_json(s):
    try:
        return {
            'id': getattr(s, 'id', None),
            'produto': {'nome': getattr(getattr(s, 'produto', None), 'nome', None)},
            'quantidade_disponivel': float(getattr(s, 'quantidade_disponivel', 0) or 0),
            'preco_por_unidade': float(getattr(s, 'preco_por_unidade', 0) or 0),
            'produtor': {
                'nome': getattr(getattr(s, 'produtor', None), 'nome', None),
                'provincia': {
                    'nome': getattr(getattr(getattr(s, 'produtor', None), 'provincia', None), 'nome', None)
                }
            },
            'imagem': getattr(s, 'imagem_url', None) or getattr(s, 'imagem', None),
            'status': getattr(getattr(s, 'status', None), 'name', None) or 'disponivel',
        }
    except Exception:
        return {
            'id': getattr(s, 'id', None),
            'produto': {'nome': None},
            'quantidade_disponivel': 0,
            'preco_por_unidade': 0,
            'produtor': {'nome': None, 'provincia': {'nome': None}},
            'imagem': None,
            'status': 'disponivel',
        }


@mercado_api_bp.route('/safras', methods=['GET'])
def listar_safras():
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 24))
        # Import local para evitar ciclos
        try:
            from app.models import Safra
            query = Safra.query
            # se existir campo 'ativa' ou 'status', tentar filtrar
            if hasattr(Safra, 'ativa'):
                query = query.filter_by(ativa=True)
            items = query.order_by(getattr(Safra, 'id')).paginate(page=page, per_page=per_page, error_out=False).items
            return jsonify({'safras': [_safra_to_json(s) for s in items]})
        except Exception as e:
            current_app.logger.warning(f"Mercado API fallback (sem modelos): {e}")
            return jsonify({'safras': []})
    except Exception as e:
        current_app.logger.error(f"Erro /api/mercado/safras: {e}")
        return jsonify({'safras': []})


@mercado_api_bp.route('/safra/<int:safra_id>', methods=['GET'])
def obter_safra(safra_id: int):
    try:
        from app.models import Safra
        s = Safra.query.get(safra_id)
        if not s:
            return jsonify({'erro': 'Safra não encontrada'}), 404
        data = _safra_to_json(s)
        data.update({
            'descricao': getattr(s, 'descricao', None),
            'imagens': getattr(s, 'imagens', []) if hasattr(s, 'imagens') else []
        })
        return jsonify(data)
    except Exception as e:
        current_app.logger.error(f"Erro /api/mercado/safra/{safra_id}: {e}")
        return jsonify({'erro': 'Não foi possível obter a safra'}), 404
