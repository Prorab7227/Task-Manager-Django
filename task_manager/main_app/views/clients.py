from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from ..models import Project, Folder

from itertools import chain
from collections import defaultdict
from django.db.models import Count, Q

@login_required
def clients(request):
    status_annotate = {
        'new': Count('id', filter=Q(status='new')),
        'working': Count('id', filter=Q(status='working')),
        'pause': Count('id', filter=Q(status='pause')),
        'done': Count('id', filter=Q(status='done')),
        'closed': Count('id', filter=Q(status='closed')),
        'archive': Count('id', filter=Q(status='archive')),
    }

    if request.user.is_superuser:
        project_clients = Project.objects.values('client').annotate(
            projects=Count('id'),
            **status_annotate
        )

        folder_clients = Folder.objects.values('client').annotate(
            folders=Count('id'),
            **status_annotate
        )

    else:
        project_clients = Project.objects.filter(
            Q(owner=request.user) | Q(members=request.user) | Q(assignee=request.user)
        ).values('client').annotate(
            projects=Count('id'),
            **status_annotate
        )

        folder_clients = Folder.objects.filter(
            Q(owner=request.user) | Q(members=request.user)
        ).values('client').annotate(
            folders=Count('id'),
            **status_annotate
        )

    # Объединяем проекты и папки
    combined_clients = defaultdict(lambda: {
        'projects': 0, 'folders': 0, 'new': 0, 'working': 0, 'pause': 0, 'done': 0, 'closed': 0, 'archive': 0
    })

    for item in chain(project_clients, folder_clients):
        client = item['client']
        for key in item:
            if key != 'client':
                combined_clients[client][key] += item[key]

    # Преобразуем в список
    clients = [{'client': client, **data} for client, data in combined_clients.items()]

    context = {'clients': clients}
    return render(request, 'main_app/user/clients.html', context)


@login_required
def client_projects(request, client):
    client_filter = {'client__isnull': True} if client == 'None' else {'client': client}
    user_filter = Q(owner=request.user) | Q(members=request.user) | Q(assignee=request.user)

    if request.user.is_superuser:
        projects = Project.objects.filter(**client_filter)
        folders = Folder.objects.filter(**client_filter)
    else:
        projects = Project.objects.filter(**client_filter).filter(user_filter)
        folders = Folder.objects.filter(**client_filter).filter(user_filter)

    for item in projects:
        item.type='project'

    for item in folders:
        item.type='subfolder'

    # Объединяем проекты и папки, сортируем по дате
    projects = sorted(
        list(projects) + list(folders), 
        key=lambda x: x.created, 
        reverse=True
    )

    context = {
        'projects': projects,
        'name_of_client': client,
    }

    return render(request, 'main_app/user/client_projects.html', context)