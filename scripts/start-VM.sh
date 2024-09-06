#!/bin/sh

#Cabe resaltar que este script solo funciona cuando las dependencias y proceso de instalación ya fue completado

# Ejecutar el programa de Heartbeat como servidor 
g++ scripts/Heartbeat_server.cpp -o Heartbeat_server
chmod +x Heartbeat_server # Dar permisos de ejecución

./Heartbeat_server &

chmod +x src/Bot_SuperTrend.py  # Dar permisos de ejecución

# Ejecutar el script Bot_SUpertrend en segundo plano como cliente
nohup python3 src/Bot_SuperTrend.py > output.log &