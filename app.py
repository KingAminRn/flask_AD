# Importerer nødvendige moduler
from flask import Flask, render_template, request, redirect, session, url_for, flash
import sqlite3         # Brukes for SQLite-databasen
import os              # Brukes for å lage en sikker sesjonsnøkkel

# Lager Flask-appen
app = Flask(__name__)

# Lager en tilfeldig hemmelig nøkkel for å beskytte brukersesjonene
app.secret_key = os.urandom(24)

# Funksjon som kjører én gang når appen starter – lager databasen og tabellene hvis de ikke finnes
def init_db():
    conn = sqlite3.connect("meldinger.db")  # Kobler til databasen (eller lager den)
    c = conn.cursor()

    # Lager tabell for kontaktskjema-meldinger
    c.execute('''
        CREATE TABLE IF NOT EXISTS kontakt (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            navn TEXT,
            epost TEXT,
            beskjed TEXT
        )
    ''')

    # Lager tabell for brukere (adminer)
    c.execute('''
        CREATE TABLE IF NOT EXISTS brukere (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brukernavn TEXT UNIQUE,
            passord TEXT,
            rolle TEXT
        )
    ''')

    conn.commit()   # Lagrer endringer
    conn.close()    # Lukker tilkoblingen

# Startside – sender brukeren videre til kontaktskjema
@app.route("/")
def index():
    return redirect("/kontakt")

# Kontakt-side hvor alle kan sende inn meldinger
@app.route("/kontakt", methods=["GET", "POST"])
def kontakt():
    session.clear()  # Sørger for at alle blir logget ut hver gang denne siden åpnes

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

        # Sender brukeren til takk-siden
        return redirect("/takk")

    # Viser skjemaet
    return render_template("kontakt.html")

# Takkeside etter at man har sendt inn skjema
@app.route("/takk")
def takk():
    return render_template("takk.html")

# Adminpanel – her ser man meldinger, kun tilgjengelig for innloggede adminer
@app.route("/admin")
def admin():
    # Sjekker om brukeren er logget inn og har rollen "admin"
    if not session.get("innlogget") or session.get("rolle") != "admin":
        return redirect("/login")

    # Henter meldinger fra databasen
    conn = sqlite3.connect("meldinger.db")
    c = conn.cursor()
    c.execute("SELECT * FROM kontakt")
    meldinger = c.fetchall()
    conn.close()

    return render_template("admin.html", meldinger=meldinger)

# Innloggingsside for admin
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Henter brukernavn og passord fra skjema
        brukernavn = request.form["brukernavn"]
        passord = request.form["passord"]

        # Sjekker mot databasen
        conn = sqlite3.connect("meldinger.db")
        c = conn.cursor()
        c.execute("SELECT * FROM brukere WHERE brukernavn = ? AND passord = ?", (brukernavn, passord))
        bruker = c.fetchone()
        conn.close()

        if bruker:
            # Innlogging vellykket – lagrer info i sesjon
            session["innlogget"] = True
            session["brukernavn"] = brukernavn
            session["rolle"] = bruker[3]  # Rollen er typisk "admin"
            return redirect("/admin")
        else:
            # Feil brukernavn/passord – viser feilmelding
            flash("Feil brukernavn eller passord!")
            return redirect("/login")

    # Viser login-siden (GET)
    # Sjekker om det finnes admin fra før, brukes for å vise registreringslenken i login.html
    conn = sqlite3.connect("meldinger.db")
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM brukere WHERE rolle = 'admin'")
    admin_count = c.fetchone()[0]
    conn.close()

    # Viser login.html, og gir beskjed om vi skal vise "registrer deg"-lenken
    return render_template("login.html", vis_registrer=(admin_count == 0))

# Side hvor hvem som helst kan registrere en ny admin
@app.route("/registrer", methods=["GET", "POST"])
def registrer():
    if request.method == "POST":
        brukernavn = request.form["brukernavn"]
        passord = request.form["passord"]

        conn = sqlite3.connect("meldinger.db")
        c = conn.cursor()

        try:
            # Prøver å opprette admin
            c.execute("INSERT INTO brukere (brukernavn, passord, rolle) VALUES (?, ?, 'admin')", (brukernavn, passord))
            conn.commit()

            # Logger inn den nye adminen automatisk
            session["innlogget"] = True
            session["brukernavn"] = brukernavn
            session["rolle"] = "admin"

            return redirect("/admin")
        except sqlite3.IntegrityError:
            # Brukernavnet finnes allerede
            flash("Brukernavnet er allerede i bruk!")
            return redirect("/registrer")
        finally:
            conn.close()

    # Viser registreringsskjemaet (GET)
    return render_template("registrer.html")

# Logg ut – sletter sesjonen og sender brukeren til login
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# Starter Flask-serveren
if __name__ == "__main__":
    init_db()        # Lager databasen hvis den ikke finnes
    app.run(debug=True)  # Kjører appen i utviklermodus
