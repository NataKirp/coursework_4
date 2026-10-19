from django import forms

from .models import Recipient, Message, Mailing


class RecipientForm(forms.ModelForm):
    class Meta:
        model = Recipient
        fields = ['email', 'full_name', 'comment']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'email': 'Email',
            'full_name': 'Ф. И. О.',
            'comment': 'Комментарий',
        }


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['subject', 'body']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'body': forms.Textarea(attrs={'class': 'form-control', 'rows': 8}),
        }
        labels = {
            'subject': 'Тема письма',
            'body': 'Тело письма',
        }


class MailingForm(forms.ModelForm):
    class Meta:
        model = Mailing
        fields = ['start_time', 'end_time', 'message', 'recipients']
        widgets = {
            'start_time': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
            'end_time': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
            'message': forms.Select(attrs={'class': 'form-select'}),
            'recipients': forms.CheckboxSelectMultiple(attrs={'class': 'list-unstyled'}),
        }
        labels = {
            'start_time': 'Дата и время начала отправки',
            'end_time': 'Дата и время окончания отправки',
            'message': 'Сообщение',
            'recipients': 'Получатели',
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['start_time'].input_formats = ['%Y-%m-%dT%H:%M']
        self.fields['end_time'].input_formats = ['%Y-%m-%dT%H:%M']

        # Улучшаем отображение каждого чекбокса (добавляем класс form-check-input)
        self.fields['recipients'].widget.attrs.update({'class': 'form-check-input'})

        if user and not user.is_manager:
            from django.db.models import Q
            self.fields['message'].queryset = self.fields['message'].queryset.filter(
                Q(owner=user) | Q(owner__isnull=True)
            )
            # Принудительно меняем queryset, чтобы выводить Email в удобном виде
            self.fields['recipients'].queryset = self.fields['recipients'].queryset.filter(
                Q(owner=user) | Q(owner__isnull=True)
            )
