from django.contrib.auth.mixins import UserPassesTestMixin


class ManagerRequiredMixin(UserPassesTestMixin):
    """Доступ только для менеджеров."""
    def test_func(self):
        return self.request.user.is_manager


class OwnerOrManagerMixin:
    """
    Миксин для get_queryset: менеджеры видят всё, пользователи — только своё.
    Использование: class MyView(LoginRequiredMixin, OwnerOrManagerMixin, ListView)
    """
    owner_field = 'owner'

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_manager:
            return qs
        return qs.filter(**{self.owner_field: user})