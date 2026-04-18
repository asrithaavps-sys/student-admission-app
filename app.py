from flask import Flask, render_template, request, send_file
import os
from scraper import run_scraper

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
RESULT_FOLDER = "results"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

LAST_FILE = None


@app.route("/", methods=["GET", "POST"])
def index():
    global LAST_FILE

    if request.method == "POST":
        file = request.files.get("file")
        intake = request.form.get("intake", "Winter")

        if file and file.filename != "":
            path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(path)
            LAST_FILE = path

            df = run_scraper(path, intake)

            return render_template(
                "index.html",
                data=df.to_dict("records"),
                intake=intake
            )

    return render_template("index.html", data=None)


@app.route("/refresh")
def refresh():
    global LAST_FILE

    if LAST_FILE:
        df = run_scraper(LAST_FILE)
        return render_template("index.html", data=df.to_dict("records"))

    return "Upload file first"


@app.route("/download")
def download():
    file_path = os.path.join("results", "output.xlsx")

    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)

    return "No file available"


if __name__ == "__main__":
    print("🚀 Server running...")
    app.run(host="0.0.0.0", port=5000)