from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("me/", views.me_view, name="me"),
    path("password-reset/", views.password_reset_view, name="password_reset"),
    path(
        "password-reset/confirm/",
        views.password_reset_confirm_view,
        name="password_reset_confirm",
    ),
]
