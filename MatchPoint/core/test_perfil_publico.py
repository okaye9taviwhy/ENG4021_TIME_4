from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Esporte, Interesse, PerfilEsporte


class PerfilPublicoTests(TestCase):
    """Testes da página de perfil público do jogador."""

    def setUp(self):
        self.volei = Esporte.objects.create(nome="Vôlei de praia")
        self.beach = Esporte.objects.create(nome="Beach tennis")

        self.eu = User.objects.create_user(
            username="eu", password="senha123",
            first_name="Gui", last_name="Stern",
        )
        self.ana = User.objects.create_user(
            username="ana", password="senha123", email="ana@exemplo.com",
            first_name="Ana", last_name="Silva",
        )
        PerfilEsporte.objects.create(usuario=self.eu, esporte=self.volei, nivel="Iniciante")
        PerfilEsporte.objects.create(usuario=self.ana, esporte=self.volei, nivel="Avançado")
        PerfilEsporte.objects.create(usuario=self.ana, esporte=self.beach, nivel="Iniciante")

        self.url_ana = reverse("perfil_publico", args=[self.ana.id])
        self.url_interesse = reverse("demonstrar_interesse", args=[self.ana.id])
        self.client.force_login(self.eu)

    # Rota e acesso

    def test_rota(self):
        self.assertEqual(self.url_ana, f"/jogador/{self.ana.id}/")

    def test_pagina_pede_login(self):
        self.client.logout()
        resposta = self.client.get(self.url_ana)
        self.assertRedirects(resposta, f"{settings.LOGIN_URL}?next={self.url_ana}")

    def test_jogador_que_nao_existe(self):
        resposta = self.client.get(reverse("perfil_publico", args=[9999]))
        self.assertEqual(resposta.status_code, 404)

    def test_conta_desativada_nao_aparece(self):
        self.ana.is_active = False
        self.ana.save()
        resposta = self.client.get(self.url_ana)
        self.assertEqual(resposta.status_code, 404)

    # Conteúdo

    def test_mostra_nome_e_esportes_em_ordem(self):
        resposta = self.client.get(self.url_ana)

        self.assertContains(resposta, "Ana Silva")
        esportes = [p.esporte.nome for p in resposta.context["esportes"]]
        self.assertEqual(esportes, ["Beach tennis", "Vôlei de praia"])
        self.assertContains(resposta, "Avançado")

    def test_nao_mostra_email(self):
        resposta = self.client.get(self.url_ana)
        self.assertNotContains(resposta, "ana@exemplo.com")

    def test_marca_esportes_em_comum(self):
        resposta = self.client.get(self.url_ana)
        self.assertContains(resposta, "Você também joga", count=1)

    def test_jogador_sem_esportes(self):
        novato = User.objects.create_user(username="novato", password="senha123")
        resposta = self.client.get(reverse("perfil_publico", args=[novato.id]))
        self.assertContains(resposta, "Ainda não adicionou esportes ao perfil.")

    # Botões

    def test_mostra_botao_de_interesse(self):
        resposta = self.client.get(self.url_ana)
        self.assertContains(resposta, f'action="{self.url_interesse}"')

    def test_interesse_ja_enviado(self):
        Interesse.objects.create(usuario_origem=self.eu, usuario_destino=self.ana)

        resposta = self.client.get(self.url_ana)

        self.assertContains(resposta, "Interesse enviado")
        self.assertNotContains(resposta, f'action="{self.url_interesse}"')

    def test_avisa_quando_o_jogador_tem_interesse_em_mim(self):
        Interesse.objects.create(usuario_origem=self.ana, usuario_destino=self.eu)
        resposta = self.client.get(self.url_ana)
        self.assertContains(resposta, "Ana tem interesse em jogar com você!")

    def test_meu_proprio_perfil(self):
        resposta = self.client.get(reverse("perfil_publico", args=[self.eu.id]))

        self.assertContains(resposta, "Este é o seu perfil")
        self.assertContains(resposta, f'href="{reverse("editar_usuario")}"')
        self.assertNotContains(resposta, "Tenho interesse")
        self.assertNotContains(resposta, "Você também joga")

    # Ligação com Encontrar Parceiros

    def test_encontrar_parceiros_tem_link_para_o_perfil(self):
        resposta = self.client.get(reverse("encontrar_parceiros"))
        self.assertContains(resposta, f'href="{self.url_ana}"')
