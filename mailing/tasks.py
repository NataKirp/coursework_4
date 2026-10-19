import logging
from celery import shared_task
from django.utils import timezone
from .models import Mailing
from .services import send_mailing, MailingNotAllowed

logger = logging.getLogger(__name__)


@shared_task
def send_scheduled_mailings():
    """
    Периодическая задача: ищет рассылки, у которых наступило время,
    и отправляет их.
    """
    now = timezone.now()

    # Ищем рассылки, которые должны работать СЕЙЧАС и ещё не отключены
    active_mailings = Mailing.objects.filter(
        start_time__lte=now,
        end_time__gte=now,
        is_disabled=False
    )

    sent_count = 0
    for mailing in active_mailings:
        # Обновляем статус в БД (на случай, если он устарел)
        mailing.update_status()

        # Проверяем, нет ли уже успешных попыток для этой рассылки.
        if mailing.attempts.filter(status='ok').exists():
            continue

        try:
            attempts = send_mailing(mailing)
            sent_count += 1
            logger.info(f"Автоматически отправлена рассылка #{mailing.pk}. Попыток: {len(attempts)}")
        except MailingNotAllowed as e:
            logger.warning(f"Не удалось отправить рассылку #{mailing.pk}: {e}")
        except Exception as e:
            logger.error(f"Ошибка при отправке рассылки #{mailing.pk}: {e}")

    return f"Отправлено рассылок: {sent_count}"
