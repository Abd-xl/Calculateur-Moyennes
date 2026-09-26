from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def accueil():
    notes = {
        "Maths": [15, 14, 16],
        "Physique": [17, 15],
        "SVT": [18, 16, 17]
    }

    return render_template("index.html", notes=notes)


if __name__ == "__main__":
    app.run(debug=True)
