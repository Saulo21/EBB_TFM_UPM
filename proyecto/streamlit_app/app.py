import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import sqlite3
from io import StringIO
import streamlit.components.v1 as components
from data_transformation import transformar_data
import json

# Configuración de la página
st.set_page_config(
    page_title="Análisis de la Ethical Black Box",
    page_icon="📊",
    layout="wide"
)

#################################################
# FUNCIONES RELACIONADAs CON LA BASE DE DATOS
#################################################

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

#################################################
# FUNCIONES RELACIONADAs CON LA BASE DE DATOS HASTA AQUÍ
#################################################


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
    option = st.radio("Select an option", ["Upload New File", "View Saved Files"], index=0)

# Cargar el archivo CSS
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

load_css("style.css")

################################################
# FUNCIONES RELACIONADADa CON MLFLOW
################################################

# Obtener información del experimento
def get_experiment_info(experiment_id):
    mlflow_url = "http://localhost:8080"
    response = requests.get(
        f"{mlflow_url}/api/2.0/mlflow/experiments/get-by-name",
        params={"experiment_name": experiment_id}
    )
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error: {response.status_code}, {response.text}")
        return None

# Obtener información
def get_run_info(experiment_id):
    mlflow_url = "http://localhost:8080"
    response = requests.post(
        f"{mlflow_url}/api/2.0/mlflow/runs/search",
        json={"experiment_ids": [experiment_id]}
    )
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error: {response.status_code}, {response.text}")
        return None
    
################################################
# FUNCIONES RELACIONADADa CON MLFLOW HASTA AQUÍ
################################################

# Transformar datos en un DataFrame con la estructura deseada
from models_transformation import transformar_modelos
from data_transformation import transformar_data

# Funciones para extraer valores
def extract_tag_value(tags, key):
    for tag in tags:
        if tag['key'] == key:
            return tag['value']
    return 'N/A'

def extract_metric_value(metrics, key):
    for metric in metrics:
        if metric['key'] == key:
            return metric['value']
    return 'N/A'

def extract_param_value(params, key):
    for param in params:
        if param['key'] == key:
            return param['value']
    return 'N/A'

# Función para crear un gráfico de radar
def create_radar_chart(metrics):
    categories = ['False Negatives', 'False Positives', 'True Negatives', 'True Positives']
    values = [metrics[cat.lower().replace(' ', '_')] for cat in categories]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='Metrics'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, max(values)]
            )
        ),
        showlegend=False,
        margin=dict(l=20, r=20, t=20, b=20)
    )

    return fig

# Función para crear gráficos de gauge para las métricas
def create_gauge_chart(value, title, min_value=0, max_value=1):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': title},
        gauge={
            'axis': {'range': [min_value, max_value]},
            'bar': {'color': "#00629b"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "#00629b",
            'steps': [
                {'range': [min_value, max_value*0.5], 'color': '#FFDDC1'},
                {'range': [max_value*0.5, max_value*0.75], 'color': '#FFC3A0'},
                {'range': [max_value*0.75, max_value], 'color': '#FF9A8B'},
            ],
        }
    ))

    fig.update_layout(
        margin=dict(l=20, r=20, t=20, b=20)
    )

    return fig

# Gráfico de barras para el Example Count
def create_example_count_chart(example_count):
    fig = go.Figure(go.Bar(
        x=[example_count],
        y=['Example Count'],
        orientation='h',
        marker=dict(color='#00629b')
    ))
    fig.update_layout(
        xaxis=dict(showgrid=False, showticklabels=False),
        yaxis=dict(showgrid=False, showticklabels=False),
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=0, b=0),
        height=100
    )
    return fig

# Función para cargar el archivo TTL
def cargar_ttl():
    uploaded_file = st.file_uploader("Choose a TTL file", type="ttl")
    if uploaded_file is not None:
        return uploaded_file
    return None

