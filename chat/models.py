from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Conversation(models.Model):
    GROUP = 'GROUP'
    DIRECT = 'DIRECT'
    TYPE_CHOICES = [
        (GROUP, _('Group')),
        (DIRECT, _('Direct')),
    ]

    conversation_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default=GROUP)
    name = models.CharField(max_length=255, blank=True, verbose_name=_('Group Name'))
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_conversations'
    )
    participants = models.ManyToManyField(User, through='Participant', related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = _('Conversation')
        verbose_name_plural = _('Conversations')

    def __str__(self):
        if self.conversation_type == self.GROUP:
            return f"Group: {self.name or self.pk}"
        return f"Direct #{self.pk}"


class Participant(models.Model):
    MEMBER = 'MEMBER'
    ADMIN = 'ADMIN'
    ROLE_CHOICES = [
        (MEMBER, _('Member')),
        (ADMIN, _('Admin')),
    ]

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_memberships')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('conversation', 'user')
        verbose_name = _('Participant')
        verbose_name_plural = _('Participants')

    def __str__(self):
        return f"{self.user.username} in {self.conversation}"


def message_image_path(instance, filename):
    return f"chat/{instance.conversation_id}/{filename}"


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sent_messages')
    content = models.TextField(blank=True, verbose_name=_('Message Content'))
    image = models.ImageField(upload_to=message_image_path, null=True, blank=True, verbose_name=_('Image'))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = _('Message')
        verbose_name_plural = _('Messages')

    def __str__(self):
        return f"Message #{self.pk} by {self.sender}"
