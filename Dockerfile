#Usar imagen de version 3.12 de python construida en Debian
FROM python:3.12-slim

#Crear un directorio de trabajo
WORKDIR /Bot_SuperTrend

#Copiar todo el proyecto
COPY . .

#Instalar requerimientos con el comando pip
RUN pip install --no-cache-dir -r requirements.txt

#Construir las dependencias de archivos requeridos
RUN pip install -e .

#Ejecutar el programa
CMD ["python", "src/Bot_SuperTrend.py"]
