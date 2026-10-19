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
            'recipients': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 8}),
        }
        labels = {
            'start_time': 'Дата и время начала отправки',
            'end_time': 'Дата и время окончания отправки',
            'message': 'Сообщение',
            'recipients': 'Получатели',
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        # datetime-local требует input_formats
        self.fields['start_time'].input_formats = ['%Y-%m-%dT%H:%M']
        self.fields['end_time'].input_formats = ['%Y-%m-%dT%H:%M']
        # показываем только «свои» message и recipients
        if user and not user.groups.filter(name='manager').exists():
            self.fields['message'].queryset = self.fields['message'].queryset.filter(owner=user)
            self.fields['recipients'].queryset = self.fields['recipients'].queryset.filter(owner=user)
