from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, flash
import mysql.connector
import os, argparse, datetime
import re  # Pour la validation des emails

APP_DIR = os.getcwd()
UPLOAD_DIR = os.path.join(APP_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Configuration MySQL - MODIFIEZ CES VALEURS SELON VOTRE INSTALLATION
MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'root',        # Votre utilisateur MySQL
    'password': '',        # Votre mot de passe MySQL (laissez vide si pas de mot de passe)
    'database': 'portail_citoyen',
    'charset': 'utf8mb4'
}

def get_db():
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        print("✅ Connexion à la base de données réussie")
        return conn
    except mysql.connector.Error as err:
        print(f"❌ Erreur de connexion MySQL: {err}")
        print("Vérifiez votre configuration MySQL dans MYSQL_CONFIG")
        return None

def init_db():
    print("🔧 Initialisation de la base de données...")
    
    # Créer la base de données si elle n'existe pas
    config_no_db = MYSQL_CONFIG.copy()
    database_name = config_no_db.pop('database')
    
    try:
        # Se connecter sans spécifier de base de données
        conn = mysql.connector.connect(**config_no_db)
        cursor = conn.cursor()
        
        # Créer la base de données si elle n'existe pas
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database_name}")
        conn.commit()
        cursor.close()
        conn.close()
        print(f"✅ Base de données '{database_name}' créée ou vérifiée")
    except mysql.connector.Error as err:
        print(f"❌ Erreur lors de la création de la base de données: {err}")
        print("Vérifiez vos paramètres de connexion MySQL")
        return

    # Maintenant, exécuter le script SQL dans la base de données
    schema_path = os.path.join(APP_DIR, "schema.sql")
    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            sql = f.read()
        print("✅ Fichier schema.sql trouvé et lu")
    except FileNotFoundError:
        print(f"❌ Fichier schema.sql introuvable à l'emplacement: {schema_path}")
        return
    
    conn = get_db()
    if conn is None:
        print("❌ Impossible de se connecter à la base de données pour initialiser les tables")
        return
        
    cursor = conn.cursor()
    
    # Vérifier si la colonne is_super_admin existe déjà
    cursor.execute("""
        SELECT COUNT(*) FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'is_super_admin'
    """)
    column_exists = cursor.fetchone()[0] > 0
    
    # Si la colonne n'existe pas, l'ajouter
    if not column_exists:
        print("⚠️  Colonne is_super_admin non trouvée, ajout...")
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN is_super_admin BOOLEAN DEFAULT FALSE")
            conn.commit()
            print("✅ Colonne is_super_admin ajoutée avec succès")
        except mysql.connector.Error as err:
            print(f"❌ Erreur lors de l'ajout de la colonne: {err}")
    
    # Exécuter chaque instruction séparément
    statements = sql.split(';')
    for statement in statements:
        if statement.strip():
            try:
                cursor.execute(statement)
                print(f"✅ Exécution: {statement[:50]}...")
            except mysql.connector.Error as err:
                print(f"⚠️  Avertissement lors de l'exécution: {statement}")
                print(f"   Erreur: {err}")
    
    conn.commit()
    
    # Vérification que le compte admin a été créé
    cursor.execute("SELECT * FROM users WHERE email = 'mermehdi457@gmail.com'")
    admin_user = cursor.fetchone()
    if admin_user:
        print("✅ Compte administrateur créé avec succès")
        print(f"   Email: {admin_user[1]}")
        print(f"   Rôle: {admin_user[2]}")
        print(f"   Super admin: {admin_user[6]}")
    else:
        print("❌ Le compte administrateur n'a pas été créé")
        # Création manuelle du compte admin
        try:
            cursor.execute("""
                INSERT INTO users (email, password, role, full_name, is_approved, is_super_admin)
                VALUES ('mermehdi457@gmail.com', 'merzouki012', 'admin', 'Super Administrateur', TRUE, TRUE)
            """)
            conn.commit()
            print("✅ Compte administrateur créé manuellement")
        except mysql.connector.Error as err:
            print(f"❌ Erreur lors de la création manuelle du compte admin: {err}")
    
    cursor.close()
    conn.close()
    print("✅ Base de données initialisée avec succès")

app = Flask(__name__)
app.secret_key = "dev-key-change-me"

def current_user():
    uid = session.get("user_id")
    if not uid: 
        return None
        
    conn = get_db()
    if conn is None:
        return None
        
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id = %s", (uid,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user

def login_required(role=None):
    def decorator(fn):
        def wrapper(*args, **kwargs):
            user = current_user()
            if not user:
                flash("Veuillez vous connecter pour accéder à cette page.", "error")
                return redirect(url_for("login"))
            if role and user["role"] != role:
                flash("Accès non autorisé.", "error")
                return redirect(url_for("index"))
            return fn(*args, **kwargs)
        wrapper.__name__ = fn.__name__
        return wrapper
    return decorator

