from .models import User, ProjectComment, TaskComment, Company
from django.db.models import Q

def global_context(request):
    users_with_tasks = User.objects.filter(tasks__isnull=False).distinct()

    usernames = users_with_tasks.values_list('username', flat=True)

    return {
        'Users': usernames
    }



def count_unread_comments(request):
    count_unread = 0
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

        count_unread = len(project_comments) + len(task_comments)
        return {'count_unread': count_unread}
    
    return {'count_unread': {}}

def count_moderate_comments(request):
    count_moderate = 0
    if request.user.is_authenticated:
        if request.user.is_superuser:
            project_comments = ProjectComment.objects.filter(read_by__isnull=True, approved=False).select_related('author', 'project').distinct()
            task_comments = TaskComment.objects.filter(read_by__isnull=True, approved=False).select_related('author', 'task').distinct()
        else:
            project_comments = ProjectComment.objects.filter(
                Q(project__assignee=request.user) |
                Q(project__members=request.user)
            ).filter(
                ~Q(read_by=request.user), approved=False
            ).select_related('author', 'project').distinct()

            task_comments = TaskComment.objects.filter(
                Q(task__assignee=request.user) |
                Q(task__members=request.user)
            ).filter(
                ~Q(read_by=request.user), approved=False
            ).select_related('author', 'task').distinct()

        count_moderate = len(project_comments) + len(task_comments)
        return {'count_moderate': count_moderate}
    
    return {'count_moderate': {}}



def companies_list(request):
    companies_list = []
    if request.user.is_authenticated:
        if request.user.is_superuser:
            companies = Company.objects.all()[:3]
        else:
            companies = Company.objects.filter(
                Q(owner=request.user) |
                Q(members=request.user)
            ).distinct()[:3]

        for company in companies:
            companies_list.append([company, company.members.count()])

        return {'companies': companies_list}
    
    return {'companies': {}}