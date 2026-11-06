from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Interesse, Match


class MeusInteressesTests(TestCase):
    """Testes da página de interesses recebidos e enviados."""

    def setUp(self):
        self.eu = User.objects.create_user(
            username="eu", password="senha123",
            first_name="Gui", last_name="Stern",
        )
        self.ana = User.objects.create_user(
            username="ana", password="senha123",
            first_name="Ana", last_name="Silva",
        )
        self.bruno = User.objects.create_user(
            username="bruno", password="senha123",
            first_name="Bruno", last_name="Costa",
        )
        self.url = reverse("meus_interesses")
        self.client.force_login(self.eu)

    def responder(self, interesse, resposta):
        return self.client.post(
            reverse("responder_interesse", args=[interesse.id]),
            {"resposta": resposta},
        )

    # Rotas e acesso

    def test_rotas(self):
        self.assertEqual(self.url, "/interesses/")
        self.assertEqual(
            reverse("responder_interesse", args=[7]), "/interesses/7/responder/"
        )

    def test_pagina_pede_login(self):
        self.client.logout()
        resposta = self.client.get(self.url)
        self.assertRedirects(resposta, f"{settings.LOGIN_URL}?next={self.url}")

    # Lista

    def test_mostra_recebidos_e_enviados(self):
        Interesse.objects.create(usuario_origem=self.ana, usuario_destino=self.eu)
        Interesse.objects.create(usuario_origem=self.eu, usuario_destino=self.bruno)
        Interesse.objects.create(usuario_origem=self.ana, usuario_destino=self.bruno)

        resposta = self.client.get(self.url)

        recebidos = [i.usuario_origem for i in resposta.context["recebidos"]]
        enviados = [i.usuario_destino for i in resposta.context["enviados"]]
        self.assertEqual(recebidos, [self.ana])
        self.assertEqual(enviados, [self.bruno])
        self.assertEqual(resposta.context["pendentes"], 1)
        self.assertContains(resposta, "1 para responder")
        self.assertContains(resposta, "Aguardando resposta")

    def test_pagina_vazia(self):
        resposta = self.client.get(self.url)
        self.assertContains(resposta, "Ninguém demonstrou interesse ainda")
        self.assertContains(resposta, "Você ainda não demonstrou interesse em ninguém")

    # Responder

    def test_aceitar_cria_match(self):
        interesse = Interesse.objects.create(usuario_origem=self.ana, usuario_destino=self.eu)

        resposta = self.responder(interesse, "aceito")

        self.assertRedirects(resposta, self.url)
        interesse.refresh_from_db()
        self.assertEqual(interesse.status, "aceito")
        self.assertTrue(
            Match.objects.filter(usuario_1=self.ana, usuario_2=self.eu).exists()
        )

    def test_aceitar_nao_duplica_match(self):
        Match.objects.create(usuario_1=self.eu, usuario_2=self.ana)
        interesse = Interesse.objects.create(usuario_origem=self.ana, usuario_destino=self.eu)

        self.responder(interesse, "aceito")

        self.assertEqual(Match.objects.count(), 1)

    def test_recusar(self):
        interesse = Interesse.objects.create(usuario_origem=self.ana, usuario_destino=self.eu)

        self.responder(interesse, "recusado")

        interesse.refresh_from_db()
        self.assertEqual(interesse.status, "recusado")
        self.assertEqual(Match.objects.count(), 0)

    def test_nao_responde_duas_vezes(self):
        interesse = Interesse.objects.create(
            usuario_origem=self.ana, usuario_destino=self.eu, status="recusado"
        )

        self.responder(interesse, "aceito")

        interesse.refresh_from_db()
        self.assertEqual(interesse.status, "recusado")
        self.assertEqual(Match.objects.count(), 0)

    def test_resposta_invalida_nao_muda_nada(self):
        interesse = Interesse.objects.create(usuario_origem=self.ana, usuario_destino=self.eu)

        self.responder(interesse, "talvez")

        interesse.refresh_from_db()
        self.assertEqual(interesse.status, "pendente")

    def test_abrir_link_de_responder_nao_muda_nada(self):
        interesse = Interesse.objects.create(usuario_origem=self.ana, usuario_destino=self.eu)

        resposta = self.client.get(reverse("responder_interesse", args=[interesse.id]))

        self.assertRedirects(resposta, self.url)
        interesse.refresh_from_db()
        self.assertEqual(interesse.status, "pendente")

    # Segurança

    def test_so_quem_recebeu_pode_responder(self):
        # O interesse é da Ana para o Bruno. Eu não posso aceitar por ele.
        interesse = Interesse.objects.create(usuario_origem=self.ana, usuario_destino=self.bruno)

        resposta = self.responder(interesse, "aceito")

        self.assertEqual(resposta.status_code, 404)
        interesse.refresh_from_db()
        self.assertEqual(interesse.status, "pendente")

    def test_quem_enviou_nao_pode_aceitar_o_proprio_interesse(self):
        interesse = Interesse.objects.create(usuario_origem=self.eu, usuario_destino=self.ana)

        resposta = self.responder(interesse, "aceito")

        self.assertEqual(resposta.status_code, 404)
        self.assertEqual(Match.objects.count(), 0)

    # Ligação com Encontrar Parceiros

    def test_encontrar_parceiros_tem_link_para_interesses(self):
        resposta = self.client.get(reverse("encontrar_parceiros"))
        self.assertContains(resposta, f'href="{self.url}"')
