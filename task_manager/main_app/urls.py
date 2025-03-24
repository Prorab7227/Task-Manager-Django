# urls.py
from django.urls import path, include
from allauth.account.views import LogoutView
from allauth.account import views as account_views

from . import views

from .views_api import *

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    # Basic
    path('', views.index, name='index'),

    path('action/', views.action_list, name='action'),

    path('mark_comment_as_read/<str:comment_type>/<int:comment_id>/', views.mark_comment_as_read, name='mark_comment_as_read'),
    path('mark_all_comments_as_read/', views.mark_all_comments_as_read, name='mark_all_comments_as_read'),

    path('accounts/profile/', views.profile_view, name='account_profile'),
    path('accounts/logout/', LogoutView.as_view(), name='account_logout'),

    path('login/', account_views.LoginView.as_view(), name='account_signin'),
    path('signup/', account_views.SignupView.as_view(), name='account_signup'),

    path('users/list/', views.users_list, name='users_list'),
    path("user/tasks/<str:username>", views.user_tasks, name="user_tasks"),
    path("user/reports/<str:username>", views.user_reports, name="user_reports"),
    path("user/statistics/<str:username>", views.user_projects_1, name="user_projects_1"),
    path("user/_projects/<str:username>", views.user_projects_2, name="user_projects_2"),

    path("clients/", views.clients, name="clients"),
    path("client-projects/<str:client>", views.client_projects, name="client_projects"),

    path("tags/", views.tag_list, name="tag_list"),
    path("tags/<str:tag_slug>/projects/", views.tag_projects, name="tag_projects"),
    path("tags/create/", views.create_tag, name="create_tag"),

    # Comments
    path("comments/", views.all_comments, name='all_comments'),
    path("comments/moderate/", views.moderate_comments, name='moderate_comments'),

    path('approve_comment/<int:comment_id>/<str:comment_type>', views.approve_comment, name='approve_comment'),
    path('edit_comment/<int:comment_id>/<str:comment_type>', views.edit_comment, name='edit_comment'),
    path('delete_comment/<int:comment_id>/<str:comment_type>', views.delete_comment, name='delete_comment'),

    # Company
    path("companies/", views.companies, name="companies"),

    # Folder
    path('folders/', views.folder_list, name='folder_list'),
    path('folders/archive/', views.folder_list_archive, name='folder_list_archive'),

    path('create/folder/', views.create_folder, name='create_folder'),
    path('folder/<str:folder_slug>', views.folder_detail, name='folder_detail'),

    path('folder/<str:folder_slug>/projects/', views.folder_projects, name='folder_projects'),
    path('folder/<str:folder_slug>/projects/files/', views.folder_projects_files, name='folder_projects_files'),

    path('folder/<str:folder_slug>/delete/', views.delete_folder, name='delete_folder'),
    path('folder/<str:folder_slug>/edit', views.edit_folder, name='edit_folder'),

    # Project
    path('projects/active/', views.project_list, name='project_list'),
    path('projects/closed/', views.project_list_closed, name='project_list_closed'),
    path('projects/archive/', views.project_list_archive, name='project_list_archive'),
    path('reports/all/', views.project_list_reports, name='project_list_reports'),
    path('projects/all/', views.project_list_all, name='project_list_all'),

    path('create/project', views.create_project, name='create_project'),
    path('create/project-report', views.project_create_report, name='project_create_report'),
    path('edit/project-report/<int:project_report_id>', views.edit_project_report, name='edit_project_report'),

    path('project/<str:project_slug>/edit/', views.edit_project, name='edit_project'),
    path('project/<str:project_slug>/', views.project_detail, name='project_detail'),

    path('project/<str:project_slug>/tasks', views.project_tasks, name='project_tasks'),
    path('project/<str:project_slug>/tasks/files', views.project_tasks_files, name='project_tasks_files'),
    path('project/<str:project_slug>/comments', views.project_comments, name='project_comments'),

    path('project/<str:project_slug>/reports', views.project_reports, name='project_reports'),
    path('project/<int:report_id>/delete-report', views.delete_report, name='delete_report'),

    path('projects/<str:project_slug>/delete/', views.delete_project, name='delete_project'),

    # Task
    path('create/task', views.create_task, name='create_task'),
    path('project/<str:project_slug>/create/task', views.create_task, name='create_task'),
    
    path('task/<str:task_slug>/', views.task_detail, name='task_detail'),
    path('task/<str:task_slug>/edit/', views.edit_task, name='edit_task'),
    path('task/<str:task_slug>/delete/', views.delete_task, name='delete_task'),

    path('task/<str:task_slug>/comments', views.task_comments, name='task_comments'),
    
    path('task/file/delete/<int:file_id>/', views.delete_task_file, name='delete_task_file'),

    # Screener
    path('tracker/', views.screener_page, name='screener'),
    path('tracker/<str:username>', views.user_screener, name='user_screener'),

    path('delete/screenshot/<int:screenshot_id>', views.delete_screenshot, name='delete_screenshot'),

    # API
    # path('api/screenshot/create/', ScreenshotCreateView.as_view(), name='screenshot-create'),
    # path('api/screener/create/', ScreenerCreateView.as_view(), name='screener-create'),

    path('api/unread-comments/', views.unread_comments_api, name='count_unread_comments'),
    path('api/moderate-comments/', views.moderate_comments_api, name='count_moderate_comments'),
    path('api/tasks-count/', views.count_tasks, name='count_tasks'),

    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/auth/session-token/', get_session_token, name='session-token'),
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),
    path('api/token/validate/', TokenValidationView.as_view(), name='token-validate'),

    path('api/upload-task-file/', TempFileUploadView.as_view(), name='temp_file_upload'),
    path('api/upload-task-comment-file/', TaskCommentFileUploadView.as_view(), name='upload_task_comment_file'),

    path('api/upload-project-comment-file/', ProjectCommentFileUploadView.as_view(), name='upload_project_comment_file'),
    path('api/upload-project-report-file/', ProjectReportFileUploadView.as_view(), name='upload_project_report_file'),

    # Other
    path('update-status/task/<int:id>/', views.task_update_status, name='task_update_status'),
    path('update-priority/task/<int:id>/', views.task_update_priority, name='task_update_priority'),

    path('update-status/project/<int:id>/', views.project_update_status, name='project_update_status'),
    path('update-priority/project/<int:id>/', views.project_update_priority, name='project_update_priority'),

    path('update-status/folder/<int:id>/', views.folder_update_status, name='folder_update_status'),
    path('update-priority/folder/<int:id>/', views.folder_update_priority, name='folder_update_priority'),
    
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]