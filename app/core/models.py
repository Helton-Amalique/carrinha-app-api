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

validar_email = EmailValidator(message='Degite um email valido')


class Cargo(models.Model):
    """Define is cargos disponiveis e seus salarios padrao"""
    nome = models.CharField(max_length=50, unique=True)
    salario_padrao = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])

    def clean(self):
        super().clean()
        if not self.nome.strip():
            raise ValidationError({"nome": "O nome do cargo não pode estar vazio."})
        if self.salario_padrao is None:
            raise ValidationError({"salario_padrao": "Informe um salário padrão válido."})

    def __str__(self):
        return self.nome


class UserManager(BaseUserManager):
    def create_user(self, email, nome, role=None, password=None, **extra_fields):
        if not email:
            raise ValidationError("O usuário deve ter um e-mail")
        if not role:
            raise ValidationError("O usuário deve ter um papel definido em (role)")
        if not password:
            raise ValidationError("O usuário deve ter uma senha definida")

        # Aceita role como string (nome do Cargo) ou como instância
        if isinstance(role, str):
            try:
                role = Cargo.objects.get(nome=role)
            except Cargo.DoesNotExist:
                raise ValidationError(f"O Cargo '{role}' não existe. Crie o cargo antes de associá-lo a um usuário.")

        email = self.normalize_email(email).lower().strip()
        nome = nome.strip().title()

        user = self.model(email=email, nome=nome, role=role, **extra_fields)

        # Aplica salário padrão se não informado
        if not user.salario and role:
            user.salario = role.salario_padrao

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, nome, password=None, **extra_fields):
        admin_role, _ = Cargo.objects.get_or_create(
            nome="ADMIN",
            defaults={"salario_padrao": Decimal("0.00")}
        )

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        return self.create_user(email, nome, role=admin_role, password=password, **extra_fields)


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    nome = models.CharField(max_length=30)
    role = models.ForeignKey(Cargo, on_delete=models.PROTECT,
                             related_name='users', null=True, blank=True)
    salario = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Salário do usuário (se vazio, aplica valor padrão do cargo).")
    data_criacao = models.DateTimeField(default=timezone.now, editable=False)
    data_atualizacao = models.DateTimeField(auto_now=True, editable=False)

    groups = models.ManyToManyField(
        Group,
        related_name="custom_user_groups",  # nome único
        blank=True,
        help_text="Os grupos aos quais este usuário pertence."
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="custom_user_permissions",  # nome único
        blank=True,
        help_text="Permissões específicas para este usuário."
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ["nome"]

    def clean(self):
        super().clean()
        if self.pk:
            original_role = User.objects.filter(pk=self.pk).values_list("role_id", flat=True).first()
            if original_role != self.role_id:
                raise ValidationError({"role": "Nao e permitido alterar o cargo do usuario."})

        if self.email:
            self.email = self.email.strip().lower()

        if self.salario is None and self.role:
            self.salario = self.role.salario_padrao

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nome} ({self.role.nome if self.role else 'Sem Cargo'})"


class Encarregado(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to=Q(role__nome="ENCARREGADO"), related_name="perfil_encarregado")
    foto = models.ImageField(upload_to='fotos_encarregados/', blank=True, null=True)
    telefone = PhoneNumberField(region="MZ")
    nrBI = models.CharField(
        max_length=30,
        unique=True,
        validators=[RegexValidator(r'^\d{9}[A-Z]{2}$', "Formato inválido para BI")],
        help_text="Número de bilhete de identidade"
    )
    endereco = models.TextField(blank=True, null=True, help_text="bairro, Q, N da casa")
    ativo = models.BooleanField(default=True, db_index=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Encarregado: {self.user.nome}"

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Aluno(models.Model):
    """Informações de aluno"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to=Q(role__nome="ALUNO"), related_name="perfil_aluno")
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
        validators=[RegexValidator(r'^\d{9}[A-Z]{2}$', "Formato inválido para BI")],
        help_text="Número de bilhete de identidade"
    )
    escola_dest = models.CharField(max_length=255)
    classe = models.CharField(max_length=25)
    # rota = models.ForeignKey(
    #     'transporte.Rota',
    #     on_delete=models.PROTECT,  # Impede que a rota seja apagada se houver alunos nela
    #     related_name='alunos_core',
    #     null=True,
    #     blank=True
    # )
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

    def save(self, *args, **kwargs):
        if self.user.nome:
            self.user.nome = self.user.nome.strip().title()
        if self.user.email:
            self.user.email = self.user.email.lower().strip()

        if self.escola_dest:
            self.escola_dest = self.escola_dest.strip()
        if self.classe:
            self.classe = self.classe.strip()

        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def idade(self):
        hoje = date.today()
        return hoje.year - self.data_nascimento.year - (
            (hoje.month, hoje.day) < (self.data_nascimento.month, self.data_nascimento.day)
        )

    def __str__(self):
        return self.user.nome


class Motorista(models.Model):
    """Perfil do motorista, ligado ao User"""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to=Q(role__nome="MOTORISTA"), related_name="perfil_motorista")
    foto = models.ImageField(upload_to='fotos_motoristas/', blank=True, null=True)
    data_nascimento = models.DateField()
    nrBI = models.CharField(
        max_length=30,
        unique=True,
        validators=[RegexValidator(r'^\d{9}[A-Z]{2}$', "Formato inválido para BI")],
        help_text="Número de bilhete de identidade"
    )
    carta_conducao = models.CharField(
        max_length=30,
        unique=True,
        validators=[RegexValidator(r'^[A-Z0-9]{6,}$', "Formato inválido para carta de condução")],
        help_text="Número da carta de condução"
    )
    telefone = PhoneNumberField(region="MZ")
    endereco = models.TextField(blank=True, null=True, help_text="bairro, Quarterao, Numero da casa")
    ativo = models.BooleanField(default=True, db_index=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def clean(self):
        super().clean()
        hoje = date.today()
        idade = hoje.year - self.data_nascimento.year - (
            (hoje.month, hoje.day) < (self.data_nascimento.month, self.data_nascimento.day)
        )
        if idade < 18:
            raise ValidationError({"data_nascimento": "O motorista deve ter pelo menos 18 anos."})

        def __str__(self):
            return f"Motorista: {self.user.nome}"

    def save(self, *args, **kwargs):
        if self.user.nome:
            self.user.nome = self.user.nome.strip().title()
        if self.user.email:
            self.user.email = self.user.email.lower().strip()
        if self.endereco:
            self.endereco = self.endereco.strip()
        self.full_clean()
        super().save(*args, **kwargs)
