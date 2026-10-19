from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    ListView,
    TemplateView,
    UpdateView, DetailView,
)

from .forms import RecipientForm, MessageForm, MailingForm
from .models import Recipient, Message, Mailing, Attempt
from .services import send_mailing, MailingNotAllowed


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = 'mailing/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 1. Пытаемся получить статистику из кэша Redis (ключ 'home_stats')
        stats = cache.get('home_stats')

        # 2. Если в кэше пусто, считаем статистику и сохраняем
        if stats is None:
            now = timezone.now()
            user = self.request.user

            # Фильтруем данные по владельцу (если пользователь не менеджер)
            if user.groups.filter(name='manager').exists():
                mailings_qs = Mailing.objects.all()
                recipients_qs = Recipient.objects.all()
                attempts_qs = Attempt.objects.all()
            else:
                mailings_qs = Mailing.objects.filter(owner=user)
                recipients_qs = Recipient.objects.filter(owner=user)
                attempts_qs = Attempt.objects.filter(mailing__owner=user)

            stats = {
                'total_mailings': mailings_qs.count(),
                'active_mailings': mailings_qs.filter(
                    start_time__lte=now,
                    end_time__gte=now,
                    is_disabled=False
                ).count(),
                'total_recipients': recipients_qs.count(),
                'total_attempts_ok': attempts_qs.filter(status=Attempt.STATUS_OK).count(),
                'total_attempts_fail': attempts_qs.filter(status=Attempt.STATUS_FAIL).count(),
            }

            # Кэшируем словарь на 5 минут (300 секунд)
            cache.set('home_stats', stats, timeout=300)

        context.update(stats)

        # Получаем последние 5 рассылок для отображения в таблице (их не кэшируем)
        now = timezone.now()
        recent_mailings = Mailing.objects.filter(owner=self.request.user).order_by('-start_time')[
                          :5] if not self.request.user.groups.filter(
            name='manager').exists() else Mailing.objects.all().order_by('-start_time')[:5]

        for m in recent_mailings:
            m.update_status()

        context['recent_mailings'] = recent_mailings

        return context


# Recipient
class RecipientListView(LoginRequiredMixin, ListView):
    model = Recipient
    template_name = 'mailing/recipient_list.html'
    context_object_name = 'recipients'
    paginate_by = 10

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.groups.filter(name='manager').exists():
            return qs
        return qs.filter(owner=self.request.user)


class RecipientCreateView(LoginRequiredMixin, CreateView):
    model = Recipient
    form_class = RecipientForm
    template_name = 'mailing/recipient_form.html'
    success_url = reverse_lazy('mailing:recipient_list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, 'Получатель добавлен.')
        return super().form_valid(form)


class RecipientUpdateView(LoginRequiredMixin, UpdateView):
    model = Recipient
    form_class = RecipientForm
    template_name = 'mailing/recipient_form.html'
    success_url = reverse_lazy('mailing:recipient_list')

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.groups.filter(name='manager').exists():
            return qs
        return qs.filter(owner=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Получатель обновлён.')
        return super().form_valid(form)


class RecipientDeleteView(LoginRequiredMixin, DeleteView):
    model = Recipient
    template_name = 'mailing/recipient_confirm_delete.html'
    success_url = reverse_lazy('mailing:recipient_list')

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.groups.filter(name='manager').exists():
            return qs
        return qs.filter(owner=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Получатель удалён.')
        return super().form_valid(form)


# Message
class MessageListView(LoginRequiredMixin, ListView):
    model = Message
    template_name = 'mailing/message_list.html'
    context_object_name = 'messages'
    paginate_by = 10

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.groups.filter(name='manager').exists():
            return qs
        return qs.filter(owner=self.request.user)


class MessageCreateView(LoginRequiredMixin, CreateView):
    model = Message
    form_class = MessageForm
    template_name = 'mailing/message_form.html'
    success_url = reverse_lazy('mailing:message_list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, 'Сообщение создано.')
        return super().form_valid(form)


class MessageUpdateView(LoginRequiredMixin, UpdateView):
    model = Message
    form_class = MessageForm
    template_name = 'mailing/message_form.html'
    success_url = reverse_lazy('mailing:message_list')

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.groups.filter(name='manager').exists():
            return qs
        return qs.filter(owner=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Сообщение обновлено.')
        return super().form_valid(form)


class MessageDeleteView(LoginRequiredMixin, DeleteView):
    model = Message
    template_name = 'mailing/message_confirm_delete.html'
    success_url = reverse_lazy('mailing:message_list')

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.groups.filter(name='manager').exists():
            return qs
        return qs.filter(owner=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Сообщение удалено.')
        return super().form_valid(form)


# Mailing
class MailingListView(LoginRequiredMixin, ListView):
    model = Mailing
    template_name = 'mailing/mailing_list.html'
    context_object_name = 'mailings'
    paginate_by = 10

    def get_queryset(self):
        qs = super().get_queryset().select_related('message', 'owner')
        if self.request.user.groups.filter(name='manager').exists():
            return qs
        return qs.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # обновим статусы всех рассылок на странице
        for m in ctx['mailings']:
            m.update_status()
        return ctx


class MailingDetailView(LoginRequiredMixin, DetailView):
    model = Mailing
    template_name = 'mailing/mailing_detail.html'
    context_object_name = 'mailing'

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.groups.filter(name='manager').exists():
            return qs
        return qs.filter(owner=self.request.user)

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        obj.update_status()          # ← требование уточнения
        return obj

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['attempts'] = self.object.attempts.order_by('-attempt_time')[:50]
        return ctx


class MailingCreateView(LoginRequiredMixin, CreateView):
    model = Mailing
    form_class = MailingForm
    template_name = 'mailing/mailing_form.html'
    success_url = reverse_lazy('mailing:mailing_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, 'Рассылка создана.')
        return super().form_valid(form)


class MailingUpdateView(LoginRequiredMixin, UpdateView):
    model = Mailing
    form_class = MailingForm
    template_name = 'mailing/mailing_form.html'
    success_url = reverse_lazy('mailing:mailing_list')

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.groups.filter(name='manager').exists():
            return qs
        return qs.filter(owner=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Рассылка обновлена.')
        return super().form_valid(form)


class MailingDeleteView(LoginRequiredMixin, DeleteView):
    model = Mailing
    template_name = 'mailing/mailing_confirm_delete.html'
    success_url = reverse_lazy('mailing:mailing_list')

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.groups.filter(name='manager').exists():
            return qs
        return qs.filter(owner=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Рассылка удалена.')
        return super().form_valid(form)


# Отправка по требованию
class MailingSendView(LoginRequiredMixin, View):
    """POST /mailings/<pk>/send/ — ручной запуск рассылки."""

    def get(self, request, pk):
        return redirect('mailing:mailing_detail', pk=pk)

    def post(self, request, pk):
        mailing = get_object_or_404(
            Mailing.objects.visible_to(request.user), pk=pk
        )
        mailing.update_status()
        try:
            attempts = send_mailing(mailing)
        except MailingNotAllowed as exc:
            messages.error(request, str(exc))
        else:
            ok = sum(1 for a in attempts if a.status == Attempt.STATUS_OK)
            fail = len(attempts) - ok
            messages.success(
                request,
                f'Рассылка отправлена: успешно {ok}, ошибок {fail}.'
            )
        return redirect('mailing:mailing_detail', pk=pk)