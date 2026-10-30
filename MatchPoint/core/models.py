
from django.conf import settings
from django.db import models


class PerfilUsuario(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil"
    )
    foto = models.URLField(blank=True)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )

    def __str__(self):
        return self.usuario.username


class Esporte(models.Model):
    nome = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nome


class PerfilEsporte(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="esportes"
    )
    esporte = models.ForeignKey(
        Esporte,
        on_delete=models.CASCADE,
        related_name="perfis"
    )
    nivel = models.CharField(max_length=50)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "esporte"],
                name="usuario_esporte_unico"
            )
        ]

    def __str__(self):
        return f"{self.usuario.username} - {self.esporte.nome}"


class Match(models.Model):
    usuario_1 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="matches_como_usuario_1"
    )
    usuario_2 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="matches_como_usuario_2"
    )
    data_hora = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Match {self.id}"


class Conversa(models.Model):
    match = models.OneToOneField(
        Match,
        on_delete=models.CASCADE,
        related_name="conversa"
    )

    def __str__(self):
        return f"Conversa {self.id}"


class Mensagem(models.Model):
    conversa = models.ForeignKey(
        Conversa,
        on_delete=models.CASCADE,
        related_name="mensagens"
    )
    remetente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mensagens_enviadas"
    )
    texto = models.TextField()
    data_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["data_hora"]

    def __str__(self):
        return f"Mensagem {self.id}"


class Interesse(models.Model):
    usuario_origem = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="interesses_enviados"
    )
    usuario_destino = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="interesses_recebidos"
    )
    status = models.CharField(max_length=30, default="pendente")
    data_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["usuario_origem", "usuario_destino"],
                name="interesse_origem_destino_unico"
            )
        ]

    def __str__(self):
        return f"{self.usuario_origem} -> {self.usuario_destino}"

class Equipe(models.Model):
    nome = models.CharField(max_length=100)
    esporte = models.ForeignKey(Esporte, on_delete=models.CASCADE)
    criador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return self.nome


class ParticipacaoEquipe(models.Model):
    equipe = models.ForeignKey(Equipe, on_delete=models.CASCADE)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    status = models.CharField(max_length=20, default="pendente")

    def __str__(self):
        return self.usuario.username
