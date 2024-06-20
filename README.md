# Chamba Trading Bot

[![Build Status](https://img.shields.io/pypi/pyversions/pybit)](https://www.python.org/downloads/)

Bot de trading versátil que puede ser implementada en distintos instrumentos financieros.
## Índice de Contenidos

- [Intro](#intro)
- [Características](#caracteristicas)
- [Instalación](#instalacion)
- [Uso](#uso)
- [Hoja de Ruta](#ruta)
- [Autores](#autores)


## Intro
Este proyecto es un Bot de Trading especializado para mercados volátiles. 
Se puede utilizar en cualquier intervalos de tiempo, aunque se recomienda especialmente en velas de 15 minutos. 
Utiliza una estrategia avanzada respaldada por dos indicadores principales: Supertrend y Double EMA.

Solo funciona con el exchange **ByBit** debido al uso de librerias específicas para conectarse a su API.

## Caracteristicas
- **Estrategia:** El bot emplea una estrategia que combina ambor indicadores para identificar oportunidades de compra y venta.
- **Ganancias Dinámicas:** Incorpora un enfoque de ganancias dinámicas para maximizar los rendimientos.
- **Take Profit y Stop Loss Dinámicos y Seguros:** El bot gestiona automáticamente el take profit y stop loss, ajustándolos dinámicamente para optimizar la rentabilidad y mitigar riesgos.

## Instalacion
Para instalar todas las bibliotecas necesarias para el proyecto necesitas utilizar Python 3.9 preferiblemente o Python 3.10. 

Utilizando la herramienta `pip` se pueden instalar todas las dependencias del proyecto. 
```
cd Bot_Supertrend
pip install -r requirements.txt
pip install -e .
```

## Uso
1. Lo primero que se necesita hacer, es actualizar y/o crear el archivo de `.env` con las variables de entorno usadas en el proyecto siguiendose de esta plantilla:

  ```
  LLT= #Ingresar un valor entre True o False 
  IP = #Ingresar la dirección IP donde va a correr el Heartbeat
  PORT = #Ingresar el puerto por donde va a existir comunicación

  Api_Key = #Ingresar llave publica de Bybit
  Api_Secret = #Ingresar llave privada de Bybit
  ```
2. Lo siguiente es correr el archivo ` src/Bot_SuperTrend.py ` 
**¡AVISO!**  Al correr este código, solo se negociará con las monedas **ETH** & **XRP** 

## Ruta

### Proximas Funcionalidades

1. **Medidores de Volumen y Volatilidad:** Mejorar la estrategia mediante la incorporación de medidores de volumen y volatilidad del mercado objetivo.
2. **Optimización del Algoritmo:** Refinar la lógica del algoritmo de trading para adaptarse a diferentes condiciones del mercado.
3. **Interfaz de Usuario Avanzada:** Diseñar una interfaz de usuario intuitiva para que los usuarios puedan personalizar la configuración y supervisar el rendimiento.

## Autores
<table>
  <tr>
<td align="center"><a href="https://github.com/Aviles17"><img src="https://avatars.githubusercontent.com/u/110882455?v=4" width="100px;" alt=""/><br /><sub><b>Santiago Avilés</b></sub></a><br /></td>
<td align="center"><a href="https://github.com/SBoteroP"><img src="https://avatars.githubusercontent.com/u/68749776?s=400&u=985d505e9c62f2f7fa7d08a46e406a451995b5a4&v=4" width="100px;" alt=""/><br /><sub><b>Santiago Botero</b></sub></a><br /></td>
  </tr>
</table>

## **Responsabilidad Financiera** 
El uso de este bot implica riesgos financieros. No garantizamos beneficios y recomendamos a los usuarios comprender los riesgos y ajustar la configuración según sus preferencias y tolerancia al riesgo.
Este proyecto está bajo la Licencia MIT. Consulta el archivo [LICENSE](LICENSE) para obtener más detalles. Es importante tener en cuenta que:
**Nota:** Asegúrese de revisar y entender completamente el código antes de implementarlo en un entorno de trading real. No somos responsables de las pérdidas financieras derivadas del uso de este bot.

