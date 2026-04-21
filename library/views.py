import json

from django.contrib.auth import authenticate, login as django_login
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods

from .models import LibraryEntry


@require_GET
def health(request):
    return JsonResponse({"status": "ok"})


def serializar_entrada(entrada):
    # Aqui uso un formato unico para create listado y detalle.
    return {
        "id": entrada.id,
        "external_game_id": entrada.external_game_id,
        "status": entrada.status,
        "hours_played": entrada.hours_played,
    }


def error_validacion(details):
    # Devolver errores 400 de validacion.
    return JsonResponse(
        {
            "error": "validation_error",
            "message": "Datos de entrada invalidos",
            "details": details,
        },
        status=400,
    )


def error_duplicado(details):
    # Para cuando intentan meter un juego duplicado.
    return JsonResponse(
        {
            "error": "duplicate_entry",
            "message": "El juego ya existe en la biblioteca",
            "details": details,
        },
        status=400,
    )


def error_no_encontrado():
    # Esto lo agrego para el detalle cuando el id no existe.
    return JsonResponse(
        {
            "error": "not_found",
            "message": "La entrada solicitada no existe",
        },
        status=404,
    )

def error_no_autenticado():
    return JsonResponse({"error": "unauthorized", "message": "No autenticado"}, status=401)

def error_credenciales():
    return JsonResponse({"error": "unauthorized", "message": "Credenciales incorrectas"}, status=401)


def leer_json(request):
    # leer JSON
    if not request.body:
        return {}

    try:
        return json.loads(request.body)
    except Exception:
        return None


@require_GET
def listar_entradas_biblioteca(request):
    if not request.user.is_authenticated:
        return error_no_autenticado()
    # Aqui devuelvo todas las entradas como lista.
    entradas = LibraryEntry.objects.filter(user=request.user).order_by("id")
    data = [serializar_entrada(entrada) for entrada in entradas]
    return JsonResponse(data, safe=False, status=200)


def modificar_entrada_biblioteca(request, entrada):
    data = leer_json(request)
    if data is None:
        return error_validacion({"body": "JSON mal formado."})

    if not isinstance(data, dict):
        return error_validacion({"body": "El JSON debe ser un objeto."})

    if data == {}:
        return error_validacion({"body": "El JSON no puede estar vacio."})

    details = {}

    if "external_game_id" in data:
        if not isinstance(data["external_game_id"], str):
            details["external_game_id"] = "Debe ser string."

    if "status" in data:
        if not isinstance(data["status"], str):
            details["status"] = "Debe ser string."
        elif data["status"] not in LibraryEntry.ALLOWED_STATUSES:
            details["status"] = "Debe ser uno de: wishlist, playing, completed, dropped."

    if "hours_played" in data:
        if isinstance(data["hours_played"], bool) or not isinstance(data["hours_played"], int):
            details["hours_played"] = "Debe ser integer."
        elif data["hours_played"] < 0:
            details["hours_played"] = "Debe ser mayor o igual que 0."

    if details:
        return error_validacion(details)

    if "external_game_id" in data:
        entrada.external_game_id = data["external_game_id"]
    if "status" in data:
        entrada.status = data["status"]
    if "hours_played" in data:
        entrada.hours_played = data["hours_played"]

    try:
        with transaction.atomic():
            entrada.save()
    except IntegrityError:
        return error_duplicado({"external_game_id": "duplicate"})

    return JsonResponse(serializar_entrada(entrada), status=200)


@csrf_exempt
@require_http_methods(["GET", "PATCH"])
def detalle_entrada_biblioteca(request, entry_id):
    if not request.user.is_authenticated:
        return error_no_autenticado()
    # Aqui busco una entrada por id para devolver su detalle o modificarla.
    try:
        entrada = LibraryEntry.objects.get(id=entry_id, user=request.user)
    except LibraryEntry.DoesNotExist:
        return error_no_encontrado()

    if request.method == "GET":
        return JsonResponse(serializar_entrada(entrada), status=200)
    elif request.method == "PATCH":
        return modificar_entrada_biblioteca(request, entrada)


