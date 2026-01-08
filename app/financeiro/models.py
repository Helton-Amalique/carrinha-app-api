"""Models para base de dados de Financeiro"""

from datetime import date
from decimal import Decimal
from django.db import models
from django.db.models import Sum
from django.conf import settings
from django.utils import timezone
from transporte.models import Rota, Veiculo
from core.models import Aluno, Encarregado
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
# from financeiro.tasks import enviar_recibos_individual
# from financeiro.tasks import enviar_alerta_email
from django.db.models.functions import Coalesce

CHOICES = [("PAGO", "Pago"), ("PENDENTE", "Pendente"), ("ATRASADO", "Atrasado"), ("PAGO PARCIAL", "Pago Parcial")]
M_PAGAMENTO = [ ("DINHEIRO", "Dinheiro"), ("TRANSFERENCIA", "Transferência"), ("CARTAO", "Cartão"),]


class TimestampMixin(models.Model):
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True


class StatusMixin(models.Model):
    status = models.CharField(max_length=20, choices=CHOICES,default="PENDENTE")
    data_pagamento = models.DateTimeField(null=True, blank=True)
    class Meta:
        abstract = True

    def atualizar_status(self):
        hoje = date.today()
        if self.status == "PAGO" and not self.data_pagamento:
            if not self.data_pagamento:
                self.data_pagamento = timezone.now()
        elif hasattr(self, "data_limite") and hoje > self.data_limite:
            self.status = "ATRASADO"

# Manager
class MensalidadeManager(models.Manager):
    def atrasadas(self):
        """Mensalidade vencidas ou com status atrasado"""
        hoje = date.today()
        return self.filter(
            models.Q(status="ATRASADO") | (models.Q(status="PENDENTE") & models.Q(data_vencimento__lt=hoje))
        )
    def pagas(self):
        return self.filter(status="PAGO")

    def pendentes(self):
        hoje = date.today()
        return self.filter(status="PENDENTE", data_vencimento__gte=hoje)

    def parciais(self):
        return self.filter(status="PAGO PARCIAL")

    def do_aluno(self, aluno):
        return self.filter(aluno=aluno)

    def de_mes(self, ano, mes):
        """Mensalidade do um determinado mes/ano"""
        return self.filter(mes_referente__year=ano, mes_referente__month=mes)

    def total_recebido(self):
        # return self.model.objects.filter(pagamento__isnull=False).aggregate(total=Sum("pagamento__valor")["total"]or Decimal("0.00"))
        return self.model.objects.filter(pagamentos__isnull=False).aggregate(
            total=Coalesce(Sum("pagamentos__valor"), Decimal("0.00"))
        )["total"]



class PagamentoManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(ativo=True)

    def por_metodo(self, metodo):
        # return self.filter(metodo_pagamento=metodo)
        return self.filter(metodo_pagamento__iexact=metodo)

    def de_periodo(self, inicio, fim):
        return self.filter(data_pagamento__range=(inicio, fim))

    def do_aluno(self, aluno):
        return self.filter(mensalidade__aluno=aluno)

    def total_pago(self):
        # return self.aggregate(total=Sum("valor"))["total"] or Decimal("0.00")
        return self.aggregate(total=Coalesce(Sum("valor"), Decimal("0.00")))["total"]


class FaturaManager(models.Manager):
    def pagas(self):
        return self.filter(status="PAGO")

    def pendentes(self):
        hoje = date.today()
        return self.filter(status="PENDENTE", data_vencimento__gte=hoje)

    def vencidas(self):
        hoje = date.today()
        return self.filter(data_vencimento__lt=hoje).exclude(status="PAGO")

    def do_periodo(self, inicio, fim):
        return self.filter(data_emissao__range=(inicio, fim))

    def total_faturado(self):
        return self.aggregate(total=Sum("valor"))["total"] or Decimal("0.00")

    def total_recebido(self):
        return self.filter(status="PAGO").aggregate(total=Sum("valor"))["total"] or Decimal("0.00")


class SalarioManager(models.Manager):
    def pagos(self):
        return self.filter(status="PAGO")

    def pendentes(self):
        return self.filter(status="PENDENTE")

    def do_funcionario(self, funcionanrio):
        return self.filter(funcionario=funcionanrio)

    def total_pago(self, funcionario=None):
        qs = self.filter(status="PAGO")
        if funcionario:
            qs = qs.filter(funcionario=funcionario)
        return qs.aggregate(total=Sum("valor"))["total"] or Decimal("0.00")


class AlertaManager(models.Manager):
    def enviados(self):
        return self.filter(status="ENVIADO")

    def falhos(self):
        return self.filter(status="FALHA NO ENVIO")

    def pendentes(self):
        return self.filter(status="PENDENTE")

    def por_tipo(self, tipo):
        return self.filter(tipo=tipo)

