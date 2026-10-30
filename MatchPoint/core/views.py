from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.db import IntegrityError, transaction
from .models import (
    PerfilUsuario, Esporte, PerfilEsporte,
    Interesse, Equipe, ParticipacaoEquipe
)
from django.conf import settings

@login_required
def editar_usuario(request):
    usuario = request.user
    perfil, criado = PerfilUsuario.objects.get_or_create(usuario=usuario)

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

    return render(request, "editar_usuario.html", {
        "usuario": usuario,
        "foto": perfil.foto,
    })


def login_usuario(request):
    erro = ""

    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        senha = request.POST.get("senha", "")

        try:
            usuario_email = User.objects.get(email=email)
        except User.DoesNotExist:
            usuario_email = None

        if usuario_email:
            usuario = authenticate(
                request,
                username=usuario_email.username,
                password=senha,
            )

            if usuario is not None:
                login(request, usuario)
                return redirect("home")

        erro = "E-mail ou senha incorretos."

    return render(request, "login.html", {"erro": erro})


def cadastro_usuario(request):
    erro = ""

    if request.method == "POST":
        nome = request.POST.get("nome", "").strip()
        email = request.POST.get("email", "").strip().lower()
        senha = request.POST.get("senha", "")
        confirmar_senha = request.POST.get("confirmar_senha", "")

        if not nome or not email or not senha:
            erro = "Preencha todos os campos."
        elif senha != confirmar_senha:
            erro = "As senhas não coincidem."
        elif User.objects.filter(email__iexact=email).exists():
            erro = "Este e-mail já está cadastrado."
        else:
            partes_nome = nome.split(maxsplit=1)

            try:
                with transaction.atomic():
                    usuario = User.objects.create_user(
                        username=email,
                        email=email,
                        password=senha,
                        first_name=partes_nome[0],
                        last_name=partes_nome[1] if len(partes_nome) > 1 else "",
                    )
                    PerfilUsuario.objects.create(usuario=usuario)

                login(request, usuario)
                return redirect("home")

            except IntegrityError:
                erro = "Não foi possível criar a conta. Tente novamente."

    return render(request, "cadastro.html", {"erro": erro})


def home(request):
    return render(request, "FigmaTela.html")


@login_required
def lista_de_usuarios(request):
    usuarios = User.objects.all().order_by("first_name")
    return render(request, "lista_de_usuarios.html", {
        "usuarios": usuarios,
    })


@login_required
def remover_usuario(request):
    if request.method == "POST":
        request.user.delete()
        return redirect("home")

    return render(request, "remover_usuario.html")



@login_required
def encontrar_parceiros(request):
    esporte_selecionado = request.GET.get("esporte", "")
    nivel_selecionado = request.GET.get("nivel", "")
    search_query = request.GET.get("search", "").strip()

    jogadores = (
        PerfilEsporte.objects
        .select_related("usuario", "esporte")
        .exclude(usuario=request.user)
    )

    if esporte_selecionado.isdigit():
        jogadores = jogadores.filter(
            esporte_id=int(esporte_selecionado)
        )

    if nivel_selecionado in [
        "Iniciante", "Intermediário", "Avançado"
    ]:
        jogadores = jogadores.filter(nivel=nivel_selecionado)

    if search_query:
        jogadores = jogadores.filter(
            usuario__first_name__icontains=search_query
        ) | jogadores.filter(
            usuario__last_name__icontains=search_query
        ) | jogadores.filter(
            usuario__username__icontains=search_query
        )

    return render(request, "encontrar_parceiros.html", {
        "jogadores": jogadores,
        "esportes": Esporte.objects.all().order_by("nome"),
        "esporte_selecionado": esporte_selecionado,
        "nivel_selecionado": nivel_selecionado,
        "search_query": search_query,
    })


@login_required
def demonstrar_interesse(request, usuario_id):
    if request.method != "POST":
        return redirect("encontrar_parceiros")

    jogador = get_object_or_404(User, pk=usuario_id)

    if jogador == request.user:
        messages.error(
            request,
            "Você não pode demonstrar interesse em si mesmo."
        )
    else:
        _, criado = Interesse.objects.get_or_create(
            usuario_origem=request.user,
            usuario_destino=jogador,
        )

        if criado:
            messages.success(
                request, "Interesse demonstrado com sucesso!"
            )
        else:
            messages.info(
                request,
                "Você já demonstrou interesse nessa pessoa."
            )

    return redirect("encontrar_parceiros")


@login_required
def agendar_quadras(request):
    quadras = [
        {
            "nome": "Rede do Posto 9",
            "esporte": "Vôlei de praia",
            "detalhes": "Dupla · 2 de 4 vagas · Todos os níveis",
            "horario": "Hoje · 17:00",
        },
        {
            "nome": "Quadra de Areia Copacabana",
            "esporte": "Beach tennis",
            "detalhes": "Dupla · 1 de 2 vagas · Intermediário",
            "horario": "Amanhã · 08:00",
        },
        {
            "nome": "Arena Leblon",
            "esporte": "Vôlei de praia",
            "detalhes": "4x4 · 3 de 8 vagas · Iniciante",
            "horario": "Sáb · 09:30",
        },
        {
            "nome": "Quadra de Saibro 3",
            "esporte": "Tênis",
            "detalhes": "Individual · 1 de 2 vagas · Intermediário",
            "horario": "Dom · 10:00",
        },
        {
            "nome": "Arena Central",
            "esporte": "Futsal",
            "detalhes": "5x5 · 7 de 10 vagas · Todos os níveis",
            "horario": "Sáb · 20:00",
        },
    ]

    return render(
        request,
        "agendar_quadras.html",
        {"quadras": quadras},
    )

