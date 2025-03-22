import json
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from ..models import User, Action, Project, Task

import re
def add_table_classes(text):
    if not text:
        return text

    # Регулярное выражение для поиска всех тегов table
    table_pattern = re.compile(r'<table(.*?)>(.*?)<\/table>', re.DOTALL)

    # Добавление классов к таблицам
    updated_text = re.sub(table_pattern, r'<table class="table table-bordered border-top border-bottom"\1>\2</table>', text)

    return updated_text

@login_required
def action_list(request):
    if request.user.is_superuser:
        actions = Action.objects.all().order_by('-acted')
    else:
        actions = Action.objects.filter(author=request.user).order_by('-acted')

    users = User.objects.all()
    user_dict = {user.id: user.username for user in users}

    processed_actions = []
    for action in actions:
        try:
            context_before = json.loads(action.context_before)[0] if action.context_before else {}
            context_after = json.loads(action.context_after)[0] if action.context_after else {}

            if not context_before:
                context_before = {}
            if not context_after:
                context_after = {}

            # Определяем object_type
            object_type = context_before.get("model", "") or context_after.get("model", "")
            object_type = object_type.split(".")[1] if "." in object_type else "Unknown"

            projectcomment_project = context_after.get("fields", {}).get("project")
            if projectcomment_project:
                try:
                    project_id = int(projectcomment_project)
                    projectcomment_project = Project.objects.get(id=project_id)
                except (ValueError, Project.DoesNotExist):
                    projectcomment_project = None

            taskcomment_task = context_after.get("fields", {}).get("task")
            if taskcomment_task:
                try:
                    task_id = int(taskcomment_task)
                    taskcomment_task = Task.objects.get(id=task_id)
                except (ValueError, Task.DoesNotExist):
                    taskcomment_task = None

            # Определяем изменения
            if action.action_type == "create":
                description = "create"
                changes = context_after.get("fields", {})

            elif action.action_type == "delete":
                description = "delete"
                taskcomment_task = context_before.get("fields", {}).get("task")
                if taskcomment_task:
                    try:
                        task_id = int(taskcomment_task)
                        taskcomment_task = Task.objects.get(id=task_id)
                    except (ValueError, Task.DoesNotExist):
                        taskcomment_task = None
                changes = context_before.get("fields", {})

            elif action.action_type == "update":
                description = "update"
                changes = {
                    key: {
                        'before': context_before.get("fields", {}).get(key),
                        'after': context_after.get("fields", {}).get(key),
                    }
                    for key in set(context_before.get("fields", {}).keys()).union(context_after.get("fields", {}).keys())
                    if context_before.get("fields", {}).get(key) != context_after.get("fields", {}).get(key)
                }


                description_text = changes.get('description', None)
                comment_text = changes.get('text', None)

                if description_text:
                    changes['description']['before'] = add_table_classes(changes['description']['before'])  # Сохраняем старое значение в before
                    changes['description']['after'] = add_table_classes(changes['description']['after'])  # Новое значение в after

                if comment_text:
                    changes['text']['before'] = add_table_classes(changes['text']['before'])  # Сохраняем старое значение в before
                    changes['text']['after'] = add_table_classes(changes['text']['after'])  # Новое значение в after


                assignee_user_id = changes.get('assignee', None)

                if assignee_user_id:
                    changes['assignee']['before'] = (
                        User.objects.filter(id=int(assignee_user_id['before'])).first()
                        if assignee_user_id['before'] is not None
                        else None
                    )
                    changes['assignee']['after'] = (
                        User.objects.filter(id=int(assignee_user_id['after'])).first()
                        if assignee_user_id['after'] is not None
                        else None
                    )


                project_changes_id = changes.get('project')

                if project_changes_id:
                    project_before = None
                    project_after = None

                    if project_changes_id.get('before') is not None:
                        try:
                            project_before = Project.objects.get(id=int(project_changes_id['before']))
                        except Project.DoesNotExist:
                            project_before = None  # Или обработка по вашему выбору, например, логирование ошибки

                    changes['project']['before'] = project_before if project_before else None

                    if project_changes_id.get('after') is not None:
                        try:
                            project_after = Project.objects.get(id=int(project_changes_id['after']))
                        except Project.DoesNotExist:
                            project_after = None  # Или обработка по вашему выбору

                    changes['project']['after'] = project_after if project_after else None

            # Добавляем дополнительные поля
            before_name = context_before.get("fields", {}).get("name") or context_before.get("fields", {}).get("title")
            after_name = context_after.get("fields", {}).get("name") or context_after.get("fields", {}).get("title")
            before_slug = context_before.get("fields", {}).get("slug")
            after_slug = context_after.get("fields", {}).get("slug")
            before_text = add_table_classes(context_before.get("fields", {}).get("text"))
            after_text = add_table_classes(context_after.get("fields", {}).get("text"))

            comment_author = context_after.get("fields", {}).get("author")
            if comment_author:
                comment_author = User.objects.filter(id=int(comment_author)).first()

            # Добавляем изменения для полей read_by в taskcomment и projectcomment
            if "read_by" in context_before.get("fields", {}):
                before_read_by_ids = context_before.get("fields", {}).get("read_by", [])
                after_read_by_ids = context_after.get("fields", {}).get("read_by", [])
                added_read_by_users = [user_dict.get(user_id) for user_id in after_read_by_ids if user_id not in before_read_by_ids]
            else:
                added_read_by_users = []

        except (json.JSONDecodeError, KeyError, IndexError) as e:
            description = "Invalid Data"
            changes = {}
            object_type = "Unknown"
            before_name = after_name = before_slug = after_slug = "Unknown"

        processed_actions.append({
            'id': action.id,
            'object_type': object_type,
            'author': user_dict.get(action.author_id, 'Unknown'),
            'acted': action.acted,
            'action_type': description,
            'changes': changes,
            'before_name': before_name,
            'after_name': after_name,
            'before_slug': before_slug,
            'after_slug': after_slug,
            'before_text': before_text,
            'after_text': after_text,
            'added_read_by_users': added_read_by_users,
            'comment_author': comment_author.username if comment_author else None,
            'projectcomment_project': projectcomment_project,
            'taskcomment_task': taskcomment_task,
        })

    for action in processed_actions:
        if action['after_name'] == "43241fds":
            print(action)

    return render(request, 'main_app/action.html', {
        'actions': processed_actions,
    })
