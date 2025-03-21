import pymongo
import os
from decouple import config

# Obtener la URL de conexión de MongoDB de las variables de entorno
url = config('MONGO_URI')

if not url:
    raise ValueError("La URL de MongoDB no está configurada correctamente en las variables de entorno")

# Crear cliente de MongoDB
client = pymongo.MongoClient(url)

# Conectar a la base de datos
db = client[config('MONGO_DB_NAME', default='foodboxconnect')]