from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from ..models import User, Task, Project, Folder, ProjectReport, Tag
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q, Count
from itertools import chain

@login_required
def index(request):
    exclude_archive = Q(project__status='archive') | Q(project__folder__status='archive')

    if request.user.is_superuser:
        tasks = Task.objects.exclude(exclude_archive).order_by("-id")
    else:
        tasks = Task.objects.filter(
            Q(project__owner=request.user) |
            Q(assignee=request.user) |
            Q(members=request.user)
        ).exclude(exclude_archive).distinct().order_by("-id")

    return render(request, 'main_app/index.html', {'tasks': tasks})

@login_required
def profile_view(request):

    user = User.objects.get(username=request.user.username)

    projects = Project.objects.filter(
        Q(owner=user) |
        Q(members=user) |
        Q(assignee=user)
    ).exclude(
        Q(status='archive')|
        Q(folder__status='archive')
    ).distinct().annotate(
        task_new=Count('tasks', filter=Q(tasks__status='new')),
        task_working=Count('tasks', filter=Q(tasks__status='working')),
        task_pause=Count('tasks', filter=Q(tasks__status='pause')),
        task_done=Count('tasks', filter=Q(tasks__status='done')),
        task_closed=Count('tasks', filter=Q(tasks__status='closed'))
    )

    return render(request, 'main_app/profile.html', {'projects': projects})

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
        else:
            print(form.errors)
    else:
        form = UserCreationForm()
    return render(request, 'account/signup.html', {'form': form})

@login_required
def user_tasks(request, username):
    if not request.user.is_superuser:
        return render(request, 'main_app/errors/access_denied.html')

    user = User.objects.get(username=username)

    tasks = Task.objects.filter(
        Q(members=user) |
        Q(assignee=user)
    ).exclude(
        Q(project__status='archive')|
        Q(project__folder__status='archive')
    ).distinct()

    context = {
        'user': user,
        'tasks': tasks,
    }

    return render(request, 'main_app/user/user_tasks.html', context)

def user_reports(request, username):
    user = User.objects.filter(username=username).first()
    reports = ProjectReport.objects.filter(author=user).order_by('-created')

    context = {
        'project_reports': reports
    }

    return render(request, 'main_app/user/user_reports.html', context)

@login_required
def user_projects_1(request, username):
    if not request.user.is_superuser:
        return render(request, 'main_app/errors/access_denied.html')

    user = get_object_or_404(User, username=username)

    projects = Project.objects.filter(
        Q(members=user) |
        Q(assignee=user) |
        Q(owner=user)
    ).exclude(
        Q(status='archive')|
        Q(folder__status='archive')
    ).distinct().annotate(
        task_new=Count('tasks', filter=Q(tasks__status='new')),
        task_working=Count('tasks', filter=Q(tasks__status='working')),
        task_pause=Count('tasks', filter=Q(tasks__status='pause')),
        task_done=Count('tasks', filter=Q(tasks__status='done')),
        task_closed=Count('tasks', filter=Q(tasks__status='closed'))
    )

    context = {
        'user': user,
        'projects': projects
    }

    return render(request, 'main_app/user/user_projects_1.html', context)

@login_required
def user_projects_2(request, username):
    if not request.user.is_superuser:
        return render(request, 'main_app/errors/access_denied.html')

    user = get_object_or_404(User, username=username)

    sub_folders = Folder.objects.filter(
        Q(assignee=user)|
        Q(members=user)
    ).filter(Q(parent_folder__isnull=False)).distinct()

    projects = Project.objects.filter(
        Q(members=user) |
        Q(assignee=user) |
        Q(owner=user)
    ).exclude(
        Q(status='archive')|
        Q(folder__status='archive')|
        Q(subfolder__isnull=False)
    ).distinct()

    for item in sub_folders:
        item.type='subfolder'
    for item in projects:
        item.type='project'

    combined_list = chain(sub_folders, projects)
    projects_sorted = sorted(combined_list, key=lambda obj: obj.created)

    context = {
        'user': user,
        'projects': projects_sorted
    }

    return render(request, 'main_app/user/user_projects_2.html', context)

@login_required
def users_list(request):
    users = User.objects.all()
    user_task_counts = {}
    total_project_count = {}
    total_task_count = {}

    for user in users:
        user_tasks = Task.objects.filter(
            Q(assignee=user)|
            Q(members=user)
        ).exclude(
            Q(project__status='archive')|
            Q(project__folder__status='archive')
        ).distinct()

        total_project_count[user] = Project.objects.filter(
            Q(assignee=user) |
            Q(members=user) |
            Q(owner=user)
        ).exclude(
            Q(status='archive')|
            Q(folder__status='archive')
        ).distinct().count()

        # Подсчет задач по статусу
        user_task_counts[user] = {
            'new': user_tasks.filter(status='new').count(),
            'working': user_tasks.filter(status='working').count(),
            'done': user_tasks.filter(status='done').count(),
        }

        total_task_count[user] = user_tasks.filter(status='new').count()+user_tasks.filter(status='working').count()+user_tasks.filter(status='done').count()
        
    context = {
        'users': users,
        'user_task_counts': user_task_counts,
        'total_task_count':total_task_count,
        'total_project_count':total_project_count
    }

    return render(request, 'main_app/user/users_list.html', context)


from django.http import JsonResponse
from ..context_processors import count_unread_comments, count_moderate_comments
def unread_comments_api(request):
    unread_data = count_unread_comments(request)
    return JsonResponse(unread_data)

def moderate_comments_api(request):
    moderate_com_data = count_moderate_comments(request)
    return JsonResponse(moderate_com_data)

def count_tasks(request):
    if request.user.is_superuser:
        tasks = Task.objects.filter(status='new')
    else:
        tasks = Task.objects.filter(
            (Q(project__owner=request.user) |
            Q(assignee=request.user) |
            Q(members=request.user)) &
            Q(status='new')
        ).distinct()

    task_count = tasks.count()

    return JsonResponse({"task_count": task_count})