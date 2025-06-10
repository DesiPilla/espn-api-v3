from django import template

register = template.Library()


@register.filter(name="add")
def multiply(value, arg):
    return value + arg


@register.filter(name="multiply")
def multiply(value, arg):
    return value * arg


@register.filter(name="range")
def filter_range(start, end):
    return range(start, end)
