# auth.py
from flask import session, redirect, url_for, flash
from functools import wraps

def login_required(f):
    """
    Decorator para garantir que o usuário esteja logado antes de acessar uma rota.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user"):
            flash("Você precisa estar logado para acessar esta página.", "warning")
            return redirect(url_for("auth.login")) # Rota de login agora está no blueprint 'auth'
        return f(*args, **kwargs)
    return decorated_function

