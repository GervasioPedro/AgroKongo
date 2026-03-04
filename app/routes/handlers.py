# app/routes/handlers.py - Error handlers para uma arquitetura desacoplada
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import current_user
from flask_limiter.util import get_remote_address
from markupsafe import escape
from sqlalchemy.exc import SQLAlchemyError
from app.extensions import db, limiter
from app.models import LogAuditoria
from app.utils.helpers import aware_utcnow

errors_bp = Blueprint('errors', __name__)

# ==================== FUNÇÃO DE LOG DE ERROS ====================
def log_error(codigo: str, detalhes: str):
    """Log persistente seguro com fallback."""
    try:
        user_id = current_user.id if current_user.is_authenticated else None
        log = LogAuditoria(
            usuario_id=user_id,
            acao=codigo,
            detalhes=f"{escape(detalhes[:500])} | Path: {escape(request.path)} | Method: {escape(request.method)} | UA: {escape(request.user_agent.string[:200])}",
            ip=request.remote_addr,
            data_criacao=aware_utcnow()
        )
        db.session.add(log)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.error("Falha ao logar erro no banco de dados.", exc_info=True)
    except Exception as e:
        current_app.logger.error(f"Falha inesperada ao logar erro: {e}", exc_info=True)

# ==================== FUNÇÃO AUXILIAR PARA RESPOSTA ====================
def _handle_error_response(error_code, error_message, template_file, log_details=""):
    """Centraliza a lógica de resposta para erros (JSON ou HTML)."""
    log_error(f"{error_code} Error", log_details or error_message)

    # Se a requisição for para a API, retorna JSON
    if request.path.startswith('/api/') or (request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html):
        return jsonify({"error": error_message}), error_code

    # Caso contrário, renderiza a página de erro HTML
    flash(error_message, "danger")
    return render_template(template_file), error_code

# ==================== ERROR HANDLERS ====================
@errors_bp.app_errorhandler(400)
def error_400(error):
    """Bad Request - requisição inválida."""
    return _handle_error_response(400, "Requisição inválida.", 'errors/400.html', str(escape(error.description or '')))

@errors_bp.app_errorhandler(401)
def error_401(error):
    """Unauthorized - não autenticado."""
    log_error("401 Unauthorized", "Acesso não autorizado")
    
    if request.path.startswith('/api/'):
        return jsonify({"error": "Autenticação necessária."}), 401
        
    flash("Faça login para continuar.", "warning")
    return redirect(url_for('auth.login', next=request.url))

@errors_bp.app_errorhandler(403)
def error_403(error):
    """Forbidden - acesso proibido."""
    return _handle_error_response(403, "Acesso proibido. Você não tem permissão para executar esta ação.", 'errors/403.html', str(escape(error.description or '')))

@errors_bp.app_errorhandler(404)
def error_404(error):
    """Not Found - recurso não encontrado."""
    return _handle_error_response(404, "O recurso solicitado não foi encontrado.", 'errors/404.html', escape(request.path))

@errors_bp.app_errorhandler(405)
def error_405(error):
    """Method Not Allowed - método HTTP não permitido."""
    return _handle_error_response(405, "Método não permitido para este recurso.", 'errors/405.html', escape(request.method))

@errors_bp.app_errorhandler(413)
def error_413(error):
    """Payload Too Large - arquivo muito grande."""
    db.session.rollback()
    return _handle_error_response(413, "Arquivo muito grande (máx 15MB).", 'errors/413.html', f"Tamanho: {request.content_length}")

@errors_bp.app_errorhandler(429)
def error_429(error):
    """Too Many Requests - rate limit excedido."""
    return _handle_error_response(429, "Muitas requisições. Por favor, aguarde alguns minutos.", 'errors/429.html', "Rate limit excedido")

@errors_bp.app_errorhandler(500)
def error_500(error):
    """Internal Server Error - erro interno do servidor."""
    db.session.rollback()
    return _handle_error_response(500, "Ocorreu um erro interno. Nossa equipa já foi notificada.", 'errors/500.html', str(escape(error)))

@errors_bp.app_errorhandler(503)
def error_503(error):
    """Service Unavailable - serviço indisponível."""
    return _handle_error_response(503, "Serviço temporariamente indisponível. Tente novamente mais tarde.", 'errors/503.html', str(escape(error)))
