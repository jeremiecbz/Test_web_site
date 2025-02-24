from flask import Flask, request, render_template, redirect,url_for, session, flash
from datetime import * 
from contextlib import contextmanager
import bcrypt
import sqlite3
import locale
try:
    locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
except locale.Error:
    locale.setlocale(locale.LC_TIME, "C")



# Création du serveur
app = Flask(__name__)

# Clé secrète pour les messages flash
app.secret_key = 'maclef'

DB = 'database.db'

@contextmanager
def connect_db():
    conn = sqlite3.connect(DB)
    try:
        cur = conn.cursor()
        cur.execute('PRAGMA foreign_keys = ON')
        cur.execute('PRAGMA encoding = "UTF-8"')
        yield cur # Return cur and continue current execution
    except Exception as e:
        conn.rollback()
        raise e
    else:
        conn.commit()
    finally:
        conn.close()
    return

jours_semaine = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

horaire_3M8 = [
    # Lundi
    ["Philosophie", "Philosophie", "Géographie", "Géographie", "Pause", "Pause", "Français", "Français", "OC", ""],
    # Mardi
    [ "","Allemand", "Maths", "Maths", "Anglais", "Pause", "Français", "Français", "Sport", "Sport"],
    # Mercredi
    ["OC", "OC", ["Allemand", "Anglais"], [ "Anglais","Allemand"], "Pause", "Maths", "Maths", "HistoireAll", "HistoireAll", ""],
    # Jeudi
    ["Maths", "Maths", "Allemand", "Philosophie", "Pause", "Biologie", "Biologie", "Physique", "Physique", ""],
    # Vendredi
    ["Appl. Maths", "Appl. Maths", "TP", "TP", "Sport", "Pause", "Anglais", "HistoireFr", "HistoireFr", ""],
    # Week-end
    ["week-end","Profitez du Week-end!!"],
    ["week-end", "Profitez du Week-end!!"]
]

periodes = [
    "08:20-09:05", 
    "09:10-09:55", 
    "10:00-11:00", 
    "11:05-11:50", 
    "11:55-12:40", 
    "12:45-13:30", 
    "13:35-14:20", 
    "14:30-15:15", 
    "15:20-16:05", 
    "16:05-16:50"
]


@app.route("/", methods=["GET", "POST"])
def index():
    today = date.today()
    #Vérifie si on est déjà connecté
    if session:
        OS ="OS_"+ session["o_s"]+ "_"+ session["classe"][:2]  
        OC ="OC_"+ session['o_c']+ "_"+ session["classe"][:2]
        user_id = session.get("id")


        
        #Selectionne les evenements qui vont arriver et qui n'ont pas été masqué par l'utilisateur
        with connect_db() as cur:    
            cur.execute(""" 
    SELECT id, nom, branche, date, jour, heure, description, classe, createur, create_date, type
    FROM tests
    WHERE ((classe = ? OR classe = ? OR classe = ?) AND branche != ?)
    AND date >= ?
    AND id NOT IN (SELECT test_id FROM hidden_tests WHERE user_id = ?)
    
    UNION ALL

    SELECT id, nom, branche, date, jour, heure, description, classe, createur, create_date, type
    FROM devoirs
    WHERE ((classe = ? OR classe = ? OR classe = ?) AND branche != ?) 
    AND date >= ?
    AND id NOT IN (SELECT devoir_id FROM hidden_devoirs WHERE user_id = ?)
    
    UNION ALL

    SELECT id, nom, branche, date, jour, heure, description, classe, createur, create_date, type
    FROM events
        WHERE ((classe = ? OR classe = ? OR classe = ?) AND branche != ?) 
    AND date >= ?
        AND id NOT IN (SELECT event_id FROM hidden_events WHERE user_id = ?)
    
        ORDER BY date ASC""",
        (session["classe"], OS, OC, session["cours_dispenses"], today, user_id, session["classe"], OS, OC, session["cours_dispenses"], today, user_id, session["classe"], OS, OC, session["cours_dispenses"], today, user_id))
            evenements = cur.fetchall()
            evenements = [{'id': id, 'nom': nom, 'branche': branche, "date": date, "jour": jour, "heure": heure, "description": description, "classe": classe, "createur": createur, "create_date": create_date, "type": type, "url_hide" : "hide_"+type, "url_link": type + "_print"}
                   for id, nom, branche, date, jour, heure, description, classe, createur, create_date, type in evenements]
            

        #Défini le debut et la fin des semaines à afficher dans le calendrier ( 4 semaines)
        start_of_week = today - timedelta(days=today.weekday())
        end_date = start_of_week + timedelta(days=27)
        weeks = []
        current_date = start_of_week


         #Selectionne tous les evenements qui ont lieux dans l'intervalle de temps du calendrier (aussi ceux avant px ceux du lundi) et aussi afficher ceux qu'on a masqué
        with connect_db() as cur:    
            cur.execute("""
    SELECT id, nom, branche, date, jour, heure, description, classe, createur, create_date, type
    FROM tests
    WHERE (classe = ? OR classe = ? OR classe = ?) 
    AND date >= ?
    
    UNION ALL

    SELECT id, nom, branche, date, jour, heure, description, classe, createur, create_date, type
    FROM devoirs
    WHERE (classe = ? OR classe = ? OR classe = ?) 
    AND date >= ?
    
    UNION ALL

    SELECT id, nom, branche, date, jour, heure, description, classe, createur, create_date, type
    FROM events
        WHERE (classe = ? OR classe = ? OR classe = ?) 
    AND date >= ?
    
        ORDER BY date ASC""", (session["classe"], OS, OC, start_of_week, session["classe"], OS, OC, start_of_week, session["classe"], OS, OC, start_of_week))
            all_evenements = cur.fetchall()
            all_evenements = [{'id': id, 'nom': nom, 'branche': branche, "date": date, "jour": jour, "heure": heure, "description": description, "classe": classe, "createur": createur, "create_date": create_date, "type": type, "url_hide" : "hide_"+type, "url_link": type + "_print"}
                   for id, nom, branche, date, jour, heure, description, classe, createur, create_date, type in all_evenements]

        while current_date <= end_date:
        # Début et fin de la semaine
            week_start = current_date
            week_end = current_date + timedelta(days=6)
            week_days = []

            for _ in range(7):
                # Trouve les événements pour cette date
                day_events = [evenement for evenement in all_evenements if evenement["date"] == str(current_date)]
                week_days.append({"date": current_date, "evenements": day_events})
                current_date += timedelta(days=1)

            weeks.append({"start": week_start, "end": week_end, "days": week_days})
            # Dictionnaire avec la date et les evenements de la date
            # Création d'une liste des semaines avec des dictionnaire de jours dans chaque semaine et des evenements associé à ces dates
        
        
        
        start_date = datetime.strptime("2024-11-04", "%Y-%m-%d")
        date_test = datetime.today()



        if request.method == 'POST':
            date_test = datetime.strptime(request.form['date_test'], "%Y-%m-%d")

            if 'avant' in request.form:
                date_test -= timedelta(days=1)  # Soustraire 1 jour
            elif 'apres' in request.form:
                date_test += timedelta(days=1)  # Ajouter 1 jour

        horaire_jour = horaire_3M8[date_test.weekday()]
        
