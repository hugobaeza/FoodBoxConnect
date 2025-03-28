from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import logging
from bson import ObjectId
from db_con import db
from django.contrib.auth.hashers import check_password
import random
import string
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

# Colecciones de MongoDB
users_collection = db["users"]
orders_collection = db["orders"]
boxes_collection = db["boxes"]

#ruta normal
from django.http import JsonResponse
from pymongo import MongoClient
from bson import json_util

# Ruta normal
def home(request):
    return JsonResponse({"message": "API está funcionando"})

@csrf_exempt
def test_api(request):
    try:
        # Test basic response
        return JsonResponse({"status": "success", "message": "API test endpoint is working"})
    except Exception as e:
        logger.error(f"Error en test_api: {str(e)}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


# Inicio de sesión
@csrf_exempt
def login(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get("email")
            password = data.get("password")
            user = users_collection.find_one({"email": email})
            
            if user and check_password(password, user.get("password")):
                return JsonResponse({
                    "status": "success",
                    "message": "Inicio de sesión exitoso",
                    "user": {
                        "id": str(user["_id"]),
                        "name": user["name"],
                        "lastname": user["lastname"],
                        "phone": user["phone"],
                        "address": user["address"],
                        "email": user["email"],
                        "role": user["role"]
                    }
                })
            else:
                return JsonResponse({"status": "error", "message": "Credenciales inválidas"}, status=401)
        except Exception as e:
            logger.error(f"Error en login: {str(e)}")
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    else:
        return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)

# Cierre de sesión
@csrf_exempt
def logout(request):
    return JsonResponse({"status": "success", "message": "Sesión cerrada correctamente"})

# Buscar pedido por order_key
@csrf_exempt
def get_order(request, order_key):
    try:
        order = orders_collection.find_one({"order_key": order_key})
        if order:
            box = boxes_collection.find_one({"_id": order.get("id_box")})
            return JsonResponse({
                "status": "success",
                "order": {
                    "order_key": order["order_key"],
                    "details": order["details"],
                    "state": order["state"],
                    "dateTime": order["dateTime"],
                    "box_position": box.get("position", "Desconocida") if box else "Desconocida"
                }
            })
        else:
            return JsonResponse({"status": "error", "message": "Pedido no encontrado"}, status=404)
    except Exception as e:
        logger.error(f"Error en get_order: {str(e)}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

# ----- NUEVOS ENDPOINTS PARA ESP32 -----

# Generar clave aleatoria de 9 dígitos
def generate_box_key():
    # Caracteres permitidos: 1234567890ABCD
    allowed_chars = "1234567890ABCD"
    return ''.join(random.choice(allowed_chars) for _ in range(9))

# Obtener estado de la caja y clave
@csrf_exempt
def box_status(request):
    try:
        serial_number = request.GET.get('serialNumber')
        if not serial_number:
            return JsonResponse({"status": "error", "message": "Número de serie requerido"}, status=400)
        
        # Buscar la caja por número de serie
        box = boxes_collection.find_one({"serie": serial_number})
        if not box:
            return JsonResponse({"status": "error", "message": f"Caja no encontrada con serie: {serial_number}"}, status=404)
        
        # Buscar el pedido asociado a la caja
        order = orders_collection.find_one({"id_box": box["_id"], "state": "pending"})
        
        response_data = {
            "on": 1 if order else 0,  # 1 si hay un pedido pendiente, 0 si no
            "position": box.get("position", "Desconocida")
        }
        
        # Incluir box_key solo si hay un pedido pendiente
        if order and "box_key" in order:
            response_data["box_key"] = order["box_key"]
        
        return JsonResponse(response_data)
    except Exception as e:
        logger.error(f"Error en box_status: {str(e)}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

# Actualizar temperatura
@csrf_exempt
def update_temperature(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            serial_number = data.get("serialNumber")
            temperature = data.get("temperature")
            
            if not serial_number or temperature is None:
                return JsonResponse({"status": "error", "message": "Número de serie y temperatura requeridos"}, status=400)
            
            # Buscar la caja por número de serie
            box = boxes_collection.find_one({"serie": serial_number})
            if not box:
                return JsonResponse({"status": "error", "message": f"Caja no encontrada con serie: {serial_number}"}, status=404)
            
            # Actualizar la temperatura en la orden activa (si existe)
            order = orders_collection.find_one({"id_box": box["_id"], "state": "pending"})
            if order:
                # Agregar registro de temperatura
                temp_data = {
                    "value": temperature,
                    "timestamp": datetime.now()
                }
                
                # Actualizar el documento con la nueva temperatura
                orders_collection.update_one(
                    {"_id": order["_id"]},
                    {"$push": {"temperature_logs": temp_data}}
                )
            
            # Actualizar la temperatura actual en la caja
            boxes_collection.update_one(
                {"_id": box["_id"]},
                {"$set": {"temperatura": temperature, "last_update": datetime.now()}}
            )
            
            return JsonResponse({"status": "success", "message": "Temperatura actualizada"})
        except Exception as e:
            logger.error(f"Error en update_temperature: {str(e)}")
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    else:
        return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)

# Actualizar estado de verificación
@csrf_exempt
def update_verification(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            serial_number = data.get("serialNumber")
            verified = data.get("verified")
            
            if serial_number is None or verified is None:
                return JsonResponse({"status": "error", "message": "Parámetros incompletos"}, status=400)
            
            # Buscar la caja por número de serie
            box = boxes_collection.find_one({"serie": serial_number})
            if not box:
                return JsonResponse({"status": "error", "message": f"Caja no encontrada con serie: {serial_number}"}, status=404)
            
            # Buscar pedido activo
            order = orders_collection.find_one({"id_box": box["_id"], "state": "pending"})
            if not order:
                return JsonResponse({"status": "error", "message": "No hay pedido activo para esta caja"}, status=404)
            
            # Registrar intento de acceso
            access_log = {
                "timestamp": datetime.now(),
                "success": verified,
                "box_id": box["_id"]
            }
            
            # Si la verificación fue exitosa, actualizar el estado del pedido
            if verified:
                orders_collection.update_one(
                    {"_id": order["_id"]},
                    {
                        "$set": {"state": "completado", "delivery_date": datetime.now()},
                        "$push": {"access_logs": access_log}
                    }
                )
                
                # Actualizar la caja para indicar que el pedido fue completado
                boxes_collection.update_one(
                    {"_id": box["_id"]},
                    {"$set": {"last_access": datetime.now()}}
                )
            else:
                # Solo registrar el intento fallido
                orders_collection.update_one(
                    {"_id": order["_id"]},
                    {"$push": {"access_logs": access_log}}
                )
            
            return JsonResponse({
                "status": "success", 
                "message": "Verificación procesada", 
                "verified": verified
            })
        except Exception as e:
            logger.error(f"Error en update_verification: {str(e)}")
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    else:
        return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)

# Crear un nuevo pedido
@csrf_exempt
def create_order(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            box_id = data.get("box_id")
            customer_id = data.get("customer_id")
            details = data.get("details", "")
            
            if not box_id or not customer_id:
                return JsonResponse({"status": "error", "message": "ID de caja y cliente requeridos"}, status=400)
            
            # Convertir a ObjectId
            box_id = ObjectId(box_id)
            customer_id = ObjectId(customer_id)
            
            # Verificar si la caja existe
            box = boxes_collection.find_one({"_id": box_id})
            if not box:
                return JsonResponse({"status": "error", "message": "Caja no encontrada"}, status=404)
            
            # Verificar si la caja ya tiene un pedido pendiente
            existing_order = orders_collection.find_one({"id_box": box_id, "state": "pending"})
            if existing_order:
                return JsonResponse({"status": "error", "message": "La caja ya tiene un pedido pendiente"}, status=400)
            
            # Generar clave para la caja
            box_key = generate_box_key()
            
            # Crear el nuevo pedido
            new_order = {
                "id_box": box_id,
                "id_customer": customer_id,
                "details": details,
                "state": "pending",
                "order_key": ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8)),
                "box_key": box_key,
                "dateTime": datetime.now(),
                "temperature_logs": [],
                "access_logs": []
            }
            
            # Insertar en la base de datos
            result = orders_collection.insert_one(new_order)
            
            # Actualizar la caja con la nueva clave
            boxes_collection.update_one(
                {"_id": box_id},
                {"$set": {"current_order_id": result.inserted_id}}
            )
            
            return JsonResponse({
                "status": "success",
                "message": "Pedido creado correctamente",
                "order_id": str(result.inserted_id),
                "order_key": new_order["order_key"],
                "box_key": box_key
            })
        except Exception as e:
            logger.error(f"Error en create_order: {str(e)}")
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    else:
        return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)

# Registrar una nueva caja
@csrf_exempt
def register_box(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            serial_number = data.get("serial_number")
            position = data.get("position", "No especificada")
            
            if not serial_number:
                return JsonResponse({"status": "error", "message": "Número de serie requerido"}, status=400)
            
            # Verificar si la caja ya existe
            existing_box = boxes_collection.find_one({"serie": serial_number})
            if existing_box:
                return JsonResponse({"status": "error", "message": "La caja ya está registrada"}, status=400)
            
            # Crear nueva caja
            new_box = {
                "serie": serial_number,
                "position": position,
                "status": "active",
                "registration_date": datetime.now(),
                "last_update": datetime.now(),
                "temperatura": 0,
                "on": 1
            }
            
            result = boxes_collection.insert_one(new_box)
            
            return JsonResponse({
                "status": "success",
                "message": "Caja registrada correctamente",
                "box_id": str(result.inserted_id)
            })
        except Exception as e:
            logger.error(f"Error en register_box: {str(e)}")
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    else:
        return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)
