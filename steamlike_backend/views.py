from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.http import require_GET


@require_GET
def frontend_app(request, path=""):
    index_path = settings.BASE_DIR / "frontend" / "dist" / "index.html"
    try:
        content = index_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return HttpResponse(
            "Frontend build not found. Run `npm ci && npm run build` inside frontend/.",
            status=503,
            content_type="text/plain; charset=utf-8",
        )
    return HttpResponse(content, content_type="text/html; charset=utf-8")
