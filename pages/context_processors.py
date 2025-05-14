from .models import Course, Enrollment

from .models import Course


def notifications(request):
    if request.user.is_authenticated:
        return {
            'unread_notifications': request.user.notifications.filter(is_read=False).count(),
            'recent_notifications': request.user.notifications.all()[:5]
        }
    return {}

def enrollment_count(request):
    if request.user and request.user.is_authenticated:
        instructor_courses = Course.objects.filter(owner=request.user)
        enrollment_count = Enrollment.objects.filter(course__in=instructor_courses).select_related('student', 'course').count()
        return {
            'enrollment_count': enrollment_count
        }
    return {}

def is_instructor(request):
    if request.user and request.user.is_authenticated:
        return {
            'is_instructor': request.user.groups.filter(name='Instructor').exists()
        }
    return {}