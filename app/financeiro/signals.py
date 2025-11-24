from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from financeiro.models import Pagamento, Mensalidade, Fatura, Salario, AlertaEnviado

#atualiza o status da mensalidade quando um pagamento e cruado
@receiver(post_save, sender=Pagamento)
def atualizar_status_mensalidade(sender, instance, created, **kwargs):
    if created:
        mensalidade = instance.mensalidade
        mensalidade.atualizar_status()

@receiver(post_save, sender=Fatura)
def gerar_recibo_fatura(sender, instance, **kwargs):
    if instance.status == "PAGO" and not instance.recibo_gerado:
        instance.recibo_gerado = True
        instance.save(update_fields=["recibo_gerado"])
        enviar_recibos_individual.delay("fatura", instance.pk)

@receiver(post_save, sender=Salario)
def gerar_recibos_salarios(post_save, instance, **kwargs):
    if instance.status == "PAGO" and not instance.recibo_gerado:
        instance.recibo_gerado = True
        instance.save(update_fields=["recibo_gerado"])
        enviar_recibos_individual.delay("salario", instance.pk)

@receiver(post_save, sender=Mensalidade)
def criar_alerta_mensalidade_atrasado(sender, instance, **kwargs):
    if instance.status == "ATRASADO":
        from financeiro.tasks import enviar_alerta_email
        AlertaEnviado.objects.create(
            encarregado=instance.aluno.encarregado,
            email=instance.aluno.encarregado.email,
            mensagem=f"A mensalidade do aluno {instance.aluno.nome}, esta em atraso",
            tipo="ATRASO",
            status="PENDENTE"
        )
        enviar_alerta_email.delay(alerta.pk)
