from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from database import get_db

auth_bp = Blueprint('auth', __name__, template_folder='../templates')

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user"):
        return redirect(url_for("main.index"))

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db()
        cursor = db.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        db.close()

        if user:
            # Verifica senha com bcrypt
            import bcrypt
            if bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8")):
                session["user"] = user["username"]
                session["role"] = user["role"]  # <-- salva a role no session
                session["user_id"] = user["id"]
                flash("Login realizado com sucesso!", "success")
                return redirect(url_for("main.index"))
            else:
                flash("Senha incorreta.", "danger")
        else:
            flash("Usuário não encontrado.", "danger")

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.pop("user", None)
    session.pop("role", None)       # <-- remove role
    session.pop("user_id", None)
    flash("Você foi desconectado.", "info")
    return redirect(url_for("main.index"))