# Lógica de la opción seleccionada en el sidebar
if option == "Upload New File":
    
    # Definir estilo personalizado para los contadores
    st.markdown("""
        <style>
        .stats-container {
            display: flex;
            justify-content: space-evenly;
            margin-top: 20px;
        }
        .stat-box {
            text-align: center;
            padding: 10px;
        }
        .stat-circle {
            border-radius: 50%;
            background-color: #0096d2;
            color: white;
            width: 80px;
            height: 80px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 10px auto;
            font-size: 24px;
        }
        .stat-title {
            font-size: 16px;
            font-weight: bold;
            margin-top: 0;
        }
        </style>
    """, unsafe_allow_html=True)

    # Tabs para la opción de "Subir Nuevo Archivo"
    tab1, tab2, tab3, tab4 = st.tabs(["Upload File", "Knowledge Graph", "ML Model", "Robot Statistics"])

    with tab1:
        st.markdown("# Upload TTL file")
        # Inicializar 'data' como None para evitar el error si no se define
        data = None
        new_data = None
        
        ttl_file = cargar_ttl()

        if ttl_file is not None:
            st.success("File successfully uploaded")
            

            # Enviar archivo TTL al servidor Flask para procesarlo
            files = {'file': ttl_file.getvalue()}
            response_csv = requests.post("http://flask_app:5000/convert_ttl_to_csv", files=files)
            response_html = requests.post("http://flask_app:5000/convert_ttl_to_html", files=files)

            if response_csv.status_code == 200 and response_html.status_code == 200:
                # Convertir la respuesta CSV en un DataFrame
                csv_content = response_csv.text
                data = pd.read_csv(StringIO(csv_content))
            
                st.markdown("# CSV analysis")
                num_rows = st.slider('Select number of rows to display', 1, 20, 10)
                st.dataframe(data.head(num_rows))
                
                # Información solicitada sobre los valores únicos en las columnas node1, label y node2
                unique_node1 = data['node1'].nunique()
                unique_label = data['label'].nunique()
                unique_node2 = data['node2'].nunique()

                st.markdown(f"Knowledge Graph Information")
                st.markdown(f"- **Total number of edge source nodes:** {unique_node1}")
                st.markdown(f"- **Total number of relationships between nodes:** {unique_label}")
                st.markdown(f"- **Total number of edge target nodes:** {unique_node2}")

                st.markdown("# Knowledge Graph")
                html_content = response_html.text
                components.html(html_content, height=600)

                # Guardar archivos en la base de datos
                save_files_to_db(ttl_file.name, ttl_file.getvalue(), csv_content.encode(), html_content.encode())
                st.success("Archivos convertidos y guardados en la base de datos.")
            else:
                st.error("Error processing the TTL file.")

        if data is None:
            st.warning("No data to display. Please upload a TTL file.")
        
elif option == "View Saved Files":
    # Tabs para la opción de "Ver Archivos Guardados"
    tab1, tab2, tab3, tab4 = st.tabs(["View Saved Files", "Knowledge Graph", "ML Model", "Robot Statistics"])

    # Inicializar 'data' como None para evitar el error si no se define
    data = None
    new_data = None
        
    with tab1:
        st.markdown("# Saved files")
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

with tab2:

    if ttl_file is not None:
        # Enviar archivo TTL al servidor Flask para procesarlo
        files = {'file': ttl_file.getvalue()}
        response_csv = requests.post("http://flask_app:5000/convert_ttl_to_csv", files=files)
        response_html = requests.post("http://flask_app:5000/convert_ttl_to_html", files=files)
        response_html_text = requests.post("http://flask_app:5000/convert_ttl_to_html_text", files=files)
        response_html_edge = requests.post("http://flask_app:5000/convert_ttl_to_html_edge", files=files)
        response_html_label_color = requests.post("http://flask_app:5000/convert_ttl_to_html_label_color", files=files)
        
        if response_csv.status_code == 200 and response_html.status_code == 200:
            # Convertir la respuesta CSV en un DataFrame
            csv_content = response_csv.text
            data = pd.read_csv(StringIO(csv_content))
            
            # Información solicitada sobre los valores únicos en las columnas node1, label y node2
            unique_node1 = data['node1'].nunique()
            unique_label = data['label'].nunique()
            unique_node2 = data['node2'].nunique()

            # Presentar la información en un formato estilizado
            st.markdown("## Knowledge Graph Information")
            
             # Crear columnas para alinear los elementos uno al lado del otro
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown(f'''
                <div class="stat-box">
                    <div class="stat-circle">{unique_node1}</div>
                    <p class="stat-title">Edge Source Nodes</p>
                </div>
                ''', unsafe_allow_html=True)

            with col2:
                st.markdown(f'''
                <div class="stat-box">
                    <div class="stat-circle">{unique_label}</div>
                    <p class="stat-title">Relationships</p>
                </div>
                ''', unsafe_allow_html=True)

            with col3:
                st.markdown(f'''
                <div class="stat-box">
                    <div class="stat-circle">{unique_node2}</div>
                    <p class="stat-title">Edge Target Nodes</p>
                </div>
                ''', unsafe_allow_html=True)
                
            st.markdown("# Knowledge Graph")
            html_content_text = response_html_text.text
            components.html(html_content_text, height=600)
            
            st.markdown("# Knowledge Graph with edge information")
            html_content_edge = response_html_edge.text
            components.html(html_content_edge, height=600)
            
            st.markdown("# Knowledge Graph with all information")
            html_content_label_color = response_html_label_color.text
            components.html(html_content_label_color, height=600)

    
