# Descripción
Código fuente del bot usado en el grupo [Seguidores de Rozemyne](https://t.me/SeguidoresDeRozemyne)
accesible desde [@ordonnanz\_bot](https://t.me/ordonnanz_bot).

# Requisitos
- python

# Ejecución
- Instala las dependencias de python.

    `pip install -r requirements.txt`

- Crea un certificado autofirmado para que el bot pueda comunicarse con los servidores
  de telegram mediante SSL.

    `openssl req -newkey rsa:2048 -sha256 -nodes -keyout ferdinand.key
    -x509 -days 3650 -out ferdinand.pem`

- Modifica los valores de **config.template**. Sólo es posible usar los puertos
  **80**, **88**, **443** y **8443**.

- Cambia el nombre de config.template.

    `mv config.template .config`

- Ejecuta el bot.

    `./ferdinand.py`

    > **Nota:** Para ejecutar el bot en el puerto 80, es posible que debas ejecutarlo
    > con permisos de superusuario (**sudo**).


# Licencia
    Copyright (c) 2021-2022 scmanjarrez. All rights reserved.
    This work is licensed under the terms of the MIT license.

Puedes encontrar la licencia completa en
[LICENSE](https://github.com/scmanjarrez/ordonnanz/blob/master/LICENSE).
