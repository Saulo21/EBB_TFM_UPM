# Usa una imagen de Python ligera
FROM python:3.9-slim

# Establece el directorio de trabajo en el contenedor
WORKDIR /app

# Copia el archivo de dependencias a la imagen
COPY requirements.txt requirements.txt

# Instala las dependencias en la imagen
RUN pip install --no-cache-dir -r requirements.txt

# Copia el código de la aplicación a la imagen
COPY . .

# Expone el puerto 8501 para la aplicación Streamlit
EXPOSE 8501

# Define el comando de inicio de la aplicación
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]

