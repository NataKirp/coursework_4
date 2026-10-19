from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Статусы активации email
    path('activation-sent/', views.ActivationSentView.as_view(), name='activation_sent'),
    path('activation-success/', views.ActivationSuccessView.as_view(), name='activation_success'),
    path('activation-failed/', views.ActivationFailedView.as_view(), name='activation_failed'),

    # Сброс пароля
    path('password-reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', views.CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset/complete/', views.CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # Обработчик ссылки из письма
    path('activate/<uidb64>/<token>/', views.activate_view, name='activate'),
]
