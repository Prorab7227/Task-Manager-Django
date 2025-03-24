from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
import re
from transliterate import translit
from django.urls import reverse
import os
from django.utils.timezone import now
from .choices import STATUS_CHOICE, PRIORITY_CHOICE

class Task(models.Model):
    title = models.CharField(max_length=100, default='', verbose_name='Task title')
    slug = models.SlugField(max_length=150, blank=True, null=False)
    description = models.TextField(blank=True, null=True, verbose_name='Description')
    
    deadline = models.DateField(verbose_name='Deadline', blank=True, null=True)
    last_modified = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name='Last Modified')
    created = models.DateTimeField(auto_now_add=True, blank=True, null=True, verbose_name='Created')

    owner = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True,related_name='owned_tasks',verbose_name='Owner')
    assignee = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True,related_name='assigned_tasks',verbose_name='Assignee')
    members = models.ManyToManyField(User, related_name='tasks', blank=True, verbose_name='Member User')

    status = models.CharField(max_length=20,default='open',
        choices=[
            ('pause', 'Pause'),
            ('new', 'New'),
            ('working', 'Working'),
            ('done', 'Done'),
            ('closed', 'Closed'),
        ],
        blank=True, null=True
    )
    priority = models.CharField(max_length=10,default='regular',choices=PRIORITY_CHOICE,verbose_name='Priority',blank=True, null=True)

    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='tasks', null=True, blank=True)

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Проверяем, требуется ли создание нового slug
        if not self.slug or self.pk is None or self.title != getattr(Task.objects.filter(pk=self.pk).first(), 'title', None):
            # Проверяем, есть ли кириллические символы
            if re.search('[а-яА-Я]', self.title):
                # Если есть, транслитерируем в латиницу
                self.slug = slugify(translit(self.title, reversed=True))
            else:
                # Если кириллицы нет, просто используем slugify
                self.slug = slugify(self.title)
            
            # Убедимся, что слаг уникален
            original_slug = self.slug
            counter = 1
            while Task.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('task_comments', kwargs={'task_slug': self.slug})
    
class TaskComment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments', verbose_name='Task')
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=True, verbose_name='Author')
    text = models.TextField(blank=True, null=True, verbose_name='Text')
    replied_for = models.ForeignKey('TaskComment', on_delete=models.CASCADE, null=True, blank=True, related_name='replies', verbose_name='Replied')
    created = models.DateTimeField(auto_now_add=True, verbose_name='Created')
    read_by = models.ManyToManyField(User, blank=True, related_name='read_task_comments')

    approved = models.BooleanField(default=False, verbose_name='Approved')

    def __str__(self):
        return self.text
    
    def update_read_status(self, user):
        """ Метод для обновления статуса прочитанного пользователем. """
        self.is_read = True
        self.read_by.add(user)
        self.save()

class TaskCommentFile(models.Model):
    name = models.CharField(max_length=150, default='', verbose_name='File name')
    task_comment = models.ForeignKey('TaskComment', on_delete=models.CASCADE, related_name='task_comment_files', verbose_name='Task Comment')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comment_file_author', verbose_name='Comment File Author')
    file_path = models.CharField(max_length=512, default='', verbose_name='File Path')
    size = models.BigIntegerField(null=True, blank=True, verbose_name='File size')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='Upload Date')

    class Meta:
        verbose_name = 'Task Comment File'
        verbose_name_plural = 'Task Comment Files'

    def __str__(self):
        return f"{self.name} ({self.task_comment})"

def task_file_upload_to(instance, filename):
    # Генерация имени файла с учетом времени и пользователя
    timestamp = now().strftime("%Y-%m-%d_%H-%M-%S")
    username = instance.author.username
    name_of_file = os.path.splitext(filename)[0]
    file_extension = os.path.splitext(filename)[1]  # Получаем расширение файла
    new_filename = f"{name_of_file}_{timestamp}_{username}{file_extension}"

    # Путь для сохранения файла
    task_slug = instance.task.slug
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
        "files",
        folder_slug,
        project_slug,
        task_slug,
        new_filename
    )

class TaskFile(models.Model):
    name = models.CharField(max_length=150, default='', verbose_name='File name')
    task = models.ForeignKey('Task', on_delete=models.CASCADE, related_name='task_files', verbose_name='Task', null=True, blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_files', verbose_name='Author')
    file_path = models.CharField(max_length=512, default='', verbose_name='File Path')
    size = models.BigIntegerField(null=True, blank=True, verbose_name='File size')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='Upload Date')

    class Meta:
        verbose_name = 'Task File'
        verbose_name_plural = 'Task Files'

    def __str__(self):
        return f"{self.name} ({self.task})"