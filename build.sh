#!/bin/bash

# Actualiza pip
pip install --upgrade pip

# Instala las dependencias
pip install -r requirements.txt

# Ejecuta las migraciones
python manage.py migrate

# Colecta los archivos estáticos
python manage.py collectstatic --no-input