# Calculate the difference in weeks
        weeks_nb = (date_test - start_date).days // 7

        jour = jours_semaine[date_test.weekday()] +" "+ date_test.strftime("%d %B %Y")
        jour = jour.replace("Ã©", "é").replace("Ã", "é")
        jour = jour.replace(jour.split(" ")[1], jour.split(" ")[1].capitalize())




        return render_template("Index.html", evenements = evenements, weeks = weeks, today = today, horaire_jour = horaire_jour, periodes = periodes, weeks_nb = weeks_nb, date_test = date_test, jour = jour)

    return render_template("Index.html")


@app.route("/devoirs", methods=["GET"])
def devoirs():
    today = date.today()
    user_id = session.get('id')
    # Verifie si on est connecté
    if not user_id:
        return redirect(url_for('account'))
    
    # Stocké sous forme : "OC_Informatique_3M" pour afficher uniquement si l'utilisateur fait parti de la "classe" OC_Info ou OS_MEP ou 3M8
    OS = "OS_" + session["o_s"] + "_" + session["classe"][:2]
    OC = "OC_" + session['o_c'] + "_" + session["classe"][:2]

    with connect_db() as cur:
        cur.execute("SELECT * FROM devoirs WHERE ((classe = ? OR classe = ? OR classe = ?) AND branche != ?) AND date >= ? AND id NOT IN ( SELECT devoir_id FROM hidden_devoirs WHERE user_id = ?) ORDER BY date ASC",
                     (session["classe"], OS, OC,session['cours_dispenses'], today, session.get("id")))
        devoirs = cur.fetchall()
        devoirs = [{'id': id, 'nom': nom, 'branche': branche, "date": date, "jour": jour, "heure": heure, "description": description, "classe": classe, "createur": createur, "create_date": create_date, "type": type}
                   for id, nom, branche, date, jour, heure, description, classe, createur, create_date, type in devoirs]

    return render_template("Devoirs.html", devoirs=devoirs, today = today + timedelta(days=7))


@app.route("/devoirs/<classe>/<nom>", methods=["GET", "POST"])
def devoir_print(classe, nom):
    old_nom = nom
    old_classe = classe
    with connect_db() as cur:
        cur.execute("SELECT id FROM devoirs WHERE nom = ? AND classe = ?", (nom, classe))
        id = cur.fetchone()
        if id == None:
            if session['nom'] != "ADMIN":
                flash("Cette Page n'existe pas !")
            else:
                flash(" Bye Bye la page !!")
            return (redirect(url_for('devoirs')))
        id= id[0]
    isModify = False
    OS = "OS_" + session["o_s"] + "_" + session["classe"][:2]
    OC = "OC_" + session['o_c'] + "_" + session["classe"][:2]
    today = date.today()
    
   
    if request.method == 'POST':
        if "av" in request.form:
            isModify = True

        elif "ap" in request.form:
            isModify = False

            nom = request.form["nom"]
            branche = request.form["branche"]
            date_u = request.form["date"]
            heure = request.form["heure"]
            description = request.form["description"]
            jour = jours_semaine[int(datetime.strptime(date_u, "%Y-%m-%d").weekday())]
    
            if branche == "OC":
                classe = "OC_" + session["o_c"] + "_" + session["classe"][:2]
            elif branche == "OS":
                classe = "OS_" + session["o_s"] + "_" + session["classe"][:2]
            else:
                classe = session["classe"]

            create_date = "Modifié le "+ datetime.now().strftime("%d %B %Y") + " à " + datetime.now().strftime("%H:%M")
            create_date = create_date.replace("Ã©", "é").replace("Ã", "é")
            create_date = create_date.replace(create_date.split(" ")[3], create_date.split(" ")[3].capitalize())

            with connect_db() as cur:
                cur.execute("SELECT * FROM devoirs WHERE nom = ? AND classe = ?", (nom, classe))
                nom_devoir = cur.fetchall()
                if nom_devoir :
                    if nom_devoir[0][0] != id:
                        flash("Nom déjà utilisé")
                        return redirect(url_for('devoir_print', nom = old_nom, classe = old_classe))

                with connect_db() as cur:
                    cur.execute("UPDATE devoirs SET nom = ?, branche = ?, date = ?, jour = ?, heure = ?,description = ?, classe = ?, createur = ?, create_date = ? WHERE id = ?",
                                 (nom, branche, date_u, jour, heure, description, classe, session['e_mail'], create_date, id ))
                
                return redirect(url_for('devoir_print', nom = nom, classe = classe))

        
    # Selctionne les infos sur les autres devoirs, box de gauche
    with connect_db() as cur:
        cur.execute("SELECT * FROM devoirs WHERE ((classe = ? OR classe = ? OR classe = ?) AND branche != ?) AND date >= ? AND id NOT IN ( SELECT devoir_id FROM hidden_devoirs WHERE user_id = ?) ORDER BY date ASC",
                     (session["classe"], OS, OC,session['cours_dispenses'], today, session.get("id")))
        devoirs = cur.fetchall()
        devoirs = [{'id': id, 'nom': nom, 'branche': branche, "date": date, "jour": jour, "heure": heure, "description": description, "classe": classe, "createur": createur, "create_date": create_date, "type": type}
                   for id, nom, branche, date, jour, heure, description, classe, createur, create_date, type in devoirs]

    # Selectionne les infos sur le test en particulier, box de droite
    with connect_db() as cur:
        cur.execute("SELECT * FROM devoirs WHERE nom = ? AND classe = ?", (nom, classe))
        infos_devoir = cur.fetchall()
        infos_devoir = infos_devoir[0]
        infos_devoir = {
            "id": infos_devoir[0],
            "nom": infos_devoir[1],
            "branche": infos_devoir[2],
            "date": infos_devoir[3],
            "jour": infos_devoir[4],
            "heure": infos_devoir[5],
            "description": infos_devoir[6],
            "classe": infos_devoir[7],
            "e_mail": infos_devoir[8],
            "create_date": infos_devoir[9],
            }
    with connect_db() as cur:
        cur.execute("SELECT nom, prenom FROM users WHERE e_mail = ?", (infos_devoir['e_mail'],))
        createur = cur.fetchone()
        createur = str(createur[0]) + " " + str(createur[1])
        # Trouve le créateur du devoir
    return render_template("Devoir_print.html", devoirs = devoirs, infos_devoir = infos_devoir, createur = createur, isModify = isModify)


