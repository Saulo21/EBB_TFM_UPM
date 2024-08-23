import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
    option = st.radio("Select an option", ["Upload New File", "View Saved Files"], index=0)

# Cargar el archivo CSS
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

load_css("style.css")

# Obtener información del experimento
def get_experiment_info(experiment_id):
    mlflow_url = "http://localhost:5000"
    response = requests.get(
        f"{mlflow_url}/api/2.0/mlflow/experiments/get-by-name",
        params={"experiment_name": "classification_of_offensive_language20"}
    )
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error: {response.status_code}, {response.text}")
        return None

# Obtener información de la corrida
def get_run_info(experiment_id):
    mlflow_url = "http://localhost:5000"
    response = requests.post(
        f"{mlflow_url}/api/2.0/mlflow/runs/search",
        json={"experiment_ids": [experiment_id]}
    )
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error: {response.status_code}, {response.text}")
        return None

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
    # Tabs para la opción de "Subir Nuevo Archivo"
    tab1, tab2, tab3 = st.tabs(["Upload File", "ML Model", "Robot Statistics"])

    with tab1:
        st.markdown("# Upload TTL file")
        ttl_file = cargar_ttl()

        # Inicializar 'data' como None para evitar el error si no se define
        data = None
    
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

        if data is None:
            st.warning("No data to display. Please upload a TTL file.")
        
elif option == "View Saved Files":
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

# Tab 2: ML Model
with tab2:
    st.markdown('# Model Details')
    if data is not None:
        if 'node1' in data.columns and 'node2' in data.columns:
            model_names = data[data['node2'] == 'Model']['node1'].unique()
            results = []
            for model in model_names:
                label_value = data[(data['node1'] == model) & (data['label'] == 'type')]['node2'].values
                label_value1 = data[(data['node1'] == model) & (data['label'] == 'label')]['node2'].values
                if len(label_value) > 0:
                    results.append((model, label_value[0], label_value1[0]))

            if results:
                for model, type_value, name_value in results:
                    st.markdown(f"""
                        <div></div>
                    """, unsafe_allow_html=True)

                    # Obtener la información del experimento y la corrida en un solo recuadro
                    experiment_info = get_experiment_info(name_value)
                    if experiment_info:
                        experiment_details = experiment_info['experiment']
                        run_info = get_run_info(experiment_details['experiment_id'])
                        if run_info:
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
                                batch_size = extract_param_value(run['data']['params'], 'batch_size')
                                epochs = extract_param_value(run['data']['params'], 'epochs')
                                optimizer = extract_param_value(run['data']['params'], 'optimizer')
                                embedding_dim = extract_param_value(run['data']['params'], 'embedding_dim')
                                units_layer_1 = extract_param_value(run['data']['params'], 'units_layer_1')
                                units_layer_2 = extract_param_value(run['data']['params'], 'units_layer_2')

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
                    <p><strong>Batch Size:</strong> {batch_size}</p>
                    <p><strong>Epochs:</strong> {epochs}</p>
                    <p><strong>Optimizer:</strong> {optimizer}</p>
                    <p><strong>Embedding Dimension:</strong> {embedding_dim}</p>
                    <p><strong>Units in Layer 1:</strong> {units_layer_1}</p>
                    <p><strong>Units in Layer 2:</strong> {units_layer_2}</p>
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
                            st.warning(f"Could not retrieve information for experiment ID {name_value}")
            else:
                st.warning("No values found for the specified robots.")
    else:
        st.warning("Please upload a file in the specified format in the 'Upload File' tab")

# Tab 3: Robot Statistics
with tab3:
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
        # Crear columnas para robots y humanos
        col1, col2 = st.columns(2)

        # Robots
        with col1:
            if 'node1' in data.columns and 'node2' in data.columns:
                # Contar robots
                robots = data[data['node2'] == 'Robot']['node1'].unique()
                num_robots = len(robots)

                st.markdown(f"""
                    <div class='stat-box'>
                        <div>Number of Robots</div>
                        <div class='stat-number'>{num_robots}</div>
                        <div class='robot-icons'>{'🤖 ' * num_robots}</div>
                    </div> 
                """, unsafe_allow_html=True)

                # Lógica adicional para obtener el valor de label para cada robot
                st.markdown("## Information about each Robot")
                if 'node1' in data.columns and 'node2' in data.columns and 'label' in data.columns:
                    # Filtrar los nombres de los robots
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

        # Humanos
        with col2:
            if 'node1' in data.columns and 'node2' in data.columns:
                # Contar humanos
                humans = data[data['node2'] == 'Human']['node1'].unique()
                num_humans = len(humans)

                st.markdown(f"""
                    <div class='stat-box'>
                        <div>Number of recognised humans</div>
                        <div class='stat-number'>{num_humans}</div>
                        <div class='robot-icons'>{'🧍' * num_humans}</div>
                    </div> 
                """, unsafe_allow_html=True)

                # Lógica adicional para obtener el valor de label para cada humano
                st.markdown("## Information about each Human")
                if 'node1' in data.columns and 'node2' in data.columns and 'label' in data.columns:
                    # Filtrar los nombres de los humanos
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
                    
                    
        # Transformar los datos utilizando la función importada
        new_data = transformar_data(data)
        
        # Botón para descargar el nuevo CSV
        @st.cache_data
        def convert_df(df):
            return df.to_csv(index=False).encode('utf-8')

        csv = convert_df(new_data)
    
        # Convertir timestamp a datetime
        new_data['timestampPregunta'] = pd.to_datetime(new_data['timestampPregunta'])
        new_data['timestampRespuesta'] = pd.to_datetime(new_data['timestampRespuesta'])
    
        # Selección de emociones a visualizar
        st.markdown("## Emotions over time")
        all_emotions = new_data['emocion'].unique()
        selected_emotions = st.multiselect("Select emotions to display", options=all_emotions, default=all_emotions)
    
        filtered_data = new_data[new_data['emocion'].isin(selected_emotions)]
    
        # Emociones a lo largo del tiempo con interactividad
        fig = px.scatter(filtered_data, x='timestampRespuesta', y='emocion', color='emocion', title='Emotions over time',
                     hover_data={'pregunta': True, 'respuesta': True})
    
        fig.update_traces(marker=dict(size=12), selector=dict(mode='markers'))
    
        st.plotly_chart(fig)
    
        # Distribución de emociones - Gráfica Circular
        st.markdown("## Distribution of emotions")
        emotion_counts = new_data['emocion'].value_counts().reset_index()
        emotion_counts.columns = ['emocion', 'count']

        fig_pie = px.pie(emotion_counts, values='count', names='emocion', title='',
                 color_discrete_sequence=px.colors.qualitative.Pastel)

        st.plotly_chart(fig_pie)
        # Interacciones por emisor y destinatario
        st.markdown("## Interactions by sender and receiver")
        fig = px.histogram(new_data, x='emisor', color='destinatario', barmode='group', title='')
        st.plotly_chart(fig)
        
    else:
        st.warning("Please upload a file in the specified format in the 'Upload File' tab")   

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
