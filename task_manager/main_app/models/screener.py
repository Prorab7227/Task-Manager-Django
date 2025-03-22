import os
from django.utils.timezone import now

from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta


class Screener(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, verbose_name='User')
    work_time = models.DurationField(default=timedelta(), verbose_name="Work Time")
    date = models.DateField(auto_now_add=True, verbose_name='Date')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'date'], name='unique_user_date')
        ]

    def __str__(self):
        return f"{self.user} {self.date}"
    

def screenshot_upload_to(instance, filename):
    # Получаем текущую дату
    current_date = now()
    # Формируем путь с учетом года, месяца, дня и имени пользователя
    return os.path.join(
        'media/screener/screenshots', 
        str(current_date.year),  # год
        str(current_date.month).zfill(2),  # месяц
        str(current_date.day).zfill(2),  # день
        instance.user.username,  # имя пользователя
        filename
    )

from django.utils.html import mark_safe

class Screenshot(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='User')
    screener = models.ForeignKey('Screener', on_delete=models.CASCADE, verbose_name='Screenshot screener')
    image = models.FileField(upload_to=screenshot_upload_to, default='', verbose_name='Image Path')
    created = models.DateTimeField(null=True, blank=True, verbose_name='Created')

    def __str__(self):
        return f"{self.user} {self.created}"
    
    def image_tag(self):
        if self.image:
            # Пример с использованием простого модального окна
            return mark_safe(f'''
                <a href="{self.image.url}" target="_blank">
                    <img src="{self.image.url}" width="120" height="60" style="object-fit: cover;" />
                </a>
            ''')
        return "No image"

    image_tag.short_description = 'Image'  # Название столбца в админке