#----Test--------------------------------------------


@app.route("/test", methods=["GET"])
def test():
    today = date.today() 
    user_id = session.get('id')
    # Verifie si on est connecté
    if not user_id:
        return redirect(url_for('account'))
    
    OS ="OS_"+ session["o_s"]+ "_"+ session["classe"][:2]  
    OC ="OC_"+ session['o_c']+ "_"+ session["classe"][:2]

    with connect_db() as cur:
        cur.execute("SELECT * FROM tests WHERE ((classe = ? OR classe = ? OR classe = ?) AND branche != ?)AND date >= ? AND id NOT IN ( SELECT test_id  FROM hidden_tests WHERE user_id = ?) ORDER BY date ASC",
                     (session["classe"], OS, OC, session['cours_dispenses'], today, user_id))
        tests = cur.fetchall()
        tests = [{'id':id, 'nom':nom, 'branche':branche,"date": date,"jour": jour,"heure": heure, "description":description,"classe": classe,"createur":createur,"create_date":create_date, "type" : type}
            for id, nom, branche,date,jour,heure,description, classe, createur, create_date, type in tests]
        
    return render_template("Tests.html", tests = tests, today = today+ timedelta(days=7))


@app.route("/test/<classe>/<nom>", methods = ["GET", "POST"])
def test_print(classe,nom):
    old_nom = nom
    old_classe = classe
    today = date.today()
    OS ="OS_"+ session["o_s"]+ "_"+ session["classe"][:2] 
    OC ="OC_"+ session['o_c']+ "_"+ session["classe"][:2]
    
    isModify = False

    with connect_db() as cur:
        cur.execute("SELECT id FROM tests WHERE nom = ? AND classe = ?", (nom, classe))
        id = cur.fetchone()
        if id== None:
            if session['nom'] != "ADMIN":
                flash("Cette Page n'existe pas !")
            else:
                flash(" Bye Bye la page !!")
            return (redirect(url_for('test')))
        id= id[0]

    if request.method == 'POST':
        if "av" in request.form:
            isModify = True

        elif "ap" in request.form:
            isModify = False

            nom = request.form["nom"]
            branche = request.form["branche"]
            date_u = request.form["date"]
            heure = request.form["heure"]
            description = request.form["description"]
            jour = jours_semaine[int(datetime.strptime(date_u, "%Y-%m-%d").weekday())]
    
            if branche == "OC":
                classe = "OC_" + session["o_c"] + "_" + session["classe"][:2]
            elif branche == "OS":
                classe = "OS_" + session["o_s"] + "_" + session["classe"][:2]
            else:
                classe = session["classe"]

            create_date = "Modifié le "+ datetime.now().strftime("%d %B %Y") + " à " + datetime.now().strftime("%H:%M")
            create_date = create_date.replace("Ã©", "é").replace("Ã", "é")
            create_date = create_date.replace(create_date.split(" ")[3], create_date.split(" ")[3].capitalize())

            with connect_db() as cur:
                cur.execute("SELECT * FROM tests WHERE nom = ? AND classe = ?", (nom, classe))
                nom_test = cur.fetchall()
                if nom_test :
                    if nom_test[0][0] != id:
                        flash("Nom déjà utilisé")
                        return redirect(url_for("test_print", nom=old_nom, classe=old_classe))

            with connect_db() as cur:
                cur.execute("UPDATE tests SET nom = ?, branche = ?, date = ?, jour = ?, heure = ?,description = ?, classe = ?, createur = ?, create_date = ? WHERE id = ?",
                             (nom, branche, date_u, jour, heure, description, classe, session['e_mail'], create_date, id ))
            
            return redirect(url_for('test_print', nom = nom, classe = classe))

    with connect_db() as cur:
        cur.execute("SELECT * FROM tests WHERE ((classe = ? OR classe = ? OR classe = ?) AND branche != ?) AND date >= ? AND id NOT IN ( SELECT test_id  FROM hidden_tests WHERE user_id = ?) ORDER BY date ASC",
                     (session["classe"], OS, OC, session['cours_dispenses'], today, session.get("id")))
        tests = cur.fetchall()
        tests = [{'id':id, 'nom':nom, 'branche':branche,"date": date,"jour": jour,"heure": heure, "description":description,"classe": classe,"createur":createur,"create_date":create_date, "type": type}
            for id, nom, branche,date,jour,heure,description, classe, createur, create_date, type in tests]
 

    with connect_db() as cur:
        cur.execute("SELECT * FROM tests WHERE nom = ? AND classe = ?",(nom, classe ))
        infos_test = cur.fetchall()
        infos_test = infos_test [0]
        infos_test = {
            "nom": infos_test[1],
            "branche": infos_test[2],
            "date": infos_test[3],
            "jour": infos_test[4],
            "heure": infos_test[5],
            "description": infos_test[6],
            "classe": infos_test[7],
            "e_mail": infos_test[8],
            "create_date": infos_test[9],
        }

    with connect_db() as cur:
        cur.execute("SELECT nom, prenom FROM users WHERE e_mail = ?",(infos_test["e_mail"], ))
        createur = cur.fetchall()[0]
        createur = str(createur[0])+" "+ str(createur[1])

    return render_template("Test_print.html",tests = tests, infos_test= infos_test, createur = createur, isModify = isModify)



