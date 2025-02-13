from flask import Flask, render_template, request, send_file, jsonify
import pandas as pd
from fpdf import FPDF
import os

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        nome_cliente = request.form.get('nome_cliente', 'Sconosciuto')
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
        return send_file(pdf_path, as_attachment=True)
    
    return render_template("index.html")

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
            
            if row[3] in ["Superserie", "Circuito"]:
                if last_type != row[3]:
                    series_value = row[1]  # Salva il valore delle serie solo per il primo esercizio
                    
                series_display = str(series_value) if last_type == row[3] else str(row[1])
            else:
                series_display = str(row[1])
                series_value = None
            
            pdf.cell(65, 10, row[0], border=1, fill=True)
            pdf.cell(30, 10, series_display, border=1, align='C', fill=True)
            pdf.cell(40, 10, str(row[2]), border=1, align='C', fill=True)
            pdf.ln()
            last_type = row[3]
    
    x_offset_cover = 155
    pdf.set_xy(x_offset_cover, 20)
    logo_path = "C:/Users/lucio/Desktop/NewchiaiaFitness/LogoNewChiaiaFitness.png"
    pdf.image(logo_path, x=x_offset_cover + 10, y=20, w=110)
    pdf.ln(70)

    pdf.set_font("Arial", "B", 14)
    pdf.set_xy(x_offset_cover + 10, pdf.get_y())
    pdf.cell(140, 10, f"Nome: {nome_cliente}", ln=True, align='L')
    pdf.set_xy(x_offset_cover + 10, pdf.get_y() + 5)
    pdf.set_text_color(0, 0, 255)
    pdf.cell(140, 10, "Blu=Superserie", ln=True, align='L')
    pdf.set_xy(x_offset_cover + 10, pdf.get_y() + 5)
    pdf.set_text_color(255, 102, 102)
    pdf.cell(140, 10, "Rosso=Circuiti", ln=True, align='L')
    pdf.set_text_color(0, 0, 0)
    pdf.set_xy(x_offset_cover + 10, pdf.get_y() + 5)
    pdf.cell(140, 10, f"Fino al: {scadenza}", ln=True, align='L')
    pdf.ln(20)
    
    output_folder = os.path.expanduser("~/Downloads")
    os.makedirs(output_folder, exist_ok=True)
    output_path = os.path.join(output_folder, filename)
    pdf.output(output_path)
    
    return output_path

if __name__ == '__main__':
    app.run(debug=True)
