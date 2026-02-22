from flask import Flask, render_template, request, redirect, send_from_directory, session, url_for
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "sua_chave_secreta"

# Configuração upload
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def criar_banco():
    conn = sqlite3.connect("rh.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS funcionarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            cpf TEXT,
            data_nascimento TEXT,
            cargo TEXT,
            salario REAL,
            status TEXT,
            documento TEXT
        )
    """)
    conn.commit()
    conn.close()

criar_banco()

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["usuario"]
        senha = request.form["senha"]
        if usuario == "admin" and senha == "1234":
            session["logado"] = True
            return redirect(url_for("index"))
        else:
            return render_template("login.html", erro="Usuário ou senha inválidos")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("logado", None)
    return redirect(url_for("login"))

@app.route("/")
def index():
    if not session.get("logado"):
        return redirect(url_for("login"))

    filtro = request.args.get("filtro")
    busca = request.args.get("busca")

    conn = sqlite3.connect("rh.db")
    cursor = conn.cursor()

    # Base da query
    query = "SELECT * FROM funcionarios WHERE 1=1"
    params = []

    if filtro:
        query += " AND status = ?"
        params.append(filtro)

    if busca:
        query += " AND nome LIKE ?"
        params.append(f"%{busca}%")

    cursor.execute(query, params)
    funcionarios = cursor.fetchall()
    
    # Cálculos para os cards do Dashboard
    cursor.execute("SELECT COUNT(*) FROM funcionarios")
    total_db = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM funcionarios WHERE status = 'Ativo'")
    ativos_db = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM funcionarios WHERE status = 'Inativo'")
    inativos_db = cursor.fetchone()[0]
    
    conn.close()

    return render_template(
        "index.html",
        funcionarios=funcionarios,
        total=total_db,
        ativos=ativos_db,
        inativos=inativos_db,
        filtro_atual=filtro
    )

@app.route("/cadastrar", methods=["POST"])
def cadastrar():
    nome = request.form["nome"]
    cpf = request.form["cpf"]
    data_nascimento = request.form["data_nascimento"]
    cargo = request.form["cargo"]
    salario = request.form["salario"]
    status = request.form["status"]

    arquivo = request.files["documento"]
    nome_arquivo = None

    if arquivo and arquivo.filename != "":
        nome_arquivo = secure_filename(arquivo.filename)
        arquivo.save(os.path.join(app.config["UPLOAD_FOLDER"], nome_arquivo))

    conn = sqlite3.connect("rh.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO funcionarios (nome, cpf, data_nascimento, cargo, salario, status, documento)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (nome, cpf, data_nascimento, cargo, salario, status, nome_arquivo))
    conn.commit()
    conn.close()

    return redirect(url_for("index"))

@app.route("/excluir/<int:id>")
def excluir(id):
    conn = sqlite3.connect("rh.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM funcionarios WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))

@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

if __name__ == "__main__":
    app.run(debug=True)