from django.contrib import admin
from .models import *

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Folder)
class FolderAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'client', 'owner', 'assignee', 'status', 'priority', 'parent_folder', 'created', 'last_modified')
    list_filter = ('status', 'priority', 'owner', 'assignee', 'parent_folder')
    search_fields = ('name', 'description', 'client', 'owner__username', 'assignee__username')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('-created',)
    
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description')
        }),
        ('Client & Users', {
            'fields': ('client', 'owner', 'assignee', 'members')
        }),
        ('Dates', {
            'fields': ('created', 'last_modified')
        }),
        ('Status & Priority', {
            'fields': ('status', 'priority')
        }),
        ('Folder Structure', {
            'fields': ('parent_folder',)
        }),
    )
    readonly_fields = ('created', 'last_modified')

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'tag', 'folder', 'subfolder', 'client', 'owner', 'assignee', 'status', 'priority', 'deadline', 'last_modified')
    list_filter = ('status', 'priority', 'owner', 'assignee', 'deadline')
    search_fields = ('name', 'client', 'tag', 'description', 'owner__username', 'assignee__username')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('-created',)
    
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description', 'tag')
        }),
        ('Client & Users', {
            'fields': ('client', 'owner', 'assignee', 'members')
        }),
        ('Dates', {
            'fields': ('deadline', 'created', 'last_modified')
        }),
        ('Status & Priority', {
            'fields': ('status', 'priority')
        }),
        ('Folders', {
            'fields': ('folder', 'subfolder')
        }),
    )
    readonly_fields = ('created', 'last_modified')

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'status', 'priority', 'owner', 'assignee', 'deadline', 'project', 'created', 'last_modified')
    list_filter = ('status', 'priority', 'owner', 'assignee', 'project', 'deadline')
    search_fields = ('title', 'description', 'owner__username', 'assignee__username', 'project__name')
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('-created',)
    
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'description')
        }),
        ('Client & Users', {
            'fields': ('owner', 'assignee', 'members')
        }),
        ('Dates', {
            'fields': ('deadline', 'created', 'last_modified')
        }),
        ('Status & Priority', {
            'fields': ('status', 'priority')
        }),
        ('Project Association', {
            'fields': ('project',)
        }),
    )
    readonly_fields = ('created', 'last_modified')

admin.site.register(ProjectComment)
admin.site.register(ProjectCommentFile)
admin.site.register(ProjectReport)
admin.site.register(ProjectReportFile)
admin.site.register(TaskComment)
admin.site.register(TaskCommentFile)
admin.site.register(Action)
admin.site.register(Tag)

@admin.register(TaskFile)
class TaskFileAdmin(admin.ModelAdmin):
    list_display = ('name', 'task', 'author', 'size', 'uploaded_at', 'formatted_size')
    search_fields = ('name', 'author__username', 'task__title')
    list_filter = ('author', 'uploaded_at')
    ordering = ('-uploaded_at',)

    def formatted_size(self, obj):
        """Форматируем размер файла в удобном виде"""
        if obj.size is not None:
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if obj.size < 1024.0:
                    return f"{obj.size:.2f} {unit}"
                obj.size /= 1024.0
        return "N/A"
    formatted_size.short_description = 'Formatted Size'

@admin.register(Screener)
class ScreenerAdmin(admin.ModelAdmin):
    list_display = ('user', 'work_time', 'date')
    list_filter = ('user', 'date')
    search_fields = ('user', 'date')
    ordering = ('-date',)

@admin.register(Screenshot)
class ScreenshotAdmin(admin.ModelAdmin):
    list_display = ('user', 'image', 'image_tag', 'created')
    list_filter = ('user',)
    ordering = ('-created',)
    readonly_fields = ('image_tag',)

    class Media:
        # Добавляем кастомный JavaScript и CSS
        js = ('admin/js/image_zoom.js',)  # Путь к вашему JS файлу
        css = {
            'all': ('admin/css/image_zoom.css',)  # Путь к вашему CSS файлу
        }