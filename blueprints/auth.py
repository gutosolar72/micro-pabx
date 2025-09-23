# blueprints/auth.py
from flask import Blueprint, render_template, request, session, redirect, url_for, flash

auth_bp = Blueprint('auth', __name__, template_folder='../templates')

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user"):
        return redirect(url_for("main.index"))

    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "123mudar@":
            session["user"] = "admin"
            flash("Login realizado com sucesso!", "success")
            return redirect(url_for("main.index"))
        else:
            flash("Usuário ou senha inválidos.", "danger")
    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    session.pop("user", None)
    flash("Você foi desconectado.", "info")
    return redirect(url_for("main.index"))

