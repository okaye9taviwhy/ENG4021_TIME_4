"""
URL configuration for MatchPoint project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from django.urls.conf import include

from core import views



urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),
    path("editar-usuario/", views.editar_usuario, name="editar_usuario"),
    path("cadastro/", views.cadastro_usuario, name="cadastro"),
    path("usuarios/", views.lista_de_usuarios, name="lista_de_usuarios"),
    path("remover-usuario/", views.remover_usuario, name="remover_usuario"),

    path("accounts/", include("django.contrib.auth.urls")),
    path("usuario/", include("usuario.urls")),

    path("encontrar-parceiros/", views.encontrar_parceiros, name="encontrar_parceiros"),
    path("interesse/<int:usuario_id>/", views.demonstrar_interesse, name="demonstrar_interesse"),
    path("agendar-quadras/", views.agendar_quadras, name="agendar_quadras"),
    path("amistosos/", views.amistosos, name="amistosos"),
    # Sistema de equipes
    path("equipes/", views.equipes, name="equipes"),
    path(
        "trocar-jogador/",
        views.trocar_jogador,
        name="trocar_jogador"
    ),
    path(
        "solicitar-entrada/<int:equipe_id>/",
        views.solicitar_entrada,
        name="solicitar_entrada"
    ),
    path(
        "responder-solicitacao/<int:participacao_id>/",
        views.responder_solicitacao,
        name="responder_solicitacao"
    ),
    path(
    "perfil-equipe/<int:usuario_id>/",
    views.perfil_equipe,
    name="perfil_equipe"
    ),
]


