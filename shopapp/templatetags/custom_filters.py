from django import template

register = template.Library()

@register.filter
def length_is(value, length):
    """
    Проверяет, соответствует ли длина строки заданному значению.
    """
    try:
        return len(value) == int(length)
    except (ValueError, TypeError):
        return False
