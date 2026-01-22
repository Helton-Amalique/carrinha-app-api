# transporte/permissions.py
from rest_framework.permissions import BasePermission

class IsAdminOrMotorista(BasePermission):
    """
    Permite acesso apenas a usuários com role ADMINISTRADOR ou MOTORISTA.
    """
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            getattr(request.user, "role", None) in ["ADMINISTRADOR", "MOTORISTA"]
        )

class IsAdminMotoristaOrEncarregado(BasePermission):
    """
    Permite acesso a ADMINISTRADOR, MOTORISTA ou ENCARREGADO.
    """
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            getattr(request.user, "role", None) in ["ADMINISTRADOR", "MOTORISTA", "ENCARREGADO"]
        )
