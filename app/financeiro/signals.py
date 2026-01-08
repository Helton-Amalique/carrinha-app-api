from django.db import models
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver
from financeiro.models import Pagamento


@receiver(post_save, sender=Pagamento)
def atualizar_status_mensalidade(sender, instance, **kwargs):
    mensalidade = instance.mensalidade
    total_pago = mensalidade.pagamento_set.filter.filter(ativo=True).aggregate(
        models.Sum('valor')
    )['valor__sum'] or 0

    if total_pago >= mensalidade.valor:
        mensalidade.status = 'PAGO'
    elif total_pago > 0:
        mensalidade.status = 'PAGO PARCIAL'
    elif mensalidade.data_vencimento and mensalidade.data_vencimento < instance.data_pagamento.date():
        mensalidade.status = "ATRASADO"
    else:
        mensalidade.status = "PENDENTE"

    mensalidade.save(update_fields=["status"])