def crear_entrada_biblioteca(request):
    if not request.user.is_authenticated:
        return error_no_autenticado()
    # Valido el JSON.
    data = leer_json(request)
    if data is None:
        return error_validacion({"body": "JSON mal formado."})

    # Valido si no es un objeto o esta vacio
    if not isinstance(data, dict):
        return error_validacion({"body": "El JSON debe ser un objeto."})

    if data == {}:
        return error_validacion({"body": "El JSON no puede estar vacio."})

# Valido y creo diccionario por si hay algo mal con los datos para devolverlos en el error
    details = {}

    if "external_game_id" not in data:
        details["external_game_id"] = "Campo obligatorio."
    elif not isinstance(data["external_game_id"], str):
        details["external_game_id"] = "Debe ser string."

    if "status" not in data:
        details["status"] = "Campo obligatorio."
    elif not isinstance(data["status"], str):
        details["status"] = "Debe ser string."
    elif data["status"] not in LibraryEntry.ALLOWED_STATUSES:
        details["status"] = "Debe ser uno de: wishlist, playing, completed, dropped."

    if "hours_played" not in data:
        details["hours_played"] = "Campo obligatorio."
    elif isinstance(data["hours_played"], bool) or not isinstance(data["hours_played"], int):
        details["hours_played"] = "Debe ser integer."
    elif data["hours_played"] < 0:
        details["hours_played"] = "Debe ser mayor o igual que 0."

#Devolver error de validacion si hay algo mal con los datos.
    if details:
        return error_validacion(details)

    try:
        # controlar bien el error de duplicado.
        with transaction.atomic():
            entrada = LibraryEntry.objects.create(
                external_game_id=data["external_game_id"],
                status=data["status"],
                hours_played=data["hours_played"],
                user=request.user,
            )
    except IntegrityError:
        return error_duplicado(
            {"external_game_id": "duplicate"}
        )

    return JsonResponse(serializar_entrada(entrada), status=201)

# Vista principal que maneja tanto el listado como la creacion segun el metodo.
@csrf_exempt
@require_http_methods(["GET", "POST"])
def entradas_biblioteca(request):
    # Aqui uso la misma ruta y segun el metodo hago listado o alta.
    if request.method == "GET":
        return listar_entradas_biblioteca(request)
    return crear_entrada_biblioteca(request)

@csrf_exempt
@require_http_methods(["POST"])
def register_user(request):
    data = leer_json(request)
    if data is None:
        return error_validacion({"body": "JSON mal formado."})
    if not isinstance(data, dict):
        return error_validacion({"body": "El JSON debe ser un objeto."})
    if data == {}:
        return error_validacion({"body": "El JSON no puede estar vacio."})
    
    details = {}
    if "username" not in data:
        details["username"] = "Campo obligatorio."
    elif User.objects.filter(username=data["username"]).exists():
        details["username"] = "El username ya esta en uso."
        
    if "password" not in data:
        details["password"] = "Campo obligatorio."
    elif len(str(data["password"])) < 6:
        details["password"] = "La contrasena es muy corta."
        
    if details:
        return error_validacion(details)
        
    user = User.objects.create_user(username=data["username"], password=data["password"])
    django_login(request, user)
    return JsonResponse({"id": user.id, "username": user.username}, status=201)

@csrf_exempt
@require_http_methods(["POST"])
def login_user(request):
    data = leer_json(request)
    if data is None: return error_validacion({"body": "JSON mal formado."})
    if not isinstance(data, dict): return error_validacion({"body": "El JSON debe ser un objeto."})
    if data == {}: return error_validacion({"body": "El JSON no puede estar vacio."})
    
    details = {}
    if "username" not in data: details["username"] = "Campo obligatorio."
    if "password" not in data: details["password"] = "Campo obligatorio."
    if details: return error_validacion(details)
    
    user = authenticate(username=data["username"], password=data["password"])
    if user is not None:
        django_login(request, user)
        return JsonResponse({"id": user.id, "username": user.username}, status=200)
    else:
        return error_credenciales()

@require_GET
def me_view(request):
    if not request.user.is_authenticated:
        return error_no_autenticado()
    return JsonResponse({"id": request.user.id, "username": request.user.username}, status=200)

