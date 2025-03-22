from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify

import re
from transliterate import translit

from .choices import STATUS_CHOICE, PRIORITY_CHOICE

# Модель для папки
class Folder(models.Model):
    name = models.CharField(max_length=100, default='', verbose_name='Folder Name')
    slug = models.SlugField(max_length=150, blank=True, null=False)
    description = models.TextField(blank=True, null=True)

    client = models.CharField(max_length=100, blank=True, null=True, verbose_name='Client')

    last_modified = models.DateTimeField(auto_now=True, verbose_name='Last Modified')
    created = models.DateTimeField(auto_now_add=True, verbose_name='Created', blank=True, null=True)

    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='owned_folders', verbose_name='Owner')
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='Assigned_folders', verbose_name='Assignee')
    members = models.ManyToManyField(User, related_name='folders', blank=True, verbose_name='Member User')

    status = models.CharField(max_length=10, default='new', choices=STATUS_CHOICE, verbose_name='Status')
    priority = models.CharField(max_length=10, default='regular', choices=PRIORITY_CHOICE, verbose_name='Priority')

    parent_folder = models.ForeignKey('Folder', on_delete=models.CASCADE, null=True, related_name='subfolders', verbose_name='Parent Folder')

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Проверяем, требуется ли создание нового slug
        if not self.slug or self.pk is None or self.name != getattr(Folder.objects.filter(pk=self.pk).first(), 'name', None):
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
            while Folder.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1

        super().save(*args, **kwargs)

    def get_full_path(self):
        """ Возвращает полный путь папки в иерархии """
        path = []
        folder = self
        while folder:
            path.append(folder.name)
            folder = folder.parent
        return " / ".join(reversed(path))