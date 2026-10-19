from django.contrib.auth import logout
from django.contrib.auth.views import (
    LoginView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.shortcuts import redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, TemplateView
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator

from .forms import (
    CustomAuthenticationForm,
    CustomPasswordResetForm,
    CustomSetPasswordForm,
    CustomUserCreationForm,
)


class RegisterView(CreateView):
    model = User
    form_class = CustomUserCreationForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('users:login')

    def form_valid(self, form):
        # Сохраняем пользователя, но делаем его неактивным до подтверждения email
        user = form.save(commit=False)
        user.is_active = False
        user.save()

        # Генерируем токен и uid для ссылки активации
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        # Ссылка вида: http://localhost:8000/users/activate/<uid>/<token>/
        activation_link = self.request.build_absolute_uri(
            f'/users/activate/{uid}/{token}/'
        )

        # Отправляем письмо (оно появится в консоли)
        send_mail(
            subject='Подтверждение регистрации',
            message=f'Здравствуйте, {user.username}!\n\n'
                    f'Для подтверждения регистрации перейдите по ссылке:\n'
                    f'{activation_link}\n\n'
                    f'Если вы не регистрировались, просто проигнорируйте это письмо.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        self.request.session['activation_email'] = user.email
        return redirect('users:activation_sent')


class CustomLoginView(LoginView):
    template_name = 'users/login.html'
    authentication_form = CustomAuthenticationForm
    redirect_authenticated_user = True


def logout_view(request):
    logout(request)
    return redirect('users:login')


class CustomPasswordResetView(PasswordResetView):
    template_name = 'users/password_reset_form.html'
    email_template_name = 'users/password_reset_email.html'
    form_class = CustomPasswordResetForm
    success_url = reverse_lazy('users:password_reset_done')


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'users/password_reset_done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'users/password_reset_confirm.html'
    form_class = CustomSetPasswordForm
    success_url = reverse_lazy('users:password_reset_complete')


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'users/password_reset_complete.html'


class ActivationSentView(TemplateView):
    template_name = 'users/activation_sent.html'


class ActivationSuccessView(TemplateView):
    template_name = 'users/activation_success.html'


class ActivationFailedView(TemplateView):
    template_name = 'users/activation_failed.html'


def activate_view(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return redirect(reverse('users:activation_success'))
    else:
        return redirect(reverse('users:activation_failed'))
