from django.shortcuts import render, redirect
from blog.forms import RegisterForm
from django.contrib.auth import login


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('blog:profile', username=user.username)
    else:
        form = RegisterForm()

    return render(
        request,
        'registration/registration_form.html',
        {'form': form},
    )
