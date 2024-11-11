import pandas as pd

def transformar_modelos(data):
    # Filtrar los modelos
    models = data[(data['label'] == 'type') & (data['node2'] == 'Model')]['node1'].unique()
    
    # Crear listas para las nuevas columnas
    ids = []
    model_names = []
    types = []
    labels = []

    # Inicializar un identificador incremental
    id_counter = 0

    # Procesar cada modelo
    for model in models:
        type_row = data[(data['node1'] == model) & (data['label'] == 'type') & (data['node2'] == 'Model')]
        if not type_row.empty:
            model_type = type_row.iloc[0]['node2']
            label_row = data[(data['node1'] == model) & (data['label'] == 'label')]
            if not label_row.empty:
                model_label = label_row.iloc[0]['node2']

                # Añadir los datos a las listas
                ids.append(id_counter)
                model_names.append(model)
                types.append(model_type)
                labels.append(model_label)

                # Incrementar el identificador
                id_counter += 1

    # Crear un DataFrame con la nueva estructura
    new_data = pd.DataFrame({
        'id': ids,
        'model': model_names,
        'type': types,
        'label': labels
    })

    return new_data

