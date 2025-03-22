from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from ..models import *
from ..forms import TagFrom
from django.db.models import Q

@login_required
def create_tag(request):

    if request.method == 'POST':
        tag_form = TagFrom(request.POST)
        if tag_form.is_valid():
            tag_form.save()
            return redirect(reverse('tag_list'))
    else:
        tag_form = TagFrom()

    context = {
        'tag_form': tag_form
    }

    return render(request, 'main_app/tag/create_tag.html', context)

@login_required
def tag_list(request):
    tags = Tag.objects.all().order_by('id')

    # Получение данных о задачах для каждого тега
    tag_data = []
    for tag in tags:
        tag_info = {
            'name': tag.name,
            'slug': tag.slug,
            'count': tag.project_tag.count(),  # Общее количество проектов с этим тегом
            'new': tag.project_tag.filter(status='new').count(),  # Количество задач со статусом "New"
            'working': tag.project_tag.filter(status='working').count(),  # Количество задач со статусом "Working"
            'pause': tag.project_tag.filter(status='pause').count(),  # Количество задач со статусом "Pause"
            'closed': tag.project_tag.filter(status='closed').count(),  # Количество задач со статусом "Closed"
            'archive': tag.project_tag.filter(status='archive').count(),  # Количество задач со статусом "Archive"
        }
        tag_data.append(tag_info)

    context = {
        'tag_data': tag_data,
    }

    return render(request, 'main_app/tag/tag_list.html', context)

@login_required
def tag_projects(request, tag_slug):
    user = request.user
    is_admin = user.is_superuser

    if is_admin:
        if tag_slug == 'None':
            projects = Project.objects.filter(
                Q(tag__isnull=True)
            ).distinct().order_by("id")
        else:
            tag_obj = Tag.objects.filter(slug=tag_slug).first()
            projects = Project.objects.filter(
                Q(tag=tag_obj)
            ).distinct().order_by("id")
    else:
        user_perm = Q(owner=user) | Q(members=user) | Q(assignee=user)

        if tag_slug == 'None':
            projects = Project.objects.filter(
                user_perm &
                Q(tag__isnull=True)
            ).distinct().order_by("id")
        else:
            tag_obj = Tag.objects.filter(slug=tag_slug).first()
            projects = Project.objects.filter(
                user_perm &
                Q(tag=tag_obj)
            ).distinct().order_by("id")
    
    for item in projects:
        item.type = 'project'

    return render(request, 'main_app/tag/tag_projects.html', {'projects': projects})