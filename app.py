from flask import Flask, render_template, request, send_file, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
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


# Modello della tabella Cliente
class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    scadenza = db.Column(db.Date, nullable=False)
    scheda_pdf = db.Column(db.String(200), nullable=True)

    def __repr__(self):
        return f"Cliente('{self.nome}', '{self.email}', '{self.scadenza}')"

# Creazione della tabella se non esiste
with app.app_context():
    db.create_all()

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

class CustomPDF(FPDF):
    def header(self):
        pass

def generate_pdf(data_list, filename="Scheda_Allenamento.pdf", category="Generale", nome_cliente="Sconosciuto", scadenza="Senza Scadenza"):
    pdf = CustomPDF("L", "mm", "A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Creazione della copertina
    pdf.add_page()
    
    x_offset_cover = 90
    pdf.set_xy(x_offset_cover, 20)
    logo_path = "LogoNewChiaiaFitness.png"
    pdf.image(logo_path, x=x_offset_cover, y=20, w=110)
    pdf.ln(70)

    pdf.set_font("Arial", "B", 14)
    pdf.set_xy(20, pdf.get_y())
    pdf.cell(140, 10, f"Nome: {nome_cliente}", ln=True, align='L')
    pdf.set_xy(20, pdf.get_y() + 5)
    pdf.cell(140, 10, f"Fino al: {scadenza}", ln=True, align='L')
    pdf.set_xy(20, pdf.get_y() + 5)
    pdf.set_text_color(0, 0, 255)
    pdf.cell(140, 10, "Blu = Superserie", ln=True, align='L')
    pdf.set_xy(20, pdf.get_y() + 5)
    pdf.set_text_color(255, 102, 102)
    pdf.cell(140, 10, "Rosso = Circuiti", ln=True, align='L')
    pdf.set_text_color(0, 0, 0)
    pdf.ln(10)

    # Offset per le tabelle dalla seconda pagina in poi
    x_offset_left = 10
    x_offset_right = 155
    tables_on_page = 0
    first_table = True  # Indica se è la prima tabella della seconda pagina

    for idx, esercizi in enumerate(data_list):
        if first_table:
            # Dopo la copertina, iniziamo una nuova pagina per le tabelle
            pdf.add_page()
            tables_on_page = 0
            first_table = False

        if tables_on_page == 2:
            pdf.add_page()
            tables_on_page = 0

        # Posizionamento: una tabella a sinistra e una a destra
        x_offset = x_offset_left if tables_on_page == 0 else x_offset_right
        pdf.set_xy(x_offset, pdf.get_y())

        # Intestazione tabella
        pdf.set_fill_color(0, 102, 204)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(65, 10, "Esercizio", border=1, align='C', fill=True)
        pdf.cell(30, 10, "Serie", border=1, align='C', fill=True)
        pdf.cell(40, 10, "Ripetizioni", border=1, align='C', fill=True)
        pdf.ln()

        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", size=10)
        last_type = None
        series_value = None

        for row in esercizi:
            pdf.set_xy(x_offset, pdf.get_y())

            # Evidenziazione superserie e circuiti
            fill_color = (173, 216, 230) if row[3] == "Superserie" else (255, 153, 102) if row[3] == "Circuito" else (255, 255, 255)
            pdf.set_fill_color(*fill_color)

            if row[3] in ["Superserie", "Circuito"]:
                if last_type != row[3]:
                    series_value = row[1]
                series_display = str(series_value) if last_type == row[3] else str(row[1])
            else:
                series_display = str(row[1])
                series_value = None

            pdf.cell(65, 10, row[0], border=1, fill=True)
            pdf.cell(30, 10, series_display, border=1, align='C', fill=True)
            pdf.cell(40, 10, str(row[2]), border=1, align='C', fill=True)
            pdf.ln()
            last_type = row[3]

        tables_on_page += 1

    output_folder = os.path.expanduser("~/Downloads")
    os.makedirs(output_folder, exist_ok=True)
    output_path = os.path.join(output_folder, filename)
    pdf.output(output_path)

    return output_path


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        nome_cliente = request.form.get('nome_cliente', 'Sconosciuto')
        email_destinatario = request.form.get('email', 'email@esempio.com')
        scadenza = request.form.get('scadenza', 'Senza Scadenza')
        category = request.form.get('category', 'Generale')
        
        allenamenti = []
        for i in range(3):
            esercizi = request.form.getlist(f'esercizio_{i}[]')
            serie = request.form.getlist(f'serie_{i}[]')
            ripetizioni = request.form.getlist(f'ripetizioni_{i}[]')
            tipo = request.form.getlist(f'tipo_{i}[]')
            if esercizi and serie and ripetizioni and tipo:
                allenamenti.append(list(zip(esercizi, serie, ripetizioni, tipo)))
        
        pdf_path = generate_pdf(allenamenti, category=category, nome_cliente=nome_cliente, scadenza=scadenza)

        # **Salva il cliente nel database**
        nuovo_cliente = Cliente(
            nome=nome_cliente,
            email=email_destinatario,
            scadenza=datetime.strptime(scadenza, "%Y-%m-%d"),
            scheda_pdf=pdf_path
        )
        db.session.add(nuovo_cliente)
        db.session.commit()
        
        return send_file(pdf_path, as_attachment=True)

    return render_template("index.html")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=True)
