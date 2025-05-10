def notifications(request):
    if request.user.is_authenticated:
        return {
            'unread_notifications': request.user.notifications.filter(is_read=False).count(),
            'recent_notifications': request.user.notifications.all()[:5]
        }
    return {}

def enrollment_count(request):
    if request.user.is_authenticated:
        return {
            'enrollment_count': request.user.enrollments.filter(is_active=True).count()
        }
    return {}