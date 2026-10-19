from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    ListView,
    TemplateView,
    UpdateView,
)

from .forms import RecipientForm, MessageForm
from .models import Recipient, Message


class HomeView(TemplateView):
    template_name = 'mailing/home.html'


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