# Models
class Mensalidade(TimestampMixin, StatusMixin):
    aluno = models.ForeignKey('core.Aluno',on_delete=models.CASCADE,related_name='mensalidades')
    valor = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))], blank=True, default=0,)
    mes_referente = models.DateField(help_text="Mes de referencia")
    data_vencimento = models.DateField()
    data_limite = models.DateField(help_text="O ultimo dia permitido para o pagamento")
    taxa_atraso = models.DecimalField(max_digits=5, decimal_places=2, default=0.10, help_text="A taxa de juros incrementa a cada 5 dias(ex:0.10 = 10%)")
    obs = models.TextField(blank=True, null=True)
    recibo_gerado = models.BooleanField(default=False)

    objects = MensalidadeManager()

    class Meta:
        unique_together = ("aluno", "mes_referente")
        ordering = ["-mes_referente"]

    @property
    def total_pago(self):
        """Soma todos os pagamentos parciais feitos para esta mensalidade."""
        total = self.pagamentos.aggregate(total=Sum('valor'))['total']
        return total or Decimal('0.00')

    @property
    def valor_devido(self):
        """Retorna o valor restante a ser pago."""
        return self.valor_atualizado - self.total_pago

    def atualizar_status(self):
        """ Calcula e atualiza o status da mensalidade com base nos pagamentos e datas."""
        if not self.pk:
            return
        new_status = "PENDENTE"
        total_pago = self.total_pago
        if total_pago >= self.valor_atualizado:
            new_status = "PAGO"
        elif total_pago > 0:
            new_status = "PAGO PARCIAL"
        elif date.today() > self.data_vencimento:
            new_status = "ATRASADO"
        if self.status != new_status:
            self.status = new_status
            fields_to_update = ['status']
            if new_status == "PAGO" and not self.data_pagamento:
                self.data_pagamento = timezone.now()
                fields_to_update.append('data_pagamento')
            self.save(update_fields=fields_to_update)

    def preencher_datas(self, ano: int, mes: int):
       """chama services gerar_calendario_anual pata preencher datas"""

    @property
    def dias_atraso(self):
        if self.status == "PAGO":
            return 0
        return max((date.today() - self.data_vencimento).days, 0)

    @property
    def valor_atualizado(self):
        """valor atualizado com a multa (pucha do service)"""
        if self.status == "ATRASADO":
            dias = self.dias_atraso
            periodos = dias // 5
            multa = self.valor * (self.taxa_atraso * periodos)
            return self.valor + multa
        return self.valor

    def clean(self):
        super().clean()
        if self.data_limite < self.data_vencimento:
            raise ValidationError("a data limite nao pode ser anterior a data de pagamento")

    def __str__(self):
        aluno_nome = getattr(self.aluno, "nome", "Novo Aluno")
        return f"{aluno_nome} - {self.valor:.2f} ({self.status})"


class Pagamento(TimestampMixin):
    """Registra um pagamento (parcial ou total) de uma mensalidade."""
    mensalidade = models.ForeignKey(Mensalidade, on_delete=models.CASCADE, related_name='pagamentos')
    valor = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    data_pagamento = models.DateTimeField(default=timezone.now)
    metodo_pagamento = models.CharField(max_length=20, choices=M_PAGAMENTO, default="DINHEIRO")
    ativo = models.BooleanField(default=True)
    observacao = models.TextField(blank=True, null=True)

    objects = PagamentoManager()
    all_objects = models.Manager()

    class Meta:
        # ordering = ['-data_pagamento']
        constraints = [
            models.UniqueConstraint(
                fields=['mensalidade', 'valor', 'data_pagamento'],
                name='unique_pagamento_mensalidade'
            )
        ]

    def clean(self):
        super().clean()
        # if self.valor > self.mensalidade.valor_devido:
        #     raise ValidationError("Valor do pagamento excede o valor devido")

        if Pagamento.object.filter(
            mensalidade=self.mensalidade,
            valor=self.valor,
            data_pagamento=self.data_pagamento
            ).exists():
                raise ValidationError("Pagamento duplicado para esta mensalidade")

    def delete(self, *args, **kwargs):
        """soft delete: apenas marca como inativos"""
        self.ativo = False
        self.save()

    def __str__(self):
        # return f"Pagamento de {self.valor} para {self.mensalidade.aluno.nome} em {self.data_pagamento.strftime('%d/%m/%Y')}"
        return f"Pagamento {self.id} - {self.valor} {self.metodo_pagamento}"


