from rest_framework import permissions
from django.core.exceptions import ObjectDoesNotExist


def is_admin(user):
    """Helper para verificar se o usuário é admin/superuser"""
    if not user or not user.is_authenticated:
        return False
    return (
        user.is_staff or user.is_superuser or (user.role == "ADMIN")
    )


class IsAdmin(permissions.BasePermission):
    """Permite acesso apenas a usuários com cargo ADMIN ou superuser"""
    def has_permission(self, request, view):
        return is_admin(request.user)


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permite acesso apenas ao dono do objeto ou administradores.
    NÃO permite leitura pública (proteção de PII).
    """
    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user.is_authenticated:
            return False

        if is_admin(user):
            return True

        # Se o objeto tiver relação direta com user
        if hasattr(obj, "user") and obj.user == user:
            return True

        # Se for aluno vinculado a encarregado (Encarregado pode ver/editar seus alunos)
        try:
            if hasattr(obj, "encarregado") and obj.encarregado.user == user:
                return True
        except ObjectDoesNotExist:
            pass

        return False


class IsEncarregadoOwner(permissions.BasePermission):
    """Permite que o encarregado edite apenas os seus próprios alunos"""
    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user.is_authenticated:
            return False

        if is_admin(user):
            return True

        if hasattr(obj, "encarregado") and obj.encarregado.user == user:
            return True

        return False


class IsAlunoOwner(permissions.BasePermission):
    """Permite que o Aluno aceda apenas ao seu próprio perfil"""
    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user.is_authenticated:
            return False

        if is_admin(user):
            return True

        if hasattr(obj, "user") and obj.user == user:
            return True

        return False


class IsMotoristaOwner(permissions.BasePermission):
    """Permite que o Motorista aceda apenas ao seu próprio perfil"""
    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user.is_authenticated:
            return False

        if is_admin(user):
            return True

        if hasattr(obj, "user") and obj.user == user:
            return True

        return False
