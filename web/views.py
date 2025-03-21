from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import datetime
from bson import ObjectId
from models import *

# Página web para mostrar los datos de temperatura
def order_view(request, order_id=None):
    if order_id:
        # Si se proporciona un ID de orden específico
        try:
            order = orders_collection.find_one({"_id": ObjectId(order_id)})
            if order:
                return render(request, 'web/order_detail.html', {'order': order})
            else:
                return render(request, 'web/error.html', {'message': 'Orden no encontrada'})
        except Exception as e:
            return render(request, 'web/error.html', {'message': str(e)})
    else:
        # Mostrar todas las órdenes
        orders = list(orders_collection.find().sort("timestamp", -1))
        return render(request, 'web/orders.html', {'orders': orders})

# API para obtener la información de una caja específica
@csrf_exempt
def get_box_key(request, box_id):
    try:
        box = boxes_collection.find_one({"box_id": box_id})
        if box:
            return JsonResponse({
                "status": "success",
                "box_key": str(box.get("_id")),
                "name": box.get("name", "")
            })
        else:
            return JsonResponse({
                "status": "error",
                "message": "Box no encontrada"
            }, status=404)
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": str(e)
        }, status=500)

# API para registrar datos de temperatura
@csrf_exempt
def register_temperature(request):
    if request.method == 'POST':
        try:
            # Decodificar el cuerpo de la solicitud JSON
            data = json.loads(request.body)
            
            # Validar los datos recibidos
            required_fields = ['box_key', 'temperature']
            for field in required_fields:
                if field not in data:
                    return JsonResponse({
                        "status": "error",
                        "message": f"Campo requerido: {field}"
                    }, status=400)
            
            # Crear registro de temperatura
            temperature_data = {
                "box_id": data['box_key'],
                "temperature": float(data['temperature']),
                "timestamp": datetime.now(),
                "status": data.get('status', 'closed')  # Por defecto está cerrado
            }
            
            # Agregar campos opcionales
            if 'humidity' in data:
                temperature_data['humidity'] = float(data['humidity'])
            
            if 'proximity' in data:
                temperature_data['proximity'] = data['proximity']
            
            # Si el estado es 'open', iniciar timer o registrar que está abierto
            if data.get('status') == 'open':
                temperature_data['opened_at'] = datetime.now()
            
            # Guardar en la colección orders
            result = orders_collection.insert_one(temperature_data)
            
            return JsonResponse({
                "status": "success",
                "order_id": str(result.inserted_id)
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                "status": "error",
                "message": "Formato JSON inválido"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status": "error", 
                "message": str(e)
            }, status=500)
    else:
        return JsonResponse({
            "status": "error",
            "message": "Método no permitido"
        }, status=405)

# API para obtener el último estado de una caja
@csrf_exempt
def get_box_status(request, box_id):
    try:
        # Buscar la box primero para verificar que existe
        box = boxes_collection.find_one({"box_id": box_id})
        if not box:
            return JsonResponse({
                "status": "error",
                "message": "Box no encontrada"
            }, status=404)
        
        # Buscar el último registro de esta caja
        last_order = orders_collection.find_one(
            {"box_id": str(box.get("_id"))},
            sort=[("timestamp", -1)]
        )
        
        if last_order:
            # Formatear la respuesta
            response_data = {
                "status": "success",
                "box_id": box_id,
                "last_temperature": last_order.get("temperature"),
                "box_status": last_order.get("status", "closed"),
                "last_updated": last_order.get("timestamp").isoformat()
            }
            
            # Agregar campos opcionales si existen
            if "humidity" in last_order:
                response_data["humidity"] = last_order.get("humidity")
            
            if "proximity" in last_order:
                response_data["proximity"] = last_order.get("proximity")
            
            return JsonResponse(response_data)
        else:
            return JsonResponse({
                "status": "success",
                "box_id": box_id,
                "message": "No hay registros para esta caja"
            })
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": str(e)
        }, status=500)