#----------Evenmenement---------------------------------------


@app.route("/evenements", methods=["GET"])
def event():
    today = date.today()
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('account'))
    
    OS ="OS_"+ session["o_s"]+ "_"+ session["classe"][:2]  
    OC ="OC_"+ session['o_c']+ "_"+ session["classe"][:2]

    with connect_db() as cur:
        cur.execute("SELECT * FROM events WHERE ((classe = ? OR classe = ? OR classe = ?) AND branche != ?) AND date >= ? AND id NOT IN ( SELECT event_id  FROM hidden_events WHERE user_id = ?) ORDER BY date ASC",
                     (session["classe"], OS, OC, session['cours_dispenses'], today, user_id))
        events = cur.fetchall()
        events = [{'id':id, 'nom':nom, 'branche':branche,"date": date,"jour": jour,"heure": heure, "description":description,"classe": classe,"createur":createur,"create_date":create_date, "type" : type}
            for id, nom, branche,date,jour,heure,description, classe, createur, create_date, type in events]
        
    return render_template("Events.html", events = events, today = today + timedelta(days=7))


@app.route("/evenements/<classe>/<nom>", methods=["GET", "POST"])
def event_print(classe, nom):
    old_nom = nom
    old_classe = classe
    with connect_db() as cur:
        cur.execute("SELECT id FROM events WHERE nom = ? AND classe = ?", (nom, classe))
        id = cur.fetchone()
        if id== None:
            if session['nom'] != "ADMIN":
                flash("Cette Page n'existe pas !")
            else:
                flash(" Bye Bye la page !!")
            return (redirect(url_for('event')))
        id= id[0]

    today = date.today()
    OS ="OS_"+ session["o_s"]+ "_"+ session["classe"][:2] 
    OC ="OC_"+ session['o_c']+ "_"+ session["classe"][:2]
    isModify = False

    if request.method == 'POST':
        if "av" in request.form:
            isModify = True

        elif "ap" in request.form:
            isModify = False

            nom = request.form["nom"]
            branche = request.form["branche"]
            date_u = request.form["date"]
            heure = request.form["heure"]
            description = request.form["description"]
            jour = jours_semaine[int(datetime.strptime(date_u, "%Y-%m-%d").weekday())]
    
            if branche == "OC":
                classe = "OC_" + session["o_c"] + "_" + session["classe"][:2]
            elif branche == "OS":
                classe = "OS_" + session["o_s"] + "_" + session["classe"][:2]
            else:
                classe = session["classe"]

            create_date = "Modifié le "+ datetime.now().strftime("%d %B %Y") + " à " + datetime.now().strftime("%H:%M")
            create_date = create_date.replace("Ã©", "é").replace("Ã", "é")
            create_date = create_date.replace(create_date.split(" ")[3], create_date.split(" ")[3].capitalize())

            with connect_db() as cur:
                cur.execute("SELECT * FROM events WHERE nom = ? AND classe = ?", (nom, classe))
                nom_event = cur.fetchall()
                if nom_event :
                    if nom_event[0][0] != id:
                        flash("Nom déjà utilisé")
                        return redirect(url_for("event_print", nom=old_nom, classe=old_classe))

            with connect_db() as cur:
                cur.execute("UPDATE events SET nom = ?, branche = ?, date = ?, jour = ?, heure = ?,description = ?, classe = ?, createur = ?, create_date = ? WHERE id = ?",
                             (nom, branche, date_u, jour, heure, description, classe, session['e_mail'], create_date, id ))
            
            return redirect(url_for('event_print', nom = nom, classe = classe))

    with connect_db() as cur:
        cur.execute("SELECT * FROM events WHERE ((classe = ? OR classe = ? OR classe = ?) AND branche != ?) AND date >= ? AND id NOT IN ( SELECT event_id FROM hidden_events WHERE user_id = ?) ORDER BY date ASC",
                     (session["classe"], OS, OC, session['cours_dispenses'], today, session.get("id")))
        events = cur.fetchall()
        events = [{'id': id, 'nom': nom, 'branche': branche, "date": date, "jour": jour, "heure": heure, "description": description, "classe": classe, "createur": createur, "create_date": create_date, "type": type}
                   for id, nom, branche, date, jour, heure, description, classe, createur, create_date, type in events]

    with connect_db() as cur:
        cur.execute("SELECT * FROM events WHERE nom = ? AND classe = ?", (nom, classe))
        infos_event = cur.fetchall()
        infos_event = infos_event[0]
        infos_event = {
            "nom": infos_event[1],
            "branche": infos_event[2],
            "date": infos_event[3],
            "jour": infos_event[4],
            "heure": infos_event[5],
            "description": infos_event[6],
            "classe": infos_event[7],
            "e_mail": infos_event[8],
            "create_date": infos_event[9],
        }

    with connect_db() as cur:
        cur.execute("SELECT nom, prenom FROM users WHERE e_mail = ?", (infos_event["e_mail"],))
        createur = cur.fetchall()[0]
        createur = str(createur[0]) + " " + str(createur[1])

    return render_template("Event_print.html", events = events, infos_event = infos_event, createur = createur, isModify = isModify)





