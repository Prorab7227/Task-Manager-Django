from datetime import datetime
import os

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from ..models import User, Task, Project, Folder, ProjectComment, ProjectCommentFile, TaskFile, ProjectReport, ProjectReportFile, Action
from ..forms import ProjectForm, ProjectCommentForm, ProjectReportForm

from django.http import HttpResponseForbidden
from django.http import HttpResponseRedirect

from django.contrib import messages
from django.urls import reverse

from django.db.models import Q
from itertools import chain

import json

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

@receiver(pre_save, sender=Project)
def pre_save_action(sender, instance, **kwargs):
    """Обработка объекта перед его сохранением (получаем старую версию объекта)."""
    if not instance.pk:  # Если это новый объект, пропускаем обработку
        return
    
    # Получаем старую версию объекта перед изменением
    instance_before_update = sender.objects.get(pk=instance.pk)
    context_before = serialize_instance(instance_before_update)
    
    # Сохраняем контекст до обновления
    instance._context_before = context_before

@receiver(post_save, sender=Project)
def post_save_action(sender, instance, created, **kwargs):
    """Обработка объекта после его сохранения (сериализация нового состояния)."""
    action_type = 'create' if created else 'update'
    
    # Сериализуем объект после изменения
    context_after = serialize_instance(instance)
    
    # Получаем контекст до изменения из pre_save
    context_before = getattr(instance, '_context_before', None)
    
    # Сохраняем экшен
    save_action(instance, action_type, context_before, context_after)

@receiver(pre_delete, sender=Project)
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


def project_update_priority(request, id):
    set_current_user(request.user)
    project = get_object_or_404(Project, id=id)
    
    if request.method == 'POST':
        new_priority = request.POST.get('priority')
        if new_priority:
            project.priority = new_priority
            project.save()
    
    # Перенаправляем на ту же страницу
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

