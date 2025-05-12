from flask import Flask, render_template, request, redirect
 
import sqlite3
 
app = Flask(__name__)
 
def init_db():
 
    conn = sqlite3.connect("meldinger.db")
 
    c = conn.cursor()
 
    c.execute('''
 
        CREATE TABLE IF NOT EXISTS kontakt (
 
            id INTEGER PRIMARY KEY AUTOINCREMENT,
 
            navn TEXT,
 
            epost TEXT,
 
            beskjed TEXT
 
        )
 
    ''')
 
    conn.commit()
 
    conn.close()
 
@app.route("/kontakt", methods=["GET", "POST"])
 
def kontakt():
 
    if request.method == "POST":
 
        navn = request.form["navn"]
 
        epost = request.form["epost"]
 
        beskjed = request.form["beskjed"]
 
        conn = sqlite3.connect('meldinger.db')  
 
        c = conn.cursor()
 
        c.execute("INSERT INTO kontakt (navn, epost, beskjed) VALUES (?, ?, ?)", (navn, epost, beskjed))
 
        conn.commit()
 
        conn.close()
 
        return redirect("/takk")
 
    return render_template("kontakt.html")
 
@app.route("/takk")
 
def takk():
 
    return "Takk for din henvendelse!"
 
@app.route("/admin")
 
def admin():
 
    conn = sqlite3.connect("meldinger.db")
 
    c = conn.cursor()
 
    c.execute("SELECT * FROM kontakt")
 
    data = c.fetchall()
 
    conn.close()
 
    return render_template("admin.html", meldinger=data)
 
if __name__ == "__main__":
 
    init_db()
 
    app.run(debug=True)
 
 
 
 
 