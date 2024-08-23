from flask import Flask, request, send_file
import os
import subprocess
import pandas as pd

app = Flask(__name__)

@app.route('/convert_ttl_to_csv', methods=['POST'])
def convert_ttl_to_csv():
    if 'file' not in request.files:
        return "No file part", 400
    
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400
    
    # Guardar el archivo TTL subido
    ttl_filename = 'uploaded_file.ttl'
    file.save(ttl_filename)
    
    # Convertir TTL a NT y luego a TSV
    nt_filename = 'output_file.nt'
    tsv_filename = 'output_file.tsv'
    subprocess.run(f"cat {ttl_filename} | graphy read -c ttl / tree / write -c ntriples > {nt_filename}", shell=True)
    subprocess.run(f"kgtk import-ntriples -i {nt_filename} -o {tsv_filename}", shell=True)
    
    # Limpiar prefijos en el TSV
    df = pd.read_csv(tsv_filename, sep='\t')
    df['node1'] = df['node1'].apply(remove_prefix)
    df['label'] = df['label'].apply(remove_prefix)
    df['node2'] = df['node2'].apply(remove_prefix)
    df.to_csv(tsv_filename, sep='\t', index=False)
    
    # Convertir TSV a CSV
    csv_filename = 'output_file.csv'
    df.to_csv(csv_filename, index=False)
    
    return send_file(csv_filename)

@app.route('/convert_ttl_to_html', methods=['POST'])
def convert_ttl_to_html():
    if 'file' not in request.files:
        return "No file part", 400
    
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400
    
    # Guardar el archivo TTL subido
    ttl_filename = 'uploaded_file.ttl'
    file.save(ttl_filename)
    
    # Convertir TTL a NT y luego a TSV
    nt_filename = 'output_file.nt'
    tsv_filename = 'output_file.tsv'
    subprocess.run(f"cat {ttl_filename} | graphy read -c ttl / tree / write -c ntriples > {nt_filename}", shell=True)
    subprocess.run(f"kgtk import-ntriples -i {nt_filename} -o {tsv_filename}", shell=True)
    
    # Generar el gráfico HTML
    html_filename = 'graph.html'
    subprocess.run(f"kgtk visualize-graph -i {tsv_filename} -o {html_filename}", shell=True)
    
    return send_file(html_filename)

def remove_prefix(value):
    if pd.isna(value):
        return value
    if isinstance(value, str) and value.startswith('^'):
        return value
    return value.split(':')[-1] if ':' in value else value

if __name__ == '__main__':
    app.run(debug=True)
