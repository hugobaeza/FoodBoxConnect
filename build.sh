#!/bin/bash

# Actualiza pip
pip install --upgrade pip

# Instala primero sqlparse con la versión exacta
pip install sqlparse==0.2.4

# Instala las demás dependencias
pip install -r requirements.txt

# Ejecuta las migraciones
python manage.py migrate

# Colecta los archivos estáticos
python manage.py collectstatic --no-input
