from itertools import chain
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required

from ..models import ProjectComment, TaskComment, Folder, Project, Task, Action, User
from ..forms import TaskCommentForm, ProjectCommentForm

from django.db.models import Q

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from django.db import transaction
from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver
from django.core.serializers import serialize


import threading
# Создаем локальный объект для хранения информации о текущем пользователе
_thread_locals = threading.local()
def set_current_user(user):
    _thread_locals.user = user

def get_current_user():
    return getattr(_thread_locals, 'user', None)

def serialize_instance(instance):
    """Функция для сериализации всех полей объекта в строку."""
    # Возвращаем первый элемент из сериализованного списка, а не весь список
    return serialize('json', [instance])  # Возвращаем строку, а не список

def save_action(instance, action_type, context_before=None, context_after=None):
    """Сохраняем экшен после создания или обновления объекта."""
    user = get_current_user()
    Action.objects.create(
        author=user,
        task=instance if isinstance(instance, Task) else None,
        project=instance if isinstance(instance, Project) else None,
        folder=instance if isinstance(instance, Folder) else None,
        action_type=action_type,
        context_before=context_before,  # сохраняем контекст до
        context_after=context_after  # сохраняем контекст после
    )

@receiver(pre_save, sender=TaskComment)
@receiver(pre_save, sender=ProjectComment)
def pre_save_action(sender, instance, **kwargs):
    """Обработка объекта перед его сохранением (получаем старую версию объекта)."""
    if not instance.pk:  # Если это новый объект, пропускаем обработку
        return
    
    # Получаем старую версию объекта перед изменением
    instance_before_update = sender.objects.get(pk=instance.pk)
    context_before = serialize_instance(instance_before_update)
    
    # Сохраняем контекст до обновления
    instance._context_before = context_before

@receiver(post_save, sender=TaskComment)
@receiver(post_save, sender=ProjectComment)
def post_save_action(sender, instance, created, **kwargs):
    """Обработка объекта после его сохранения (сериализация нового состояния)."""
    action_type = 'create' if created else 'update'
    
    # Сериализуем объект после изменения
    context_after = serialize_instance(instance)
    
    # Получаем контекст до изменения из pre_save
    context_before = getattr(instance, '_context_before', None)
    
    # Сохраняем экшен
    save_action(instance, action_type, context_before, context_after)

@receiver(pre_delete, sender=TaskComment)
@receiver(pre_delete, sender=ProjectComment)
def delete_action(sender, instance, **kwargs):
    try:        
        with transaction.atomic():
            context_before = serialize_instance(instance)
            
            user = get_current_user()

            action = Action.objects.create(
                author=user,
                task=instance if isinstance(instance, Task) else None,
                project=instance if isinstance(instance, Project) else None,
                folder=instance if isinstance(instance, Folder) else None,
                action_type='delete',
                context_before=context_before,  
                context_after=None 
            )
    except Exception as e:
        print(f"Ошибка при создании Action: {e}")
        raise  # Повторное выбрасывание исключения для диагностики


import re
def add_table_classes(text):
    if not text:
        return text

    # Регулярное выражение для поиска всех тегов table
    table_pattern = re.compile(r'<table(.*?)>(.*?)<\/table>', re.DOTALL)

    # Добавление классов к таблицам
    updated_text = re.sub(table_pattern, r'<table class="table table-bordered border-top border-bottom"\1>\2</table>', text)

    return updated_text