@app.route("/new_account", methods = ["GET"])
def new_account():
    # Rempli les espace s'il les avait déjà donné avant mais avec e_mail invalide
    return render_template("New_Account.html", nom = session.get("new_account_nom"), cours_dispenses = session.get("new_account_cours_dispenses"),classe = session.get("new_account_classe"),prenom = session.get("new_account_prenom")  )


@app.route("/login", methods=["GET"])
def login():
    user_id = session.get('id')
    if not user_id:
        return render_template("Login.html")
    
    return redirect(url_for('index'))


@app.route("/account", methods=["GET"])
def account():
    loggedin = session.get('loggedin')
    if loggedin:
            return render_template("Account.html")
        
    return redirect(url_for('login'))


@app.route("/parametres", methods=["GET"])
def parametres():
    today = date.today()
    user_id = session.get('id') 
    if not user_id:
        return redirect(url_for('account'))
    
    OS = "OS_" + session["o_s"] + "_" + session["classe"][:2]  
    OC = "OC_" + session['o_c'] + "_" + session["classe"][:2]
    
    with connect_db() as cur:
        # Affiche les tests / devoirs/ events masqués
        cur.execute("SELECT * FROM tests WHERE id IN ( SELECT test_id FROM hidden_tests WHERE user_id = ?)", (user_id, ))
        tests = cur.fetchall()
        tests = [{'id':id, 'nom':nom, 'branche':branche,"date": date,"jour": jour,"heure": heure, "description":description,"classe": classe,"createur":createur,"create_date":create_date, "type": type+"_print"}
            for id, nom, branche,date,jour,heure,description, classe, createur, create_date,type in tests]
        
        # Affiche les tests/ devoirs / events passés
        cur.execute("SELECT * FROM tests WHERE (classe = ? OR classe = ? OR classe = ?) AND date < ? ORDER BY date ASC", (session["classe"], OS, OC, today))
        tests_passe = cur.fetchall()
        tests_passe = [{'id':id, 'nom':nom, 'branche':branche,"date": date,"jour": jour,"heure": heure, "description":description,"classe": classe,"createur":createur,"create_date":create_date, "type": type+"_print"}
            for id, nom, branche,date,jour,heure,description, classe, createur, create_date, type in tests_passe]
        
        cur.execute("SELECT * FROM devoirs WHERE id IN ( SELECT devoir_id FROM hidden_devoirs WHERE user_id = ?)", (user_id, ))
        devoirs = cur.fetchall()
        devoirs = [{'id':id, 'nom':nom, 'branche':branche,"date": date,"jour": jour,"heure": heure, "description":description,"classe": classe,"createur":createur,"create_date":create_date, "type": type+"_print"}
            for id, nom, branche,date,jour,heure,description, classe, createur, create_date, type in devoirs]
        
        cur.execute("SELECT * FROM devoirs WHERE (classe = ? OR classe = ? OR classe = ?) AND date < ? ORDER BY date ASC", (session["classe"], OS, OC, today))
        devoirs_passe = cur.fetchall()
        devoirs_passe = [{'id':id, 'nom':nom, 'branche':branche,"date": date,"jour": jour,"heure": heure, "description":description,"classe": classe,"createur":createur,"create_date":create_date, "type": type+"_print"}
            for id, nom, branche,date,jour,heure,description, classe, createur, create_date, type in devoirs_passe]

        cur.execute("SELECT * FROM events WHERE id IN ( SELECT event_id FROM hidden_events WHERE user_id = ?)", (user_id, ))
        events = cur.fetchall()
        events = [{'id': id, 'nom': nom, 'branche': branche, "date": date, "jour": jour, "heure": heure, "description": description, "classe": classe, "createur": createur, "create_date": create_date, "type": type+"_print"}
                  for id, nom, branche, date, jour, heure, description, classe, createur, create_date, type in events]

        cur.execute("SELECT * FROM events WHERE (classe = ? OR classe = ? OR classe = ?) AND date < ? ORDER BY date ASC", (session["classe"], OS, OC, today))
        events_passe = cur.fetchall()
        events_passe = [{'id': id, 'nom': nom, 'branche': branche, "date": date, "jour": jour, "heure": heure, "description": description, "classe": classe, "createur": createur, "create_date": create_date, "type": type+"_print"}
                        for id, nom, branche, date, jour, heure, description, classe, createur, create_date, type in events_passe]

    return render_template("Parametres.html", tests=tests, tests_passe=tests_passe, devoirs=devoirs, devoirs_passe=devoirs_passe, events = events, events_passe = events_passe)



@app.route("/essai", methods=["GET"])
def essai():
    return render_template("essai.html")

@app.route("/new_class", methods=["GET"])
def new_class():
    return render_template("add_class.html")

@app.route("/add_class", methods=["POST"])
def add_class():
    class_name = request.form['class_name']
    with connect_db() as cur:
        cur.execute("SELECT * FROM horaires WHERE classe = ?", (class_name,))
        data = cur.fetchall()
        if data:
            flash("Classe déjà existante")
            return redirect(url_for('new_class'))
        else:
            for jour in range (1,6):
                for periode in range (1,11):
                    matiere = request.form[str(jour) + ";" + str(periode)]
                    cur.execute("INSERT INTO horaires (classe, jour, periode, matiere) VALUES (?,?,?,?)", (class_name, jour, periode, matiere))
        return redirect(url_for('new_class'))
            

