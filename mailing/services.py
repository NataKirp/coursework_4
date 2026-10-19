import logging

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import Attempt, Mailing

logger = logging.getLogger(__name__)


class MailingNotAllowed(Exception):
    """Отправка не разрешена: рассылка отключена или вне временного окна."""


def send_mailing(mailing: Mailing) -> list[Attempt]:
    """
    Отправляет рассылку по всем получателям.

    - Проверяет, что рассылка не отключена и текущее время внутри [start_time, end_time].
    - Для каждого получателя вызывает send_mail().
    - Формирует Attempt (ok / fail) и сохраняет их одним batch-запросом.

    Возвращает список созданных Attempt (в памяти, с заполненными pk после bulk_create).
    Исключение MailingNotAllowed — если отправка запрещена по времени/статусу.
    """
    now = timezone.now()

    # 1. Проверки
    if mailing.is_disabled:
        raise MailingNotAllowed('Рассылка отключена менеджером.')

    if not (mailing.start_time <= now <= mailing.end_time):
        raise MailingNotAllowed(
            f'Сейчас {now:%d.%m.%Y %H:%M}. '
            f'Отправка разрешена только в интервале '
            f'{mailing.start_time:%d.%m.%Y %H:%M} — '
            f'{mailing.end_time:%d.%m.%Y %H:%M}.'
        )

    # 2. Актуализируем статус в БД перед отправкой
    mailing.update_status()

    # 3. Собираем попытки
    attempts: list[Attempt] = []

    for recipient in mailing.recipients.all():
        try:
            send_mail(
                subject=mailing.message.subject,
                message=mailing.message.body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient.email],
                fail_silently=False,
            )
            attempts.append(
                Attempt(
                    mailing=mailing,
                    status=Attempt.STATUS_OK,
                    server_response='250 OK',
                )
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception('Ошибка отправки на %s', recipient.email)
            attempts.append(
                Attempt(
                    mailing=mailing,
                    status=Attempt.STATUS_FAIL,
                    server_response=str(exc)[:1000],
                )
            )

    # 4. Batch-создание попыток
    if attempts:
        Attempt.objects.bulk_create(attempts)  # ← требование ТЗ

    logger.info(
        'Рассылка #%s: отправлено %s попыток (успешных: %s).',
        mailing.pk,
        len(attempts),
        sum(1 for a in attempts if a.status == Attempt.STATUS_OK),
    )

    return attempts