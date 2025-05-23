from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Profile
from .forms import ProfileForm

@login_required
def profile_view(request):
    user = request.user
    profile, created = Profile.objects.get_or_create(user=user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            # Update User fields
            user.first_name = form.cleaned_data.get('first_name', user.first_name)
            user.last_name = form.cleaned_data.get('last_name', user.last_name)
            user.email = form.cleaned_data.get('email', user.email)
            user.save()
            profile.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        initial = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
        }
        form = ProfileForm(instance=profile, initial=initial)
    return render(request, 'profile.html', {'form': form, 'user': user})