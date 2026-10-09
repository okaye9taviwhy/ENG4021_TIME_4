from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render, redirect
from django.contrib.auth.models import User

from .models import PerfilUsuario


@login_required
def editar_usuario(request):
    usuario = request.user

    perfil, criado = PerfilUsuario.objects.get_or_create(
        usuario=usuario
    )

    if request.method == "POST":
        nome = request.POST.get("nome", "").strip()
        email = request.POST.get("email", "").strip()
        foto = request.POST.get("foto", "").strip()
        senha = request.POST.get("senha", "")

        if not nome or not email:
            messages.error(request, "Preencha o nome e o e-mail.")
        elif User.objects.filter(email=email).exclude(pk=usuario.pk).exists():
            messages.error(request, "Este e-mail já está em uso.")
        else:
            partes_nome = nome.split(maxsplit=1)

            usuario.first_name = partes_nome[0]
            usuario.last_name = partes_nome[1] if len(partes_nome) > 1 else ""
            usuario.email = email
            usuario.save()

            perfil.foto = foto
            perfil.save()

            if senha:
                usuario.set_password(senha)
                usuario.save()
                update_session_auth_hash(request, usuario)

            messages.success(request, "Perfil atualizado com sucesso!")
            return redirect("editar_usuario")

    return render(
        request,
        "editar_usuario.html",
        {
            "usuario": usuario,
            "foto": perfil.foto,
        },
    )
    
