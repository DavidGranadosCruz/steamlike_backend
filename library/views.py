import json

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
    # Aqui devuelvo todas las entradas como lista.
    entradas = LibraryEntry.objects.order_by("id")
    data = [serializar_entrada(entrada) for entrada in entradas]
    return JsonResponse(data, safe=False, status=200)


@require_GET
def detalle_entrada_biblioteca(request, entry_id):
    # Aqui busco una entrada por id para devolver su detalle.
    try:
        entrada = LibraryEntry.objects.get(id=entry_id)
    except LibraryEntry.DoesNotExist:
        return error_no_encontrado()

    return JsonResponse(serializar_entrada(entrada), status=200)


def crear_entrada_biblioteca(request):
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
        # Esto ya lo tenia de antes para controlar bien el error de duplicado.
        with transaction.atomic():
            entrada = LibraryEntry.objects.create(
                external_game_id=data["external_game_id"],
                status=data["status"],
                hours_played=data["hours_played"],
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
