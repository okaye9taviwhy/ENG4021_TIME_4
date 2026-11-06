from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Esporte, PerfilEsporte


class SugestoesParceirosTests(TestCase):
    """Testes da página de sugestões de parceiros."""

    def setUp(self):
        self.volei = Esporte.objects.create(nome="Vôlei de praia")
        self.beach = Esporte.objects.create(nome="Beach tennis")
        self.futsal = Esporte.objects.create(nome="Futsal")

        # Eu jogo vôlei no intermediário e beach tennis no iniciante
        self.eu = self.jogador("eu", "Gui Stern", [
            (self.volei, "Intermediário"),
            (self.beach, "Iniciante"),
        ])

        self.url = reverse("sugestoes_parceiros")
        self.client.force_login(self.eu)

    def jogador(self, username, nome, esportes, ativo=True):
        primeiro, sobrenome = nome.split()
        usuario = User.objects.create_user(
            username=username, password="senha123",
            first_name=primeiro, last_name=sobrenome, is_active=ativo,
        )
        for esporte, nivel in esportes:
            PerfilEsporte.objects.create(usuario=usuario, esporte=esporte, nivel=nivel)
        return usuario

    def sugeridos(self):
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, 200)
        return [s["usuario"].username for s in resposta.context["sugestoes"]]

    # Rota e acesso

    def test_rota(self):
        self.assertEqual(self.url, "/sugestoes/")

    def test_pagina_pede_login(self):
        self.client.logout()
        resposta = self.client.get(self.url)
        self.assertRedirects(resposta, f"{settings.LOGIN_URL}?next={self.url}")

    # Quem aparece e em que ordem

    def test_ordem_das_sugestoes(self):
        self.jogador("ana", "Ana Silva", [(self.volei, "Intermediário")])
        self.jogador("bruno", "Bruno Costa", [(self.volei, "Avançado")])
        self.jogador("carla", "Carla Dias", [
            (self.volei, "Iniciante"),
            (self.beach, "Iniciante"),
        ])

        # Carla: mesmo nível no beach tennis e 2 esportes em comum
        # Ana: mesmo nível no vôlei, 1 esporte em comum
        # Bruno: só nível vizinho
        self.assertEqual(self.sugeridos(), ["carla", "ana", "bruno"])

    def test_nao_sugere_nivel_muito_diferente(self):
        # Eu sou iniciante no beach tennis; avançado está a 2 níveis
        self.jogador("davi", "Davi Lopes", [(self.beach, "Avançado")])
        self.assertEqual(self.sugeridos(), [])

    def test_nao_sugere_esporte_que_eu_nao_jogo(self):
        self.jogador("edu", "Edu Reis", [(self.futsal, "Intermediário")])
        self.assertEqual(self.sugeridos(), [])

    def test_nao_sugere_conta_desativada_nem_eu_mesmo(self):
        self.jogador("fabi", "Fabi Melo", [(self.volei, "Intermediário")], ativo=False)
        self.assertEqual(self.sugeridos(), [])

    def test_jogador_aparece_uma_vez_com_todos_os_esportes_em_comum(self):
        self.jogador("carla", "Carla Dias", [
            (self.volei, "Intermediário"),
            (self.beach, "Iniciante"),
        ])

        resposta = self.client.get(self.url)
        sugestoes = resposta.context["sugestoes"]

        self.assertEqual(len(sugestoes), 1)
        self.assertEqual(len(sugestoes[0]["esportes"]), 2)

    def test_mostra_selo_de_nivel(self):
        self.jogador("ana", "Ana Silva", [(self.volei, "Intermediário")])
        self.jogador("bruno", "Bruno Costa", [(self.volei, "Avançado")])

        resposta = self.client.get(self.url)

        self.assertContains(resposta, "Mesmo nível que você")
        self.assertContains(resposta, "Nível próximo do seu")

    def test_limite_de_sugestoes(self):
        for numero in range(15):
            self.jogador(f"jogador{numero}", f"Jogador N{numero}", [(self.volei, "Intermediário")])

        self.assertEqual(len(self.sugeridos()), 12)

    # Avisos quando não há sugestões

    def test_sem_esportes_no_perfil(self):
        novato = User.objects.create_user(username="novato", password="senha123")
        self.client.force_login(novato)

        resposta = self.client.get(self.url)

        self.assertContains(resposta, "Seu perfil ainda não tem esportes")

    def test_sem_jogador_compativel(self):
        resposta = self.client.get(self.url)
        self.assertContains(resposta, "Nenhum jogador compatível por enquanto")

    # Ligação com Encontrar Parceiros

    def test_encontrar_parceiros_tem_link_para_sugestoes(self):
        resposta = self.client.get(reverse("encontrar_parceiros"))
        self.assertContains(resposta, f'href="{self.url}"')
