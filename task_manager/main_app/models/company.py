from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify

import re
from transliterate import translit

def upload_to_func(instance):
    return f'media/company/{instance.name}/logo'

class Company(models.Model):    
    name = models.CharField(max_length=100, verbose_name='Name')
    slug = models.SlugField(max_length=150, null=False, blank=True, verbose_name='Slug')
    description = models.TextField(blank=True, null=True, verbose_name='Description')

    created = models.DateTimeField(auto_now_add=True, verbose_name='Created')
    logo = models.ImageField(upload_to=upload_to_func, null=True, blank=True, verbose_name='Logo')

    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_companies',
        verbose_name='Owner'
    )

    members = models.ManyToManyField(User, related_name='members', blank=True, verbose_name='Members')

    folders = models.ManyToManyField('Folder', related_name='folders', blank=True, verbose_name='Folders')
    projects = models.ManyToManyField('Project', related_name='projects', blank=True, verbose_name='Projects')
    tasks = models.ManyToManyField('Task', related_name='tasks', blank=True, verbose_name='Tasks')

    class Meta:
        verbose_name = 'Company'
        verbose_name_plural = 'Companies'

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Проверяем, требуется ли создание нового slug
        if not self.slug or self.pk is None or self.name != getattr(Company.objects.filter(pk=self.pk).first(), 'name', None):
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
            while Company.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1

        super().save(*args, **kwargs)