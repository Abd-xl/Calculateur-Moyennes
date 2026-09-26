from flask import Flask, render_template, request

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def accueil():
    notes = {
        "Maths": [15, 14, 16],
        "Physique": [17, 15],
        "SVT": [18, 16, 17]
    }

    message = None

    if request.method == "POST":
        matiere = request.form["matiere"]
        note = request.form["note"]
        message = f"Reçu : {matiere} — {note}/20"

    return render_template("index.html", notes=notes, message=message)


if __name__ == "__main__":
    app.run(debug=True)
