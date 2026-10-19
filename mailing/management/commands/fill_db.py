"""
Заполняет БД тестовыми данными для проверки сервиса рассылок.

Использование:
    python manage.py fill_db
    python manage.py fill_db --clear       # предварительно удалить старые тестовые данные
    python manage.py fill_db --user admin  # привязать данные к пользователю admin
"""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from mailing.models import Attempt, Mailing, Message, Recipient


class Command(BaseCommand):
    help = 'Заполняет БД тестовыми получателями, сообщениями и рассылками'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Удалить существующие данные приложения mailing перед заполнением',
        )
        parser.add_argument(
            '--user',
            type=str,
            default=None,
            help='Username, которому привязать данные (по умолчанию — первый суперпользователь)',
        )

    def handle(self, *args, **options):
        user = self._resolve_user(options['user'])

        if options['clear']:
            self._clear_data()

        recipients = self._create_recipients(user)
        messages_ = self._create_messages(user)
        mailings = self._create_mailings(user, recipients, messages_)

        self._print_summary(recipients, messages_, mailings)

    # ---------------- helpers ----------------
    def _resolve_user(self, username):
        User = get_user_model()
        if username:
            try:
                return User.objects.get(username=username)
            except User.DoesNotExist:
                self.stderr.write(self.style.ERROR(
                    f'Пользователь "{username}" не найден.'
                ))
                raise SystemExit(1)

        user = User.objects.filter(is_superuser=True).order_by('pk').first()
        if user:
            return user

        self.stdout.write(self.style.WARNING(
            'Суперпользователь не найден — создаю "admin" с паролем "admin123".'
        ))
        return User.objects.create_superuser(
            username='admin', email='admin@example.com', password='admin123'
        )

    def _clear_data(self):
        # порядок важен из-за FK: Attempt → Mailing → (Message, Recipient)
        Attempt.objects.all().delete()
        Mailing.objects.all().delete()
        Message.objects.all().delete()
        Recipient.objects.all().delete()
        self.stdout.write(self.style.WARNING('Старые данные mailing удалены.'))

    def _create_recipients(self, user):
        data = [
            ('ivanov@example.com', 'Иванов Иван Иванович', 'VIP-клиент'),
            ('petrova@example.com', 'Петрова Мария Сергеевна', 'Постоянный покупатель'),
            ('sidorov@example.com', 'Сидоров Алексей Петрович', ''),
            ('kuznetsova@example.com', 'Кузнецова Ольга Андреевна', 'Новый клиент'),
            ('smirnov@example.com', 'Смирнов Дмитрий Николаевич', 'Оптовая закупка'),
            ('popova@example.com', 'Попова Екатерина Викторовна', ''),
            ('vasiliev@example.com', 'Васильев Андрей Игоревич', 'Договор №42'),
            ('novikova@example.com', 'Новикова Анна Дмитриевна', 'Рекламации не было'),
        ]
        objs = [
            Recipient(email=email, full_name=name, comment=comment, owner=user)
            for email, name, comment in data
        ]
        return Recipient.objects.bulk_create(objs, ignore_conflicts=True)

    def _create_messages(self, user):
        data = [
            (
                'Добро пожаловать!',
                'Здравствуйте!\n\nСпасибо за регистрацию. '
                'Мы рады видеть вас среди наших клиентов.\n\nС уважением, команда.',
            ),
            (
                'Скидки 20% на этой неделе',
                'Только до воскресенья — скидка 20% на весь ассортимент.\n'
                'Промокод: WEEK20.',
            ),
            (
                'Напоминание о заказе',
                'Ваш заказ готов к выдаче. Заберите его в ближайшее время.',
            ),
            (
                'Новинки каталога',
                'В нашем каталоге появились новые товары. Загляните!',
            ),
            (
                'Опрос',
                'Пожалуйста, оцените наш сервис по 5-балльной шкале. '
                'Это займёт не больше минуты.',
            ),
        ]
        objs = [
            Message(subject=subject, body=body, owner=user)
            for subject, body in data
        ]
        return Message.objects.bulk_create(objs)

    def _create_mailings(self, user, recipients, messages_):
        now = timezone.now()

        # 1. Активная: окно сейчас, статус должен стать 'started'
        active = Mailing.objects.create(
            start_time=now - timedelta(minutes=30),
            end_time=now + timedelta(hours=2),
            message=messages_[0],
            owner=user,
        )
        active.recipients.set([r.pk for r in recipients[:4]])

        # 2. Будущая: start через час → 'created'
        future = Mailing.objects.create(
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=3),
            message=messages_[1],
            owner=user,
        )
        future.recipients.set([r.pk for r in recipients[:3]])

        # 3. Завершённая: окно в прошлом → 'finished'
        past = Mailing.objects.create(
            start_time=now - timedelta(days=2),
            end_time=now - timedelta(days=1),
            message=messages_[2],
            owner=user,
        )
        past.recipients.set([r.pk for r in recipients[2:6]])

        # 4. Отключённая менеджером
        disabled = Mailing.objects.create(
            start_time=now - timedelta(minutes=10),
            end_time=now + timedelta(hours=1),
            message=messages_[3],
            owner=user,
            is_disabled=True,
        )
        disabled.recipients.set([r.pk for r in recipients[:2]])

        # 5. Ещё одна активная, больше получателей — для проверки "Отправить"
        another_active = Mailing.objects.create(
            start_time=now - timedelta(minutes=5),
            end_time=now + timedelta(hours=1),
            message=messages_[4],
            owner=user,
        )
        another_active.recipients.set([r.pk for r in recipients])

        # Историю попыток создадим для завершённой (past) — как будто уже отправляли
        attempts = []
        for recipient in past.recipients.all():
            attempts.append(Attempt(
                mailing=past,
                status=Attempt.STATUS_OK,
                server_response='250 OK (seed)',
            ))
        if attempts:
            Attempt.objects.bulk_create(attempts)

        # и одну «неуспешную» попытку для истории
        Attempt.objects.create(
            mailing=past,
            status=Attempt.STATUS_FAIL,
            server_response='SMTP 550 mailbox unavailable (seed)',
        )

        # Обновим статусы в БД
        for m in Mailing.objects.all():
            m.update_status()

        return [active, future, past, disabled, another_active]

    def _print_summary(self, recipients, messages_, mailings):
        self.stdout.write(self.style.SUCCESS('Тестовые данные созданы:'))
        self.stdout.write(f'  Получателей: {Recipient.objects.count()}')
        self.stdout.write(f'  Сообщений:   {Message.objects.count()}')
        self.stdout.write(f'  Рассылок:    {Mailing.objects.count()}')
        self.stdout.write(f'  Попыток:     {Attempt.objects.count()}')
        self.stdout.write('')
        self.stdout.write('Статусы рассылок:')
        for m in Mailing.objects.order_by('pk'):
            self.stdout.write(
                f'  #{m.pk}: {m.get_status_display():<10} '
                f'окно {m.start_time:%d.%m %H:%M} — {m.end_time:%d.%m %H:%M}'
                f'{" [отключена]" if m.is_disabled else ""}'
            )