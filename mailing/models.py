from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Recipient(models.Model):
    email = models.EmailField(unique=True, verbose_name='Email')
    full_name = models.CharField(max_length=255, verbose_name='Ф. И. О.')
    comment = models.TextField(blank=True, verbose_name='Комментарий')
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recipients',
        null=True,
        blank=True,
        verbose_name='Владелец',
    )

    class Meta:
        verbose_name = 'Получатель'
        verbose_name_plural = 'Получатели'
        ordering = ['email']

    def __str__(self):
        return f'{self.full_name} <{self.email}>'


class Message(models.Model):
    subject = models.CharField(max_length=255, verbose_name='Тема письма')
    body = models.TextField(verbose_name='Тело письма')
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='messages',
        null=True,
        blank=True,
        verbose_name='Владелец',
    )

    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'
        ordering = ['subject']

    def __str__(self):
        return self.subject


class MailingManager(models.Manager):
    def visible_to(self, user):
        qs = self.get_queryset()
        if user.groups.filter(name='manager').exists():
            return qs
        return qs.filter(owner=user)


class Mailing(models.Model):
    STATUS_CREATED = 'created'
    STATUS_STARTED = 'started'
    STATUS_FINISHED = 'finished'
    STATUS_CHOICES = [
        (STATUS_CREATED, 'Создана'),
        (STATUS_STARTED, 'Запущена'),
        (STATUS_FINISHED, 'Завершена'),
    ]

    start_time = models.DateTimeField(verbose_name='Дата и время начала отправки')
    end_time = models.DateTimeField(verbose_name='Дата и время окончания отправки')
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_CREATED,
        verbose_name='Статус',
        db_index=True,
    )
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='mailings',
        verbose_name='Сообщение',
    )
    recipients = models.ManyToManyField(
        Recipient,
        related_name='mailings',
        verbose_name='Получатели',
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mailings',
        null=True,
        blank=True,
        verbose_name='Владелец',
    )
    is_disabled = models.BooleanField(default=False, verbose_name='Отключена')
    objects = MailingManager()

    class Meta:
        verbose_name = 'Рассылка'
        verbose_name_plural = 'Рассылки'
        ordering = ['-start_time']

    def __str__(self):
        return f'Рассылка #{self.pk} — {self.get_status_display()}'

    def clean(self):
        now = timezone.now()
        # Допускаем создание рассылки с start_time в прошлом в пределах 5 минут
        # (на время заполнения формы и клик "Сохранить").
        tolerance = timedelta(minutes=5)
        if self.start_time and self.start_time < (now - tolerance):
            raise ValidationError(
                {'start_time': 'Дата начала не может быть в прошлом (более 5 минут назад).'}
            )
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError(
                {'end_time': 'Дата окончания должна быть позже даты начала.'}
            )

    def _compute_status(self) -> str:
        if self.is_disabled:
            return self.STATUS_FINISHED
        now = timezone.now()
        if now < self.start_time:
            return self.STATUS_CREATED
        if self.start_time <= now <= self.end_time:
            return self.STATUS_STARTED
        return self.STATUS_FINISHED

    def update_status(self, save: bool = True) -> str:
        """
        Пересчитывает статус. Если он изменился — обновляет его в БД.
        Возвращает актуальный статус.
        """
        new_status = self._compute_status()
        if new_status != self.status:
            self.status = new_status
            if save and self.pk:
                type(self).objects.filter(pk=self.pk).update(status=new_status)
        return new_status


class Attempt(models.Model):
    STATUS_OK = 'ok'
    STATUS_FAIL = 'fail'
    STATUS_CHOICES = [
        (STATUS_OK, 'Успешно'),
        (STATUS_FAIL, 'Не успешно'),
    ]

    attempt_time = models.DateTimeField(auto_now_add=True, verbose_name='Дата и время попытки')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, verbose_name='Статус')
    server_response = models.TextField(blank=True, verbose_name='Ответ сервера')
    mailing = models.ForeignKey(
        Mailing,
        on_delete=models.CASCADE,
        related_name='attempts',
        verbose_name='Рассылка',
    )

    class Meta:
        verbose_name = 'Попытка рассылки'
        verbose_name_plural = 'Попытки рассылок'
        ordering = ['-attempt_time']

    def __str__(self):
        return f'Попытка #{self.pk} — {self.get_status_display()}'