def super_admin_required(fn):
    def wrapper(*args, **kwargs):
        user = current_user()
        if not user or not user.get("is_super_admin"):
            flash("Accès réservé au super administrateur.", "error")
            return redirect(url_for("index"))
        return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__
    return wrapper

def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

@app.route("/")
def index():
    user = current_user()
    if user:
        if user["role"] == "agent":
            return redirect(url_for("agent_dashboard"))
        elif user["role"] == "admin" and user.get("is_super_admin"):
            return redirect(url_for("admin_dashboard"))
        else:
            return redirect(url_for("citizen_dashboard"))
    return render_template("index.html")

@app.route("/agent_home")
def agent_home():
    return render_template("agent_home.html")
#enregistrer __> e/registre


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email","").strip().lower()
        password = request.form.get("password","")
        full_name = request.form.get("full_name","").strip()
        role = request.form.get("role","citizen")
        
        # Validation des données
        if not email or not password or not full_name:
            flash("Tous les champs sont obligatoires.", "error")
            return render_template("register.html")
            
        if not is_valid_email(email):
            flash("Format d'email invalide.", "error")
            return render_template("register.html")
            
        if len(password) < 6:
            flash("Le mot de passe doit contenir au moins 6 caractères.", "error")
            return render_template("register.html")
        
        # Vérifier si l'email existe déjà
        conn = get_db()
        if conn is None:
            flash("Erreur de connexion à la base de données.", "error")
            return render_template("register.html")
            
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            cursor.close()
            conn.close()
            flash("Un compte avec cet email existe déjà.", "error")
            return render_template("register.html")
        
        # Pour les agents, le compte n'est pas approuvé automatiquement
        is_approved = True if role == "citizen" else False
        
        # Créer l'utilisateur
        try:
            cursor.execute("INSERT INTO users (email, password, role, full_name, is_approved, is_super_admin) VALUES (%s, %s, %s, %s, %s, %s)",
                        (email, password, role, full_name, is_approved, False))
            conn.commit()
            cursor.close()
            conn.close()
            
            if role == "agent":
                flash("Votre demande de compte agent a été soumise. Vous pourrez vous connecter une fois approuvé.", "success")
            else:
                flash("Inscription réussie! Vous pouvez maintenant vous connecter.", "success")
            
            return redirect(url_for("login"))
        except mysql.connector.Error as err:
            flash(f"Erreur lors de la création du compte: {err}", "error")
            return render_template("register.html")
    
    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email","").strip().lower()
        password = request.form.get("password","")
        
        print(f"🔐 Tentative de connexion avec: {email}")
        
        conn = get_db()
        if conn is None:
            flash("Erreur de connexion à la base de données.", "error")
            return render_template("login.html")
            
        cursor = conn.cursor(dictionary=True)
        
        # Initialisation de la variable user pour éviter l'erreur UnboundLocalError
        user = None
        
        # Vérification détaillée pour le débogage
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user_by_email = cursor.fetchone()
        
        if user_by_email:
            print(f"✅ Utilisateur trouvé: {user_by_email['email']}")
            print(f"   Rôle: {user_by_email['role']}")
            print(f"   Super admin: {user_by_email.get('is_super_admin', 'N/A')}")
            print(f"   Approuvé: {user_by_email['is_approved']}")
            
            # Maintenant vérifiez le mot de passe
            cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
            user = cursor.fetchone()
            
            if user:
                print("✅ Mot de passe correct")
            else:
                print("❌ Mot de passe incorrect")
                print(f"   Mot de passe fourni: {password}")
                print(f"   Mot de passe attendu: {user_by_email['password']}")
        else:
            print(f"❌ Aucun utilisateur trouvé avec l'email: {email}")
        
        cursor.close()
        conn.close()
        
        # Vérification que user est bien défini avant de l'utiliser
        if user:
            # Vérifier si le compte agent est approuvé
            if user["role"] == "agent" and not user["is_approved"]:
                flash("Votre compte agent n'a pas encore été approuvé.", "error")
                return render_template("login.html")
                
            session["user_id"] = user["id"]
            flash("Connexion réussie!", "success")
            
            if user["role"] == "agent":
                return redirect(url_for("agent_dashboard"))
            elif user["role"] == "admin" and user.get("is_super_admin"):
                return redirect(url_for("admin_dashboard"))
            else:
                return redirect(url_for("citizen_dashboard"))
                
        flash("Identifiants invalides", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Vous avez été déconnecté.", "success")
    return redirect(url_for("login"))

@app.route("/citoyen")
@login_required(role="citizen")
def citizen_dashboard():
    user = current_user()
    conn = get_db()
    if conn is None:
        flash("Erreur de connexion à la base de données.", "error")
        return redirect(url_for("index"))
        
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM requests WHERE citizen_id = %s ORDER by created_at DESC", (user["id"],))
    reqs = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("citizen_dashboard.html", user=user, reqs=reqs)

@app.route("/citoyen/nouvelle", methods=["GET","POST"])
@login_required(role="citizen")
def citizen_new():
    user = current_user()
    if request.method == "POST":
        type_ = request.form.get("type")
        title = request.form.get("title")
        desc = request.form.get("description")
        attach = None
        file = request.files.get("attachment")
        if file and file.filename:
            fname = datetime.datetime.now().strftime("%Y%m%d%H%M%S_") + file.filename
            path = os.path.join(UPLOAD_DIR, fname)
            file.save(path)
            attach = fname
            
        conn = get_db()
        if conn is None:
            flash("Erreur de connexion à la base de données.", "error")
            return redirect(url_for("citizen_dashboard"))
            
        cursor = conn.cursor()
        try:
            cursor.execute("""INSERT INTO requests (citizen_id,type,title,description,attachment)
                            VALUES (%s,%s,%s,%s,%s)""",(user["id"], type_, title, desc, attach))
            conn.commit()
            cursor.close()
            conn.close()
            flash("Demande envoyée avec succès.", "success")
            return redirect(url_for("citizen_dashboard"))
        except mysql.connector.Error as err:
            flash(f"Erreur lors de l'envoi de la demande: {err}", "error")
            return redirect(url_for("citizen_dashboard"))
            
    return render_template("citizen_new.html", user=user)
    # Ajoutez ces routes après la route citizen_new

@app.route("/citoyen/req/<int:req_id>/edit", methods=["GET", "POST"])
@login_required(role="citizen")
def citizen_edit_request(req_id):
    user = current_user()
    conn = get_db()
    if conn is None:
        flash("Erreur de connexion à la base de données.", "error")
        return redirect(url_for("citizen_dashboard"))
        
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM requests WHERE id = %s AND citizen_id = %s", (req_id, user["id"]))
    req = cursor.fetchone()
    
    if not req:
        cursor.close()
        conn.close()
        flash("Demande non trouvée.", "error")
        return redirect(url_for("citizen_dashboard"))
    
    # Vérifier si la demande peut être modifiée (seulement si en attente)
    if req["status"] != "En attente":
        cursor.close()
        conn.close()
        flash("Seules les demandes 'En attente' peuvent être modifiées.", "error")
        return redirect(url_for("citizen_dashboard"))
    
    if request.method == "POST":
        type_ = request.form.get("type")
        title = request.form.get("title")
        desc = request.form.get("description")
        
        # Gestion du fichier
        file = request.files.get("attachment")
        if file and file.filename:
            # Supprimer l'ancien fichier s'il existe
            if req["attachment"]:
                old_file_path = os.path.join(UPLOAD_DIR, req["attachment"])
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)
            
            # Sauvegarder le nouveau fichier
            fname = datetime.datetime.now().strftime("%Y%m%d%H%M%S_") + file.filename
            path = os.path.join(UPLOAD_DIR, fname)
            file.save(path)
            attach = fname
        else:
            attach = req["attachment"]
            
        try:
            cursor.execute("""
                UPDATE requests 
                SET type = %s, title = %s, description = %s, attachment = %s, updated_at = NOW()
                WHERE id = %s
            """, (type_, title, desc, attach, req_id))
            conn.commit()
            cursor.close()
            conn.close()
            flash("Demande modifiée avec succès.", "success")
            return redirect(url_for("citizen_dashboard"))
        except mysql.connector.Error as err:
            flash(f"Erreur lors de la modification: {err}", "error")
            return redirect(url_for("citizen_edit_request", req_id=req_id))
    
    cursor.close()
    conn.close()
    return render_template("citizen_edit.html", req=req, user=user)