#-Gestion du Compte-------------------------------------------------------------

@app.route("/creat_account", methods=["POST"])
def creat_account():
    nom = request.form["nom"]
    prenom = request.form["prenom"]
    e_mail = request.form["e_mail"]
    mot_de_passe= request.form["mot_de_passe"].encode('utf-8')
    classe = request.form["classe"]
    o_s = request.form["o_s"]
    o_c = request.form["o_c"]
    groupe = request.form["groupe"]
    cours_dispenses = request.form["cours_dispenses"]
    isBillingue = request.form["isBillingue"]
    
    with connect_db() as cur:
        cur.execute("SELECT id FROM users WHERE e_mail = ?",(e_mail, ))
        data_user = cur.fetchall()
        # Verifie si l'email n'a pas déjà été utilisé
        if data_user !=[]:
            flash("Nom d'utilisateur déja utilisé")
            return redirect(url_for("new_account"))  

    if nom == "ADMIN":
        flash(" Dommage Frommage !!!")
        return redirect(url_for('new_account'))

    salt = bcrypt.gensalt()
    hashed_mot_de_passe = bcrypt.hashpw(mot_de_passe, salt)  

    # Crée un nouvel utilisateur
    with connect_db() as cur:
        cur.execute('INSERT INTO users (nom, prenom, e_mail,mot_de_passe, classe, o_s, o_c, groupe, cours_dispenses, isBillingue) VALUES (?,?,?,?,?,?,?,?,?,?)', (nom, prenom, e_mail,hashed_mot_de_passe,classe, o_s, o_c, groupe, cours_dispenses, isBillingue))
    
    # Selectionne l'id du nouvel utilisateur 
    with connect_db() as cur:
        cur.execute("SELECT id FROM users WHERE e_mail = ?",(e_mail, ))
        data_user = cur.fetchall()[0][0]

    session["id"] = data_user
    session["loggedin"] = True
    session["nom"]= nom
    session["prenom"]= prenom
    session["e_mail"]= e_mail
    session["o_s"]= o_s
    session["o_c"]= o_c
    session["classe"]= classe
    session["groupe"] = groupe
    session["cours_dispenses"]= cours_dispenses
    session["isBillingue"] = isBillingue
    
    return redirect(url_for('index'))

@app.route("/modify_account", methods=["POST"])
def modify_account():
    if session["e_mail"] == 'admin@eduvaud.ch':
        flash("Impossible de modifier son compte pour l'admin")
        return redirect(url_for('account'))

    elif session['e_mail'] != request.form['e_mail']:
        flash("Impossible de modifier l'e-mail, veuillez contacteur l'admin à l'adresse admin@eduvaud.ch")
        return redirect(url_for("account"))
    
    #Verifie que personne ne devienne ADMIN
    elif request.form["nom"] == "ADMIN":        
        flash("Dommage Frommage")
        return redirect(url_for('account'))
    
    else:
        session["nom"]= request.form["nom"]
        session["prenom"]= request.form["prenom"]
        session["o_s"]= request.form["o_s"]
        session["o_c"]= request.form["o_c"]
        session["classe"]= request.form["classe"]
        session["groupe"] = request.form['groupe']
        session["isBillingue"] = request.form["isBillingue"]
        session["cours_dispenses"]= request.form["matieres"]
        with connect_db() as cur:
            cur.execute("UPDATE users SET nom = ?, prenom = ?, classe = ?, o_s = ?, o_c = ?, groupe = ?, cours_dispenses = ?, isBillingue = ? WHERE e_mail = ?", 
                        (session["nom"], session["prenom"], session["classe"], session["o_s"], session["o_c"], session["groupe"], session["cours_dispenses"], session["isBillingue"], session['e_mail']))
        return redirect(url_for("account"))


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for('account'))


@app.route("/try_login", methods=["POST"])
def try_login():
    e_mail_login = request.form["e_mail"]
    mot_de_passe_login = request.form ['mot_de_passe'].encode('utf-8')
    with connect_db() as cur:
        cur.execute("SELECT * FROM users WHERE e_mail = ?",(e_mail_login, ))
        data_user = cur.fetchall()
        data_user = [{"id": id, "nom": nom, "prenom": prenom,"e_mail": e_mail,"mot_de_passe": mot_de_passe,"classe": classe ,"o_s": o_s,"o_c": o_c,"groupe":groupe , "cours_dispenses": cours_dispenses,"isBillingue": isBillingue}
                      for id, nom, prenom, e_mail, mot_de_passe,classe, o_s, o_c, groupe, cours_dispenses, isBillingue in data_user]
    
    if data_user == []:
        flash("Nom d'utilisateur ou mot de passe incorrect. user")
        return redirect(url_for("login"))

    # Selectionne la première et unique liste de data_user pour avoir le dictionnaire 
    data_user = data_user[0]

    if  bcrypt.checkpw(mot_de_passe_login, data_user["mot_de_passe"]):
        session["id"] = data_user["id"]
        session["loggedin"] = True
        session["nom"]= data_user["nom"]
        session["prenom"]= data_user["prenom"]
        session["e_mail"]= data_user["e_mail"]
        session["o_s"]= data_user["o_s"]
        session["o_c"]= data_user["o_c"]
        session["classe"]= data_user["classe"]
        session["groupe"] = data_user["groupe"]
        session["cours_dispenses"]= data_user["cours_dispenses"]

        return redirect(url_for("index"))

    else:
        flash("Nom d'utilisateur ou mot de passe incorrect. mdp")
        return redirect(url_for("login"))


@app.route("/delete_account", methods=["POST"])
def delete_account():
    with connect_db() as cur:
        cur.execute("DELETE FROM hidden_tests WHERE user_id = ?", (session['id'],))
        cur.execute("DELETE FROM hidden_events WHERE user_id = ?", (session['id'],))
        cur.execute("DELETE FROM hidden_devoirs WHERE user_id = ?", (session['id'],))
        cur.execute("DELETE FROM users WHERE e_mail = ?", (session['e_mail'], ))
    session.clear()
    return redirect(url_for("account"))

