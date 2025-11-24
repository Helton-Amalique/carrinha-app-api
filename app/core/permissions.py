from rest_framework import permissions
from django.core.exceptions import ObjectDoesNotExist


def is_admin(user):
    """Helper para verificar se o usuário é admin/superuser"""
    return (
        user.is_staff
        or user.is_superuser
        or (user.role and user.role.nome.upper() == "ADMIN")
    )


class IsAdmin(permissions.BasePermission):
    """Permite acesso apenas a usuários com cargo ADMIN ou superuser"""
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and is_admin(user))


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Permite leitura pública, mas escrita apenas para o dono ou admin"""
    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user.is_authenticated:
            return False

        if is_admin(user):
            return True

        if request.method in permissions.SAFE_METHODS:
            return True

        # Se o objeto tiver relação com user
        if hasattr(obj, "user") and obj.user == user:
            return True

        # Se for aluno vinculado a encarregado
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
