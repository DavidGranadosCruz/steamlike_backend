import json

from django.conf import settings
from django.contrib.auth import get_user_model, authenticate, login, logout, update_session_auth_hash
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from django.db import IntegrityError, transaction
from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods

from .catalog_service import CatalogService, CatalogServiceError, CatalogServiceUnavailable
from .email_service import EmailService, EmailServiceError, EmailServiceUnavailable
from .models import LibraryEntry


@require_GET
def health(request):
    return JsonResponse({"status": "ok"})


# Ejercicio 3
def serializar_entrada(entrada):
    # Aqui uso un formato unico para create, listado y detalle.
    return {
        "id": entrada.id,
        "external_game_id": entrada.external_game_id,
        "status": entrada.status,
        "hours_played": entrada.hours_played,
    }


# Ejercicio 3
def error_validacion(details):
    # Esto ya lo tenia de antes para devolver 400 de validacion.
    return JsonResponse(
        {
            "error": "validation_error",
            "message": "Datos de entrada invalidos",
            "details": details,
        },
        status=400,
    )


# Ejercicio 3
def error_duplicado(details):
    # Esto ya lo tenia de antes para el caso de juego duplicado.
    return JsonResponse(
        {
            "error": "duplicate_entry",
            "message": "El juego ya existe en la biblioteca",
            "details": details,
        },
        status=400,
    )


# Ejercicio 3
def error_no_encontrado():
    # Esto lo agregue antes para responder claro cuando el id no existe.
    return JsonResponse(
        {
            "error": "not_found",
            "message": "La entrada solicitada no existe",
        },
        status=404,
    )


def error_no_autorizado(message="No autenticado."):
    return JsonResponse(
        {
            "error": "unauthorized",
            "message": message,
        },
        status=401,
    )


# Ejercicio 4
def error_servicio_no_disponible():
    return JsonResponse(
        {
            "error": "external_service_unavailable",
            "message": "El catálogo externo no está disponible. Inténtalo más tarde."
        }, status=503
    )

def error_servicio_externo():
    return JsonResponse(
        {
            "error": "external_service_error",
            "message": "Error al consultar el catálogo externo."
        }, status=502
    )

def error_email_no_disponible():
    return JsonResponse(
        {
            "error": "external_service_unavailable",
            "message": "El servicio de email no está disponible. Inténtalo más tarde."
        }, status=503
    )

def error_email_externo():
    return JsonResponse(
        {
            "error": "external_service_error",
            "message": "Error al consultar el servicio de email."
        }, status=502
    )

def error_id_externo_invalido():
    return JsonResponse(
        {
            "error": "invalid_external_game_id",
            "message": "El juego indicado no existe en el catálogo externo.",
            "details": { "external_game_id": "not_found" }
        }, status=400
    )


# Ejercicio 3
def leer_json(request):
    # Leo el body como JSON de forma simple
    if not request.body:
        return {}

    try:
        return json.loads(request.body)
    except Exception:
        return None



def email_valido(email):
    try:
        validate_email(email)
    except ValidationError:
        return False
    return True


def enviar_email_bienvenida(user):
    subject = "Bienvenido a Nexus Play"
    text = (
        f"Hola {user.username},\n\n"
        "Tu cuenta se ha creado correctamente en Nexus Play.\n"
        "Ya puedes buscar juegos y añadirlos a tu biblioteca.\n"
    )
    html = (
        f"<p>Hola {user.username},</p>"
        "<p>Tu cuenta se ha creado correctamente en Nexus Play.</p>"
        "<p>Ya puedes buscar juegos y añadirlos a tu biblioteca.</p>"
    )
    EmailService().send_email(
        to=user.email,
        subject=subject,
        text=text,
        html=html,
        action="register_welcome",
        user=user,
    )


# Ejercicio 3
def buscar_entrada(entry_id):
    # Me ahorro repetir la busqueda de id en detalle y patch.
    try:
        return LibraryEntry.objects.get(id=entry_id)
    except LibraryEntry.DoesNotExist:
        return None


