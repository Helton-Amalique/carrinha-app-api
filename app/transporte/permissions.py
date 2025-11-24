from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role.nome == "Admin"

class IsMotorista(BasePermission):
    def has_object_permission(self, request, view, obj):
        # Motorista só acessa veículos/rotas que estão vinculados a ele
        if hasattr(obj, "motorista"):
            return obj.motorista.user == request.user
        if hasattr(obj, "veiculo"):
            return obj.veiculo.motorista and obj.veiculo.motorista.user == request.user
        return False

class IsResponsavel(BasePermission):
    def has_object_permission(self, request, view, obj):
        # Responsável só acessa rotas dos filhos
        if hasattr(obj, "alunos"):
            return obj.alunos.filter(encarregado__user=request.user).exists()
        return False
