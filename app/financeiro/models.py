
from datetime import date
from decimal import Decimal
from django.db import models
from django.db.models import Sum
from django.conf import settings
from django.utils import timezone
from transporte.models import Rota, Veiculo
from alunos.models import Aluno, Encarregado
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
# from financeiro.tasks import enviar_recibos_individual
# from financeiro.tasks import enviar_alerta_email

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
        """Mensalidade pagas"""
        return self.filter(status="PAGO")

    def pendentes(self):
        """Mensalidade ainda nao pagas e dentro do prazo"""
        hoje = date.today()
        return self.filter(status="PENDENTE", data_vencimento__gte=hoje)

    def parciais(self):
        """Mensalidades com pagamentos parcial"""
        return self.filter(status="PAGO PARCIAL")

    def do_aluno(self, aluno):
        """Mensalidade de um aluno especifico"""
        return self.filter(aluno=aluno)

    def de_mes(self, ano, mes):
        """Mensalidade do um determinado mes/ano"""
        return self.filter(mes_referente__year=ano, mes_referente__month=mes)

    def total_recebido(self):
        """Soma de todos os pagamentos realizados."""
        # return self.model.objects.filter(pagamento__isnull=False).aggregate(total=Sum("pagamentos__valor"))["total"] or Decimal("0.00")
        return self.model.objects.filter(pagamentos__isnull=False).aggregate(
        total=Sum("pagamentos__valor"))["total"] or Decimal("0.00")



class PagamentoManager(models.Manager):
    def por_metodo(self, metodo):
        """Filter pagamento por metodo (DINHEIRO, TRANSFERENCIA, CARTAO)"""
        return self.filter(metodo_pagamento=metodo)

    def de_periodo(self, inicio, fim):
        """Pagamento realizados dentro de um intervalo de datas"""
        return self.filter(data_pagamento__range=(inicio, fim))

    def do_aluno(self, aluno):
        """Pagamento de um aluno especifico"""
        return self.filter(mensalidade__aluno=aluno)

    def total_pago(self):
        """Soma de todos os pagamentos registrados"""
        return self.aggregate(total=Sum("valor"))["total"] or Decimal("0.00")


class FaturaManager(models.Manager):
    def pagas(self):
        """Faturas pagas"""
        return self.filter(status="PAGO")

    def pendentes(self):
        """Faturas ainda nao pagas e dentro do prazo"""
        hoje = date.today()
        return self.filter(status="PENDENTE", data_vencimento__gte=hoje)

    def vencidas(self):
        """Faturas vencidas (data de vencimento ja passou)"""
        hoje = date.today()
        return self.filter(data_vencimento__lt=hoje).exclude(status="PAGO")

    def do_periodo(self, inicio, fim):
        """Fatura emitidas dentro de um intervalo de datas"""
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

    def do_funcionario(self, funcionario):
        return self.filter(funcionario=funcionario)

    def total_pago(self, funcionario=None):
        qs = self.filter(status="PAGO")
        if funcionario:
            qs = qs.filter(funcionario=funcionario)
        return qs.aggregate(total=Sum("valor"))["total"] or Decimal("0.00")


class DespesaManager(models.Manager):
    def por_categoria(self, categoria):
        return self.filter(categoria=categoria)

    def de_periodo(self, inicio, fim):
        return self.filter(data__range=(inicio, fim))

    def total_despesas(self):
        return self.aggregate(total=models.Sum("valor"))["total"] or Decimal("0.00")


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
    aluno = models.ForeignKey('alunos.Aluno',on_delete=models.CASCADE,related_name='mensalidades')
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
       pass


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
        aluno_nome = getattr(self.aluno.user, "nome", "Novo Aluno")
        return f"{aluno_nome} - {self.valor:.2f} ({self.status})"


class Pagamento(TimestampMixin):
    """Registra um pagamento (parcial ou total) de uma mensalidade."""
    mensalidade = models.ForeignKey(Mensalidade, on_delete=models.CASCADE, related_name='pagamentos')
    valor = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    data_pagamento = models.DateTimeField(default=timezone.now)
    metodo_pagamento = models.CharField(max_length=20, choices=M_PAGAMENTO, default="DINHEIRO")
    observacao = models.TextField(blank=True, null=True)

    objects = PagamentoManager()

    class Meta:
        ordering = ['-data_pagamento']

    def clean(self):
        super().clean()
        if self.valor > self.mensalidade.valor_devido:
            raise ValidationError("Valor do pagamento excede o valor devido")

    def __str__(self):
        return f"Pagamento de {self.valor} para {self.mensalidade.aluno.nome} em {self.data_pagamento.strftime('%d/%m/%Y')}"


class Salario(TimestampMixin, StatusMixin):
    """Pagamento de salario para os funcionarios"""
    funcionario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role__in': ['FUNCIONARIO', 'MOTORISTA', 'ADMINISTRADOR']},
        related_name='salarios'
    )
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    mes_referente = models.DateField("Mes de referencia")
    obs = models.TextField(blank=True, null=True)
    recibo_gerado = models.BooleanField(default=False)

    objects = SalarioManager()

    class Meta:
        ordering = ["-mes_referente"]
        verbose_name = "Salario"
        verbose_name_plural = "Salarios"

    @classmethod
    def total_pago_funcionarios(cls, funcionario):
        return cls.objects.total_pago(funcionario)

    @classmethod
    def salario_pendente(cls, funcionario=None):
        qs = cls.objects.pendentes()
        if funcionario:
            qs = qs.filter(funcionario=funcionario)
        return qs

    def gerar_recibo_automatico(self):
        if not self.recibo_gerado and self.status == "PAGO":
            self.recibo_gerado = True
            self.save(update_fields=["recibo_gerado"])
            enviar_alerta_email.delay("salario", self.pk)

    def clean(self):
        if self.data_pagamento and self.data_pagamento > date.today():
            raise ValidationError("Data de pagamento nao pode ser no futuro.")
        if self.valor < 0:
            raise ValidationError("O valor do salario nao pode ser negativo")

    def save(self, *args, **kwargs):
        status_ant = None
        if self.pk:
            status_ant = Salario.objects.get(pk=self.pk).status

        super().save(*args, **kwargs)

        if self.status == "PAGO" and not self.recibo_gerado and status_ant != "PAGO":
            self.gerar_recibo_automatico()

    def __str__(self):
        nome_func = getattr(self.funcionario, "nome", str(self.funcionario))
        return f'{nome_func} - {self.valor:.2f} ({self.mes_referente:%m/%Y}) - {self.status}'

from django.db import models
from django.utils import timezone
from decimal import Decimal
from django.core.validators import MinValueValidator

class Despesa(models.Model):
    CATEGORIAS = [
        ("COMBUSTIVEL", "Combustível"),
        ("MANUTENCAO", "Manutenção"),
        # ("SALARIO", "Salário"),
        ("ALUGUEL", "Aluguel"),
        ("OUTROS", "Outros"),
    ]

    descricao = models.CharField(max_length=255)
    categoria = models.CharField(max_length=30, choices=CATEGORIAS, default="OUTROS")
    valor = models.DecimalField(max_digits=10, decimal_places=2,
                                validators=[MinValueValidator(Decimal("0.01"))])
    data = models.DateField(default=timezone.now)
    observacao = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-data"]
        verbose_name = "Despesa"
        verbose_name_plural = "Despesas"

    def __str__(self):
        return f"{self.descricao} - {self.valor:.2f} ({self.data:%d/%m/%Y})"
