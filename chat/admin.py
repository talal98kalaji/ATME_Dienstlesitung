from django.contrib import admin
from .models import Conversation, Participant, Message


class ParticipantInline(admin.TabularInline):
    model = Participant
    extra = 1


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation_type', 'name', 'created_by', 'created_at')
    list_filter = ('conversation_type',)
    inlines = [ParticipantInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'sender', 'created_at')
    search_fields = ('content',)
    list_filter = ('created_at',)
