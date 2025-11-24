from decimal import Decimal
from django.db.models import Sum
from django.utils.timezone import now
from financeiro.models import Pagamento, Fatura, Despesa, Salario

def relatorio_financeiro(ano=None, mes=None):
    """
    Gera um relatório consolidado de receitas e despesas.
    Se ano/mes forem fornecidos, filtra por período específico.
    """

    filtros = {}
    if ano and mes:
        filtros.update({"data_pagamento__year": ano, "data_pagamento__month": mes})


    total_pagamentos = Pagamento.objects.filter(**filtros).aggregate(
        total=Sum("valor")
    )["total"] or Decimal("0.00")

    total_faturas = Fatura.objects.filter(status="PAGO", **filtros).aggregate(
        total=Sum("valor")
    )["total"] or Decimal("0.00")

    receitas = total_pagamentos + total_faturas


    filtros_despesas = {}
    if ano and mes:
        filtros_despesas.update({"data__year": ano, "data__month": mes})

    total_despesas = Despesa.objects.filter(**filtros_despesas).aggregate(
        total=Sum("valor")
    )["total"] or Decimal("0.00")

    total_salarios = Salario.objects.filter(status="PAGO", **filtros_despesas).aggregate(
        total=Sum("valor")
    )["total"] or Decimal("0.00")

    despesas = total_despesas + total_salarios


    saldo_liquido = receitas - despesas

    return {
        "ano": ano or now().year,
        "mes": mes or now().month,
        "receitas": receitas,
        "despesas": despesas,
        "saldo_liquido": saldo_liquido,
    }