#--- Truc ADMIN pour debugger----------------

@app.route("/admin_loggedin", methods=["GET"])
def admin_loggedin():
    session["nom"]= "ADMIN"
    session["prenom"]= "Devlopper"
    session["loggedin"]= True
    return redirect(url_for('index'))


@app.route("/admin_logout")
def admin_logout():
    session.clear()
    return (redirect(url_for("index")))


#--Gestion des Tests-----

@app.route("/create_test", methods = ["POST"])
def create_test():
    
    type = "test"

    nom = request.form["nom"]
    branche = request.form["branche"]
    date = request.form["date"]
    heure = request.form["heure"]
    description = request.form["description"]
    jour = jours_semaine[int(datetime.strptime(date, "%Y-%m-%d").weekday())]
    
    # Change le nom de la classe si c'est dans l'OS ou l'OC pour affecter aussi les autres qui sont dans les mêmes options
    if branche == "OC":
        classe = "OC_"+ session["o_c"]+ "_"+ session["classe"][:2]
    elif branche == "OS":
        classe = "OS_" +session["o_s"]+ "_" + session["classe"][:2]
    else:
        classe = session["classe"]
    
    create_date = "Créé le "+ datetime.now().strftime("%d %B %Y") + " à " + datetime.now().strftime("%H:%M")
    create_date = create_date.replace("Ã©", "é").replace("Ã", "é")
    create_date = create_date.replace(create_date.split(" ")[3], create_date.split(" ")[3].capitalize())

    #verifie si le nom n'est pas déjà utilisé pour la classe
    with connect_db() as cur:
        cur.execute("SELECT * FROM tests WHERE nom = ? AND classe = ?",(nom, classe ))
        nom_test = cur.fetchall()
        if nom_test !=[]:
            flash("Nom déja utilisé")
            return redirect(url_for("test"))

    # Ajoute à la base de données les infos du test
    with connect_db() as cur:
        cur.execute('INSERT INTO tests (nom, branche, date, jour, heure, description, classe, createur, create_date, type) VALUES (?,?,?,?,?,?,?,?,?,?)', (nom, branche,date,jour,heure,description, classe, session["e_mail"], create_date, type))
    
    return redirect(url_for("test_print",nom = nom, classe = classe))


@app.route("/delete_test", methods=["POST"])
def delete_test():
    test_id = request.form["id"]

    redirect_url = request.form["redirect"]

    # Supprime en premier dans les tests masqué pour ne pas avoir de message d'erreur
    with connect_db() as cur:
        cur.execute("DELETE FROM hidden_tests WHERE test_id = ?", (test_id,))
        cur.execute("DELETE FROM tests WHERE id = ?", (test_id,))

    return redirect(redirect_url)


@app.route("/hide_test", methods=["POST"])
def hide_test():
    test_id = request.form["id"]
    user_id = session.get("id")

    # Pour rediriger vers la page initiale par ex. index-> index ou test -> test 
    redirect_url = request.form["redirect"]

    with connect_db() as cur:        
        cur.execute( "INSERT OR IGNORE INTO hidden_tests (user_id, test_id) VALUES (?, ?)", (user_id, test_id))

    return redirect(redirect_url)


@app.route("/unhide_test", methods=["POST"])
def unhide_test():
    test_id = request.form["id"]
    user_id = session["id"]

    with connect_db() as cur:
        cur.execute( "DELETE FROM hidden_tests WHERE user_id = ? AND test_id = ?", (user_id, test_id),)

    return redirect(url_for('parametres'))

#-- Pour ADMIN ---------------
@app.route("/delete_all_test", methods = ["POST"])
def delete_all_test():
    with connect_db() as cur:
        cur.execute("DELETE FROM hidden_tests")
        cur.execute("DELETE FROM tests")

    return redirect(url_for("index"))



#--------Devoirs--------------------------

@app.route("/create_devoir", methods=["POST"])
def create_devoir():
    type = "devoir"

    nom = request.form["nom"]
    branche = request.form["branche"]
    date = request.form["date"]
    heure = request.form["heure"]
    description = request.form["description"]
    jour = jours_semaine[int(datetime.strptime(date, "%Y-%m-%d").weekday())]
    
    if branche == "OC":
        classe = "OC_" + session["o_c"] + "_" + session["classe"][:2]
    elif branche == "OS":
        classe = "OS_" + session["o_s"] + "_" + session["classe"][:2]
    else:
        classe = session["classe"]

    create_date = "Créé le " + datetime.now().strftime("%d %B %Y") + " à " + datetime.now().strftime("%H:%M")
    create_date = create_date.replace("Ã©", "é").replace("Ã", "é")
    create_date = create_date.replace(create_date.split(" ")[3], create_date.split(" ")[3].capitalize())

    with connect_db() as cur:
        cur.execute("SELECT * FROM devoirs WHERE nom = ? AND classe = ?", (nom, classe))
        nom_devoir = cur.fetchall()
        if nom_devoir != []:
            flash("Nom déjà utilisé")
            return redirect(url_for("devoirs"))

    with connect_db() as cur:
        cur.execute('INSERT INTO devoirs (nom, branche, date, jour, heure, description, classe, createur, create_date, type) VALUES (?,?,?,?,?,?,?,?,?,?)', 
                    (nom, branche, date, jour, heure, description, classe, session["e_mail"], create_date, type))

    return redirect(url_for("devoir_print", nom=nom, classe=classe))


@app.route("/delete_devoir", methods=["POST"])
def delete_devoir():
    devoir_id = request.form["id"]
    redirect_url = request.form["redirect"]
    with connect_db() as cur:
        cur.execute("DELETE FROM hidden_devoirs WHERE devoir_id = ?", (devoir_id,))
        cur.execute("DELETE FROM devoirs WHERE id = ?", (devoir_id,))

    return redirect(redirect_url)



