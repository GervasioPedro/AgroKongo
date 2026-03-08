# app/routes/mercado.py - Versão refatorada com padrões enterprise
from flask import Blueprint, request, current_app, jsonify
from flask_login import current_user
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models import Safra, Transacao, TransactionStatus, Usuario
from app.shared.responses import success_response, error_response, not_found_error

mercado_bp = Blueprint('mercado', __name__)

# ==================== API ENDPOINTS (JSON) ====================

# ... (api_explorar_produtos, api_detalhes_produto, api_iniciar_encomenda, api_perfil_produtor) ...

@mercado_bp.route('/api/validar-fatura/<code>', methods=['GET'])
def api_validar_fatura(code):
    """Verifica a autenticidade de uma fatura via QR Code e retorna JSON."""
    query = Transacao.query.options(
        joinedload(Transacao.safra),
        joinedload(Transacao.vendedor),
        joinedload(Transacao.comprador)
    )
    venda = query.filter(Transacao.fatura_ref == code).first()

    if not venda:
        return not_found_error(message='Fatura não encontrada.')

    acesso_completo = False
    if current_user.is_authenticated:
        if current_user.id in [venda.comprador_id, venda.vendedor_id] or current_user.tipo == 'admin':
            acesso_completo = True
    
    if acesso_completo:
        return success_response(
            data=venda.to_dict(),
            message='Fatura validada com sucesso',
            status_code=200
        )
    else:
        # Acesso público: apenas validação básica (sem dados sensíveis)
        dados_publicos = {
            'fatura_ref': venda.fatura_ref,
            'status': venda.status,
            'data_criacao': venda.data_criacao.isoformat() if venda.data_criacao else None,
            'valida': True
        }
        return success_response(
            data=dados_publicos,
            message='Fatura válida (acesso público)',
            status_code=200
        )

# ... (resto do código) ...
