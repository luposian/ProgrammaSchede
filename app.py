from flask import Flask, render_template, request, send_file, redirect, url_for, jsonify
from flask_mail import Mail, Message
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
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,
    'max_overflow': 5,
    'pool_timeout': 30,
    'pool_recycle': 1800,
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'], pool_pre_ping=True)
db = SQLAlchemy(app, engine_options={"pool_pre_ping": True})
migrate = Migrate(app, db)

# Configura Flask-Mail per l'invio delle email
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Cambia se usi un altro provider (es: Outlook)
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'schedenewchiaiafitness@gmail.com'  # 🔹 Inserisci la tua email
app.config['MAIL_PASSWORD'] = 'Luciotto10.'  # 🔹 Inserisci la password o App Password
app.config['MAIL_DEFAULT_SENDER'] = ('New Chiaia Fitness', 'schedenewchiaiafitness@gmail.com')

mail = Mail(app)  # Inizializza Flask-Mail


# Modello della tabella Cliente
class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    scadenza = db.Column(db.Date, nullable=False)
    scheda_pdf = db.Column(db.String(200), nullable=True)
    scheda_dati = db.Column(JSON, nullable=True)

    def __repr__(self):
        return f"Cliente('{self.nome}', '{self.email}', '{self.scadenza}')"

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

@app.route('/scarica_scheda/<int:cliente_id>')
def scarica_scheda(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)

    if cliente.scheda_pdf and os.path.exists(cliente.scheda_pdf):
        return send_file(cliente.scheda_pdf, as_attachment=True)
    else:
        return "Errore: Il file della scheda non esiste", 404

@app.route('/invia_scheda/<int:cliente_id>')
def invia_scheda(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)

    if cliente.scheda_pdf and os.path.exists(cliente.scheda_pdf):
        try:
            msg = Message("Scheda New Chiaia Fitness", recipients=[cliente.email])
            msg.body = f"Ciao {cliente.nome},\n\nIn allegato trovi la tua scheda di allenamento.\n\nNew Chiaia Fitness."
            
            with app.open_resource(cliente.scheda_pdf) as pdf:
                msg.attach("Scheda_Allenamento.pdf", "application/pdf", pdf.read())

            mail.send(msg)
            return redirect(url_for('clienti'))
        
        except Exception as e:
            return f"Errore nell'invio dell'email: {e}"
    
    return "Errore: Il file della scheda non esiste", 404


class CustomPDF(FPDF):
    def header(self):
        pass

def generate_pdf(data_list, filename="Scheda_Allenamento.pdf", nome_cliente="Sconosciuto", scadenza="Senza Scadenza"):
    if not data_list:
        print("⚠️ Nessun dato ricevuto per generare il PDF.")
        return None

    pdf = CustomPDF("L", "mm", "A4")
    pdf.set_auto_page_break(auto=True, margin=15)

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
                pdf.set_fill_color(173, 216, 230)
            elif tipo == "Circuito":
                pdf.set_fill_color(255, 102, 102)
            else:
                pdf.set_fill_color(255, 255, 255)

            pdf.cell(65, 10, esercizio, border=1, fill=True)
            pdf.cell(30, 10, str(serie), border=1, align='C', fill=True)
            pdf.cell(40, 10, str(ripetizioni), border=1, align='C', fill=True)
            pdf.ln()

    output_folder = "static/pdfs"
    os.makedirs(output_folder, exist_ok=True)
    output_path = os.path.join(output_folder, filename)
    pdf.output(output_path)
    return output_path

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        nome_cliente = request.form.get('nome_cliente', 'Sconosciuto')
        email_destinatario = request.form.get('email', '')
        scadenza = request.form.get('scadenza', 'Senza Scadenza')

        # 🏋️‍♂️ Estrazione degli allenamenti
        allenamenti = []
        for i in range(3):  
            esercizi = request.form.getlist(f'esercizio_{i}[]')
            serie = request.form.getlist(f'serie_{i}[]')
            ripetizioni = request.form.getlist(f'ripetizioni_{i}[]')
            tipo = request.form.getlist(f'tipo_{i}[]')

            if esercizi and serie and ripetizioni and tipo:
                allenamenti.append(list(zip(esercizi, serie, ripetizioni, tipo)))

        # 🚨 Controlla se ci sono dati validi prima di generare il PDF
        if not allenamenti:
            return "Errore: Nessun allenamento fornito!", 400

        # 📝 Genera il PDF
        pdf_path = generate_pdf(allenamenti, nome_cliente=nome_cliente, scadenza=scadenza)

        # 🚨 Controllo se il PDF è stato generato correttamente
        if not pdf_path or not os.path.exists(pdf_path):
            return "Errore: Generazione del PDF fallita!", 500

        # 🔍 Controlla se il cliente esiste già nel database
        cliente_esistente = Cliente.query.filter_by(email=email_destinatario).first()

        if cliente_esistente:
            # 📌 Se esiste, aggiorna i dati
            cliente_esistente.nome = nome_cliente
            cliente_esistente.scadenza = datetime.strptime(scadenza, "%Y-%m-%d")
            cliente_esistente.scheda_pdf = pdf_path
            cliente_esistente.scheda_dati = allenamenti
        else:
            # 🆕 Se non esiste, crea un nuovo cliente
            nuovo_cliente = Cliente(
                nome=nome_cliente,
                email=email_destinatario,
                scadenza=datetime.strptime(scadenza, "%Y-%m-%d"),
                scheda_pdf=pdf_path,
                scheda_dati=allenamenti
            )
            db.session.add(nuovo_cliente)

        # ✅ Salva nel database
        db.session.commit()

        return send_file(pdf_path, as_attachment=True)

    return render_template("index.html")


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=True)
