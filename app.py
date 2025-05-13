# Importerer nødvendige moduler fra Flask og andre biblioteker
from flask import Flask, render_template, request, redirect, session, url_for, flash
import sqlite3  # Brukes for å håndtere SQLite-databasen
import os       # For å generere en tilfeldig secret key

# Oppretter Flask-applikasjonen
app = Flask(__name__)

# Setter en hemmelig nøkkel som brukes til å sikre sesjonsdata
app.secret_key = os.urandom(24)

# Initialiserer databasen – kjøres én gang når appen starter
def init_db():
    conn = sqlite3.connect("meldinger.db")
    c = conn.cursor()

    # Oppretter tabellen for kontaktskjema-meldinger hvis den ikke finnes
    c.execute('''
        CREATE TABLE IF NOT EXISTS kontakt (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            navn TEXT,
            epost TEXT,
            beskjed TEXT
        )
    ''')

    # Oppretter tabellen for brukere (admin) med unikt brukernavn
    c.execute('''
        CREATE TABLE IF NOT EXISTS brukere (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brukernavn TEXT UNIQUE,
            passord TEXT,
            rolle TEXT
        )
    ''')

    # Lagrer endringer og lukker tilkoblingen
    conn.commit()
    conn.close()

# Hovedruten – videresender automatisk til /kontakt
@app.route("/")
def index():
    return redirect("/kontakt")

# Rute for kontaktskjemaet
@app.route("/kontakt", methods=["GET", "POST"])
def kontakt():
    if request.method == "POST":
        # Henter data fra skjemaet
        navn = request.form["navn"]
        epost = request.form["epost"]
        beskjed = request.form["beskjed"]

        # Lagrer meldingen i databasen
        conn = sqlite3.connect("meldinger.db")
        c = conn.cursor()
        c.execute("INSERT INTO kontakt (navn, epost, beskjed) VALUES (?, ?, ?)", (navn, epost, beskjed))
        conn.commit()
        conn.close()

        # Sender bruker til takk-siden
        return redirect("/takk")

    # Viser kontaktsiden (GET-forespørsel)
    return render_template("kontakt.html")

# Takkeside etter at en melding er sendt
@app.route("/takk")
def takk():
    return render_template("takk.html")

# Admin-panelet hvor man ser innsendte meldinger
@app.route("/admin")
def admin():
    # Sjekker at brukeren er innlogget og har rollen "admin"
    if not session.get("innlogget") or session.get("rolle") != "admin":
        return redirect("/login")

    # Henter alle meldinger fra databasen for visning
    conn = sqlite3.connect("meldinger.db")
    c = conn.cursor()
    c.execute("SELECT * FROM kontakt")
    meldinger = c.fetchall()
    conn.close()

    return render_template("admin.html", meldinger=meldinger)

# Login-side for admin
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Henter brukernavn og passord fra skjema
        brukernavn = request.form["brukernavn"]
        passord = request.form["passord"]

        # Sjekker om brukeren finnes i databasen
        conn = sqlite3.connect("meldinger.db")
        c = conn.cursor()
        c.execute("SELECT * FROM brukere WHERE brukernavn = ? AND passord = ?", (brukernavn, passord))
        bruker = c.fetchone()
        conn.close()

        if bruker:
            # Hvis bruker finnes – logg inn og lagre info i sesjon
            session["innlogget"] = True
            session["brukernavn"] = brukernavn
            session["rolle"] = bruker[3]  # rolle = 'admin'
            return redirect("/admin")
        else:
            # Feil innlogging – vis feilmelding og prøv igjen
            flash("Feil brukernavn eller passord!")
            return redirect("/login")

    # Sjekker om det finnes noen admin-brukere – brukes for å vise registreringslenke
    conn = sqlite3.connect("meldinger.db")
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM brukere WHERE rolle = 'admin'")
    admin_count = c.fetchone()[0]
    conn.close()

    return render_template("login.html", vis_registrer=(admin_count == 0))

# Side for å registrere første admin-bruker
@app.route("/registrer", methods=["GET", "POST"])
def registrer():
    conn = sqlite3.connect("meldinger.db")
    c = conn.cursor()
    
    # Teller hvor mange admin-brukere som finnes
    c.execute("SELECT COUNT(*) FROM brukere WHERE rolle = 'admin'")
    admin_count = c.fetchone()[0]

    # Hvis det allerede finnes en admin, send til innlogging
    if admin_count > 0:
        return redirect("/login")

    if request.method == "POST":
        brukernavn = request.form["brukernavn"]
        passord = request.form["passord"]

        try:
            # Prøver å legge inn ny admin-bruker
            c.execute("INSERT INTO brukere (brukernavn, passord, rolle) VALUES (?, ?, 'admin')", (brukernavn, passord))
            conn.commit()

            # Logger inn brukeren automatisk
            session["innlogget"] = True
            session["brukernavn"] = brukernavn
            session["rolle"] = "admin"

            return redirect("/admin")
        except sqlite3.IntegrityError:
            # Håndterer duplikate brukernavn
            flash("Brukernavn allerede i bruk!")
            return redirect("/registrer")
        finally:
            conn.close()

    return render_template("registrer.html")

# Logg ut-funksjon – fjerner brukerens sesjon
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# Kjører appen hvis dette er hovedfilen
if __name__ == "__main__":
    init_db()  # Oppretter nødvendige tabeller
    app.run(debug=True)  # Starter Flask-serveren i debug-modus
