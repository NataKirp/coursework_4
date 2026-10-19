from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.contrib.auth.hashers import make_password


class Command(BaseCommand):
    help = 'Создает группу manager и пользователя manager'

    def handle(self, *args, **options):
        group, created = Group.objects.get_or_create(name='manager')
        if created:
            self.stdout.write(self.style.SUCCESS('Группа "manager" создана.'))

        if not User.objects.filter(username='manager').exists():
            User.objects.create(
                username='manager',
                email='manager@example.com',
                password=make_password('manager123'),
                is_staff=True,
            )
            self.stdout.write(self.style.SUCCESS('Пользователь "manager" (пароль: manager123) создан.'))
        else:
            self.stdout.write('Пользователь "manager" уже существует.')

        user = User.objects.get(username='manager')
        user.groups.add(group)
        self.stdout.write(self.style.SUCCESS('Пользователь "manager" добавлен в группу "manager".'))