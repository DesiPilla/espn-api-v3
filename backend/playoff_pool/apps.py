from django.apps import AppConfig


class PlayoffPoolConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "backend.playoff_pool"

    def ready(self):
        from nflreadpy.config import update_config, CacheMode

        update_config(cache_mode=CacheMode.FILESYSTEM)
