from django.urls import path
from allauth.account.views import EmailVerificationSentView

from .views import (admin_dashboard,
                     mail_inbox, 
                     sent_mail, 
                     mail_draft, 
                     mail_compose,
                    instructor_application,
                    verify_application,
                    reject_application,
                    instructors_list,
                    instructor_profile,
                    rate_instructor,
                    ) 

app_name = 'account'

urlpatterns = [
    path('user/mail/inbox/', mail_inbox, name='mail_inbox'),
    path('user/mail/sent', sent_mail, name='sent_mail'),
    path('user/mail/drafts', mail_draft, name='mail_draft'),
    path('user/mail/compose', mail_compose, name='mail_compose'),
    path('user/admin/dashboard/', admin_dashboard, name='dashboard'),

    path('user/instructor/application/', instructor_application, name='instructor_application'),
    path('user/instructor/list/', instructors_list, name='instructors_list'),
    path('user/instructor/profile/<int:instructor_id>/', instructor_profile, name='instructor_profile'),
    path('user/instructor/rate/<int:instructor_id>/', rate_instructor, name='rate_instructor'),
    path('user/instructor/verify/<int:application_id>/', verify_application, name='verify_application'),
    path('user/instructor/reject/<int:application_id>/', reject_application, name='reject_application'),
]