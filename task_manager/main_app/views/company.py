from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from ..models import User, Task, Project, Folder, Action, TaskFile, Company
from ..forms import FolderForm

from django.http import HttpResponseRedirect

from django.contrib import messages
from django.urls import reverse

from django.db.models import Q

from django.db import transaction
from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver
from django.core.serializers import serialize


@login_required
def companies(request):

    if request.user.is_superuser:
        company_list = Company.objects.all().order_by('-id')
    else:
        company_list = Company.objects.filter(
            Q(owner=request.user)|
            Q(members=request.user)
        ).order_by('-id').distinct()

    context = {
        'company_list': company_list,
    }

    return render(request, 'main_app/company/companies.html', context)