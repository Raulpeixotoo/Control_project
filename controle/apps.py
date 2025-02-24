from django.apps import AppConfig


class ControleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'controle'

    def ready(self):
        # Importa os filtros personalizados ao iniciar o aplicativo
        import controle.templatetags.custom_filters