def project_update_status(request, id):
    set_current_user(request.user)
    project = get_object_or_404(Project, id=id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status:
            project.status = new_status
            project.save()
    
    # Перенаправляем на ту же страницу
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def project_list_all(request):
    request_user = request.user
    is_admin = request_user.is_superuser
    
    if is_admin:
        projects = Project.objects.filter(
            Q(subfolder__isnull=True)
        ).distinct().order_by("id")

        sub_folders = Folder.objects.filter(
            Q(parent_folder__isnull=False)
        ).distinct().order_by("id")
    else:
        user_perm = Q(owner=request_user) | Q(members__in=[request_user]) | Q(assignee=request_user)

        sub_folders = Folder.objects.filter(
            user_perm &
            Q(parent_folder__isnull=False)
        ).distinct().order_by("id")

        projects = Project.objects.filter(
            user_perm
        ).order_by("id")
    
    for item in sub_folders:
        item.type = 'subfolder'
    
    for item in projects:
        item.type = 'project'
    
    combined_list = chain(sub_folders, projects)
    
    return render(request, 'main_app/project/project_list_all.html', {'projects': combined_list})

@login_required
def project_list(request):
    user = request.user
    is_admin = user.is_superuser
    
    if is_admin:
        projects = Project.objects.filter(
            ~Q(status__in=['archive', 'closed']) &
            ~Q(folder__status='archive') &
            Q(subfolder__isnull=True)
        ).distinct().order_by("id")

        sub_folders = Folder.objects.filter(
            Q(parent_folder__isnull=False) &
            ~Q(parent_folder__status='archive') &
            ~Q(status__in=['archive', 'closed'])
        ).distinct().order_by("id")
    else:
        user_perm = Q(owner=user) | Q(members=user) | Q(assignee=user)

        projects = Project.objects.filter(
            user_perm &
            ~Q(status__in=['archive', 'closed']) &
            ~Q(folder__status='archive') &
            Q(subfolder__isnull=True) 
        ).distinct().order_by("id")

        sub_folders = Folder.objects.filter(
            user_perm &
            ~Q(status__in=['archive', 'closed']) &
            ~Q(parent_folder__status='archive') &
            Q(parent_folder__isnull=False)
        ).distinct().order_by("id")
    
    for item in sub_folders:
        item.type = 'subfolder'
    
    for item in projects:
        item.type = 'project'
    
    combined_list = chain(sub_folders, projects)
    
    return render(request, 'main_app/project/project_list.html', {'projects': combined_list})

@login_required
def project_list_closed(request):
    user = request.user
    is_admin = user.is_superuser
    
    if is_admin:
        projects = Project.objects.filter(
            Q(status='closed') &
            Q(subfolder__isnull=True)
        ).distinct().order_by("id")

        sub_folders = Folder.objects.filter(
            Q(status='closed') &
            Q(parent_folder__isnull=False)
        ).distinct().order_by("id")
    else:
        user_filter = Q(owner=user) | Q(members=user) | Q(assignee=user)

        projects = Project.objects.filter(
            user_filter &
            Q(status='closed') &
            Q(subfolder__isnull=True)
        ).distinct().order_by("id")

        sub_folders = Folder.objects.filter(
            user_filter &
            Q(status='closed') &
            Q(parent_folder__isnull=False)
        ).distinct().order_by("id")
    
    for item in sub_folders:
        item.type = 'subfolder'
    
    for item in projects:
        item.type = 'project'
    
    combined_list = chain(sub_folders, projects)
    
    return render(request, 'main_app/project/project_list_closed.html', {'projects': combined_list})

@login_required
def project_list_archive(request):
    user = request.user
    is_admin = user.is_superuser
    
    if is_admin:
        projects = Project.objects.filter(
            Q(status='archive') &
            Q(subfolder__isnull=True)
        ).distinct().order_by("id")

        sub_folders = Folder.objects.filter(
            Q(status='archive') &
            Q(parent_folder__isnull=False)
        ).distinct().order_by("id")
    else:
        user_filter = Q(owner=user) | Q(members=user) | Q(assignee=user)

        projects = Project.objects.filter(
            user_filter &
            Q(status='archive') &
            Q(subfolder__isnull=True)
        ).distinct().order_by("id")

        sub_folders = Folder.objects.filter(
            user_filter &
            Q(status='archive') &
            Q(parent_folder__isnull=False)
        ).distinct().order_by("id")

    for item in sub_folders:
        item.type = 'subfolder'
    for item in projects:
        item.type = 'project'

    combined_list = chain(sub_folders, projects)

    return render(request, 'main_app/project/project_list_archive.html', {'projects': combined_list})


@login_required
def create_project(request):
    set_current_user(request.user)
    folder_slug = request.GET.get('folder')
    subfolder_slug = request.GET.get('subfolder')
    user_id = request.GET.get('user')
    client = request.GET.get('client')

    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            if folder_slug:
                folder = Folder.objects.get(slug=folder_slug)
                project.folder = folder
            project.save()
            form.save_m2m()
            return redirect('project_tasks', project_slug=project.slug)
        else:
            print(form.errors)
            return render(request, 'main_app/project/create_project.html', {
                'form': form,
                'users': User.objects.all()
            })
    else:
        form = ProjectForm()
        
        if user_id:
            form.fields['assignee'].initial = user_id
            
        if folder_slug:
            folder = Folder.objects.get(slug=folder_slug)
            form.fields['folder'].initial = folder
            form.fields['assignee'].initial = folder.assignee
            form.fields['members'].initial = folder.members.all()

            if subfolder_slug:
                subfolder = Folder.objects.get(slug=subfolder_slug)
                form.fields['subfolder'].initial = subfolder
            return render(request, 'main_app/project/create_project.html', {'form': form, 'users': User.objects.all(), 'folder':folder})
        
        if client:
            form.fields['client'].initial = client
            
        return render(request, 'main_app/project/create_project.html', {'form': form, 'users': User.objects.all()})

import re
def add_table_classes(text):
    if not text:
        return text

    # Regular expression for searching for all Table tags
    table_pattern = re.compile(r'<table(.*?)>(.*?)<\/table>', re.DOTALL)

    # Adding classes to tables
    updated_text = re.sub(table_pattern, r'<table class="table table-bordered border-top border-bottom"\1>\2</table>', text)

    return updated_text

@login_required
def project_detail(request, project_slug):
    project = get_object_or_404(Project, slug=project_slug)
    project.description = add_table_classes(project.description)

    if not request.user.is_superuser:
        if request.user not in project.members.all() and request.user != project.assignee and request.user != project.owner:
            return render(request, 'main_app/errors/access_denied.html')

    return render(request, 'main_app/project/project_detail.html', {
        'project': project,
    })

@login_required
def delete_project(request, project_slug):
    set_current_user(request.user)
    project = get_object_or_404(Project, slug=project_slug)
    if request.method == "POST":
        project.delete()
        messages.success(request, "The project was deleted successfully.")
        return redirect(reverse('project_list'))
    return redirect(reverse('project_detail', args=[project_slug]))

@login_required
def edit_project(request, project_slug):
    project = get_object_or_404(Project, slug=project_slug)
    users_all = User.objects.all()
    folders_all = Folder.objects.all()

    project_form = ProjectForm(request.POST or None, instance=project)

    if request.method == 'POST' and project_form.is_valid():
        # Обновление других полей, которые не входят в форму
        project = project_form.save(commit=False)

        # Обработка и установка даты дедлайна
        deadline_str = request.POST.get('deadline', project.deadline)
        try:
            project.deadline = datetime.strptime(deadline_str, '%d.%m.%Y').date()
        except ValueError:
            project.deadline = None

        # Установка папки проекта
        folder_id = request.POST.get('folder')
        if folder_id:
            try:
                project.folder = Folder.objects.get(pk=folder_id)
            except Folder.DoesNotExist:
                project.folder = None
        else:
            project.folder = None

        # Установка назначенного пользователя
        assignee_id = request.POST.get('assignee')
        if assignee_id:
            project.assignee = User.objects.get(id=assignee_id)
        else:
            project.assignee = None

        # Установка участников проекта
        assigned_usernames = request.POST.getlist('members')
        members = User.objects.filter(id__in=assigned_usernames)
        project.members.set(members)

        # Сохранение проекта
        project.save()

        # Перенаправление на страницу проекта
        return redirect('project_detail', project_slug=project.slug)

    return render(request, 'main_app/project/edit_project.html', {
        'project': project,
        'project_form': project_form,
        'users_all': users_all,
        'folders_all': folders_all,
    })

@login_required
def project_tasks(request, project_slug):
    project = get_object_or_404(Project, slug=project_slug)

    if not request.user.is_superuser:
        if request.user not in project.members.all() and request.user != project.assignee and request.user != project.owner:
            return render(request, 'main_app/errors/access_denied.html')

    return render(request, 'main_app/project/project_tasks.html', {
        'project': project,
    })

@login_required
def project_tasks_files(request, project_slug):
    project = get_object_or_404(Project, slug=project_slug)

    # Фильтруем задачи, относящиеся к проекту
    tasks_in_project = Task.objects.filter(project=project)

    # Фильтруем файлы задач, относящиеся к задачам из проекта
    tasks_files = TaskFile.objects.filter(task__in=tasks_in_project).order_by("-id")

    # Проверка прав доступа
    if not request.user.is_superuser:
        if request.user not in project.members.all() and request.user != project.assignee and request.user != project.owner:
            return render(request, 'main_app/errors/access_denied.html')

    return render(request, 'main_app/project/project_tasks_files.html', {
        'project': project,
        'tasks_files': tasks_files,
    })

@login_required
def project_comments(request, project_slug):
    set_current_user(request.user)
    project = get_object_or_404(Project, slug=project_slug)
    project_comments = ProjectComment.objects.filter(
        project=project
    ).filter(
        (Q(author=request.user) | Q(approved=True)) &
        Q(replied_for__isnull=True)
    ).order_by('-created')

    if request.method == 'POST':
        if 'delete_comment_id' in request.POST:
            comment_id = request.POST.get('delete_comment_id')
            comment = get_object_or_404(ProjectComment, id=comment_id, project=project)

            if request.user == comment.author or request.user.is_superuser:
                comment.delete()
            else:
                return HttpResponseForbidden("You do not have permission to delete this comment.")
            return redirect('project_comments', project_slug=project.slug)

        comment_form = ProjectCommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.author = request.user
            comment.project = project

            # Проверка на наличие комментария, на который отвечают
            replied_comment_id = request.POST.get('replied_comment_id')
            if replied_comment_id:
                replied_comment = get_object_or_404(ProjectComment, id=replied_comment_id)
                comment.replied_for = replied_comment

            comment.save()

            # Process pre-uploaded files
            uploaded_files_json = request.POST.get('uploaded_files', '[]')
            try:
                uploaded_files = json.loads(uploaded_files_json)
                
                # Create TaskCommentFile objects for each pre-uploaded file
                for file_data in uploaded_files:
                    ProjectCommentFile.objects.create(
                        name=file_data['name'],
                        project_comment=comment,
                        author=request.user,
                        file_path=file_data['url'],
                        size=file_data['size']
                    )
            except json.JSONDecodeError:
                # Skip file creation if JSON parsing fails
                pass

            return redirect('project_comments', project_slug=project.slug)
        else:
            print(comment_form.errors)

    else:
        comment_form = ProjectCommentForm()

    if not request.user.is_superuser:
        if request.user not in project.members.all() and request.user != project.assignee and request.user != project.owner:
            return render(request, 'main_app/errors/access_denied.html')

    for comment in project_comments:
        comment.text = add_table_classes(comment.text)

    return render(request, 'main_app/project/project_comments.html', {
        'project': project,
        'comment_form': comment_form,
        'project_comments': project_comments,
    })


@login_required
def project_list_reports(request):
    if request.user.is_superuser:
        project_reports = ProjectReport.objects.all().order_by("-id")
    else:
        project_reports = ProjectReport.objects.filter(
            author=request.user
        ).distinct().order_by("-id")

    context = {
        'project_reports': project_reports
    }

    return render(request, 'main_app/project/project_list_reports.html', context)

@login_required
def project_reports(request, project_slug):
    project = get_object_or_404(Project, slug=project_slug)

    project_reports = ProjectReport.objects.filter(project=project).order_by("-id")

    context = {
        'project': project,
        'project_reports':project_reports,
    }

    return render(request, 'main_app/project/project_reports.html', context)


@login_required
def project_create_report(request):
    project_slug = request.GET.get('project_slug')
    if project_slug:
        project = get_object_or_404(Project, slug=project_slug)
    else:
        project = None

    if request.method == 'POST':
        form = ProjectReportForm(request.POST)  # Учитываем файлы в форме
        if form.is_valid():
            report = form.save(commit=False)
            report.author = request.user
            if project:
                report.project = project
            report.save()
            
            # Process pre-uploaded files
            uploaded_files_json = request.POST.get('uploaded_files', '[]')
            try:
                uploaded_files = json.loads(uploaded_files_json)
                
                # Create TaskCommentFile objects for each pre-uploaded file
                for file_data in uploaded_files:
                    ProjectReportFile.objects.create(
                        name=file_data['name'],
                        project_report = report,
                        author=request.user,
                        file_path=file_data['url'],
                        size=file_data['size']
                    )
            except json.JSONDecodeError:
                # Skip file creation if JSON parsing fails
                pass

            # Перенаправление на страницу отчетов проекта
            if project:
                return redirect('project_reports', project_slug=project.slug)
            else:
                return redirect('project_list_reports')

    else:
        form = ProjectReportForm(
            initial={'project':project if project else None,}
        )

    context = {
        'project': project if project_slug else None,
        'form': form
    }

    return render(request, 'main_app/project/create_project_report.html', context)

def edit_project_report(request, project_report_id):
    project_report = get_object_or_404(ProjectReport, id=project_report_id)

    if request.method == "POST":
        form = ProjectReportForm(request.POST, request.FILES, instance=project_report)
        if form.is_valid():
            form.save()
            return redirect('project_list_reports')
    else:
        form = ProjectReportForm(instance=project_report)

    return render(request, 'main_app/project/create_project_report.html', {'form': form})

@login_required
def delete_report(request, report_id):
    set_current_user(request.user)
    report = get_object_or_404(ProjectReport, id=report_id)
    project_slug = report.project.slug

    if request.method == "POST":
        report.delete()
        messages.success(request, "The report was deleted successfully.")
        return redirect(reverse('project_reports', args=[project_slug]))
    return redirect(reverse('project_reports', args=[project_slug]))