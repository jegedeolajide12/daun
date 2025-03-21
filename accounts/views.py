from django.shortcuts import render

# Create your views here.

def admin_dashboard(request):
    context = {}
    return render(request, 'account/admin/dashboard.html', context)

def mail_inbox(request):
    context = {}
    return render(request, 'account/mail/mail_inbox.html', context)

def sent_mail(request):
    context = {}
    return render(request, 'account/mail/sent_mail.html', context)

def mail_draft(request):
    context = {}
    return render(request, 'account/mail/mail_draft.html', context)


def mail_compose(request):
    context = {}
    return render(request, 'account/mail/mail_compose.html', context)
