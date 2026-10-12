from pathlib import Path

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.deconstruct import deconstructible


@deconstructible
class PrivateChatStorage(FileSystemStorage):
    def __init__(self):
        super().__init__(
            location=Path(settings.BASE_DIR) / "private_chat"
        )

    def url(self, name):
        raise ValueError(
            "Chat images require an authenticated endpoint."
        )