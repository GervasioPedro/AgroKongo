from flask import Blueprint, jsonify
from flask_login import login_required, current_user

comprador_api_bp = Blueprint('comprador_api', __name__, url_prefix='/api/comprador')


@comprador_api_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    """Retorna dados mínimos esperados pelo frontend do dashboard do comprador."""
    try:
        from app.models import Transacao
        # Busca últimas 20 transações do comprador atual, se o modelo existir
        txs = (Transacao.query
               .filter_by(comprador_id=current_user.id)
               .order_by(Transacao.data_criacao.desc())
               .limit(20)
               .all())
        compras = []
        for t in txs:
            compras.append({
                'id': getattr(t, 'id', None),
                'fatura_ref': getattr(t, 'fatura_ref', None),
                'status': (getattr(getattr(t, 'status', None), 'name', None) or 'pendente').lower(),
                'safra': {
                    'produto': getattr(getattr(getattr(t, 'safra', None), 'produto', None), 'nome', None)
                             or getattr(getattr(t, 'safra', None), 'produto_nome', None)
                },
                'quantidade_comprada': int(getattr(t, 'quantidade', 0) or 0),
                'valor_total_pago': float(getattr(t, 'valor_total', 0) or 0),
                'data_criacao': getattr(getattr(t, 'data_criacao', None), 'isoformat', lambda: None)(),
                'vendedor': {
                    'nome': getattr(getattr(t, 'vendedor', None), 'nome', None)
                }
            })
    except Exception:
        # Fallback quando modelos não estão acessíveis
        compras = []

    stats = {
        'total': len(compras),
        'pendentes': sum(1 for c in compras if c['status'] == 'pendente'),
        'ativas': sum(1 for c in compras if c['status'] in ['analise', 'escrow', 'enviado'])
    }
    return jsonify({'compras': compras, 'stats': stats})