@app.route("/citoyen/req/<int:req_id>/delete", methods=["POST"])
@login_required(role="citizen")
def citizen_delete_request(req_id):
    user = current_user()
    conn = get_db()
    if conn is None:
        flash("Erreur de connexion à la base de données.", "error")
        return redirect(url_for("citizen_dashboard"))
        
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM requests WHERE id = %s AND citizen_id = %s", (req_id, user["id"]))
    req = cursor.fetchone()
    
    if not req:
        cursor.close()
        conn.close()
        flash("Demande non trouvée.", "error")
        return redirect(url_for("citizen_dashboard"))
    
    # Vérifier si la demande peut être supprimée (seulement si en attente)
    if req["status"] != "En attente":
        cursor.close()
        conn.close()
        flash("Seules les demandes 'En attente' peuvent être supprimées.", "error")
        return redirect(url_for("citizen_dashboard"))
    
    try:
        # Supprimer le fichier joint s'il existe
        if req["attachment"]:
            file_path = os.path.join(UPLOAD_DIR, req["attachment"])
            if os.path.exists(file_path):
                os.remove(file_path)
        
        cursor.execute("DELETE FROM requests WHERE id = %s", (req_id,))
        conn.commit()
        cursor.close()
        conn.close()
        flash("Demande supprimée avec succès.", "success")
    except mysql.connector.Error as err:
        flash(f"Erreur lors de la suppression: {err}", "error")
    
    return redirect(url_for("citizen_dashboard"))

