from flask import Flask, render_template, request, redirect, send_from_directory
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ==============================
# HOME PAGE
# ==============================

@app.route("/")
def home():
    return render_template("index.html")


# ==============================
# SIGN UP
# ==============================

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        connection = sqlite3.connect("notehub.db")
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO users (name, email, password)
            VALUES (?, ?, ?)
            """,
            (name, email, password)
        )

        connection.commit()
        connection.close()

        return redirect("/login")

    return render_template("signup.html")


# ==============================
# LOGIN
# ==============================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        connection = sqlite3.connect("notehub.db")
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE email = ? AND password = ?
            """,
            (email, password)
        )

        user = cursor.fetchone()

        connection.close()

        if user:
            return redirect("/dashboard")

        else:
            return "Invalid email or password"

    return render_template("login.html")


# ==============================
# DASHBOARD
# ==============================

@app.route("/dashboard")
def dashboard():

    return render_template("dashboard.html")


# ==============================
# CREATE NOTE
# ==============================

@app.route("/create-note", methods=["GET", "POST"])
def create_note():

    if request.method == "POST":

        title = request.form["title"]
        subject = request.form["subject"]
        content = request.form["content"]

        pdf = request.files.get("pdf")

        pdf_filename = None

        # Check if a PDF was uploaded
        if pdf and pdf.filename:

            filename = secure_filename(pdf.filename)

            pdf_path = os.path.join(
                app.config["UPLOAD_FOLDER"],
                filename
            )

            pdf.save(pdf_path)

            pdf_filename = filename

        # Save note information in database
        connection = sqlite3.connect("notehub.db")
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO notes
            (title, subject, content, pdf_filename, user_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                title,
                subject,
                content,
                pdf_filename,
                1
            )
        )

        connection.commit()
        connection.close()

        # Temporary message to check PDF filename
        return f"Note created successfully! PDF: {pdf_filename}"

    return render_template("create_note.html")


# ==============================
# EXPLORE NOTES
# ==============================

@app.route("/explore")
def explore():

    connection = sqlite3.connect("notehub.db")
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM notes
        ORDER BY created_at DESC
        """
    )

    notes = cursor.fetchall()

    connection.close()

    return render_template(
        "explore.html",
        notes=notes
    )


# ==============================
# SEARCH NOTES
# ==============================

@app.route("/search", methods=["GET", "POST"])
def search():

    notes = []
    searched = False

    if request.method == "POST":

        keyword = request.form["keyword"]

        connection = sqlite3.connect("notehub.db")
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM notes
            WHERE title LIKE ?
            OR subject LIKE ?
            OR content LIKE ?
            ORDER BY created_at DESC
            """,
            (
                "%" + keyword + "%",
                "%" + keyword + "%",
                "%" + keyword + "%"
            )
        )

        notes = cursor.fetchall()

        connection.close()

        searched = True

    return render_template(
        "search.html",
        notes=notes,
        searched=searched
    )


# ==============================
# EDIT NOTE
# ==============================

@app.route("/edit-note/<int:note_id>", methods=["GET", "POST"])
def edit_note(note_id):

    connection = sqlite3.connect("notehub.db")
    cursor = connection.cursor()

    if request.method == "POST":

        title = request.form["title"]
        subject = request.form["subject"]
        content = request.form["content"]

        cursor.execute(
            """
            UPDATE notes
            SET title = ?, subject = ?, content = ?
            WHERE id = ?
            """,
            (
                title,
                subject,
                content,
                note_id
            )
        )

        connection.commit()
        connection.close()

        return redirect("/explore")

    cursor.execute(
        """
        SELECT *
        FROM notes
        WHERE id = ?
        """,
        (note_id,)
    )

    note = cursor.fetchone()

    connection.close()

    return render_template(
        "edit_note.html",
        note=note
    )


# ==============================
# DELETE NOTE
# ==============================

@app.route("/delete-note/<int:note_id>")
def delete_note(note_id):

    connection = sqlite3.connect("notehub.db")
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM notes
        WHERE id = ?
        """,
        (note_id,)
    )

    connection.commit()
    connection.close()

    return redirect("/explore")


# ==============================
# SERVE PDF FILES
# ==============================

@app.route("/uploads/<filename>")
def uploaded_file(filename):

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename
    )


# ==============================
# RUN APPLICATION
# ==============================

if __name__ == "__main__":

    app.run(debug=True)