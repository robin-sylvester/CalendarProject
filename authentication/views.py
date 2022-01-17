from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import generic

from authentication.forms import SignUpForm

from django.contrib.auth import get_user_model

User = get_user_model()


class SignUpView(generic.CreateView):
    form_class = SignUpForm
    model = User
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'