@app.route("/uploads/<path:fname>")
def uploaded_file(fname):
    return send_from_directory(UPLOAD_DIR, fname)

@app.route("/agent")
@login_required(role="agent")
def agent_dashboard():
    conn = get_db()
    if conn is None:
        flash("Erreur de connexion à la base de données.", "error")
        return redirect(url_for("index"))
        
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT r.*, u.full_name, u.email FROM requests r JOIN users u ON u.id=r.citizen_id ORDER BY created_at DESC")
    reqs = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("agent_dashboard.html", reqs=reqs)

@app.route("/agent/req/<int:req_id>", methods=["GET","POST"])
@login_required(role="agent")
def agent_request(req_id):
    conn = get_db()
    if conn is None:
        flash("Erreur de connexion à la base de données.", "error")
        return redirect(url_for("agent_dashboard"))
        
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT r.*, u.full_name, u.email FROM requests r JOIN users u ON u.id=r.citizen_id WHERE r.id=%s", (req_id,))
    req = cursor.fetchone()
    
    if not req:
        cursor.close()
        conn.close()
        flash("Demande non trouvée.", "error")
        return redirect(url_for("agent_dashboard"))
        
    if request.method == "POST":
        status = request.form.get("status")
        try:
            cursor.execute("UPDATE requests SET status=%s, updated_at=NOW() WHERE id=%s", (status, req_id))
            conn.commit()
            cursor.close()
            conn.close()
            flash("Statut mis à jour.", "success")
            return redirect(url_for("agent_dashboard"))
        except mysql.connector.Error as err:
            flash(f"Erreur lors de la mise à jour: {err}", "error")
            return redirect(url_for("agent_request", req_id=req_id))
    
    cursor.close()
    conn.close()
    return render_template("agent_request.html", req=req)

@app.route("/admin/approve_agents", methods=["GET", "POST"])
@login_required(role="admin")
@super_admin_required
def approve_agents():
    conn = get_db()
    if conn is None:
        flash("Erreur de connexion à la base de données.", "error")
        return redirect(url_for("admin_dashboard"))
        
    cursor = conn.cursor(dictionary=True)
    
    # Récupérer les agents en attente d'approbation
    cursor.execute(
        "SELECT * FROM users WHERE role = 'agent' AND is_approved = 0"
    )
    pending_agents = cursor.fetchall()
    
    if request.method == "POST":
        agent_id = request.form.get("agent_id")
        action = request.form.get("action")
        
        try:
            if action == "approve":
                cursor.execute("UPDATE users SET is_approved = 1 WHERE id = %s", (agent_id,))
                flash("Compte agent approuvé avec succès.", "success")
            elif action == "reject":
                cursor.execute("DELETE FROM users WHERE id = %s", (agent_id,))
                flash("Compte agent rejeté.", "success")
            
            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for("approve_agents"))
        except mysql.connector.Error as err:
            flash(f"Erreur lors de l'opération: {err}", "error")
            return redirect(url_for("approve_agents"))
    
    cursor.close()
    conn.close()
    return render_template("approve_agents.html", pending_agents=pending_agents)

@app.route("/admin")
@login_required(role="admin")
@super_admin_required
def admin_dashboard():
    return render_template("admin_dashboard.html")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--init-db", action="store_true")
    args = parser.parse_args()
    if args.init_db:
        init_db()
        print("✅ Base initialisée. Vous pouvez maintenant démarrer l'application avec: python app.py")
    else:
        print("🌐 Démarrage de l'application Flask...")
        print("📧 Compte administrateur: mermehdi457@gmail.com / merzouki012")
        print("👤 Compte agent: agent@test.com / agent123")
        print("👤 Compte citoyen: citoyen@test.com / test123")
        print("🌐 URL: http://localhost:5000")
        app.run(debug=True, host='0.0.0.0', port=5000)