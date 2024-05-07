from django.core.mail import send_mail
from .models import Ticket
from .models import FAQ
from django.shortcuts import render, get_object_or_404, redirect
from .forms import CommentForm
from django.contrib.auth.models import User


def ticket_detail(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.ticket = ticket
            comment.user = request.user  # Make sure to set the user here
            comment.save()
            return redirect('ticket_detail', pk=ticket.pk)
    else:
        comment_form = CommentForm()
    return render(request, 'support/ticket_detail.html', {'ticket': ticket, 'comment_form': comment_form})


def faq_list(request):
    faqs = FAQ.objects.all()
    return render(request, 'support/faq_list.html', {'faqs': faqs})


def contact(request):
    if request.method == 'POST':
        user = request.user
        name = user.username
        email = user.email
        message = request.POST['message']
        send_mail('Support Request from {}'.format(name), message, email, ['xchangeua@gmail.com'])
    return render(request, 'support/contact.html')


def ticket_list(request):
    tickets = Ticket.objects.filter(user=request.user)
    return render(request, 'support/ticket_list.html', {'tickets': tickets})


def create_ticket(request):
    if request.method == 'POST':
        title = request.POST['title']
        description = request.POST['description']
        ticket = Ticket.objects.create(title=title, description=description, user=request.user)
        return redirect('ticket_list')
    return render(request, 'support/create_ticket.html')
