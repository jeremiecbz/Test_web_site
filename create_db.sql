CREATE TABLE IF NOT EXISTS users (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "nom" TEXT NOT NULL,
    "prenom" TEXT NOT NULL,
    "e_mail" TEXT NOT NULL,
    "mot_de_passe" TEXT NOT NULL,
    "classe" TEXT NOT NULL,
    "o_s" TEXT NOT NULL,
    "o_c" TEXT NOT NULL,
    "groupe" TEXT NOT NULL,
    "cours_dispenses" TEXT,
    "isBillingue" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tests (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "nom" TEXT NOT NULL,
    "branche" TEXT NOT NULL,
    "date" TEXT NOT NULL,
    "jour" TEXT NOT NULL,
    "heure" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "classe" TEXT NOT NULL,
    "createur" TEXT NOT NULL,
    "create_date" TEXT NOT NULL,
    "type" TEXT NOT NULL
);


CREATE TABLE IF NOT EXISTS hidden_tests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    test_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (test_id) REFERENCES tests(id)
);


CREATE TABLE IF NOT EXISTS devoirs (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "nom" TEXT NOT NULL,
    "branche" TEXT NOT NULL,
    "date" TEXT NOT NULL,
    "jour" TEXT NOT NULL,
    "heure" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "classe" TEXT NOT NULL,
    "createur" TEXT NOT NULL,
    "create_date" TEXT NOT NULL,
    "type" TEXT NOT NULL
    );


CREATE TABLE IF NOT EXISTS hidden_devoirs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    devoir_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (devoir_id) REFERENCES devoirs(id)
);



CREATE TABLE IF NOT EXISTS events (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "nom" TEXT NOT NULL,
    "branche" TEXT NOT NULL,
    "date" TEXT NOT NULL,
    "jour" TEXT NOT NULL,
    "heure" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "classe" TEXT NOT NULL,
    "createur" TEXT NOT NULL,
    "create_date" TEXT NOT NULL,
    "type" TEXT NOT NULL
);


CREATE TABLE IF NOT EXISTS hidden_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    event_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (event_id) REFERENCES events(id)
);

INSERT INTO users (nom, prenom, e_mail,mot_de_passe, classe, o_s, o_c, groupe, cours_dispenses, isBillingue) VALUES ('ADMIN', 'admin', 'admin@eduvaud.ch','admin', '3M8', 'Maths et Physique', 'Informatique', 'A','', 'oui'  )
