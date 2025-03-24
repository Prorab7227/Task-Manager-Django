from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify

import re, os
from transliterate import translit
from django.utils.timezone import now

from django.urls import reverse

from .choices import STATUS_CHOICE, PRIORITY_CHOICE

# Модель для проекта
class Project(models.Model):
    name = models.CharField(max_length=100, default='', verbose_name='Project Name')
    slug = models.SlugField(max_length=150, blank=True, null=False)
    description = models.TextField(blank=True, null=True)

    client = models.CharField(max_length=100, blank=True, null=True, verbose_name='Client')
    
    owner = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True,related_name='owned_projects',verbose_name='Owner')
    assignee = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True,related_name='assigned_projects',verbose_name='Assignee')
    members = models.ManyToManyField(User, related_name='projects', blank=True, verbose_name='Member User')
    
    deadline = models.DateField(verbose_name='Deadline', blank=True, null=True)
    last_modified = models.DateTimeField(auto_now=True, verbose_name='Last Modified')
    created = models.DateTimeField(auto_now_add=True, verbose_name='Created', blank=True, null=True)

    status = models.CharField(max_length=10,default='new',choices=STATUS_CHOICE,verbose_name='Status')
    priority = models.CharField(max_length=10,default='regular',choices=PRIORITY_CHOICE,verbose_name='Priority')

    # tag = models.CharField( null=True, blank=True, verbose_name='Project tag')
    tag = models.ForeignKey('Tag', on_delete=models.SET_NULL, null=True, related_name='project_tag', verbose_name='Project tag')

    folder = models.ForeignKey('Folder', on_delete=models.CASCADE, null=True, blank=True, related_name='folder')
    subfolder = models.ForeignKey('Folder', on_delete=models.CASCADE, null=True, blank=True, related_name='subfolder')

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Проверяем, требуется ли создание нового slug
        if not self.slug or self.pk is None or self.name != getattr(Project.objects.filter(pk=self.pk).first(), 'name', None):
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
            while Project.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('project_comments', kwargs={'project_slug': self.slug})

    
class ProjectComment(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='comments', verbose_name='Project')
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=True, verbose_name='Author')
    text = models.TextField(blank=True, null=True, verbose_name='Text')
    replied_for = models.ForeignKey('ProjectComment', on_delete=models.CASCADE, null=True, related_name='replies', verbose_name='Replied')
    created = models.DateTimeField(auto_now_add=True, verbose_name='Created')
    read_by = models.ManyToManyField(User, blank=True, related_name='read_project_comments')

    approved = models.BooleanField(default=False, verbose_name='Approved')

    def __str__(self):
        return self.text
    
    def update_read_status(self, user):
        """ Метод для обновления статуса прочитанного пользователем. """
        self.is_read = True
        self.read_by.add(user)
        self.save()

class ProjectCommentFile(models.Model):
    name = models.CharField(max_length=150, default='', verbose_name='File name')
    project_comment = models.ForeignKey('ProjectComment', on_delete=models.CASCADE, related_name='project_comment_files', verbose_name='Project Comment')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='project_comment_file_author', verbose_name='Comment File Author')
    file_path = models.CharField(max_length=512, default='', verbose_name='File Path')
    size = models.BigIntegerField(null=True, blank=True, verbose_name='File size')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='Upload Date')

    class Meta:
        verbose_name = 'Project Comment File'
        verbose_name_plural = 'Project Comment Files'

    def __str__(self):
        return f"{self.name} ({self.project_comment})"

def project_report_file_upload_to(instance, filename):
    # Генерация имени файла с учетом времени и пользователя
    timestamp = now().strftime("%Y-%m-%d_%H-%M-%S")
    username = instance.author.username
    name_of_file = os.path.splitext(filename)[0]
    file_extension = os.path.splitext(filename)[1]  # Получаем расширение файла
    new_filename = f"{name_of_file}_{timestamp}_{username}{file_extension}"

    # Путь для сохранения файла
    if instance.task.project:
        project_slug = instance.task.project.slug
        if instance.task.project.folder:
            folder_slug = instance.task.project.folder.slug
        else:
            folder_slug = "none-folder"
    else:
        project_slug = "none-project"
        folder_slug = "none-folder"

    # Генерация пути для файла
    return os.path.join(
        "media",
        "reports",
        folder_slug,
        project_slug,
        new_filename
    )

class ProjectReport(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='reports', verbose_name='Project')
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=True, verbose_name='Author')
    text = models.TextField(verbose_name='Text')
    link = models.URLField(verbose_name='Link', null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True, verbose_name='Created')

    class Meta:
        verbose_name = 'Project Report'
        verbose_name_plural = 'Project Reports'

    def __str__(self):
        return f"{self.author} {self.created} {self.project.name}"

class ProjectReportFile(models.Model):
    name = models.CharField(max_length=500, null=True, blank=True, verbose_name='File Name')
    project_report = models.ForeignKey('ProjectReport', on_delete=models.CASCADE, related_name='report_files', verbose_name='Project')
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=True, verbose_name='Author')
    file_path = models.CharField(max_length=512, null=True, verbose_name='File Path')
    size = models.BigIntegerField(null=True, blank=True, verbose_name='File size')
    created = models.DateTimeField(auto_now_add=True, verbose_name='Created')

    class Meta:
        verbose_name = 'Project Report File'
        verbose_name_plural = 'Project Report Files'

    def __str__(self):
        return f"{self.author} {self.created} {self.name}"