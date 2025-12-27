# utils/decorators.py
from functools import wraps
from flask import session, redirect, url_for

def login_requerido(tipo=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'tipo' not in session:
                return redirect(url_for('auth_bp.login_produtor'))
            if tipo and session['tipo'] != tipo:
                return redirect(url_for('publico_bp.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator