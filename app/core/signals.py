from django.db.models.signals import post_save
from django.dispatch import receiver
from core.models import User, Encarregado, Aluno, Motorista


@receiver(post_save, sender=User)
def criar_perfil(sender, instance, created, **kwargs):
    """Cria automaticamente o perfil correspondente ao cargo de usuario quando um novo User e criado"""
    if not created or not instance.role:
        return

    role_nome = instance.role.nome.upper()

    if role_nome == "ENCARREGADO":
        Encarregado.objects.get_or_create(user=instance)
    elif role_nome == "ALUNO":
        Aluno.objects.get_or_create(user=instance, defaults={"encarregado": None})
    elif role_nome == "MOTORISTA":
        Motorista.objects.get_or_create(user=instance)
