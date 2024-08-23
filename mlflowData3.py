import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import json

# Transformar datos en un DataFrame con la estructura deseada
from models_transformation import transformar_modelos

# Configuración de la página
st.set_page_config(
    page_title="Análisis de la Ethical Black Box",
    page_icon="📊",
    layout="wide"
)

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
    st.image('images/logo_gsi.png', width=75)
    st.markdown(
        """
        <div style="font-size: 20px; margin-top: 10px;">
            App created by 
            <a href="https://gsi.upm.es" style="color: #00629b;">Intelligent Systems Group</a>.
        </div>
        """,
        unsafe_allow_html=True
    )

# Cargar el archivo CSS
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

load_css("style.css")

# Función para cargar el archivo CSV
def cargar_csv():
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    if uploaded_file is not None:
        data = pd.read_csv(uploaded_file)
        return data
    return None

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

# Obtener información de la corrida
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

# Subir y analizar CSV
st.markdown("# Upload CSV file")
data = cargar_csv()
if data is not None:
    st.success("File successfully uploaded")
    st.markdown("# CSV analysis")
    st.dataframe(data)
    
    # Transformar los datos utilizando la función importada
    new_data = transformar_modelos(data)
        
    st.markdown("# Transformed CSV")
    st.dataframe(new_data)

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
