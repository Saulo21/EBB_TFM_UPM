# data_transformation.py
import pandas as pd

def transformar_data(data):
    # Crear nuevo DataFrame con la estructura deseada
    actions = data[(data['label'] == 'type') & (data['node2'] == 'Action')]

    # Crear listas para las nuevas columnas
    ids = []
    questions = []
    senders = []
    receivers = []
    responses = []
    emotions = []
    timestamps_question = []
    timestamps_response = []

    # Inicializar un identificador incremental
    id_counter = 1

    # Procesar cada acción
    for action in actions['node1'].unique():
        question_row = data[(data['node1'] == action) & (data['label'] == 'comment')]
        if not question_row.empty:
            question = question_row.iloc[0]['node2'].replace("'", "")
            sender_row = data[(data['node1'] == action) & (data['label'] == 'performedBy')]
            if not sender_row.empty:
                sender = sender_row.iloc[0]['node2']
                receiver_row = data[(data['node1'] == action) & (data['label'] == 'objectOfAction')]
                if not receiver_row.empty:
                    receiver = receiver_row.iloc[0]['node2']
                    response_action = data[(data['label'] == 'responseTo') & (data['node2'] == action)]
                    if not response_action.empty:
                        response_node = response_action.iloc[0]['node1']
                        response_row = data[(data['node1'] == response_node) & (data['label'] == 'comment')]
                        if not response_row.empty:
                            response = response_row.iloc[0]['node2'].replace("'", "")
                            emotion_row = data[(data['node1'] == response_node) & (data['label'] == 'detectedEmotion')]
                            emotion = emotion_row.iloc[0]['node2'] if not emotion_row.empty else ""
                            timestamp_question_row = data[(data['node1'] == action) & (data['label'] == 'date')]
                            timestamp_question = timestamp_question_row.iloc[0]['node2'].replace("^", "") if not timestamp_question_row.empty else ""
                            timestamp_response_row = data[(data['node1'] == response_node) & (data['label'] == 'date')]
                            timestamp_response = timestamp_response_row.iloc[0]['node2'].replace("^", "") if not timestamp_response_row.empty else ""

                            # Añadir los datos a las listas
                            ids.append(id_counter)
                            questions.append(question)
                            senders.append(sender)
                            receivers.append(receiver)
                            responses.append(response)
                            emotions.append(emotion)
                            timestamps_question.append(timestamp_question)
                            timestamps_response.append(timestamp_response)

                            # Incrementar el identificador
                            id_counter += 1

    # Crear un DataFrame con la nueva estructura
    new_data = pd.DataFrame({
        'id': ids,
        'pregunta': questions,
        'emisor': senders,
        'destinatario': receivers,
        'respuesta': responses,
        'emocion': emotions,
        'timestampPregunta': timestamps_question,
        'timestampRespuesta': timestamps_response
    })

    return new_data