@login_required
def all_comments(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            project_comments = ProjectComment.objects.filter(read_by__isnull=True, approved=True).select_related('author', 'project').distinct()
            task_comments = TaskComment.objects.filter(read_by__isnull=True, approved=True).select_related('author', 'task').distinct()
        else:
            project_comments = ProjectComment.objects.filter(
                Q(project__assignee=request.user) |
                Q(project__members=request.user)
            ).filter(
                ~Q(read_by=request.user), approved=True
            ).select_related('author', 'project').distinct()

            task_comments = TaskComment.objects.filter(
                Q(task__assignee=request.user) |
                Q(task__members=request.user)
            ).filter(
                ~Q(read_by=request.user), approved=True
            ).select_related('author', 'task').distinct()

    project_comments = list(project_comments)
    for comment in project_comments:
        comment.type = 'project'

    task_comments = list(task_comments)
    for comment in task_comments:
        comment.type = 'task'

    all_comments = chain(project_comments, task_comments)
    sorted_comments = sorted(all_comments, key=lambda comment: comment.created, reverse=True)

    for comment in sorted_comments:
        comment.text = add_table_classes(comment.text)

    context = {
        'comments': sorted_comments
    }
    return render(request, 'main_app/comments/all_comments.html', context)

from django.http import JsonResponse
@login_required
def mark_all_comments_as_read(request):
    if request.method == 'POST':
        user = request.user

        # Отмечаем все комментарии как прочитанные
        for comment in ProjectComment.objects.exclude(read_by=user):
            comment.read_by.add(user)

        for comment in TaskComment.objects.exclude(read_by=user):
            comment.read_by.add(user)

        # Редиректим на предыдущую страницу или на главную
        return redirect(request.META.get('HTTP_REFERER', reverse('index')))

    return JsonResponse({'error': 'Invalid request'}, status=400)

def mark_comment_as_read(request, comment_type, comment_id):
    if comment_type == 'project':
        comment = get_object_or_404(ProjectComment, id=comment_id)
    elif comment_type == 'task':
        comment = get_object_or_404(TaskComment, id=comment_id)
    else:
        return JsonResponse({'error': 'Invalid comment type'}, status=400)

    if request.method == 'POST':
        comment.read_by.add(request.user)  # Добавление текущего пользователя
        comment.save()
        if comment_type == 'project':
            redirect_url = comment.project.get_absolute_url() if comment.project else '/'
        elif comment_type == 'task':
            redirect_url = comment.task.get_absolute_url() if comment.task else '/'
        return redirect(redirect_url)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


def moderate_comments(request):

    if request.user.is_authenticated:
        if request.user.is_superuser:
            project_comments = ProjectComment.objects.filter(read_by__isnull=True, approved=False).select_related('author', 'project')
            task_comments = TaskComment.objects.filter(read_by__isnull=True, approved=False).select_related('author', 'task')
        else:
            return render(request, 'main_app/errors/access_denied.html')

    project_comments = list(project_comments)
    for comment in project_comments:
        comment.form = ProjectCommentForm(instance=comment)
        comment.type = 'project'

    task_comments = list(task_comments)
    for comment in task_comments:
        comment.form = TaskCommentForm(instance=comment)
        comment.type = 'task'

    all_comments = chain(project_comments, task_comments)
    sorted_comments = sorted(all_comments, key=lambda comment: comment.created, reverse=True)

    for comment in sorted_comments:
        comment.text = add_table_classes(comment.text)

    context = {
        'comments': sorted_comments
    }

    return render(request, 'main_app/comments/moderate_comments.html', context)



from django.contrib import messages
def approve_comment(request, comment_id, comment_type):
    if comment_type == 'task':
        comment = get_object_or_404(TaskComment, id=comment_id)
    else:
        comment = get_object_or_404(ProjectComment, id=comment_id)
    
    comment.approved = True
    comment.save()
    messages.success(request, "Comment approved.")
    return redirect('moderate_comments')


def edit_comment(request, comment_id, comment_type):
    if comment_type == 'task':
        comment = get_object_or_404(TaskComment, id=comment_id)
        CommentFormClass = TaskCommentForm
    elif comment_type == 'project':
        comment = get_object_or_404(ProjectComment, id=comment_id)
        CommentFormClass = ProjectCommentForm
    else:
        return redirect('moderate_comments')  # Перенаправление в случае неверного типа комментария

    if request.method == 'POST':
        comment_form = CommentFormClass(request.POST, instance=comment)  # Передаём данные формы
        if comment_form.is_valid():
            set_current_user(request.user)  # Устанавливаем текущего пользователя
            comment_form.save()
            return redirect('moderate_comments')  # ВАЖНО: возвращаем redirect

    else:
        comment_form = CommentFormClass(instance=comment)

    context = {
        'comment': comment,
        'comment_form': comment_form
    }

    return render(request, 'main_app/comments/edit_comment.html', context)
    

def delete_comment(request, comment_id, comment_type):
    if comment_type == 'task':
        comment = get_object_or_404(TaskComment, id=comment_id)
    else:
        comment = get_object_or_404(ProjectComment, id=comment_id)
    
    comment.delete()
    messages.success(request, "Comment deleted.")
    return redirect('moderate_comments')