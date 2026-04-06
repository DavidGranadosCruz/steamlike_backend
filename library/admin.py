from django.contrib import admin
from .models import LibraryEntry

@admin.register(LibraryEntry)
class LibraryEntryAdmin(admin.ModelAdmin):
    list_display = ("external_game_id", "status", "hours_played")
    search_fields = ("external_game_id",)
    list_filter = ("status",)
