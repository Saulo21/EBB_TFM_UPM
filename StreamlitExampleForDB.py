import streamlit as st
import pandas as pd
import requests
import sqlite3
from io import StringIO
import streamlit.components.v1 as components
from data_transformation import transformar_data

# Configuración de la página
st.set_page_config(
    page_title="Análisis de la Ethical Black Box",
    page_icon="📊",
    layout="wide"
)

# Inicializar base de datos
def init_db():
    conn = sqlite3.connect('files.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            ttl BLOB,
            csv BLOB,
            html BLOB
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Guardar archivos en la base de datos
def save_files_to_db(filename, ttl_content, csv_content, html_content):
    conn = sqlite3.connect('files.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO files (filename, ttl, csv, html)
        VALUES (?, ?, ?, ?)
    ''', (filename, ttl_content, csv_content, html_content))
    conn.commit()
    conn.close()

# Cargar lista de archivos guardados desde la base de datos
def load_files_from_db():
    conn = sqlite3.connect('files.db')
    c = conn.cursor()
    c.execute('SELECT id, filename FROM files')
    files = c.fetchall()
    conn.close()
    return files

# Obtener contenido de un archivo específico desde la base de datos
def get_file_content(file_id):
    conn = sqlite3.connect('files.db')
    c = conn.cursor()
    c.execute('SELECT ttl, csv, html FROM files WHERE id=?', (file_id,))
    file_content = c.fetchone()
    conn.close()
    return file_content

# Logo en la parte superior centrado
c1, c2, c3 = st.columns([1, 3, 1])
with c1:
    st.image('images/logo_amor_azulupm.png', width=300)

# Logo y título
c1, c2, c3 = st.columns([1, 3, 1])
with c2:
    st.caption("")
    new_title = '''
    <div style="
        text-align: center;
        color: #00629b;
        font-size: 80px;
        font-weight: bold;
        font-family: 'Arial', sans-serif;
        background: linear-gradient(90deg, rgba(0,98,155,1) 0%, rgba(0,170,224,1) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
    ">
        Ethical Black Box
    </div>
    <hr style="border: 1px solid #00629b;">
    '''
    st.markdown(new_title, unsafe_allow_html=True)

# Sidebar para navegación
with st.sidebar:
    tab_title = '<p style="color:#00629b; font-size: 40px; margin-bottom: 0;">Control Panel</p>'
    st.markdown(tab_title, unsafe_allow_html=True)
    option = st.radio("Seleccione una opción", ["Subir Nuevo Archivo", "Ver Archivos Guardados"], index=0)

# Cargar el archivo CSS
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

load_css("style.css")

# Función para cargar el archivo TTL
def cargar_ttl():
    uploaded_file = st.file_uploader("Choose a TTL file", type="ttl")
    if uploaded_file is not None:
        return uploaded_file
    return None

# Lógica de la opción seleccionada en el sidebar
if option == "Subir Nuevo Archivo":
    # Tabs para la opción de "Subir Nuevo Archivo"
    tab1, tab2, tab3 = st.tabs(["Upload CSV", "ML Model", "Robot Statistics"])

    with tab1:
        st.markdown("# Upload TTL file")
        ttl_file = cargar_ttl()

        if ttl_file is not None:
            st.success("File successfully uploaded")

            # Enviar archivo TTL al servidor Flask para procesarlo
            files = {'file': ttl_file.getvalue()}
            response_csv = requests.post("http://localhost:5000/convert_ttl_to_csv", files=files)
            response_html = requests.post("http://localhost:5000/convert_ttl_to_html", files=files)

            if response_csv.status_code == 200 and response_html.status_code == 200:
                # Convertir la respuesta CSV en un DataFrame
                csv_content = response_csv.text
                data = pd.read_csv(StringIO(csv_content))

                st.markdown("# CSV analysis")
                num_rows = st.slider('Select number of rows to display', 1, 20, 10)
                st.dataframe(data.head(num_rows))

                st.markdown("# Knowledge Graph")
                html_content = response_html.text
                components.html(html_content, height=600)

                # Guardar archivos en la base de datos
                save_files_to_db(ttl_file.name, ttl_file.getvalue(), csv_content.encode(), html_content.encode())

                st.success("Archivos convertidos y guardados en la base de datos.")
                st.download_button(label="Descargar CSV", data=csv_content, file_name="converted.csv")
                st.download_button(label="Descargar HTML", data=html_content, file_name="converted.html")
            else:
                st.error("Error processing the TTL file.")

elif option == "Ver Archivos Guardados":
    # Tabs para la opción de "Ver Archivos Guardados"
    tab1, tab2, tab3 = st.tabs(["View Saved Files", "ML Model", "Robot Statistics"])

    with tab1:
        st.markdown("# Archivos Guardados")
        files = load_files_from_db()
        if files:
            file_dict = {filename: file_id for file_id, filename in files}
            selected_file = st.selectbox("Selecciona un archivo", list(file_dict.keys()))
            if selected_file:
                file_id = file_dict[selected_file]
                ttl_content, csv_content, html_content = get_file_content(file_id)

                st.markdown("# CSV analysis")
                data = pd.read_csv(StringIO(csv_content.decode()))
                num_rows = st.slider('Select number of rows to display', 1, 20, 10)
                st.dataframe(data.head(num_rows))

                st.markdown("# Knowledge Graph")
                components.html(html_content.decode(), height=600)

                st.download_button(label="Descargar CSV", data=csv_content, file_name="converted.csv")
                st.download_button(label="Descargar HTML", data=html_content, file_name="converted.html")
        else:
            st.write("No hay archivos guardados")

# Tab 3: Placeholder para futuras funcionalidades
with tab3:
    st.markdown("# Estadísticas de Robots")
    st.write("Contenido futuro para estadísticas de robots.")

# Pie de página
st.markdown(
    """
    <hr style="border: 1px solid #00629b;">
    """,
    unsafe_allow_html=True
)

# Crear una columna vacía a la izquierda y a la derecha para centrar el contenido
col1, col2, col3 = st.columns([0.1, 3, 0.1])
with col2:
    col2a, col2b, col2c, col2d = st.columns([0.8, 2, 1.5, 1.5])
    with col2a:
        st.image('images/logo_gsi.png', width=75)
    with col2b:
        st.markdown(
            """
            <div style="font-size: 20px; margin-top: 20px;">
                App created by 
                <a href="https://gsi.upm.es" style="color: #00629b;">Intelligent Systems Group</a>.
            </div>
            """,
            unsafe_allow_html=True
        )
    with col2c:
        st.image('images/logo_amor_azulupm.png', width=200)
    with col2d:
        st.image('images/ministerio.png', width=200)

    st.markdown(
        """
        <div style="padding-bottom: 30px;"></div>
        """,
        unsafe_allow_html=True
    )
