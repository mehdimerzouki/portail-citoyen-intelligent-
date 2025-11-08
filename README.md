markdown
# Portail Citoyen Intelligent — Démo (Flask + SQL)

## Démarrer
1) Installer les dépendances :
pip install flask

text
2) Initialiser la base :
pyt
hon app.py --init-db
text
3) Lancer :
python app.py

text

Identifiants :
- citoyen@test.com / test123
- agent@test.com / test123

## Fonctionnalités
- Espace citoyen pour créer et suivre des demandes
- Espace agent pour traiter les demandes
- Téléchargement de pièces jointes
- Gestion des statuts des demandes
Structure des dossiers :
text
mon_projet/
├── app.py
├── schema.sql
├── README.md
├── static/
│   └── styles.css
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── citizen_dashboard.html
│   ├── citizen_new.html
│   ├── agent_dashboard.html
│   └── agent_request.html
└── uploads/ (sera créé automatiquement)
Instructions d'utilisation :
Créez un dossier pour votre projet

Placez tous les fichiers dans leurs dossiers respectifs

Ouvrez un terminal dans le dossier du projet

Exécutez python app.py --init-db pour initialiser la base de données

Exécutez python app.py pour démarrer le serveur

Ouvrez votre navigateur à l'adresse http://localhost:5000

L'application est maintenant prête à être utilisée avec les comptes de démonstration.

