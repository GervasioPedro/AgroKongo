from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload # Importar joinedload

comprador_api_bp = Blueprint('comprador_api', __name__, url_prefix='/api/comprador')


@comprador_api_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    """Retorna dados mínimos esperados pelo frontend do dashboard do comprador."""
    try:
        from app.models import Transacao, Safra, Produto, Usuario
        # Otimização: Usar joinedload para evitar N+1 queries
        txs = (Transacao.query
               .options(
                   joinedload(Transacao.safra).joinedload(Safra.produto),
                   joinedload(Transacao.vendedor)
               )
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
                    'produto': getattr(getattr(t.safra, 'produto', None), 'nome', None)
                },
                'quantidade_comprada': int(getattr(t, 'quantidade_comprada', 0) or 0),
                'valor_total_pago': float(getattr(t, 'valor_total_pago', 0) or 0),
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
