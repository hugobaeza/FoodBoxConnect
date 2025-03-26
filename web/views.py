from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import logging
from bson import ObjectId
from db_con import db
from django.contrib.auth.hashers import check_password

# Configurar logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

# Colecciones de MongoDB
users_collection = db["users"]
orders_collection = db["orders"]
boxes_collection = db["boxes"]

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
