from django import template
from datetime import datetime

register = template.Library()

@register.filter
def add_params(value, params):
    param_list = params.split(" ")
    attributes = {
        "class": param_list[0],
        "type": param_list[1] if len(param_list) > 1 else "text",
        "placeholder": param_list[2] if len(param_list) > 2 else ""
    }
    return value.as_widget(attrs=attributes)

@register.filter
def size_to_mb(value):
    try:
        return value / (1024 * 1024)  # Возвращаем число с плавающей запятой
    except (TypeError, ZeroDivisionError):
        return 0.0  # В случае ошибки возвращаем 0.0

