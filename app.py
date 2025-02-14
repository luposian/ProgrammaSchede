from flask import Flask, render_template, request, send_file, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
from fpdf import FPDF
from utils import generate_pdf
from datetime import datetime
import os



app = Flask(__name__)

# Configura il database con PostgreSQL su Render
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://clienti_db_user:vLLLRAV1IVQmKWtj29KV1ckdMJoIZSr8@dpg-cunbbi8gph6c73eq88lg-a/clienti_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modello della tabella Cliente
class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    scadenza = db.Column(db.Date, nullable=False)
    scheda_pdf = db.Column(db.String(200), nullable=True)

# Creazione della tabella se non esiste
if __name__ == '__main__':
    with app.app_context():
        db.create_all()

     
    def __repr__(self):
        return f"Cliente('{self.nome}', '{self.email}', '{self.scadenza}')"

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        nome_cliente = request.form.get('nome_cliente', 'Sconosciuto')
        scadenza = request.form.get('scadenza', 'Senza Scadenza')
        category = request.form.get('category', 'Generale')
        email_destinatario = request.form.get('email')
        
        allenamenti = []
        for i in range(3):
            esercizi = request.form.getlist(f'esercizio_{i}[]')
            serie = request.form.getlist(f'serie_{i}[]')
            ripetizioni = request.form.getlist(f'ripetizioni_{i}[]')
            tipo = request.form.getlist(f'tipo_{i}[]')
            if esercizi and serie and ripetizioni and tipo:
                allenamenti.append(list(zip(esercizi, serie, ripetizioni, tipo)))
        
        pdf_path = generate_pdf(allenamenti, category=category, nome_cliente=nome_cliente, scadenza=scadenza)

                return send_file(pdf_path, as_attachment=True)
    
    return render_template("index.html")

        # Salva il cliente nel database
        nuovo_cliente = Cliente(
            nome=nome_cliente,
            email=email_destinatario,
            scadenza=datetime.strptime(scadenza, "%Y-%m-%d"),
            scheda_pdf=pdf_path
        )
        db.session.add(nuovo_cliente)
        db.session.commit()



@app.route('/clienti')
def clienti():
    clienti_lista = Cliente.query.order_by(Cliente.scadenza).all()
    return render_template("clienti.html", clienti=clienti_lista)

@app.route('/elimina_cliente/<int:cliente_id>')
def elimina_cliente(cliente_id):
    cliente = Cliente.query.get(cliente_id)
    if cliente:
        db.session.delete(cliente)
        db.session.commit()
    return redirect(url_for('clienti'))

    
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=True) 