@require_GET
def listar_entradas_biblioteca(request):
    if not request.user.is_authenticated:
        return error_no_autorizado()

    # Devuelvo todas las entradas como lista.
    entradas = LibraryEntry.objects.filter(user=request.user).order_by("id")
    data = [serializar_entrada(entrada) for entrada in entradas]
    return JsonResponse(data, safe=False, status=200)


def detalle_entrada_biblioteca(request, entry_id):
    if not request.user.is_authenticated:
        return error_no_autorizado()

    # Devuelvo el detalle de una entrada por id.
    entrada = buscar_entrada(entry_id)
    if entrada is None or entrada.user != request.user:
        return error_no_encontrado()

    return JsonResponse(serializar_entrada(entrada), status=200)


def crear_entrada_biblioteca(request):
    if not request.user.is_authenticated:
        return error_no_autorizado()

    # Esto ya lo tenia de antes: valido JSON y campos para crear.
    data = leer_json(request)
    if data is None:
        return error_validacion({"body": "JSON mal formado."})

    if not isinstance(data, dict):
        return error_validacion({"body": "El JSON debe ser un objeto."})

    if data == {}:
        return error_validacion({"body": "El JSON no puede estar vacio."})

    details = {}

    if "external_game_id" not in data:
        details["external_game_id"] = "Campo obligatorio."
    elif not isinstance(data["external_game_id"], str):
        details["external_game_id"] = "Debe ser string."
    elif not data["external_game_id"].strip():
        details["external_game_id"] = "No puede estar vacio."

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

    if details:
        return error_validacion(details)

    data["external_game_id"] = data["external_game_id"].strip()

    try:
        existe = CatalogService().external_game_id_exists(data["external_game_id"])
    except CatalogServiceUnavailable:
        return error_servicio_no_disponible()
    except CatalogServiceError:
        return error_servicio_externo()

    if not existe:
        return error_id_externo_invalido()

    try:
        with transaction.atomic():
            entrada = LibraryEntry.objects.create(
                user=request.user,
                external_game_id=data["external_game_id"],
                status=data["status"],
                hours_played=data["hours_played"],
            )
    except IntegrityError:
        return error_duplicado({"external_game_id": "duplicate"})

    return JsonResponse(serializar_entrada(entrada), status=201)


# Ejercicio 5
def actualizar_entrada_biblioteca(request, entry_id):
    if not request.user.is_authenticated:
        return error_no_autorizado()

    # Aqui hago el PATCH porque modifico algunos campos
    data = leer_json(request)
    if data is None:
        return error_validacion({"body": "JSON mal formado."})

    if not isinstance(data, dict):
        return error_validacion({"body": "El JSON debe ser un objeto."})

    if data == {}:
        return error_validacion({"body": "El JSON no puede estar vacio."})

    entrada = buscar_entrada(entry_id)
    if entrada is None or entrada.user != request.user:
        return error_no_encontrado()

    details = {}
    campos_permitidos = {"status", "hours_played"}

    for campo in data:
        if campo not in campos_permitidos:
            details[campo] = "Campo no permitido."

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

    if "status" in data:
        entrada.status = data["status"]

    if "hours_played" in data:
        entrada.hours_played = data["hours_played"]

    entrada.save()
    return JsonResponse(serializar_entrada(entrada), status=200)


