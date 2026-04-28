from django.conf import settings
from django.db import models
from django.contrib.auth.models import User

class LibraryEntry(models.Model):
    STATUS_WISHLIST = "wishlist"
    STATUS_PLAYING = "playing"
    STATUS_COMPLETED = "completed"
    STATUS_DROPPED = "dropped"

    ALLOWED_STATUSES = (
        STATUS_WISHLIST,
        STATUS_PLAYING,
        STATUS_COMPLETED,
        STATUS_DROPPED,
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    external_game_id = models.CharField(max_length=100)

    class Meta:
        unique_together = ("user", "external_game_id")
    status = models.CharField(max_length=20, default=STATUS_WISHLIST)
    hours_played = models.IntegerField(default=0)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="library_entries",
    )

    def external_id_length(self) -> int:
        return len(self.external_game_id or "")

    def external_id_upper(self) -> str:
        return (self.external_game_id or "").upper()

    def hours_played_label(self) -> str:
        if self.hours_played == 0:
            return "none"
        elif self.hours_played < 10:
            return "low"
        else:
            return "high"

    def status_value(self) -> int:
        if self.status == self.STATUS_WISHLIST:
            return 0
        elif self.status == self.STATUS_PLAYING:
            return 1
        elif self.status == self.STATUS_COMPLETED:
            return 2
        elif self.status == self.STATUS_DROPPED:
            return 3
        else:
            return -1
