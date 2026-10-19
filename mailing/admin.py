from django.contrib import admin

from .models import Attempt, Mailing, Message, Recipient


@admin.register(Recipient)
class RecipientAdmin(admin.ModelAdmin):
    list_display = ('email', 'full_name', 'owner')
    search_fields = ('email', 'full_name')
    list_filter = ('owner',)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'owner')
    search_fields = ('subject', 'body')


@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    list_display = ('id', 'message', 'start_time', 'end_time', 'status', 'owner')
    list_filter = ('status', 'is_disabled')
    filter_horizontal = ('recipients',)
    readonly_fields = ('status',)


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ('id', 'mailing', 'attempt_time', 'status')
    list_filter = ('status',)
    readonly_fields = ('attempt_time',)
