# app/utils/decorators_atualizado - Decorators atualizados para status_conta
# RN03: Limitação de Estado - Usuário PENDENTE_VERIFICACAO não pode criar anúncios

from functools import wraps
from flask import flash, redirect, url_for, abort
from flask_login import current_user

from app.models import StatusConta


def produtor_required(f):
    """Decorator: Requer usuário do tipo produtor."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.tipo != 'produtor':
            flash('Acesso restrito a produtores.', 'warning')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def produtor_verified_required(f):
    """
    RN03: Limitação de Estado
    Usuário com status PENDENTE_VERIFICACAO não pode criar anúncios
    Retorna erro 403 Forbidden até que Admin mude para VERIFICADO
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        if current_user.tipo != 'produtor':
            flash('Acesso restrito a produtores.', 'warning')
            return redirect(url_for('main.dashboard'))
        
        # RN03: Verificar status textual
        if current_user.status_conta != StatusConta.VERIFICADO:
            abort(403, description='Sua conta precisa ser verificada pela administração para publicar produtos.')
        
        return f(*args, **kwargs)
    return decorated_function


def conta_validada_required(f):
    """
    Decorator para verificar se conta está validada
    Mantido para compatibilidade com código existente
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        # Verificar tanto o booleano quanto o status textual
        if not current_user.conta_validada or current_user.status_conta != StatusConta.VERIFICADO:
            flash('ℹ️ O seu perfil está em processo de verificação. Terá acesso total após a validação dos documentos.', 'info')
            return redirect(url_for('produtor.dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator: Requer usuário administrador."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.tipo != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def comprador_verified_required(f):
    """
    Decorator para compradores com conta validada
    Para operações que requerem verificação
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        if current_user.tipo != 'comprador':
            flash('Acesso restrito a compradores.', 'warning')
            return redirect(url_for('main.dashboard'))
        
        # Verificar se conta está validada (se aplicável)
        if current_user.status_conta == StatusConta.REJEITADO:
            flash('Sua conta foi rejeitada. Entre em contato com o suporte.', 'danger')
            return redirect(url_for('main.dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function


def check_account_status(f):
    """
    Middleware para verificar status da conta e redirecionar se necessário
    Usado em views principais
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return f(*args, **kwargs)
        
        # Se status for REJEITADO, mostrar mensagem
        if current_user.status_conta == StatusConta.REJEITADO:
            flash('Sua conta foi rejeitada. Verifique seu email para mais informações.', 'warning')
        
        # Se status for SUSPENSO, bloquear acesso
        if current_user.status_conta == StatusConta.SUSPENSO:
            flash('Sua conta está suspensa. Entre em contato com o suporte.', 'danger')
            return redirect(url_for('auth.logout'))
        
        return f(*args, **kwargs)
    return decorated_function
