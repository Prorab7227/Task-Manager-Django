from django.db import models

from django.contrib.auth.models import User

import re
from transliterate import translit
from django.utils.text import slugify

class Tag(models.Model):
    name = models.CharField(max_length=100, verbose_name='Project Name')
    slug = models.SlugField(max_length=150, blank=True)

    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='Author')

    edited_at = models.DateTimeField(auto_now=True, verbose_name='Edited at')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created at')

    def save(self, *args, **kwargs):
        # Проверяем, требуется ли создание нового slug
        if not self.slug or self.pk is None or self.name != getattr(Tag.objects.filter(pk=self.pk).first(), 'name', None):
            # Проверяем, есть ли кириллические символы
            if re.search('[а-яА-Я]', self.name):
                # Если есть, транслитерируем в латиницу
                self.slug = slugify(translit(self.name, reversed=True))
            else:
                # Если кириллицы нет, просто используем slugify
                self.slug = slugify(self.name)
            
            # Убедимся, что слаг уникален
            original_slug = self.slug
            counter = 1
            while Tag.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name