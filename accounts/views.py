from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import CreateView, FormView
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator

from .models import RecruiterProfile


class RegisterView(CreateView):
    """User registration view"""
    form_class = UserCreationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('dashboard:index')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Create recruiter profile
        RecruiterProfile.objects.create(user=self.object)
        login(self.request, self.object)
        messages.success(self.request, 'Welcome to Hire Smart! Your account has been created.')
        return response


class LoginView(FormView):
    """User login view"""
    form_class = AuthenticationForm
    template_name = 'accounts/login.html'
    success_url = reverse_lazy('dashboard:index')

    def form_valid(self, form):
        login(self.request, form.get_user())
        messages.success(self.request, f'Welcome back, {form.get_user().username}!')
        return super().form_valid(form)


def logout_view(request):
    """User logout view"""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('landing')


@login_required
def profile(request):
    """User profile view"""
    profile, created = RecruiterProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        profile.company_name = request.POST.get('company_name', '')
        profile.designation = request.POST.get('designation', '')
        profile.phone = request.POST.get('phone', '')
        profile.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('accounts:profile')

    context = {'profile': profile}
    return render(request, 'accounts/profile.html', context)