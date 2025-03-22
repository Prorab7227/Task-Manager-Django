from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from ..models import User, Task, Project, Folder, TaskFile, Action
from ..forms import FolderForm

from django.http import HttpResponseRedirect

from django.contrib import messages
from django.urls import reverse

from django.db.models import Q

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

@receiver(pre_save, sender=Folder)
def pre_save_action(sender, instance, **kwargs):
    """Обработка объекта перед его сохранением (получаем старую версию объекта)."""
    if not instance.pk:  # Если это новый объект, пропускаем обработку
        return
    
    # Получаем старую версию объекта перед изменением
    instance_before_update = sender.objects.get(pk=instance.pk)
    context_before = serialize_instance(instance_before_update)
    
    # Сохраняем контекст до обновления
    instance._context_before = context_before

@receiver(post_save, sender=Folder)
def post_save_action(sender, instance, created, **kwargs):
    """Обработка объекта после его сохранения (сериализация нового состояния)."""
    action_type = 'create' if created else 'update'
    
    # Сериализуем объект после изменения
    context_after = serialize_instance(instance)
    
    # Получаем контекст до изменения из pre_save
    context_before = getattr(instance, '_context_before', None)
    
    # Сохраняем экшен
    save_action(instance, action_type, context_before, context_after)

@receiver(pre_delete, sender=Folder)
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




def folder_update_priority(request, id):
    set_current_user(request.user)
    folder = get_object_or_404(Folder, id=id)
    
    if request.method == 'POST':
        new_priority = request.POST.get('priority')
        if new_priority:
            folder.priority = new_priority
            folder.save()
    
    # Перенаправляем на ту же страницу
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

