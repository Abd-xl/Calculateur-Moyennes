import copy
import hashlib
import hmac
import io
import json
import os
import secrets
import uuid
from datetime import datetime, timezone
from functools import wraps

from flask import Flask, abort, flash, g, jsonify, redirect, render_template, request, send_file, session, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf
from sauvegarde import DonneesInvalidesError, _valider_donnees

app = Flask(__name__)
secret = os.environ.get("SECRET_KEY")
if os.environ.get("RENDER") == "true" and not secret:
    raise RuntimeError("Configure SECRET_KEY dans Render.")
database_url = os.environ.get("DATABASE_URL", "sqlite:///calculateur.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
elif database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
app.config.update(
    SECRET_KEY=secret or "development-only-change-this-secret",
    SQLALCHEMY_DATABASE_URI=database_url,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "true" if os.environ.get("RENDER") == "true" else "false").lower() == "true",
    PERMANENT_SESSION_LIFETIME=60 * 60 * 24 * 30,
)
db = SQLAlchemy(app)
csrf = CSRFProtect(app)
def get_client_ip():
    """Retourne l'IP cliente selon l'environnement d'exécution."""
    if os.environ.get("RENDER") == "true":
        # Render place l'adresse cliente au début de X-Forwarded-For.
        # Ne pas appliquer ProxyFix ici : il sélectionne les éléments de droite
        # selon le nombre de proxys de confiance, ce qui n'est pas adapté à ce format.
        forwarded_for = request.headers.get("X-Forwarded-For", "")
        if forwarded_for:
            return forwarded_for.split(",", 1)[0].strip()
    return get_remote_address()


# Le stockage mémoire évite d'ajouter un service externe pour l'instant.
# Il est local au processus et se réinitialise au redémarrage ; un stockage partagé
# sera préférable si l'application utilise plusieurs workers ou instances.
limiter = Limiter(
    key_func=get_client_ip,
    app=app,
    default_limits=[],
    storage_uri=os.environ.get("RATELIMIT_STORAGE_URI", "memory://"),
)
VISITOR_COOKIE = "calculateur_visitor"


def utcnow():
    return datetime.now(timezone.utc)


def hash_token(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class Visitor(db.Model):
    __tablename__ = "anonymous_visitors"
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(36), unique=True, nullable=False, index=True)
    token_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)
    browser_info = db.Column(db.String(512), nullable=False, default="Inconnu")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    last_seen_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    data = db.Column(db.JSON, nullable=False, default=lambda: {"notes": {}, "coef": {}})
    # False jusqu’au premier échange réussi : permet d’importer l’ancien localStorage une seule fois.
    data_initialized = db.Column(db.Boolean, nullable=False, default=False)


@app.context_processor
def template_helpers():
    return {"csrf_token": generate_csrf}


@app.before_request
def identify_browser():
    g.visitor = None
    g.new_visitor_token = None
    if request.path.startswith("/admin") or request.path.startswith("/static/"):
        return
    token = request.cookies.get(VISITOR_COOKIE)
    visitor = Visitor.query.filter_by(token_hash=hash_token(token)).first() if token else None
    if visitor is None:
        token = secrets.token_urlsafe(32)
        visitor = Visitor(
            public_id=uuid.uuid4().hex,
            token_hash=hash_token(token),
            browser_info=request.user_agent.string[:512] or "Inconnu",
            data={"notes": {}, "coef": {}},
        )
        db.session.add(visitor)
        db.session.commit()
        g.new_visitor_token = token
    else:
        visitor.last_seen_at = utcnow()
        visitor.browser_info = request.user_agent.string[:512] or visitor.browser_info
        db.session.commit()
    g.visitor = visitor


