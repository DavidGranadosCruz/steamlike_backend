# Configuración del User por defecto de Django y sesiones

Este documento recoge los pasos necesarios para:

- Usar el **User por defecto de Django**
- Habilitar **sesiones y autenticación**
- Enlazar un modelo con `User`

---

## 1. Comprobar la configuración base en `settings.py`

### 1.1 Aplicaciones necesarias

Django necesita las apps de autenticación y sesiones activas.

```python
# settings.py
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "Corsheaders",
    "tus_apps",
]
```

---

### 1.2 Middleware necesario

Para que funcionen las **sesiones** y `request.user`, deben estar activa esta configuración:

```python
# settings.py
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
```

> Si falta `SessionMiddleware` o `AuthenticationMiddleware`, **no existirán las sesiones ni `request.user`**.




---

## 2. Uso del modelo User por defecto

En cualquier archivo donde se necesite el modelo User:

```python
from django.contrib.auth import get_user_model

User = get_user_model()
```

Este modelo:
- gestiona contraseñas de forma segura (hash)
- se integra con sesiones y autenticación

---

## 3. Enlazar un modelo con `User`

### 3.1 Modificar el modelo

En `models.py`:

```python
from django.conf import settings
from django.db import models

class LibraryEntry(models.Model):
    external_game_id = models.CharField(max_length=100)
    status = models.CharField(max_length=20)
    hours_played = models.IntegerField(default=0)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, # Importante
        on_delete=models.CASCADE,
        null=True,        # para no romper datos existentes
        blank=True,
        related_name="library_entries",
    )
```

---

### 3.2 Crear y aplicar la migración

```bash
python manage.py makemigrations
python manage.py migrate
```

En este punto:
- el proyecto debe arrancar sin errores
- los datos existentes no se han borrado

---

## 4. Operaciones habituales con usuarios y sesiones

### 4.1 Crear un usuario

```python
from django.contrib.auth import get_user_model

User = get_user_model()

user = User.objects.create_user(
    username="ana",
    password="1234"
)
# create_user:
#  - recibe la contraseña en texto plano
#  - la hashea automáticamente
#  - guarda únicamente el hash en la base de datos
```

---

### 4.2 Autenticar un usuario (login)

```python
from django.contrib.auth import authenticate, login

user = authenticate(request, username=username, password=password)
# authenticate:
#  - recibe la contraseña en texto plano
#  - la compara con el hash almacenado
#  - devuelve el usuario si las credenciales son correctas

if user is not None:
    login(request, user)
    # login:
    #  - crea una sesión en el servidor
    #  - asocia la sesión al usuario
    #  - provoca el envío de la cookie de sesión al cliente
```

---

### 4.3 Cerrar sesión (logout)

```python
from django.contrib.auth import logout

logout(request)
# logout:
#  - elimina la sesión en el servidor
#  - invalida la cookie de sesión
#  - request.user pasa a ser un usuario anónimo
```

---

### 4.4 Comprobar si el usuario está autenticado

```python
if request.user.is_authenticated:
    pass
# is_authenticated: indica si la petición está asociada a una sesión válida
```

---

### 4.5 Obtener el usuario actual desde la petición

```python
user = request.user

# request.user:
#  - devuelve el usuario autenticado si existe sesión válida
#  - devuelve un usuario anónimo si no hay sesión
```

---

### 4.6 Filtrar datos asociados al usuario

```python
LibraryEntry.objects.filter(user=request.user)

# Este filtrado:
#  - garantiza que solo se accede a los recursos del usuario autenticado
#  - evita exponer datos de otros usuarios
```



