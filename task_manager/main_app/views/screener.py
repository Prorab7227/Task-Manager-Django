from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from ..models import User, Screenshot, Screener, Project, Tag

from datetime import timedelta
from django.db.models import Sum
from django.utils import timezone

from django.db.models.signals import post_delete
from django.dispatch import receiver
import os

@receiver(post_delete, sender=Screenshot)
def delete_screenshot_file(sender, instance, **kwargs):
    """Удаляет файл изображения при удалении объекта Screenshot"""
    if instance.image and os.path.isfile(instance.image.path):
        os.remove(instance.image.path)


# Helper function to format timedelta as h:m:s
def format_timedelta(timedelta_obj):
    total_seconds = int(timedelta_obj.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02}:{minutes:02}:{seconds:02}"

@login_required
def screener_page(request):
    # Check if the user is a superuser
    if request.user.is_superuser:
        # If the user is a superuser, show data for all users
        users = User.objects.all()
    else:
        # If the user is not a superuser, show only their own data
        users = User.objects.filter(id=request.user.id)

    # Get current time for calculating work periods
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)
    week_start = today_start - timedelta(days=today_start.weekday())  # Monday of this week
    month_start = today_start.replace(month=today_start.month, day=1)

    user_data = []

    for user in users:
        # Получаем последний скриншот для пользователя
        last_screenshot = Screenshot.objects.filter(user=user).last()

        # Рассчитываем общее рабочее время за разные периоды
        work_times = Screener.objects.filter(user=user)

        today_work_time = work_times.filter(date__gte=today_start).aggregate(total_time=Sum('work_time'))['total_time'] or timedelta()
        yesterday_work_time = work_times.filter(date__gte=yesterday_start, date__lt=today_start).aggregate(total_time=Sum('work_time'))['total_time'] or timedelta()
        week_work_time = work_times.filter(date__gte=week_start).aggregate(total_time=Sum('work_time'))['total_time'] or timedelta()
        month_work_time = work_times.filter(date__gte=month_start).aggregate(total_time=Sum('work_time'))['total_time'] or timedelta()

        # Добавляем данные пользователя
        user_data.append({
            'user': user,
            'last_screenshot': last_screenshot,  # Передаем ID последнего скриншота
            'today_work_time': format_timedelta(today_work_time),
            'yesterday_work_time': format_timedelta(yesterday_work_time),
            'week_work_time': format_timedelta(week_work_time),
            'month_work_time': format_timedelta(month_work_time),
        })

    context = {
        'user_data': user_data
    }

    return render(request, 'main_app/user/screener.html', context)


@login_required
def user_screener(request, username):
    user = User.objects.get(username=username)
    today = timezone.now().date()

    selected_date_str = request.GET.get('date', today)

    if isinstance(selected_date_str, str):
        try:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = today
    else:
        selected_date = selected_date_str

    selected_day_start = datetime.combine(selected_date, datetime.min.time())
    selected_day_end = datetime.combine(selected_date, datetime.max.time())

    screener_work_times = Screener.objects.filter(user=user, date__range=[selected_day_start, selected_day_end])

    total_work_time = sum([screener.work_time.total_seconds() for screener in screener_work_times], 0)
    total_work_time = timedelta(seconds=total_work_time)

    start_time_str = request.GET.get('start_time')
    end_time_str = request.GET.get('end_time')

    start_time = None
    end_time = None

    if start_time_str:
        try:
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
        except ValueError:
            pass

    if end_time_str:
        try:
            end_time = datetime.strptime(end_time_str, '%H:%M').time()
        except ValueError:
            pass

    screenshots = Screenshot.objects.filter(user=user, created__date=selected_date)

    if start_time and end_time:
        screenshots = screenshots.filter(created__time__gte=start_time, created__time__lte=end_time)
    elif start_time:
        screenshots = screenshots.filter(created__time__gte=start_time)
    elif end_time:
        screenshots = screenshots.filter(created__time__lte=end_time)

    screenshots = screenshots.order_by('-created')

    context = {
        'user': user,
        'screenshots': screenshots,
        'selected_date': selected_date,
        'total_work_time': total_work_time,
        'start_time': start_time_str,
        'end_time': end_time_str,
    }

    return render(request, 'main_app/user/user_screener.html', context)


from django.contrib import messages
@login_required
def delete_screenshot(request, screenshot_id):
    screenshot = get_object_or_404(Screenshot, id=screenshot_id)

    if request.method == "POST":
        if os.path.exists(screenshot.image.path):
            os.remove(screenshot.image.path)
        else:
            messages.error(request, "File not found.")

        screenshot.delete()
        return redirect(request.META.get('HTTP_REFERER', 'home'))  # Перезагрузка текущей страницы