# Ejercicio 4
def sustituir_entrada_biblioteca(request, entry_id):
    if not request.user.is_authenticated:
        return error_no_autorizado()

    # Aqui leo el body como JSON para el PUT
    data = leer_json(request)
    if data is None:
        return error_validacion({"body": "JSON mal formado."})

    if not isinstance(data, dict):
        return error_validacion({"body": "El JSON debe ser un objeto."})

    if data == {}:
        return error_validacion({"body": "El JSON no puede estar vacio."})

    # Busco la entrada y verifico si es del usuario autenticado
    entrada = buscar_entrada(entry_id)
    if entrada is None or entrada.user != request.user:
        return error_no_encontrado()

    details = {}

    # Valido que me lleguen todos los campos obligatorios para el PUT
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

    if details:
        return error_validacion(details)

    # Sustituyo por completo los valores anteriores
    entrada.external_game_id = data["external_game_id"]
    entrada.status = data["status"]
    entrada.hours_played = data["hours_played"]

    # Intento guardar, capturando un posible error de id externo duplicado
    try:
        entrada.save()
    except IntegrityError:
        return error_duplicado({"external_game_id": "duplicate"})

    return JsonResponse(serializar_entrada(entrada), status=200)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def entradas_biblioteca(request):
    # En esta ruta hago listado si es GET o alta si es POST.
    if request.method == "GET":
        return listar_entradas_biblioteca(request)
    return crear_entrada_biblioteca(request)


@csrf_exempt
@require_http_methods(["GET", "PATCH", "PUT"])
def entrada_biblioteca_detalle(request, entry_id):
    # En detalle hago GET para ver, PATCH para actualizar y PUT para sustituir.
    if request.method == "GET":
        return detalle_entrada_biblioteca(request, entry_id)
    elif request.method == "PUT":
        return sustituir_entrada_biblioteca(request, entry_id)
    return actualizar_entrada_biblioteca(request, entry_id)


@csrf_exempt
@require_http_methods(["POST"])
def registrar_usuario(request):
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
    elif not isinstance(data["username"], str):
        details["username"] = "Debe ser string."

    if "password" not in data:
        details["password"] = "Campo obligatorio."
    elif not isinstance(data["password"], str):
        details["password"] = "Debe ser string."
    elif len(data["password"]) < 8:
        details["password"] = "La contraseña debe tener mínimo 8 caracteres."

    if "email" not in data:
        details["email"] = "Campo obligatorio."
    elif not isinstance(data["email"], str):
        details["email"] = "Debe ser string."
    elif not data["email"].strip():
        details["email"] = "No puede estar vacio."
    elif not email_valido(data["email"].strip()):
        details["email"] = "Debe tener un formato valido."

    if details:
        return error_validacion(details)

    email = data["email"].strip()
    User = get_user_model()
    # Comprobar si existe el usuario y uso objects.filter() para obtener el usuario
    if User.objects.filter(username=data["username"]).exists():
        return error_validacion({"username": "El username ya está en uso."})

    user = User.objects.create_user(
        username=data["username"],
        password=data["password"],
        email=email,
    )

    try:
        enviar_email_bienvenida(user)
    except (EmailServiceUnavailable, EmailServiceError):
        pass

    return JsonResponse(
        {"id": user.id, "username": user.username, "email": user.email},
        status=201,
    )


@csrf_exempt
@require_http_methods(["POST"])
def iniciar_sesion(request):
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
    elif not isinstance(data["username"], str):
        details["username"] = "Debe ser string."

    if "password" not in data:
        details["password"] = "Campo obligatorio."
    elif not isinstance(data["password"], str):
        details["password"] = "Debe ser string."

    if details:
        return error_validacion(details)

    user = authenticate(request, username=data["username"], password=data["password"])
    if user is not None:
        login(request, user)
        return JsonResponse({"id": user.id, "username": user.username}, status=200)
    else:
        return error_no_autorizado(message="Credenciales incorrectas")


@require_GET
def usuario_actual(request):
    if request.user.is_authenticated:
        return JsonResponse({"id": request.user.id, "username": request.user.username}, status=200)
    else:
        return error_no_autorizado(message="No autenticado")

