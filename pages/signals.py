from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Task,UserTask, Enrollment, Submission, StudentActivity, Notification

@receiver(post_save, sender=Enrollment)
def create_enrollment_notification(sender, instance, created, **kwargs):
    if created:
        # Logic to create a notification for the user
        Notification.objects.create(
            recipient=instance.course.owner,
            notification_type='enrollment',
            title=f"New Enrollment in {instance.course.name}",
            message=f"{instance.user.get_full_name()} has enrolled in {instance.course.name}.",
            related_course=instance.course,
            related_enrollment=instance,
        )
    
@receiver(post_save, sender=StudentActivity):
def create_activity_notification(sender, instance, created, **kwargs):
    if created if instance.activity_type in ['assignment_submit', 'quiz_attempt'] else False:
        # Logic to create a notification for the user
        Notification.objects.create(
            recipient=instance.course.owner,
            notification_type='progress',
            title=f"New {instance.get_activity_type_display()} in {instance.course.name}",
            message=f"{instance.user.get_full_name()} submitted {instance.title}.",
            related_course=instance.course,
        )