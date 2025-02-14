from flask import Flask, render_template, request, send_file, jsonify, redirect, url_for
import pandas as pd
from fpdf import FPDF
import os
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# Configurazione del database PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:///clienti.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modello per i clienti
class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    scadenza = db.Column(db.Date, nullable=False)
    scheda_pdf = db.Column(db.String(200), nullable=False)

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

        # Salva il cliente nel database
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
    
    pdf.add_page()
    x_offset_left = 10
    x_offset_right = 155
    y_start = pdf.get_y()
    
    for idx in range(len(data_list)):
        if idx == 2:
            pdf.add_page()
            x_offset = x_offset_left
        else:
            x_offset = x_offset_left if idx == 0 else x_offset_right
        
        pdf.set_xy(x_offset, y_start)
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
        for i, row in enumerate(data_list[idx]):
            pdf.set_xy(x_offset, pdf.get_y())
            fill_color = (173, 216, 230) if row[3] == "Superserie" else (255, 153, 102) if row[3] == "Circuito" else (255, 255, 255)
            pdf.set_fill_color(*fill_color)
            pdf.cell(65, 10, row[0], border=1, fill=True)
            pdf.cell(30, 10, str(row[1]), border=1, align='C', fill=True)
            pdf.cell(40, 10, str(row[2]), border=1, align='C', fill=True)
            pdf.ln()
    
    output_path = f"/tmp/{filename}"
    pdf.output(output_path)
    return output_path

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=True)
