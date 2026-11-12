from django.urls import path
from core import views

urlpatterns = [
    path("login/", views.login_usuario, name="login_usuario"),
]