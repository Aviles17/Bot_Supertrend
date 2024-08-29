#!/bin/sh

# Ejecutar el programa de Heartbeat como servidor 
./Heartbeat_server &

# Ejecutar el script Bot_SUpertrend en segundo plano como cliente
nohup python src/Bot_SuperTrend.py > output.log &

# Mantener el contenedor activo
tail -f /dev/null