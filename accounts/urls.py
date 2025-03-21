from django.urls import path

from .views import admin_dashboard, mail_inbox, sent_mail, mail_draft, mail_compose

app_name = 'account'

urlpatterns = [
    path('user/mail/inbox/', mail_inbox, name='mail_inbox'),
    path('user/mail/sent', sent_mail, name='sent_mail'),
    path('user/mail/drafts', mail_draft, name='mail_draft'),
    path('user/mail/compose', mail_compose, name='mail_compose'),
    path('user/admin/dashboard/', admin_dashboard, name='dashboard')
]