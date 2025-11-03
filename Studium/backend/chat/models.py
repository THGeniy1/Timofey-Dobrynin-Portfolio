from django.db import models
from django.utils import timezone
from authentication.models import CustomUser


class Chat(models.Model):
    participants = models.ManyToManyField(CustomUser, related_name='chats')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    user1_read = models.BooleanField(default=True)
    user2_read = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Чат"
        verbose_name_plural = "Чаты"
        ordering = ['-updated_at']

    def __str__(self):
        users = ", ".join([u.username for u in self.participants.all()])
        return f"Чат между: {users}"


class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, null=True, related_name="users_chat")
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, related_name="message_owner")
    message = models.TextField(null=True, blank=True)
    file_path = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    read_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
        ordering = ['created_at']

    def __str__(self):
        text = self.message[:40] if self.message else '[Файл]'
        return f"{self.sender.email}: {text}"

    def mark_delivered(self):
        if not self.delivered_at:
            self.delivered_at = timezone.now()
            self.save(update_fields=['delivered_at'])

    def mark_read(self):
        if not self.read_at:
            self.read_at = timezone.now()
            self.save(update_fields=['read_at'])


class Files(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='message_file', blank=True)
    name = models.TextField()
    size = models.CharField(max_length=50)
    path = models.TextField(max_length=1000, blank=True)

    create_date = models.DateTimeField(auto_now_add=True)


class ChatUnread(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='unread_counts')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='unread_chats')
    unread_count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('chat', 'user')

    def __str__(self):
        return f"{self.user.username} - {self.chat.id}: {self.unread_count} непрочитанных"
