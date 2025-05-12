from flask import Flask, render_template, request, redirect, session, url_for, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

def init_db():
    conn = sqlite3.connect("meldinger.db")
    c = conn.cursor()

    # Meldinger-tabell
    c.execute('''
        CREATE TABLE IF NOT EXISTS kontakt (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            navn TEXT,
            epost TEXT,
            beskjed TEXT
        )
    ''')

    # Admin-brukere-tabell
    c.execute('''
        CREATE TABLE IF NOT EXISTS brukere (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brukernavn TEXT UNIQUE,
            passord TEXT,
            rolle TEXT
        )
    ''')

    conn.commit()
    conn.close()

@app.route("/")
def index():
    return redirect("/kontakt")

@app.route("/kontakt", methods=["GET", "POST"])
def kontakt():
    if request.method == "POST":
        navn = request.form["navn"]
        epost = request.form["epost"]
        beskjed = request.form["beskjed"]

        conn = sqlite3.connect("meldinger.db")
        c = conn.cursor()
        c.execute("INSERT INTO kontakt (navn, epost, beskjed) VALUES (?, ?, ?)", (navn, epost, beskjed))
        conn.commit()
        conn.close()

        return redirect("/takk")

    return render_template("kontakt.html")

@app.route("/takk")
def takk():
    return render_template("takk.html")

@app.route("/admin")
def admin():
    if not session.get("innlogget") or session.get("rolle") != "admin":
        return redirect("/login")

    conn = sqlite3.connect("meldinger.db")
    c = conn.cursor()
    c.execute("SELECT * FROM kontakt")
    meldinger = c.fetchall()
    conn.close()

    return render_template("admin.html", meldinger=meldinger)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        brukernavn = request.form["brukernavn"]
        passord = request.form["passord"]

        conn = sqlite3.connect("meldinger.db")
        c = conn.cursor()
        c.execute("SELECT * FROM brukere WHERE brukernavn = ? AND passord = ?", (brukernavn, passord))
        bruker = c.fetchone()
        conn.close()

        if bruker:
            session["innlogget"] = True
            session["brukernavn"] = brukernavn
            session["rolle"] = bruker[3]
            return redirect("/admin")
        else:
            flash("Feil brukernavn eller passord!")
            return redirect("/login")

    # Sjekk om det finnes noen administratorer:
    conn = sqlite3.connect("meldinger.db")
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM brukere WHERE rolle = 'admin'")
    admin_count = c.fetchone()[0]
    conn.close()

    return render_template("login.html", vis_registrer=(admin_count == 0))

@app.route("/registrer", methods=["GET", "POST"])
def registrer():
    conn = sqlite3.connect("meldinger.db")
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM brukere WHERE rolle = 'admin'")
    admin_count = c.fetchone()[0]

    if admin_count > 0:
        return redirect("/login")  # En admin finnes allerede

    if request.method == "POST":
        brukernavn = request.form["brukernavn"]
        passord = request.form["passord"]

        try:
            c.execute("INSERT INTO brukere (brukernavn, passord, rolle) VALUES (?, ?, 'admin')", (brukernavn, passord))
            conn.commit()
            session["innlogget"] = True
            session["brukernavn"] = brukernavn
            session["rolle"] = "admin"
            return redirect("/admin")
        except sqlite3.IntegrityError:
            flash("Brukernavn allerede i bruk!")
            return redirect("/registrer")
        finally:
            conn.close()

    return render_template("registrer.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
