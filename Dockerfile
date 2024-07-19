#Usar imagen de version 3.12 de python construida en Debian
FROM python:3.12-slim

#Instalar y actualizar paquetes de C++ 
RUN apt-get update && apt-get install -y g++ procps

#Crear un directorio de trabajo
WORKDIR /Bot_SuperTrend

#Copiar todo el proyecto
COPY . .

#Compilar heartbeat C++
RUN g++ scripts/Heartbeat_server.cpp -o Heartbeat_server

#Instalar requerimientos con el comando pip
RUN pip install --no-cache-dir -r requirements.txt

#Construir las dependencias de archivos requeridos
RUN pip install -e .

#Establecer permisos de ejecución para el script de Python
RUN chmod +x src/Bot_SuperTrend.py

#Establecer permisos elevados para el ejecutable de Heartbeat
RUN chmod +x Heartbeat_server

#Establecer permisos elevados para el ejecutable de inicio
RUN chmod +x scripts/start.sh

#Ejecutar iniciador de software (start.sh)
CMD ["./scripts/start.sh"]

#Para la ejecución de la imagen (Ya construida) usar el comando: docker run --network=host --name bot-supertrend-container <nombre-imagen>
