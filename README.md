# Descripción
Código fuente del bot de telegram @ehe_te_nandayo_bot

# Requisitos
- python

# Ejecución
- Instala las dependencias de python.

    `pip install -r requirements.txt`

- Crea un certificado autofirmado para que el bot pueda comunicarse con los servidores de telegram mediante SSL.

    `openssl req -newkey rsa:2048 -sha256 -nodes -keyout ferdinand.key -x509 -days 3650 -out ferdinand.pem`

- Modifica los valores de **config.template**. Sólo es posible usar los puertos **80**, **88**, **443** y **8443**.

- Cambia el nombre de config.template.

    `mv config.template .config`

- Ejecuta el bot.

    `./ferdinand.py