@app.route("/hide_devoir", methods=["POST"])
def hide_devoir():
    devoir_id = request.form["id"]
    redirect_url = request.form["redirect"]
    with connect_db() as cur:
        user_id = session.get("id")
        cur.execute("INSERT OR IGNORE INTO hidden_devoirs (user_id, devoir_id) VALUES (?, ?)", (user_id, devoir_id))

    return redirect(redirect_url)


@app.route("/unhide_devoir", methods=["POST"])
def unhide_devoir():
    devoir_id = request.form["id"]
    user_id = session["id"]
    with connect_db() as cur:
        cur.execute("DELETE FROM hidden_devoirs WHERE user_id = ? AND devoir_id = ?", (user_id, devoir_id), )

    return redirect(url_for('parametres'))

#-- Pour ADMIN-------------------

@app.route("/delete_all_devoirs", methods=["POST"])
def delete_all_devoirs():
    with connect_db() as cur:
        cur.execute("DELETE FROM hidden_devoirs" )
        cur.execute("DELETE FROM devoirs")

    return redirect(url_for("index"))



#-------Events-------------------

@app.route("/create_event", methods=["POST"])
def create_event(): 
    type = "event"

    nom = request.form["nom"]
    branche = request.form["branche"]
    date = request.form["date"]
    heure = request.form["heure"]
    description = request.form["description"]
    jour = jours_semaine[int(datetime.strptime(date, "%Y-%m-%d").weekday())]

    if branche == "OC":
        classe = "OC_" + session["o_c"] + "_" + session["classe"][:2]
    elif branche == "OS":
        classe = "OS_" + session["o_s"] + "_" + session["classe"][:2]
    else:
        classe = session["classe"]

    create_date = "Créé le " + datetime.now().strftime("%d %B %Y") + " à " + datetime.now().strftime("%H:%M")
    create_date = create_date.replace("Ã©", "é").replace("Ã", "é")
    create_date = create_date.replace(create_date.split(" ")[3], create_date.split(" ")[3].capitalize())

    with connect_db() as cur:
        cur.execute("SELECT * FROM events WHERE nom = ? AND classe = ?", (nom, classe))
        nom_event = cur.fetchall()
        if nom_event != []:
            flash("Nom déjà utilisé")
            return redirect(url_for("event"))

    with connect_db() as cur:
        cur.execute('INSERT INTO events (nom, branche, date, jour, heure, description, classe, createur, create_date, type) VALUES (?,?,?,?,?,?,?,?,?, ?)', 
                    (nom, branche, date, jour, heure, description, classe, session["e_mail"], create_date, type))
    return redirect(url_for("event_print", nom=nom, classe=classe))



@app.route("/delete_event", methods=["POST"])
def delete_event():
    event_id = request.form["id"]
    redirect_url = request.form["redirect"]
    with connect_db() as cur:
        cur.execute("DELETE FROM hidden_events WHERE event_id = ?", (event_id,))
        cur.execute("DELETE FROM events WHERE id = ?", (event_id,))

    return redirect(redirect_url)


@app.route("/hide_event", methods=["POST"])
def hide_event():
    event_id = request.form["id"]
    redirect_url = request.form["redirect"]
    with connect_db() as cur:
        user_id = session.get("id")
        cur.execute("INSERT OR IGNORE INTO hidden_events (user_id, event_id) VALUES (?, ?)", (user_id, event_id))

    return redirect(redirect_url)


@app.route("/unhide_event", methods=["POST"])
def unhide_event():
    event_id = request.form["id"]
    user_id = session["id"]

    with connect_db() as cur:
        cur.execute("DELETE FROM hidden_events WHERE user_id = ? AND event_id = ?", (user_id, event_id))

    return redirect(url_for('parametres'))


#-- Pour ADMIN----------------

@app.route("/delete_all_events", methods=["POST"])
def delete_all_events():
    with connect_db() as cur:
        cur.execute("DELETE FROM hidden_events" )
        cur.execute("DELETE FROM events")

    return redirect(url_for("index"))


#--- AU CAS OU --------------------
@app.route('/MAJ', methods= ["GET"])
def maj():
    with connect_db() as cur:
        cur.execute("SELECT * FROM users WHERE nom = 'ADMIN' ")
        data_user = cur.fetchall()
        if data_user == []:
            salt = bcrypt.gensalt()
            hashed_mot_de_passe = bcrypt.hashpw('admin'.encode('utf-8'), salt) 
            cur.execute("INSERT INTO users (nom, prenom, e_mail,mot_de_passe, classe, o_s, o_c, groupe, cours_dispenses, isBillingue) VALUES (?,?,?,?,?,?,?,?,?,?)", ("ADMIN","amdin","admin@eduvaud.ch",hashed_mot_de_passe,"3M8", "Maths et Physique", "Informatique", "A", "","non"))

     #   cur.execute("""CREATE TABLE IF NOT EXISTS users (
#    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
 #   "nom" TEXT NOT NULL,
  #  "prenom" TEXT NOT NULL,
   # "e_mail" TEXT NOT NULL,
    #"mot_de_passe" TEXT NOT NULL,
#    "classe" TEXT NOT NULL,
 #   "o_s" TEXT NOT NULL,
  #  "o_c" TEXT NOT NULL,
   # "groupe" TEXT NOT NULL,
    #"cours_dispenses" TEXT,
#    "isBillingue" TEXT NOT NULL
#);""")
    #   cur.execute("DROP TABLE tests")
    #    cur.execute("DROP TABLE events")
    #    cur.execute("DROP TABLE devoirs")

    return redirect(url_for('index'))

    





if __name__ == '__main__':
    with connect_db() as cur:
        with open('create_db.sql') as f:
            cur.executescript(f.read())
    app.run(host='0.0.0.0', port=5000, debug=True) 
