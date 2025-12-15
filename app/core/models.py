from django.db import models
from django.db.models import Q
from decimal import Decimal
from datetime import date
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser, BaseUserManager, Group, Permission
from django.core.validators import MinValueValidator, EmailValidator, RegexValidator
from phonenumber_field.modelfields import PhoneNumberField

validar_email = EmailValidator(message='Digite um email válido')


class UserManager(BaseUserManager):
    def create_user(self, email, nome, role=None, password=None, **extra_fields):
        if not email:
            raise ValidationError("O usuário deve ter um e-mail")
        if not role:
            raise ValidationError("O usuário deve ter um cargo definido (role)")
        if not password:
            raise ValidationError("O usuário deve ter uma senha definida")

        email = self.normalize_email(email).lower().strip()
        nome = nome.strip().title()

        user = self.model(email=email, nome=nome, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, nome, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        return self.create_user(email, nome, role="ADMIN", password=password, **extra_fields)


class User(AbstractUser):
    CARGO_CHOICES = [
        ("ADMIN", "Administrador"),
        ("ALUNO", "Aluno"),
        ("ENCARREGADO", "Encarregado"),
        ("MOTORISTA", "Motorista"),
    ]

    username = None
    email = models.EmailField(unique=True, validators=[validar_email])
    nome = models.CharField(max_length=30)
    role = models.CharField(max_length=20, choices=CARGO_CHOICES, default="ADMIN")

    salario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        default=Decimal("0.00"),
        help_text="Salário do usuário (se vazio, aplica valor padrão)."
    )
    data_criacao = models.DateTimeField(default=timezone.now, editable=False)
    data_atualizacao = models.DateTimeField(auto_now=True, editable=False)

    groups = models.ManyToManyField(
        Group,
        related_name="custom_user_groups",
        blank=True,
        help_text="Os grupos aos quais este usuário pertence."
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="custom_user_permissions",
        blank=True,
        help_text="Permissões específicas para este usuário."
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ["nome"]

    def save(self, *args, **kwargs):
        if self.nome:
            self.nome = self.nome.strip().title()
        if self.email:
            self.email = self.email.strip().lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nome} - {self.email} ({self.get_role_display()})"


class Encarregado(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to=Q(role="ENCARREGADO"),
        related_name="perfil_encarregado"
    )
    foto = models.ImageField(upload_to='fotos_encarregados/', blank=True, null=True)
    telefone = PhoneNumberField(region="MZ")
    nrBI = models.CharField(
        max_length=30,
        unique=True,
        db_index=True,
        validators=[RegexValidator(r'^\d{12}[A-Z]{1}$', "Formato inválido para BI")],
        help_text="Número de bilhete de identidade"
    )
    endereco = models.TextField(blank=True, null=True, help_text="bairro, Q, N da casa")
    ativo = models.BooleanField(default=True, db_index=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Encarregado: {self.user.nome} - {self.user.email}"


class Aluno(models.Model):
    """Perfil vinculado a um usuário com role=Aluno"""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to=Q(role="ALUNO"),
        related_name="perfil_aluno"
    )
    encarregado = models.ForeignKey(
        "core.Encarregado",
        on_delete=models.CASCADE,
        related_name='alunos',
    )
    foto = models.ImageField(upload_to='fotos_alunos/', blank=True, null=True)
    data_nascimento = models.DateField()
    nrBI = models.CharField(
        max_length=30,
        unique=True,
        db_index=True,
        validators=[RegexValidator(r'^\d{12}[A-Z]{1}$', "Formato inválido para BI")],
        help_text="Número de bilhete de identidade"
    )
    escola_dest = models.CharField(max_length=255, db_index=True)
    classe = models.CharField(max_length=25)
    mensalidade = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.0'))],
        default=Decimal('0.00')
    )
    ativo = models.BooleanField(default=True, db_index=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def clean(self):
        hoje = date.today()
        if self.data_nascimento > hoje:
            raise ValidationError({"data_nascimento": "A data de nascimento não pode ser no futuro."})

        idade = hoje.year - self.data_nascimento.year - (
            (hoje.month, hoje.day) < (self.data_nascimento.month, self.data_nascimento.day)
        )
        if idade < 3:
            raise ValidationError({"data_nascimento": "O aluno deve ter pelo menos 3 anos."})

    @property
    def idade(self):
        hoje = date.today()
        return hoje.year - self.data_nascimento.year - (
            (hoje.month, hoje.day) < (self.data_nascimento.month, self.data_nascimento.day)
        )

    def __str__(self):
        return f"Aluno: {self.user.nome} - {self.user.email}"


class Motorista(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to=Q(role="MOTORISTA"),
        related_name="perfil_motorista"
    )
    foto = models.ImageField(upload_to='fotos_motoristas/', blank=True, null=True)
    data_nascimento = models.DateField()
    nrBI = models.CharField(
        max_length=30,
        unique=True,
        db_index=True,
        validators=[RegexValidator(r'^\d{12}[A-Z]{1}$', "Formato inválido para BI")],
        help_text="Número de bilhete de identidade"
    )
    carta_conducao = models.CharField(
        max_length=30,
        unique=True,
        db_index=True,
        validators=[RegexValidator(r'^[A-Z0-9]{6,}$', "Formato inválido para carta de condução")],
        help_text="Número da carta de condução"
    )
    telefone = PhoneNumberField(region="MZ")
    endereco = models.TextField(blank=True, null=True, help_text="bairro, Quarteirão, Número da casa")
    ativo = models.BooleanField(default=True, db_index=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def clean(self):
        hoje = date.today()
        idade = hoje.year - self.data_nascimento.year - (
            (hoje.month, hoje.day) < (self.data_nascimento.month, self.data_nascimento.day)
        )
        if idade < 18:
            raise ValidationError({"data_nascimento": "O motorista deve ter pelo menos 18 anos."})

    def __str__(self):
        return f"Motorista: {self.user.nome} - {self.user.email}"

    def save(self, *args, **kwargs):
        if self.endereco:
            self.endereco = self.endereco.strip()
        super().save(*args, **kwargs)