@app.after_request
def set_visitor_cookie(response):
    token = getattr(g, "new_visitor_token", None)
    if token:
        response.set_cookie(
            VISITOR_COOKIE, token, max_age=60 * 60 * 24 * 365,
            httponly=True, secure=app.config["SESSION_COOKIE_SECURE"],
            samesite="Lax", path="/",
        )
    return response


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_authenticated"):
            return redirect(url_for("admin_login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def current_data():
    return copy.deepcopy(g.visitor.data or {"notes": {}, "coef": {}})


def save_data(data):
    _valider_donnees(data)
    g.visitor.data = copy.deepcopy(data)
    g.visitor.data_initialized = True
    db.session.commit()


@app.route("/")
def accueil():
    data = current_data()
    notes, coef = data["notes"], data["coef"]
    moyennes = {}
    total = total_coef = 0
    for matiere, liste_notes in notes.items():
        moyenne = sum(n["note"] * 20 / n["bareme"] for n in liste_notes) / len(liste_notes) if liste_notes else 0
        moyennes[matiere] = moyenne
        total += moyenne * coef[matiere]
        total_coef += coef[matiere]
    return render_template(
        "index.html", notes=notes, coef=coef, moyennes=moyennes,
        moyenne_generale=total / total_coef if total_coef else 0,
        message=request.args.get("message"), erreur_chargement=None,
    )


@app.route("/api/etat")
def etat_api():
    response = jsonify(current_data())
    response.headers["Cache-Control"] = "no-store"
    return response


@app.route("/api/synchroniser", methods=["POST"])
def synchroniser_api():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Données invalides."}), 400
    try:
        save_data(data)
    except (DonneesInvalidesError, TypeError) as erreur:
        db.session.rollback()
        return jsonify({"error": str(erreur)}), 400
    response = jsonify(current_data())
    response.headers["Cache-Control"] = "no-store"
    return response


@app.route("/ajouter", methods=["GET", "POST"])
def ajouter():
    data = current_data()
    notes, coef = data["notes"], data["coef"]
    if request.method == "GET":
        return render_template("ajouter.html", notes=notes, coef=coef)
    try:
        mode = request.form["mode"]
        note = float(request.form["note"])
        bareme = int(request.form["bareme"])
        if bareme not in (10, 20) or not 0 <= note <= bareme:
            raise ValueError("Note invalide pour ce barème.")
        if mode == "existante":
            matiere = request.form["matiere_existante"]
            if matiere not in coef:
                raise ValueError("Matière inconnue.")
            coefficient = coef[matiere]
        elif mode == "nouvelle":
            matiere = request.form["nouvelle_matiere"].strip()
            coefficient = int(request.form["coefficient"])
            if not matiere or coefficient <= 0:
                raise ValueError("Matière ou coefficient invalide.")
            existing = next((m for m in notes if m.casefold() == matiere.casefold()), None)
            if existing:
                if coef[existing] != coefficient:
                    raise ValueError("Cette matière existe déjà avec un autre coefficient.")
                matiere = existing
            else:
                notes[matiere] = []
                coef[matiere] = coefficient
        else:
            raise ValueError("Mode invalide.")
        notes[matiere].append({"note": note, "bareme": bareme})
        save_data(data)
        return redirect(url_for("accueil", message=f"Note ajoutée : {matiere} — {note:g}/{bareme}"))
    except (KeyError, TypeError, ValueError, DonneesInvalidesError) as erreur:
        db.session.rollback()
        data = current_data()
        return render_template("ajouter.html", notes=data["notes"], coef=data["coef"], message=str(erreur)), 400


@app.route("/notes")
def liste_notes():
    data = current_data()
    return render_template("notes.html", notes=data["notes"], coef=data["coef"])


@app.route("/tableur")
def tableur():
    data = current_data()
    return render_template("tableur.html", notes=data["notes"], coef=data["coef"])


@app.route("/supprimer", methods=["POST"])
def supprimer():
    data = current_data()
    try:
        matiere = request.form["matiere"]
        index = int(request.form["index"])
        del data["notes"][matiere][index]
        save_data(data)
    except (KeyError, IndexError, TypeError, ValueError, DonneesInvalidesError):
        db.session.rollback()
    return redirect(url_for("accueil"))


@app.route("/modifier", methods=["POST"])
def modifier():
    data = current_data()
    try:
        matiere = request.form["matiere"]
        index = int(request.form["index"])
        nouvelle_note = float(request.form["nouvelle_note"])
        note = data["notes"][matiere][index]
        if not 0 <= nouvelle_note <= note["bareme"]:
            raise ValueError("Note hors barème.")
        note["note"] = nouvelle_note
        save_data(data)
    except (KeyError, IndexError, TypeError, ValueError, DonneesInvalidesError):
        db.session.rollback()
    return redirect(url_for("accueil"))


@app.route("/supprimer-matiere", methods=["POST"])
def supprimer_matiere_route():
    data = current_data()
    try:
        matiere = request.form["matiere"]
        del data["notes"][matiere]
        del data["coef"][matiere]
        save_data(data)
    except (KeyError, TypeError, ValueError, DonneesInvalidesError):
        db.session.rollback()
    return redirect(url_for("accueil"))


@app.route("/admin/connexion", methods=["GET", "POST"])
@limiter.limit("5 per minute; 20 per hour", methods=["POST"])
def admin_login():
    if session.get("admin_authenticated"):
        return redirect(url_for("admin_dashboard"))
    if request.method == "POST":
        expected_email = os.environ.get("ADMIN_EMAIL", "").strip().lower()
        expected_password = os.environ.get("ADMIN_PASSWORD", "")
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if expected_email and expected_password and hmac.compare_digest(email, expected_email) and hmac.compare_digest(password, expected_password):
            session.clear()
            session["admin_authenticated"] = True
            session.permanent = True
            return redirect(url_for("admin_dashboard"))
        flash("Identifiants administrateur incorrects ou non configurés.", "error")
    return render_template("admin_login.html")


@app.route("/admin/deconnexion", methods=["POST"])
@admin_required
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


@app.route("/admin")
@admin_required
def admin_dashboard():
    visitors = Visitor.query.order_by(Visitor.last_seen_at.desc()).all()
    return render_template("admin.html", users=visitors)


@app.route("/admin/utilisateur/<int:user_id>")
@admin_required
def admin_user_detail(user_id):
    visitor = db.session.get(Visitor, user_id)
    if visitor is None:
        abort(404)
    return render_template("admin_user.html", user=visitor, data=visitor.data or {"notes": {}, "coef": {}})


@app.route("/admin/export.json")
@admin_required
def admin_export():
    payload = {
        "exported_at": utcnow().isoformat(),
        "visitors": [
            {
                "id": v.id, "anonymous_id": v.public_id, "browser_info": v.browser_info,
                "created_at": v.created_at.isoformat() if v.created_at else None,
                "last_seen_at": v.last_seen_at.isoformat() if v.last_seen_at else None,
                "data": v.data or {"notes": {}, "coef": {}},
            }
            for v in Visitor.query.order_by(Visitor.id).all()
        ],
    }
    file = io.BytesIO(json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"))
    file.seek(0)
    return send_file(file, mimetype="application/json", as_attachment=True, download_name="export-visiteurs.json")


@app.errorhandler(403)
def forbidden(_):
    return render_template("error.html", code=403, message="Accès réservé à l’administrateur."), 403


@app.errorhandler(404)
def not_found(_):
    return render_template("error.html", code=404, message="Visiteur introuvable."), 404


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)
