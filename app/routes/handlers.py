# app/routes/handlers.py - Error handlers leves, com log e UX amigável
# Versão Corrigida - 26/02/2026
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import current_user
from flask_limiter.util import get_remote_address
from markupsafe import escape
from sqlalchemy.exc import SQLAlchemyError
from app.extensions import db, limiter
from app.models import LogAuditoria
from app.utils.helpers import aware_utcnow

errors_bp = Blueprint('errors', __name__)


# ==================== RATE LIMITING PARA ERROS ====================
def error_rate_key():
    # Proteção XSS: escapar path antes de usar em string
    return f"{get_remote_address()}:{escape(request.path)}"


@errors_bp.before_request
@limiter.limit("20 per minute", key_func=error_rate_key)
def limit_errors():
    pass


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
        current_app.logger.error("Falha log erro (DB)", exc_info=True)
    except Exception as e:
        current_app.logger.error(f"Falha log erro: {e}", exc_info=True)


# ==================== ERROR HANDLERS ====================
@errors_bp.app_errorhandler(400)
def error_400(error):
    """Bad Request - requisição inválida."""
    log_error("400 Bad Request", str(escape(error.description or '')))

    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify({"erro": "Requisição inválida."}), 400

    return render_template('errors/400.html'), 400


@errors_bp.app_errorhandler(401)
def error_401(error):
    """Unauthorized - não autenticado."""
    log_error("401 Unauthorized", "Acesso não autorizado")
    flash("Faça login para continuar.", "warning")
    return redirect(url_for('auth.login', next=request.url))


@errors_bp.app_errorhandler(403)
def error_403(error):
    """Forbidden - acesso proibido."""
    log_error("403 Forbidden", str(escape(error.description or '')))
    flash("Acesso proibido – verifique permissões.", "danger")
    return render_template('errors/403.html'), 403


@errors_bp.app_errorhandler(404)
def error_404(error):
    """Not Found - página não encontrada."""
    log_error("404 Not Found", escape(request.path))
    return render_template('errors/404.html'), 404


@errors_bp.app_errorhandler(405)
def error_405(error):
    """Method Not Allowed - método HTTP não permitido."""
    log_error("405 Method Not Allowed", escape(request.method))
    return render_template('errors/405.html'), 405


@errors_bp.app_errorhandler(413)
def error_413(error):
    """Payload Too Large - arquivo muito grande."""
    log_error("413 Payload Too Large", f"Tamanho: {request.content_length}")
    db.session.rollback()
    flash("Arquivo muito grande (máx 15MB).", "warning")
    return render_template('errors/413.html'), 413


@errors_bp.app_errorhandler(414)
def error_414(error):
    """URI Too Long - URL muito longa."""
    log_error("414 URI Too Long", escape(request.url[:500]))
    db.session.rollback()
    return render_template('errors/414.html'), 414


@errors_bp.app_errorhandler(429)
def error_429(error):
    """Too Many Requests - rate limit excedido."""
    log_error("429 Too Many Requests", "Rate limit excedido")
    flash("Muitas requisições – aguarde alguns minutos.", "warning")
    return render_template('errors/429.html'), 429


@errors_bp.app_errorhandler(500)
def error_500(error):
    """Internal Server Error - erro interno do servidor."""
    db.session.rollback()
    log_error("500 Internal Error", str(escape(error)))
    flash("Ocorreu um erro interno. Nossa equipa já foi notificada.", "danger")
    return render_template('errors/500.html'), 500


@errors_bp.app_errorhandler(503)
def error_503(error):
    """Service Unavailable - serviço indisponível."""
    log_error("503 Service Unavailable", str(escape(error)))
    return render_template('errors/503.html'), 503