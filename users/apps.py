from django.apps import AppConfig, apps


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "users"

    def ready(self):
        User = apps.get_model('auth', 'User')

        def is_manager(self):
            return self.is_superuser or self.groups.filter(name='manager').exists()

        # Добавляем свойство is_manager в стандартную модель User
        User.add_to_class('is_manager', property(is_manager))
