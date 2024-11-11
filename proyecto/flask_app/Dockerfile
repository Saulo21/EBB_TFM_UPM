# Usa una imagen de Python ligera
FROM python:3.9-slim

# Establece el directorio de trabajo en el contenedor
WORKDIR /app

# Copia el archivo de dependencias a la imagen
COPY requirements.txt requirements.txt

# Instala las dependencias en la imagen
RUN pip install -r requirements.txt

# Copia el código de la aplicación a la imagen
COPY . .

# Expone el puerto 5000 para la aplicación Flask
EXPOSE 5000

# Define el comando de inicio de la aplicación
CMD ["python", "app.py"]