# Tab 2: ML Model
with tab3:
    st.markdown('# Models List')
    if data is not None:
        # Transformar los datos utilizando la función importada
        #st.markdown("# CSV analysis")
        #st.dataframe(data)
    
        # Transformar los datos utilizando la función importada
        new_data = transformar_modelos(data)
        
        #st.markdown("# Transformed CSV")
        #st.dataframe(new_data)

        # Crear un desplegable con los valores de la columna 'label'
        labels = new_data['label'].unique()
        selected_label = st.selectbox("Select Model", labels)

        if selected_label:
            st.markdown('# Model Details')
            experiment_info = get_experiment_info(selected_label)
            if experiment_info:
                experiment_details = experiment_info['experiment']
                run_info = get_run_info(experiment_details['experiment_id'])
            
                if run_info:
                    run_info_str = json.dumps(run_info, indent=4)
                    st.download_button(label="Download run info JSON", data=run_info_str, file_name="run_info.json", mime="application/json")

                    run_details_markup = ""
                    for run in run_info['runs']:
                        user = extract_tag_value(run['data']['tags'], 'mlflow.user')
                        accuracy = extract_metric_value(run['data']['metrics'], 'accuracy')
                        f1_score = extract_metric_value(run['data']['metrics'], 'f1_score')
                        loss = extract_metric_value(run['data']['metrics'], 'loss')
                        false_negatives = extract_metric_value(run['data']['metrics'], 'false_negatives')
                        false_positives = extract_metric_value(run['data']['metrics'], 'false_positives')
                        true_negatives = extract_metric_value(run['data']['metrics'], 'true_negatives')
                        true_positives = extract_metric_value(run['data']['metrics'], 'true_positives')
                        example_count = extract_metric_value(run['data']['metrics'], 'example_count')
                        precision_score = extract_metric_value(run['data']['metrics'], 'precision_score')

                        # Extraer todos los parámetros de manera dinámica
                        params = run['data']['params']
                        params_markup = ""
                        for param in params:
                            params_markup += f"<p><strong>{param['key'].replace('_', ' ').capitalize()}:</strong> {param['value']}</p>"

                        run_details_markup += f"""
        <div style='background-color:#ffffff; padding:30px; border-radius:15px; margin-bottom:20px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);'>
            <div style='display: flex; flex-direction: column; align-items: center;'>
                <div style='background-color: #e6f4f9; padding:15px; border-radius:10px; margin-bottom:10px; width: 80%;'>
                    <h3 style='color:#00629b;'>General Information</h3>
                    <p><strong>User:</strong> {user}</p>
                    <p><strong>Experiment ID:</strong> {experiment_details['experiment_id']}</p>
                    <p><strong>Name:</strong> {experiment_details['name']}</p>
                </div>
                <div style='background-color: #e6f4f9; padding:15px; border-radius:10px; margin-bottom:10px; width: 80%;'>
                    <h3 style='color:#00629b;'>Model Parameters</h3>
                    {params_markup}
                </div>
            </div>
        </div>
    """
                    st.markdown(run_details_markup, unsafe_allow_html=True)

                    col1, col2 = st.columns([2, 2])
                    with col1:
                        st.plotly_chart(create_gauge_chart(accuracy, "Accuracy"), use_container_width=True)
                        st.plotly_chart(create_gauge_chart(precision_score, "Precision Score"), use_container_width=True)
                    with col2:
                        st.plotly_chart(create_gauge_chart(f1_score, "F1 Score"), use_container_width=True)
                        st.plotly_chart(create_gauge_chart(loss, "Loss", min_value=0, max_value=max(1, loss)), use_container_width=True)

                    col1, col2, col3 = st.columns([0.1, 2, 0.1])
                    with col2:
                        st.plotly_chart(create_radar_chart({
                            'false_negatives': false_negatives,
                            'false_positives': false_positives,
                            'true_negatives': true_negatives,
                            'true_positives': true_positives
                        }), use_container_width=True)
                    
                    col1, col2, col3 = st.columns([0.1, 2, 0.1])
                    with col2:
                        st.markdown(f"""
                        <div style='background-color:#f0f0f0; padding:20px; border-radius:10px; margin-bottom:10px;'>
                            <h4 style='color:#004d80; font-size:24px; margin-bottom:10px;'>Example Count</h4>
                            <div style='display: flex; align-items: center; justify-content: center;'>
                                <span style='font-size: 30px; font-weight: bold; color: #00629b;'>{example_count}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.warning(f"Could not retrieve information for experiment ID {selected_label}")
            else:
                st.warning(f"No information found for experiment ID {selected_label}")

        else:
            st.warning("Please upload a CSV file in the 'Upload CSV' tab")
    
# Tab 3: Robot Statistics
with tab4:
    # CSS Styling
    st.markdown("""
        <style>
            .main-title {
                text-align: center;
                color: #00a9e0;
                font-size: 3em;
                font-weight: bold;
                margin-bottom: 20px;
            }
            .stat-box {
                background-color: #e8f4fc;
                padding: 30px;
                border-radius: 15px;
                box-shadow: 2px 2px 12px rgba(0, 0, 0, 0.1);
                text-align: center;
                margin-bottom: 20px;
            }
            .stat-number {
                font-size: 2.5em;
                color: #00a9e0;
                margin: 10px 0;
            }
            .robot-icons {
                font-size: 2em;
            }
            .card-container {
                display: flex;
                flex-wrap: wrap;
                justify-content: space-around;
                margin-top: 20px;
            }
            .card {
                background-color: #ffffff;
                border-radius: 15px;
                box-shadow: 2px 2px 12px rgba(0, 0, 0, 0.1);
                margin: 10px;
                padding: 20px;
                text-align: center;
                width: 250px;
            }
            .card-title {
                font-size: 1.5em;
                color: #00a9e0;
                margin-bottom: 10px;
            }
            .card-content {
                font-size: 1.2em;
                color: #333333;
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("# Robot Statistics")

    if data is not None:
        # Columns for Robots and Humans
        col1, col2 = st.columns(2)

        # Robots Statistics
        with col1:
            if 'node1' in data.columns and 'node2' in data.columns:
                # Counting Robots
                robots = data[data['node2'] == 'Robot']['node1'].unique()
                num_robots = len(robots)

                st.markdown(f"""
                    <div class='stat-box'>
                        <div>Number of Robots</div>
                        <div class='stat-number'>{num_robots}</div>
                        <div class='robot-icons'>{'🤖 ' * num_robots}</div>
                    </div> 
                """, unsafe_allow_html=True)

                # Displaying Information about Each Robot
                st.markdown("## Information about each Robot")
                if 'node1' in data.columns and 'node2' in data.columns and 'label' in data.columns:
                    robot_names = data[data['node2'] == 'Robot']['node1'].unique()

                    results = []
                    for robot in robot_names:
                        label_value = data[(data['node1'] == robot) & (data['label'] == 'type')]['node2'].values
                        label_value1 = data[(data['node1'] == robot) & (data['label'] == 'label')]['node2'].values
                        if len(label_value) > 0:
                            results.append((robot, label_value[0], label_value1[0]))

                    if results:
                        st.markdown("<div class='card-container'>", unsafe_allow_html=True)
                        for robot, type_value, name_value in results:
                            st.markdown(f"""
                                <div class='card'>
                                    <div class='card-title'>{robot}</div>
                                    <div class='card-content'>Type: {type_value}</div>
                                    <div class='card-content'>Name: {name_value}</div>
                                </div>
                            """, unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)
                    else:
                        st.warning("No values found for the specified robots.")

        # Humans Statistics
        with col2:
            if 'node1' in data.columns and 'node2' in data.columns:
                # Counting Humans
                humans = data[data['node2'] == 'Human']['node1'].unique()
                num_humans = len(humans)

                st.markdown(f"""
                    <div class='stat-box'>
                        <div>Number of recognised humans</div>
                        <div class='stat-number'>{num_humans}</div>
                        <div class='robot-icons'>{'🧍' * num_humans}</div>
                    </div> 
                """, unsafe_allow_html=True)

                # Displaying Information about Each Human
                st.markdown("## Information about each Human")
                if 'node1' in data.columns and 'node2' in data.columns and 'label' in data.columns:
                    human_names = data[data['node2'] == 'Human']['node1'].unique()

                    results = []
                    for human in human_names:
                        label_value = data[(data['node1'] == human) & (data['label'] == 'type')]['node2'].values
                        label_value1 = data[(data['node1'] == human) & (data['label'] == 'label')]['node2'].values
                        if len(label_value) > 0:
                            results.append((human, label_value[0], label_value1[0]))

                    if results:
                        st.markdown("<div class='card-container'>", unsafe_allow_html=True)
                        for human, type_value, name_value in results:
                            st.markdown(f"""
                                <div class='card'>
                                    <div class='card-title'>{human}</div>
                                    <div class='card-content'>Type: {type_value}</div>
                                    <div class='card-content'>Name: {name_value}</div>
                                </div>
                            """, unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)
                    else:
                        st.warning("No values found for the specified humans.")

        st.dataframe(data)

        # Transforming the data using the imported function
        new_data = transformar_data(data)

        st.markdown("# Transformed CSV")
        st.dataframe(new_data)

        # Button to Download the Transformed CSV
        @st.cache_data
        def convert_df(df):
            return df.to_csv(index=False).encode('utf-8')

        csv = convert_df(new_data)

        st.download_button(
            label="Download transformed CSV",
            data=csv,
            file_name='transformed_data.csv',
            mime='text/csv',
        )

        # Convert timestamp to datetime
        new_data['timestampPregunta'] = pd.to_datetime(new_data['timestampPregunta'])
        new_data['timestampRespuesta'] = pd.to_datetime(new_data['timestampRespuesta'])

        # Selection of Emotions to Display
        st.markdown("## Emociones a lo largo del tiempo")
        all_emotions = new_data['emocion'].unique()
        selected_emotions = st.multiselect("Select emotions to display", options=all_emotions, default=all_emotions)

        filtered_data = new_data[new_data['emocion'].isin(selected_emotions)]

        # Emotions over Time with Interactivity
        fig = px.scatter(filtered_data, x='timestampRespuesta', y='emocion', color='emocion', title='Emociones a lo largo del tiempo',
                        hover_data={'pregunta': True, 'respuesta': True})

        fig.update_traces(marker=dict(size=12), selector=dict(mode='markers'))

        st.plotly_chart(fig)

        # Distribution of Emotions
        st.markdown("## Distribución de emociones")
        fig = px.histogram(new_data, x='emocion', title='Distribución de emociones')
        st.plotly_chart(fig)

        # Interactions by Sender and Receiver
        st.markdown("## Interacciones por emisor y destinatario")
        fig = px.histogram(new_data, x='emisor', color='destinatario', barmode='group', title='Interacciones por emisor y destinatario')
        st.plotly_chart(fig)

        # Response Time Duration
        st.markdown("## Duración de las respuestas")
        new_data['response_time'] = new_data['timestampRespuesta'] - new_data['timestampPregunta']
        new_data['response_time'] = new_data['response_time'].dt.total_seconds()
        fig = px.box(new_data, y='response_time', points='all', title='Duración de las respuestas en segundos')
        st.plotly_chart(fig)

    
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

