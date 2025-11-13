from random import random
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LogoutView
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from django.views import View
from django.views.generic import TemplateView, CreateView, ListView, DetailView, UpdateView
from django.views.decorators.cache import cache_page

from django.http import HttpRequest, HttpResponse, JsonResponse, HttpResponseForbidden
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy

from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _, ngettext

from sqlalchemy import lambda_stmt

from .models import Profile


class HelloView(View):
    welcome_message = _("welcome hello world")

    def get(self, request: HttpRequest) -> HttpResponse:
        items_str = request.GET.get("items") or 0
        items = int(items_str)
        products_line = ngettext(
            "one product",
            "{count} products",
            items,
        )
        products_line = products_line.format(count=items)
        return HttpResponse(
            f"<h1>{self.welcome_message}</h1>"
            f"\n<h2>{products_line}</h2>"
        )


class AboutMeView(LoginRequiredMixin, UpdateView):
    model = Profile
    fields = ("avatar",)
    template_name = "myauth/about-me.html"
    success_url = reverse_lazy("myauth:about-me")

    def get_object(self, queryset=None):
        return self.request.user.profile


class RegisterView(CreateView):
    form_class = UserCreationForm
    template_name = 'myauth/register.html'
    success_url = reverse_lazy('myauth:about-me')

    def form_valid(self, form):
        response = super().form_valid(form)
        Profile.objects.create(user=self.object)

        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user = authenticate(
            self.request,
            username=username,
            password=password,
        )
        login(request=self.request, user=user)
        return response


@method_decorator(login_required, name='dispatch')
class AboutMeView(TemplateView):
    template_name = "myauth/about-me.html"

    def get(self, request):
        return render(request, self.template_name, {"profile": request.user.profile})

    def post(self, request):
        profile = request.user.profile
        avatar = request.FILES.get("avatar")
        if avatar:
            profile.avatar = avatar
            profile.save()
        return redirect("myauth:about-me")


class RegisterView(CreateView):
    form_class = UserCreationForm
    template_name = "myauth/register.html"
    success_url = reverse_lazy("myauth:about-me")

    def form_valid(self, form):
        response = super().form_valid(form)
        # Profile.objects.create(user=self.object)
        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password1")
        user = authenticate(
            self.request,
            username=username,
            password=password,
        )
        login(request=self.request, user=user)
        return response


class MyLogoutView(LogoutView):
    next_page = reverse_lazy("myauth:login")


@user_passes_test(lambda u: u.is_superuser)
def set_cookie_view(request: HttpRequest) -> HttpResponse:
    response = HttpResponse("Cookie set")
    response.set_cookie("fizz", "buzz", max_age=3600)
    return response


@cache_page(60 * 2)
def get_cookie_view(request: HttpRequest) -> HttpResponse:
    value = request.COOKIES.get("fizz", "default value")
    return HttpResponse(f"Cookie value: {value!r} + {random()}")


@permission_required("myauth.view_profile", raise_exception=True)
def set_session_view(request: HttpRequest) -> HttpResponse:
    request.session["foobar"] = "spameggs"
    return HttpResponse("Session set!")


@login_required
def get_session_view(request: HttpRequest) -> HttpResponse:
    value = request.session.get("foobar", "default")
    return HttpResponse(f"Session value: {value!r}")


class FooBarView(View):
    def get(self, request: HttpRequest) -> JsonResponse:
        return JsonResponse({"foo": "bar", "spam": "eggs"})


#User
class UsersListView(ListView):
    model = User
    template_name = 'myauth/users_list.html'
    context_object_name = 'users'


class UserProfileDetailView(DetailView):
    model = User
    template_name = 'myauth/profile.html'
    context_object_name = 'user_obj'


class UserProfileUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Profile
    fields = ("avatar",)
    template_name = "myauth/profile_update.html"
    success_url = reverse_lazy("myauth:users-list")

    def get_object(self, queryset=None):
        return Profile.objects.get(pk=self.kwargs["pk"])

    def test_func(self):
        return self.request.user == self.get_object().user

