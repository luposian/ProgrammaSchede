from flask import Flask, render_template, request, send_file, redirect, url_for, jsonify
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.dialects.postgresql import JSON
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import os
    
    app = Flask(__name__)
    
    # Configura il database con PostgreSQL su Render
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://clienti_db_user:vLLLRAV1IVQmKWtj29KV1ckdMJoIZSr8@dpg-cunbbi8gph6c73eq88lg-a.frankfurt-postgres.render.com/clienti_db'
    # 🔥 Aggiungi queste configurazioni per evitare errori di timeout
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,         # Numero massimo di connessioni nel pool
    'max_overflow': 5,       # Connessioni extra se il pool è pieno
    'pool_timeout': 30,      # Tempo massimo di attesa per una connessione
    'pool_recycle': 1800,    # Ricicla le connessioni dopo 30 minuti
    }
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Configura un pool di connessioni con pre-ping
    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'], pool_pre_ping=True)
    db = SQLAlchemy(app, engine_options={"pool_pre_ping": True})
    migrate = Migrate(app, db)  # Inizializzazione di Flask-Migrate
    
    
    # Modello della tabella Cliente
    class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    scadenza = db.Column(db.Date, nullable=False)
    scheda_pdf = db.Column(db.String(200), nullable=True)
    scheda_dati = db.Column(JSON, nullable=True)  # Nuovo campo per salvare i dati in formato JSON
    
    def __repr__(self):
        return f"Cliente('{self.nome}', '{self.email}', '{self.scadenza}')"
    
    # Creazione della tabella se non esiste
    with app.app_context():
    db.create_all()
    
    @app.route('/clienti')
    def clienti():
    try:
        clienti_lista = Cliente.query.with_entities(
            Cliente.id, Cliente.nome, Cliente.email, Cliente.scadenza, Cliente.scheda_pdf
        ).order_by(Cliente.scadenza).all()
    
        for cliente in clienti_lista:
            if cliente.scheda_pdf and not os.path.exists(cliente.scheda_pdf):
                print(f"⚠️ File PDF {cliente.scheda_pdf} non trovato!")
    
        return render_template("clienti.html", clienti=clienti_lista)
    except Exception as e:
        return f"Errore durante il caricamento dei clienti: {e}"
    
    
    @app.route('/elimina_cliente/<int:cliente_id>')
    def elimina_cliente(cliente_id):
    try:
        cliente = Cliente.query.get(cliente_id)
        if cliente:
            db.session.delete(cliente)
            db.session.commit()
            print(f"✅ Cliente {cliente.nome} eliminato con successo!")
        else:
            print(f"⚠️ Cliente con ID {cliente_id} non trovato!")
    
    except Exception as e:
        print(f"❌ Errore durante l'eliminazione del cliente: {e}")
    
    return redirect(url_for('clienti'))
    
    
    @app.route('/modifica_scheda/<int:cliente_id>')
    def modifica_scheda(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    return render_template("index.html", cliente=cliente)
    
    
    class CustomPDF(FPDF):
    def header(self):
        pass
    
    def generate_pdf(data_list, filename="Scheda_Allenamento.pdf", nome_cliente="Sconosciuto", scadenza="Senza Scadenza"):
    if not data_list:
        print("⚠️ Nessun dato ricevuto per generare il PDF.")
        return None
    
    pdf = CustomPDF("L", "mm", "A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    
        # Assicura che la cartella static esista
    if not os.path.exists("static"):
        os.makedirs("static")
    
    pdf.add_page()
    x_offset_cover = 90  
    pdf.set_xy(x_offset_cover, 20)
    logo_path = "LogoNewChiaiaFitness.png"
    
    if os.path.exists(logo_path):
        pdf.image(logo_path, x=x_offset_cover, y=20, w=110)
    else:
        print(f"⚠️ Il file logo {logo_path} non esiste!")
    
    pdf.ln(70)
    
    pdf.set_font("Arial", "B", 14)
    pdf.set_xy(20, pdf.get_y())
    pdf.cell(140, 10, f"Nome: {nome_cliente}", ln=True, align='L')
    pdf.cell(140, 10, f"Fino al: {scadenza}", ln=True, align='L')
    
    pdf.ln(10)
    
    for idx, esercizi in enumerate(data_list):
        pdf.add_page()
        pdf.set_font("Arial", "B", 12)
        pdf.cell(200, 10, f"Allenamento {idx + 1}", ln=True, align="C")
        pdf.ln(5)
    
        pdf.set_fill_color(0, 102, 204)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(65, 10, "Esercizio", border=1, align='C', fill=True)
        pdf.cell(30, 10, "Serie", border=1, align='C', fill=True)
        pdf.cell(40, 10, "Ripetizioni", border=1, align='C', fill=True)
        pdf.ln()
    
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", size=10)
    
        for row in esercizi:
            esercizio, serie, ripetizioni, tipo = row
            if tipo == "Superserie":
                pdf.set_fill_color(173, 216, 230)  # Blu
            elif tipo == "Circuito":
                pdf.set_fill_color(255, 102, 102)  # Rosso
            else:
                pdf.set_fill_color(255, 255, 255)
    
            pdf.cell(65, 10, esercizio, border=1, fill=True)
            pdf.cell(30, 10, str(serie), border=1, align='C', fill=True)
            pdf.cell(40, 10, str(ripetizioni), border=1, align='C', fill=True)
            pdf.ln()
    
    output_folder = "static/pdfs"
    os.makedirs(output_folder, exist_ok=True)  # Crea la cartella se non esiste
    output_path = os.path.join(output_folder, filename)
    
    pdf.output(output_path)
    return output_path
    
    
    @app.route('/', methods=['GET', 'POST'])
    def index():
    if request.method == 'POST':
        nome_cliente = request.form.get('nome_cliente', 'Sconosciuto')
        email_destinatario = request.form.get('email', '')
        scadenza = request.form.get('scadenza', 'Senza Scadenza')
    
        # Genera la scheda PDF
        allenamenti = []
        for i in range(3):  
            esercizi = request.form.getlist(f'esercizio_{i}[]')
            serie = request.form.getlist(f'serie_{i}[]')
            ripetizioni = request.form.getlist(f'ripetizioni_{i}[]')
            tipo = request.form.getlist(f'tipo_{i}[]')
            if esercizi and serie and ripetizioni and tipo:
                allenamenti.append(list(zip(esercizi, serie, ripetizioni, tipo)))
    
        pdf_path = generate_pdf(allenamenti, nome_cliente=nome_cliente, scadenza=scadenza)
    
        cliente_esistente = Cliente.query.filter_by(email=email_destinatario).first()
    
        if cliente_esistente:
            cliente_esistente.nome = nome_cliente
            cliente_esistente.scadenza = datetime.strptime(scadenza, "%Y-%m-%d")
            cliente_esistente.scheda_pdf = pdf_path
            cliente_esistente.scheda_dati = allenamenti
        else:
            nuovo_cliente = Cliente(
                nome=nome_cliente,
                email=email_destinatario,
                scadenza=datetime.strptime(scadenza, "%Y-%m-%d"),
                scheda_pdf=pdf_path,
                scheda_dati=allenamenti
            )
            db.session.add(nuovo_cliente)
    
        db.session.commit()
        return send_file(pdf_path, as_attachment=True)
    
    
    return render_template("index.html")
    
    
    
    if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=True)
