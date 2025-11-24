from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdmin(permissions.BasePermission):
    """Permite acesso apenas a usuarios com cargo ADMIN ou superuser"""
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (
            user.is_superuser or (user.role and user.role.nome.upper() == "ADMIN")
        ))


class IsOwnerOrReadOnly(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        user = request.user

        if user and user.is_authenticated:
            if user.is_staff or user.is_superuser or (user.role and user.role.nome.upper() == "ADMIN"):
                return True
        if request.method in permissions.SAFE_METHODS:
            return True

        if hasattr(obj, "user") and obj.user == user:
            return True
        if hasattr(obj, "superuser") and obj.encarregado.user == user:
            return True

        return False


class IsEncarregadoOwner(permissions.BasePermission):
    """permite que o encarregado edite apenas os seus proprios alunos"""
    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user.is_authenticated:
            return False
        if user.ise_staff or user.is_superuser or (user.role and user.role.nome.upper() == "ADMIN"):
            return True

        if hasattr(obj, "encarregado") and obj.encarregado.user == user:
            return True

        return False


class IsAlunoOwner(permissions.BasePermission):
    """Permite que o Aluno aceda apenas ao seu proprio perfil"""
    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user.is_authenticated:
            return False

        if user.is_staff or user.is_superuser or (user.role and user.role.nome.upper() == "ADMIN"):
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

        if user.is_staff or user.is_superuser or (user.role and user.role.nome.upper() == "ADMIN"):
            return True

        if hasattr(obj, "user") and obj.user == user:
            return True

        return False
