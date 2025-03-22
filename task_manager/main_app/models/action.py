from django.db import models
from django.contrib.auth.models import User

class Action(models.Model):
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='Author')
    task = models.ForeignKey('Task', on_delete=models.SET_NULL, related_name='actions', null=True, blank=True, verbose_name='Task')
    project = models.ForeignKey('Project', on_delete=models.SET_NULL, related_name='actions', null=True, blank=True, verbose_name='Project')
    folder = models.ForeignKey('Folder', on_delete=models.SET_NULL, related_name='actions', null=True, blank=True, verbose_name='Folder')
    action_type = models.CharField(max_length=100, verbose_name='Action Type')
    acted = models.DateTimeField(auto_now_add=True, verbose_name='Acted')

    context_before = models.TextField(blank=True, null=True, verbose_name='Context before')
    context_after = models.TextField(blank=True, null=True, verbose_name='Context after')