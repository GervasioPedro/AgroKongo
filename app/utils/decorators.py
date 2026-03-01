from functools import wraps
from flask import abort, flash, redirect, url_for, current_app
from flask_login import current_user
from app.models import LogAuditoria
from app.extensions import db

def admin_required(f):
    """Protege rotas exclusivas para a administração da AgroKongo."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 1. Bloqueio Imediato: Não autenticado
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))

        # 2. Verificação de Role
        if current_user.tipo != 'admin':
            # Auditoria de Incidente
            try:
                log = LogAuditoria(
                    usuario_id=current_user.id,
                    acao="ACESSO_NEGADO_ADMIN",
                    detalhes=f"Tentativa de invasão na rota: {f.__name__}"
                )
                db.session.add(log)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Erro ao registar log de segurança: {e}")

            flash("⚠️ Acesso Negado. Esta área requer privilégios de administrador.", "danger")
            return redirect(url_for('main.index'))

        return f(*args, **kwargs)
    return decorated_function

def produtor_required(f):
    """
    Garante que o utilizador é um produtor E que a sua conta foi
    validada documentalmente pela equipa AgroKongo.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 1. Bloqueio: Não autenticado
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))

        # 2. Bloqueio: Não é produtor
        if current_user.tipo != 'produtor':
            flash("Esta funcionalidade é exclusiva para produtores agrícolas.", "warning")
            return redirect(url_for('main.index'))

        # 3. Bloqueio: Conta ainda não validada (Estado Crítico para MVP)
        if not current_user.conta_validada:
            flash("ℹ️ O seu perfil está em processo de verificação. Terá acesso total após a validação dos documentos.", "info")
            # Redireciona para o dashboard do produtor (área segura) ou perfil
            return redirect(url_for('produtor.dashboard'))

        return f(*args, **kwargs)
    return decorated_function