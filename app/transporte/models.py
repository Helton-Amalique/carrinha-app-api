"""Models para base de dados de  transporte"""
import datetime
from datetime import date
from decimal import Decimal
from django.db import models
from core.models import Aluno
from django.db.models import Q
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, MinValueValidator, EmailValidator
from phonenumber_field.modelfields import PhoneNumberField

validar_placa = RegexValidator(
    regex=r'^[A-Z]{2,3}-\d{1,4}(-[A-Z]{1,2})?$',
    message='Placa inválida. Ex: ABC-1234 ou ABC-123-XY'
)

validar_email = EmailValidator(message="Email invalido")


class ActivoManager(models.Manager):
    def ativos(self):
        return self.filter(ativo=True)


class Veiculo(models.Model):
    marca = models.CharField(max_length=20)
    modelo = models.CharField(max_length=50)
    matricula = models.CharField(max_length=20, unique=True, validators=[validar_placa], db_index=True, help_text="Placa de matricula do veiculo")
    capacidade = models.PositiveIntegerField(validators=[MinValueValidator(1)], help_text="Numero maximo de Passageiros")
    motorista = models.ForeignKey(
        "core.Motorista",
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="veiculos"
    )
    ativo = models.BooleanField(default=True, db_index=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    objects = ActivoManager()

    class Meta:
        verbose_name = 'Veículo'
        verbose_name_plural = 'Veículos'
        ordering = ['matricula']

    def save(self, *args, **kwargs):
        if self.marca:
            self.marca = self.marca.strip().title()
        if self.modelo:
            self.modelo = self.modelo.strip().title()
        if self.matricula:
            self.matricula = self.matricula.strip().upper()
        super().save(*args, **kwargs)

    @property
    def vagas_disponiveis(self):
        """Retorna o número de lugares disponíveis no veículo."""
        # Assumindo que a relação inversa de Aluno para Rota é 'alunos'
        # e que o Veiculo so pode ter uma rota
        rota_unica = self.rotas.first()
        if not rota_unica:
            return self.capacidade
        alunos_na_rota = rota_unica.alunos.count()
        return max(self.capacidade - alunos_na_rota, 0)

    def __str__(self):
        return f'{self.modelo} - {self.matricula}'


class Rota(models.Model):
    """Informações sobre a rota da carrinha escolar"""
    nome = models.CharField(max_length=255, db_index=True)
    veiculo = models.ForeignKey(Veiculo, on_delete=models.PROTECT, related_name="rotas")
    hora_partida = models.TimeField(default=datetime.time(5, 30))
    hora_chegada = models.TimeField(default=datetime.time(7, 0))
    descricao = models.TextField(blank=True, null=True)
    alunos = models.ManyToManyField(Aluno, related_name='rotas_transporte')
    ativo = models.BooleanField(default=True, db_index=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Rota'
        verbose_name_plural = 'Rotas'
        ordering = ["nome"]

    def clean(self):
        super().clean()
        if self.veiculo and not self.veiculo.motorista:
            raise ValidationError({'veiculo': 'O veículo selecionado não tem um motorista atribuído.'})
        if self.veiculo and not self.veiculo.ativo:
            raise ValidationError({'veiculo': 'O veiculo selecionado esta inativo.'})
        if self.hora_chegada <= self.hora_partida:
            raise ValidationError({'hora_chegada': 'A hora de chegada deve ser posterior a hora de partida.'})
        # if self.veiculo and self.alunos.count() > self.veiculo.capacidade:
        #     raise ValidationError({'alunos': 'Numero de alunos excede a capacidade do veiculo'})
        if self.veiculo and self.veiculo.rotas.filter(ativo=True).exclude(pk=self.pk).exists():
            raise ValidationError({'veiculo': 'Este veiculo ja possui uma rota ativa. '})

    @property
    def motorista(self):
        """retorna o motorista do veiculo da rota, se houver"""
        return self.veiculo.motorista

    def __str__(self):
        return f"Rota: {self.nome} - Veiculo: {self.veiculo.matricula}"
