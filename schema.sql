-- Création de la table des utilisateurs
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('citizen', 'agent', 'admin') NOT NULL DEFAULT 'citizen',
    full_name VARCHAR(255) NOT NULL,
    is_approved BOOLEAN DEFAULT FALSE,
    is_super_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Création de la table des demandes
CREATE TABLE IF NOT EXISTS requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    citizen_id INT NOT NULL,
    type VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    attachment VARCHAR(255),
    status ENUM('En attente', 'En cours', 'Terminée', 'Rejetée') DEFAULT 'En attente',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (citizen_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Insertion du compte administrateur super admin
INSERT IGNORE INTO users (email, password, role, full_name, is_approved, is_super_admin) 
VALUES ('mermehdi457@gmail.com', 'merzouki012', 'admin', 'Super Administrateur', TRUE, TRUE);

-- Insertion d'un compte agent de test (non approuvé)
INSERT IGNORE INTO users (email, password, role, full_name, is_approved, is_super_admin) 
VALUES ('agent@test.com', 'agent123', 'agent', 'Agent Test', FALSE, FALSE);

-- Insertion d'un compte citoyen de test
INSERT IGNORE INTO users (email, password, role, full_name, is_approved, is_super_admin) 
VALUES ('citoyen@test.com', 'test123', 'citizen', 'Citoyen Test', TRUE, FALSE);