# Ejercicio 2
@csrf_exempt
@require_http_methods(["POST"])
def cambiar_contraseña(request):
    if not request.user.is_authenticated:
        return error_no_autorizado()

    data = leer_json(request)
    if data is None:
        return error_validacion({"body": "JSON mal formado."})

    if not isinstance(data, dict):
        return error_validacion({"body": "El JSON debe ser un objeto."})

    if data == {}:
        return error_validacion({"body": "El JSON no puede estar vacio."})

    details = {}

    if "current_password" not in data:
        details["current_password"] = "Campo obligatorio."
    elif not isinstance(data["current_password"], str):
        details["current_password"] = "Debe ser string."

    if "new_password" not in data:
        details["new_password"] = "Campo obligatorio."
    elif not isinstance(data["new_password"], str):
        details["new_password"] = "Debe ser string."
    elif len(data["new_password"]) < 8:
        details["new_password"] = "La contraseña debe tener mínimo 8 caracteres."

    if details:
        return error_validacion(details)

    if not request.user.check_password(data["current_password"]):
        return error_validacion({"current_password": "La contraseña actual es incorrecta."})

    request.user.set_password(data["new_password"])
    request.user.save()

    update_session_auth_hash(request, request.user)

    return JsonResponse({"ok": True}, status=200)


# Ejercicio 6
@csrf_exempt
@require_http_methods(["POST"])
def cerrar_sesion(request):
    # Si el usuario esta logueado se cierra la sesion, si no, no pasa nada
    # En ambos casos devolvemos un 204 sin contenido en el body
    logout(request)
    return HttpResponse(status=204)


@csrf_exempt
@require_http_methods(["POST"])
def debug_email_test(request):
    if not settings.DEBUG:
        raise Http404()

    data = leer_json(request)
    if data is None:
        return error_validacion({"body": "JSON mal formado."})

    if not isinstance(data, dict):
        return error_validacion({"body": "El JSON debe ser un objeto."})

    if data == {}:
        return error_validacion({"body": "El JSON no puede estar vacio."})

    details = {}
    for field in ("to", "subject", "text"):
        if field not in data:
            details[field] = "Campo obligatorio."
        elif not isinstance(data[field], str):
            details[field] = "Debe ser string."
        elif not data[field].strip():
            details[field] = "No puede estar vacio."

    if details:
        return error_validacion(details)

    try:
        EmailService().send_email(
            to=data["to"].strip(),
            subject=data["subject"].strip(),
            text=data["text"].strip(),
            action="send_email",
        )
    except EmailServiceUnavailable:
        return error_email_no_disponible()
    except EmailServiceError:
        return error_email_externo()

    return JsonResponse({"ok": True}, status=200)


# Ejercicio 2 semana 4
@require_GET
def buscar_catalogo(request):
    q = request.GET.get("q", "").strip()
    if not q:
        return error_validacion({"q": "Parámetro obligatorio y no vacío."})

    try:
        data = CatalogService().search_games(q)
    except CatalogServiceUnavailable:
        return error_servicio_no_disponible()
    except CatalogServiceError:
        return error_servicio_externo()

    return JsonResponse(data, safe=False, status=200)

# Ejercicio 3 semana 4
@csrf_exempt
@require_http_methods(["POST"])
def resolver_catalogo(request):
    data = leer_json(request)
    if data is None or not isinstance(data, dict):
        return error_validacion({"body": "Se requiere un JSON válido."})

    external_game_ids = data.get("external_game_ids")
    if not isinstance(external_game_ids, list) or len(external_game_ids) == 0:
        return error_validacion({"external_game_ids": "Debe ser una lista no vacía."})

    ids_limpios = []
    for gid in external_game_ids:
        if not isinstance(gid, str) or not gid.strip():
            return error_validacion({"external_game_ids": "Todos los elementos deben ser strings no vacíos."})
        ids_limpios.append(gid.strip())

    try:
        resultados = CatalogService().resolve_games(ids_limpios)
    except CatalogServiceUnavailable:
        return error_servicio_no_disponible()
    except CatalogServiceError:
        return error_servicio_externo()

    return JsonResponse(resultados, safe=False, status=200)

