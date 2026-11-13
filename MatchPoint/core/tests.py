from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Esporte, Interesse, PerfilEsporte


class EncontrarParceirosTests(TestCase):
    """Testes da view e da rota de Encontrar Parceiros."""

    def setUp(self):
        self.volei = Esporte.objects.create(nome="Vôlei de praia")
        self.beach = Esporte.objects.create(nome="Beach tennis")

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

        PerfilEsporte.objects.create(
            usuario=self.eu, esporte=self.volei, nivel="Iniciante"
        )
        PerfilEsporte.objects.create(
            usuario=self.ana, esporte=self.volei, nivel="Avançado"
        )
        PerfilEsporte.objects.create(
            usuario=self.bruno, esporte=self.beach, nivel="Iniciante"
        )

        self.url = reverse("encontrar_parceiros")
        self.client.force_login(self.eu)

    def jogadores_na_pagina(self, **filtros):
        """Abre a página com os filtros e devolve os usuários listados."""
        resposta = self.client.get(self.url, filtros)
        self.assertEqual(resposta.status_code, 200)
        return sorted(
            perfil.usuario.username for perfil in resposta.context["jogadores"]
        )

    # Rota e acesso

    def test_rota(self):
        self.assertEqual(self.url, "/encontrar-parceiros/")

    def test_sem_login_vai_para_o_login(self):
        self.client.logout()
        resposta = self.client.get(self.url)
        self.assertRedirects(resposta, f"{settings.LOGIN_URL}?next={self.url}")

    def test_mostra_os_outros_jogadores_e_nao_o_proprio(self):
        resposta = self.client.get(self.url)
        self.assertTemplateUsed(resposta, "encontrar_parceiros.html")
        self.assertEqual(self.jogadores_na_pagina(), ["ana", "bruno"])

    # Filtros

    def test_filtro_por_esporte(self):
        self.assertEqual(
            self.jogadores_na_pagina(esporte=self.volei.id), ["ana"]
        )

    def test_filtro_por_nivel(self):
        self.assertEqual(self.jogadores_na_pagina(nivel="Iniciante"), ["bruno"])

    def test_filtros_invalidos_sao_ignorados(self):
        self.assertEqual(
            self.jogadores_na_pagina(esporte="abc", nivel="Profissional"),
            ["ana", "bruno"],
        )

    # Busca

    def test_busca_por_nome(self):
        self.assertEqual(self.jogadores_na_pagina(search="ana"), ["ana"])

    def test_busca_por_nome_completo(self):
        self.assertEqual(self.jogadores_na_pagina(search="Ana Silva"), ["ana"])

    def test_busca_sem_resultado_mostra_aviso(self):
        resposta = self.client.get(self.url, {"search": "Zé"})
        self.assertEqual(len(resposta.context["jogadores"]), 0)
        self.assertContains(resposta, "Nenhum jogador encontrado")

    # Demonstrar interesse

    def test_demonstrar_interesse(self):
        resposta = self.client.post(
            reverse("demonstrar_interesse", args=[self.ana.id])
        )
        self.assertRedirects(resposta, self.url)
        self.assertTrue(
            Interesse.objects.filter(
                usuario_origem=self.eu, usuario_destino=self.ana
            ).exists()
        )

    def test_demonstrar_interesse_duas_vezes_nao_duplica(self):
        url_interesse = reverse("demonstrar_interesse", args=[self.ana.id])
        self.client.post(url_interesse)
        self.client.post(url_interesse)
        self.assertEqual(Interesse.objects.count(), 1)

    def test_nao_pode_demonstrar_interesse_em_si_mesmo(self):
        self.client.post(reverse("demonstrar_interesse", args=[self.eu.id]))
        self.assertEqual(Interesse.objects.count(), 0)