def folder_update_status(request, id):
    set_current_user(request.user)
    folder = get_object_or_404(Folder, id=id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status:
            folder.status = new_status
            folder.save()
    
    # Перенаправляем на ту же страницу
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def folder_list(request):
    if request.user.is_superuser:
        folders = Folder.objects.exclude(
            Q(status='archive')|
            Q(parent_folder__isnull=False)
        ).order_by("-id")
    else:
        folders = Folder.objects.filter(
            Q(owner=request.user) | 
            Q(assignee=request.user) |
            Q(members=request.user)
        ).exclude(
            Q(status='archive')|
            Q(parent_folder__isnull=False)
        ).distinct().order_by("-id")

    return render(request, 'main_app/folder/folder_list.html', {'folders': folders})

@login_required
def folder_list_archive(request):
    if request.user.is_superuser:
        folders = Folder.objects.filter(status='archive').order_by("-id")
    else:
        folders = Folder.objects.filter(
            Q(owner=request.user) | 
            Q(members__in=[request.user]) |
            Q(owner__is_superuser=True, members=request.user) |
            Q(owner__is_superuser=True, owner=request.user) |
            Q(assignee=request.user)
        ).filter(status='archive').distinct().order_by("-id")

    return render(request, 'main_app/folder/folder_list_archive.html', {'folders': folders})

@login_required
def create_folder(request):
    set_current_user(request.user)
    parent_folder_slug = request.GET.get('parentfolder')
    parent_folder = None

    if request.method == 'POST':
        form = FolderForm(request.POST)
        if form.is_valid():
            folder = form.save(commit=False)
            folder.owner = request.user

            if parent_folder_slug:
                parent_folder = get_object_or_404(Folder, slug=parent_folder_slug)
                folder.parent_folder = parent_folder

            folder.save()
            form.save_m2m()

            return redirect('folder_projects', folder_slug=folder.slug)
        else:
            print(form.errors)
            return render(request, 'main_app/folder/create_folder.html', {'form': form, 'users': User.objects.all()})
    else:
        if parent_folder_slug:
            parent_folder = get_object_or_404(Folder, slug=parent_folder_slug)

        form = FolderForm(initial={'parent_folder':parent_folder})

        return render(request, 'main_app/folder/create_folder.html', {'form': form, 'users': User.objects.all()})

@login_required
def folder_detail(request, folder_slug):
    folder = get_object_or_404(Folder, slug=folder_slug)
    projects = Project.objects.filter(folder_id=folder.id)

    # Проверка: текущий пользователь назначен на папку
    if not request.user.is_superuser:
        if request.user not in folder.members.all() and request.user != folder.assignee and request.user != folder.owner:
            return render(request, 'main_app/errors/access_denied.html')

    return render(request, 'main_app/folder/folder_detail.html', {
        'folder': folder,
        'projects': projects,
    })

@login_required
def delete_folder(request, folder_slug):
    set_current_user(request.user)
    folder = get_object_or_404(Folder, slug=folder_slug)

    if request.method == "POST":
        folder.delete()
        messages.success(request, "The folder was deleted successfully.")
        return redirect(reverse('folder_list'))
    return redirect(reverse('folder_list', args=[folder_slug]))


@login_required
def edit_folder(request, folder_slug):
    set_current_user(request.user)
    folder = get_object_or_404(Folder, slug=folder_slug)
    users_all = User.objects.all()

    folder_form = FolderForm(request.POST or None, instance=folder)

    if request.method == 'POST' and folder_form.is_valid():
        folder = folder_form.save(commit=False)

        assigned_usernames = request.POST.getlist('members')
        members = User.objects.filter(id__in=assigned_usernames)
        folder.members.set(members)

        assignee_id = request.POST.get('assignee')
        if assignee_id:
            folder.assignee = User.objects.get(id=assignee_id)
        else:
            folder.assignee = None

        folder.save()

        return redirect('folder_detail', folder_slug=folder.slug)

    return render(request, 'main_app/folder/edit_folder.html', {
        'folder': folder,
        'folder_form': folder_form,
        'users_all': users_all,
    })

from itertools import chain
@login_required
def folder_projects(request, folder_slug):
    folder = get_object_or_404(Folder, slug=folder_slug)
    sorted_list = 0

    if folder.parent_folder:
        projects_sorted = Project.objects.filter(subfolder=folder)
        for item in projects_sorted:
            item.type='project'

    else:
        sub_folders = folder.subfolders.exclude(status__in=['closed', 'archive'])
        for item in sub_folders:
            item.type='subfolder'

        projects = Project.objects.filter(folder=folder, subfolder__isnull=True).exclude(status__in=['closed', 'archive'])
        for item in projects:
            item.type='project'

        combined_list = chain(sub_folders, projects)
        projects_sorted = sorted(combined_list, key=lambda obj: obj.created)

    if not request.user.is_superuser:
        if request.user not in folder.members.all() and request.user != folder.assignee and request.user != folder.owner:
            return render(request, 'main_app/errors/access_denied.html')

    context = {
        'folder': folder,
        'projects': projects_sorted,
    }

    return render(request, 'main_app/folder/folder_projects.html', context)

@login_required
def folder_projects_files(request, folder_slug):
    folder = get_object_or_404(Folder, slug=folder_slug)

    # Получаем все проекты, относящиеся к данной папке
    projects_in_folder = Project.objects.filter(folder=folder)

    # Получаем все задачи, которые принадлежат этим проектам
    tasks_in_projects = Task.objects.filter(project__in=projects_in_folder)

    # Фильтруем файлы задач, которые принадлежат этим задачам
    tasks_files = TaskFile.objects.filter(task__in=tasks_in_projects).order_by("-id")

    # Проверка: текущий пользователь назначен на папку
    if not request.user.is_superuser:
        if request.user not in folder.members.all() and request.user != folder.assignee and request.user != folder.owner:
            return render(request, 'main_app/errors/access_denied.html')

    return render(request, 'main_app/folder/folder_projects_files.html', {
        'folder': folder,
        'tasks_files': tasks_files,
    })