@login_required
def amistosos(request):
    '''
    Esta função exibe os amistosos abertos para participação.
    Por enquanto os dados são de exemplo, porque ainda não existe
    uma tabela de amistosos no banco de dados.
    Ela utiliza a página amistosos.html para exibir os amistosos.
    '''
    amistosos = [
        {
            'nome': 'Furacão FC x Real Vizinhança',
            'esporte': 'Futsal',
            'detalhes': 'Faltam 2 jogadores · Intermediário · Arena Central',
            'horario': 'Sáb · 16:00',
        },
        {
            'nome': 'Torneio 4x4 de Verão',
            'esporte': 'Vôlei de praia',
            'detalhes': '8 times inscritos · Todos os níveis · Posto 9',
            'horario': 'Dom · 10:00',
        },
        {
            'nome': 'Praia Fest — Duplas',
            'esporte': 'Vôlei de praia',
            'detalhes': 'Faltam 3 duplas · Iniciante · Leblon',
            'horario': 'Sex · 18:00',
        },
        {
            'nome': 'Copa das Duplas Mistas',
            'esporte': 'Beach tennis',
            'detalhes': '6 duplas inscritas · Avançado · Copacabana',
            'horario': 'Qua · 19:30',
        },
        {
            'nome': 'Amistoso Vila Norte',
            'esporte': 'Futsal',
            'detalhes': 'Faltam 5 jogadores · Todos os níveis · Ginásio Vila Norte',
            'horario': 'Ter · 20:30',
        },
    ]
    contexto = {
        'amistosos': amistosos,
    }
    return render(request, 'amistosos.html', contexto)
# EQUIPES ESPORTIVAS - SPRINT 7


# Verificar se estamos testando no computador local
def teste_local(request):
    return settings.DEBUG and request.get_host().split(":")[0] in [
        "127.0.0.1", "localhost"
    ]


# Escolher qual jogador estamos simulando
def jogador_atual(request):

    nome = request.session.get("jogador", "ana")

    jogadores = {
        "ana": ("Ana", "Silva"),
        "pedro": ("Pedro", "Costa"),
        "julia": ("Julia", "Martins")
    }

    if nome not in jogadores:
        nome = "ana"

    primeiro_nome, sobrenome = jogadores[nome]

    usuario, criado = User.objects.get_or_create(
        username="teste_equipe_" + nome
    )

    if criado:
        usuario.first_name = primeiro_nome
        usuario.last_name = sobrenome
        usuario.set_unusable_password()
        usuario.save()

    return usuario


# Trocar de jogador
def trocar_jogador(request):

    if not teste_local(request):
        return redirect("home")

    if request.method == "POST":

        jogador = request.POST.get("jogador")

        if jogador in ["ana", "pedro", "julia"]:
            request.session["jogador"] = jogador

    return redirect("equipes")


# Página principal das equipes
def equipes(request):

    if not teste_local(request):
        return redirect("home")

    usuario = jogador_atual(request)

    # Criar equipe
    if request.method == "POST":

        nome = request.POST.get("nome", "").strip()
        esporte_id = request.POST.get("esporte")

        if nome and esporte_id:

            esporte = Esporte.objects.filter(id=esporte_id).first()

            if esporte:

                equipe = Equipe.objects.create(
                    nome=nome,
                    esporte=esporte,
                    criador=usuario
                )

                # O criador entra automaticamente na equipe
                ParticipacaoEquipe.objects.create(
                    equipe=equipe,
                    usuario=usuario,
                    status="aceito"
                )

                return redirect("equipes")

    lista_equipes = Equipe.objects.all()

    esportes = Esporte.objects.all()

    participacoes = ParticipacaoEquipe.objects.all()

    return render(request, "equipes.html", {
        "equipes": lista_equipes,
        "esportes": esportes,
        "participacoes": participacoes,
        "usuario_atual": usuario
    })


# Solicitar entrada em uma equipe
def solicitar_entrada(request, equipe_id):

    if not teste_local(request):
        return redirect("home")

    if request.method == "POST":

        usuario = jogador_atual(request)

        equipe = get_object_or_404(Equipe, id=equipe_id)

        if equipe.criador != usuario:

            participacao = ParticipacaoEquipe.objects.filter(
                equipe=equipe,
                usuario=usuario
            ).first()

            if participacao is None:

                ParticipacaoEquipe.objects.create(
                    equipe=equipe,
                    usuario=usuario,
                    status="pendente"
                )

            elif participacao.status == "recusado":

                participacao.status = "pendente"
                participacao.save()

    return redirect("equipes")


# Aceitar ou recusar jogadores
def responder_solicitacao(request, participacao_id):

    if not teste_local(request):
        return redirect("home")

    if request.method == "POST":

        usuario = jogador_atual(request)

        participacao = get_object_or_404(
            ParticipacaoEquipe,
            id=participacao_id
        )

        resposta = request.POST.get("resposta")

        # Apenas o criador pode responder
        if participacao.equipe.criador == usuario:

            if participacao.status == "pendente":

                if resposta == "aceito" or resposta == "recusado":

                    participacao.status = resposta
                    participacao.save()

    return redirect("equipes")

# Visualizar perfil de um jogador
def perfil_equipe(request, usuario_id):

    if not teste_local(request):
        return redirect("home")

    usuario = get_object_or_404(User, id=usuario_id)

    esportes = PerfilEsporte.objects.filter(usuario=usuario)

    return render(request, "perfil_equipe.html", {
        "usuario": usuario,
        "esportes": esportes
    })

