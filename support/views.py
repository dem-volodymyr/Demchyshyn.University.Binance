from .utils import generate_ai_response  # Add this import
from django.core.mail import send_mail
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Ticket, FAQ
from .forms import CommentForm


@login_required
def ticket_list(request):
    """Display all tickets for the logged-in user"""
    tickets = Ticket.objects.filter(user=request.user)
    return render(request, 'support/ticket_list.html', {'tickets': tickets})


# Keep other view functions below this

def faq_list(request):
    faqs = FAQ.objects.all()
    return render(request, 'support/faq_list.html', {'faqs': faqs})


def ticket_detail(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.ticket = ticket
            comment.user = request.user
            comment.save()
            generate_ai_response(ticket, comment)  # Trigger AI response на новий коментар
            return redirect('ticket_detail', pk=ticket.pk)
    else:
        comment_form = CommentForm()
    return render(request, 'support/ticket_detail.html', {'ticket': ticket, 'comment_form': comment_form})


def create_ticket(request):
    if request.method == 'POST':
        title = request.POST['title']
        description = request.POST['description']
        ticket = Ticket.objects.create(
            title=title,
            description=description,
            user=request.user,
            status='open'
        )
        # Trigger AI response immediately
        from .utils import generate_ai_response
        generate_ai_response(ticket)
        return redirect('ticket_detail', pk=ticket.pk)
    return render(request, 'support/create_ticket.html')


def contact(request):
    if request.method == 'POST':
        user = request.user
        name = user.username
        email = user.email
        message = request.POST['message']
        send_mail(
            f'Support Request from {name}',
            message,
            email,
            ['xchangeua@gmail.com'],
            fail_silently=False,
        )
        return redirect('contact')  # Redirect after POST
    return render(request, 'support/contact.html')
