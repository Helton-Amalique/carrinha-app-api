
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from financeiro.models import AlertaEnviado


@shared_task
def enviar_alerta_email(alerta_id):
    """Task assincrona para enviar email de alerta.
    Recebo o ID do alerta e dispara o email para o encarregado"""

    try:
        alerta = AlertaEnviado.objects.get(pk=alerta_id)
    except AlertaEnviado.DoesNotExist:
        return f"Alerta {alerta_id} nao encontrado."

    assunto = f"Alerta de {alerta.get_tipo_display()}"
    mensagem = alerta.mensagem
    destinatario = alerta.email

    if destinatario:
        try:
            send_mail(
                assunto,
                mensagem,
                settings.DEFAULT_FROM_EMAIL,
                [destinatario],
                fail_silently=False,
            )
            alerta.status = "ENVIADO"
            alerta.save(update_fields=["status"])
            return f"Alerta enviado para {destinatario}"
        except Exception as e:
            alerta.status = "FALHA NO ENVIO"
            alerta.save(update_fields=["status"])
            return f"Falha ao enviar alerta: {str(e)}"
    else:
        alerta.status = "FALHA NO ENVIO"
        alerta.save(update_fields=["status"])
        return "Nenhum destinatario definido"
