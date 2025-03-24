import os, re

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from ..models import User, Task, Project, TaskComment, TaskFile, TaskCommentFile
from ..forms import TaskForm, ProjectCommentForm, TaskCommentForm, TaskFileForm

from django.http import HttpResponseForbidden
from django.http import HttpResponseRedirect

from django.db.models import Q

from django.contrib import messages
from django.urls import reverse

def task_update_priority(request, id):
    task = get_object_or_404(Task, id=id)
    
    if request.method == 'POST':
        new_priority = request.POST.get('priority')
        if new_priority:
            task.priority = new_priority
            task.save()
    
    # Redirect to the same page
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

def task_update_status(request, id):
    task = get_object_or_404(Task, id=id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status:
            task.status = new_status
            task.save()
    
    # Redirect to the same page
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

import json
@login_required
def create_task(request, project_slug=None):
    projects = Project.objects.all()
    pro_members = None
    
    if project_slug:
        project = get_object_or_404(Project, slug=project_slug)
        assignee = project.assignee
        pro_members = project.members.all()
    else:
        project = Project.objects.filter(name="General").first()
        
    user = request.GET.get('user')
    if user:
        assignee = User.objects.filter(id=user).first()

    if request.method == 'POST':
        task_form = TaskForm(request.POST)
        project_id = request.POST.get('project')
        selected_project = Project.objects.filter(id=int(project_id)).first() if project_id and project_id.isdigit() else None

        if task_form.is_valid():
            # Save the task
            task = task_form.save(commit=False)
            task.owner = request.user
            task.project = selected_project
            task.save()
            task_form.save_m2m()

            # We get information about pre -uploaded files
            uploaded_files_json = request.POST.get('uploaded_files', '[]')
            try:
                uploaded_files = json.loads(uploaded_files_json)
                
                # Create Taskfile objects for each uploaded file
                for file_data in uploaded_files:
                    TaskFile.objects.create(
                        name=file_data['name'],
                        task=task,
                        author=request.user,
                        file_path=file_data['url'],
                        size=file_data['size']
                    )
            except json.JSONDecodeError:
                # In the case of parsing error json, just skip the creation of files
                pass

            return redirect('project_tasks', project_slug=selected_project.slug) if selected_project else redirect('index')

    else:
        initial_dict_form = {
            'assignee': assignee,
            'project': project,
            'members': pro_members if pro_members else None
        }
        task_form = TaskForm(initial=initial_dict_form)

    context = {
        'projects': projects,
        'project': project,
        'task_form': task_form
    }

    return render(request, 'main_app/task/create_task.html', context)

@login_required
def delete_task(request, task_slug):
    task = get_object_or_404(Task, slug=task_slug)
    if task.project:
        project_slug = task.project.slug  # We save the project ID to return to its details
        if request.method == "POST":
            task.delete()
            messages.success(request, "The task was deleted successfully.")
            return redirect(reverse('project_tasks', args=[project_slug]))
    else:
        if request.method == "POST":
            task.delete()
            messages.success(request, "The task was deleted successfully.")
            return redirect('index')

@login_required
def edit_task(request, task_slug):
    task = get_object_or_404(Task, slug=task_slug)
    projects = Project.objects.all()
    users_all = User.objects.all()

    # Initialization of the form with the data data
    task_form = TaskForm(request.POST or None, instance=task)

    if request.method == 'POST' and task_form.is_valid():
        # Preservation of edited data from the form
        task = task_form.save(commit=False)

        # Updating participants in the task
        assigned_user_ids = request.POST.getlist('members')
        members = User.objects.filter(id__in=assigned_user_ids)
        task.members.set(members)
        task.save()
        # We get information about pre -uploaded files
        uploaded_files_json = request.POST.get('uploaded_files', '[]')
        try:
            uploaded_files = json.loads(uploaded_files_json)
            
            # Create Taskfile objects for each uploaded file
            for file_data in uploaded_files:
                TaskFile.objects.create(
                    name=file_data['name'],
                    task=task,
                    author=request.user,
                    file_path=file_data['url'],
                    size=file_data['size']
                )
        except json.JSONDecodeError:
            # In the case of parsing error json, just skip the creation of files
            pass

        return redirect('task_detail', task_slug=task.slug)

    context = {
        'task': task,
        'task_form': task_form,
        'users_all': users_all,
        'projects': projects,
    }

    return render(request, 'main_app/task/edit_task.html', context)


def add_table_classes(text):
    if not text:
        return text

    # Regular expression for searching for all Table tags
    table_pattern = re.compile(r'<table(.*?)>(.*?)<\/table>', re.DOTALL)

    # Adding classes to tables
    updated_text = re.sub(table_pattern, r'<table class="table table-bordered border-top border-bottom"\1>\2</table>', text)

    return updated_text

@login_required
def task_detail(request, task_slug):
    task = get_object_or_404(Task, slug=task_slug)
    if task.description:
        task.description = add_table_classes(task.description)

    # Access check
    if not request.user.is_superuser:
        if request.user not in task.members.all() and request.user != task.assignee and request.user != task.owner:
            return render(request, 'main_app/errors/access_denied.html')

    form = TaskFileForm(request.POST or None, request.FILES or None)
    task_files = task.task_files.all().order_by("-id")  # Getting all files related to the task

    if request.method == 'POST':
        # Получаем информацию о предварительно загруженных файлах
        uploaded_files_json = request.POST.get('uploaded_files', '[]')
        try:
            uploaded_files = json.loads(uploaded_files_json)
            
            # Создаем объекты TaskFile для каждого загруженного файла
            for file_data in uploaded_files:
                TaskFile.objects.create(
                    name=file_data['name'],
                    task=task,
                    author=request.user,
                    file_path=file_data['url'],
                    size=file_data['size']
                )
            return redirect(request.path)
        except json.JSONDecodeError:
            # В случае ошибки парсинга JSON просто пропускаем создание файлов
            pass

    context = {
        'task': task,
        'form': form,
        'task_files': task_files,
    }

    return render(request, 'main_app/task/task_detail.html', context)


@login_required
def delete_task_file(request, file_id):
    file_item = get_object_or_404(TaskFile, id=file_id)

    if request.method == "POST":
        file_item.delete()
        messages.success(request, "The file was deleted successfully.")
        return redirect(request.META.get('HTTP_REFERER', 'home'))  # Rebooting the current page
    return redirect(request.META.get('HTTP_REFERER', 'home'))  # Rebooting the current page

@login_required
def task_comments(request, task_slug):
    task = get_object_or_404(Task, slug=task_slug)
    task_comments = TaskComment.objects.filter(
        task=task
    ).filter(
        (Q(author=request.user) | Q(approved=True)) &
        Q(replied_for__isnull=True)
    ).order_by('-created')

    if request.method == 'POST':
        # Проверка, если передан ID комментария для удаления
        if 'delete_comment_id' in request.POST:
            comment_id = request.POST.get('delete_comment_id')
            comment = get_object_or_404(TaskComment, id=comment_id, task=task)

            # Удаление разрешено только автору комментария или администратору
            if request.user == comment.author or request.user.is_superuser:
                comment.delete()
            else:
                return HttpResponseForbidden("You do not have permission to delete this comment.")
            return redirect('task_comments', task_slug=task.slug)

        # Обработка добавления нового комментария или ответа
        comment_form = TaskCommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.author = request.user
            comment.task = task

            # Проверка на наличие комментария, на который отвечают
            replied_comment_id = request.POST.get('replied_comment_id')
            if replied_comment_id:
                replied_comment = get_object_or_404(TaskComment, id=replied_comment_id)
                comment.replied_for = replied_comment

            comment.save()

            # Обработка предварительно загруженных файлов
            uploaded_files_json = request.POST.get('uploaded_files', '[]')
            try:
                uploaded_files = json.loads(uploaded_files_json)
                
                # Создание объектов TaskCommentFile для каждого загруженного файла
                for file_data in uploaded_files:
                    TaskCommentFile.objects.create(
                        name=file_data['name'],
                        task_comment=comment,
                        author=request.user,
                        file_path=file_data['url'],
                        size=file_data['size']
                    )
            except json.JSONDecodeError:
                # Пропуск создания файлов, если произошла ошибка парсинга JSON
                pass

            return redirect('task_comments', task_slug=task.slug)
        else:
            print(comment_form.errors)

    else:
        comment_form = TaskCommentForm()

    # Проверка: текущий пользователь назначен на задачу
    if not request.user.is_superuser:
        if request.user not in task.members.all() and request.user != task.assignee and request.user != task.owner:
            return render(request, 'main_app/errors/access_denied.html')

    for comment in task_comments:
        comment.text = add_table_classes(comment.text)

    return render(request, 'main_app/task/task_comments.html', {
        'task': task,
        'comment_form': comment_form,
        'task_comments': task_comments,
    })