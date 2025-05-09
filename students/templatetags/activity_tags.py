from django import template

register = template.Library()

@register.filter(name='activity_color')
def activity_color(activity_type):
    color_map = {
        'module_complete': 'success',
        'quiz_attempt': 'info',
        'assignment_submit': 'warning',
        'forum_post': 'primary',
        'message': 'secondary'
    }
    return color_map.get(activity_type, 'light')