class Salario(TimestampMixin, StatusMixin):
    """Pagamento de salario para o funcionarios"""
    funcionario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role__in': ['FUNCIONARIO', 'MOTORISTA', 'ADMINISTRADOR']},
        related_name='salarios'
    )
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    mes_referente = models.DateField("Mes de referencia", max_length=20)
    obs = models.TextField(blank=True, null=True)
    recibo_gerado = models.BooleanField(default=False)

    objects = SalarioManager()

    class Meta:
        ordering = ["-mes_referente"]
        verbose_name = "Salario"
        verbose_name_plural = "Salarios"

    @classmethod
    def total_pago_funcionarios(cls, funcionario):
        """Total de salarios ja pagos a um funcionario"""
        # return cls.objects.filter(funcionario=funcion, status="PAGO").aggregate(total=Sum("valor"))["total"] or Decimal("0.00")
        return cls.objects.total_pago(funcionario)

    @classmethod
    def salario_pendente(cls, funcion=None):
        quant = cls.objects.pendentes()
        # return quant.filter(funcionario=funcion) if funcion else quant
        if funcion:
            quant = quant.filter(funcionario=funcion)
        return quant

    def gerar_recibo_automatico(self):
        """Gera recibo e envia email para o funcionario."""
        if not self.recibo_gerado and self.status == "PAGO":
            self.recibo_gerado = True
            self.save(update_fields=["recibo_gerado"]) # Fixed field name 'recibo_gereado' to 'recibo_gerado'
            # enviar_alerta_email.delay("salario", self.pk)

    def clean(self):
        """Validacoes antes de salvar"""
        if self.data_pagamento and self.data_pagamento > date.today():
            raise ValidationError("Data de pagamento nao pode ser no futuro.")
        if self.valor < 0:
            raise ValidationError("O valor do salario nao pode ser negativo")


    def save(self, *args, **kwargs):
        status_ant = None
        if self.pk:
            status_ant = Salario.objects.get(pk=self.pk).status

        super().save(*args, **kwargs)

        if self.status == "PAGO" and not self.recibo_gerado and self.recibo_gerado != "PAGO":
            self.gerar_recibo_automatico()

    def __str__(self):
        nome_func = getattr(self.funcionario, "nome", str(self.funcionario))
        return f'{nome_func} - {self.valor:.2f} ({self.mes_referente:%m/%Y}) - {self.status}'


class Fatura(StatusMixin):
    descricao = models.CharField(max_length=255)
    valor = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal(0.0))])
    data_emissao = models.DateField(default=timezone.now)
    data_vencimento = models.DateField()
    obs = models.TextField(blank=True, null=True)
    recibo_gerado = models.BooleanField(default=False)
    email_destinatario = models.EmailField(help_text=" Email do destinatario da fatura")

    objects = FaturaManager()

    class Meta:
        ordering = ["-data_emissao"]
        verbose_name_plural = "Faturas"


    def gerar_recibo_automatico(self):
        """Dispara task para gerar recibos(service q fara o envio real)"""
        if not self.recibo_gerado and self.status =="PAGO" and self.email_destinatario:
            self.recibo_gerado = True
            self.save(update_fields=["recibo_gerado"])
            # enviar_alerta_email.delay("fatura", self.pk)

    def clean(self):
        if self.data_emissao > date.today():
            raise ValidationError("A data de emissoa nao pode ser no futuro.")
        if self.data_vencimento < self.data_emissao:
            raise ValidationError("A data de vencimento nao pode ser anterior a data de emissao.")
        if self.valor < 0:
            raise ValidationError("O valor da fatura nao pode ser negativo")

    def save(self, *args, **kwargs):
        status_ant = None
        if self.pk:
            status_ant = Fatura.objects.get(pk=self.pk).status

        super().save(*args, **kwargs)

        if self.status == "PAGO" and not self.recibo_gerado and status_ant != "PAGO":
            self.gerar_recibo_automatico()

    def __str__(self):
        return f"{self.descricao} - {self.valor:.2f} ({self.status})"


class AlertaEnviado(TimestampMixin, models.Model):
    """Alerta enviados para os encarregados"""
    TIPO_CHOICES = [
        ("ATRASO", "Pagamento em atraso"),
        ("INICIO", "Inicio do periodo de pagamento"),
        ("PENDENTE", "pagamento pendente"),
        ("OUTRO", "Outro"),
    ]

    STATUS_CHOICES = [
        ("ENVIADO", "Enviado"),
        ("FALHA NO ENVIO", "Falha no envio"),
        ("PENDENTE", "Pendente")
    ]

    encarregado = models.ForeignKey('core.Encarregado',on_delete=models.CASCADE, related_name='alerta_enviados')
    alunos = models.ManyToManyField('core.Aluno', related_name="alerta_enviados")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default="OUTRO")
    email = models.EmailField(help_text="Email usado no envio")
    mensagem = models.TextField()
    enviado_em = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="ENVIADO")

    objects = AlertaManager()

    class Meta:
        ordering = ["-enviado_em"]

    def clean(self):
        if not self.email:
            raise ValidationError("O email do encarregado e obrigatorio para envio de alerta.")
        if not self.mensagem.strip():
            raise ValidationError("A mensagem nao pode ser vazia")
        if self.alunos.count() == 0:
            raise ValidationError("O alerta deve esta associado a pelo menos um aluno")

    def __str__(self):
        # return f"{self.eviado_em.strftime('%d/%m/%Y %H:%M')}"
        return f"Alerta {self.status} - {self.encarregado.user.email} ({self.alunos.count()} alunos)"
