from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
import requests

# Create your views here.


# Create your views here.
def home(request):
    return render(request, "home.html")


def register(request):
    return render(request, "register.html")


def callback_view(request):
    return redirect(reverse('table'))

