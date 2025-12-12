from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from core.models import Motorista
from transporte.models import Veiculo, Rota
from transporte.serializers import MotoristaSerializer, VeiculoSerializer, RotaSerializer
from .permissions import IsAdminOrMotorista, IsAdminMotoristaOrEncarregado


# ---------------- Motorista ----------------
class MotoristaViewSet(viewsets.ModelViewSet):
    queryset = Motorista.objects.all()
    serializer_class = MotoristaSerializer
    permission_classes = [IsAuthenticated]  # só autenticados

    def get_queryset(self):
        user = self.request.user
        role_nome = getattr(user.role, "nome", "").upper()
        if role_nome == "ADMIN":
            return Motorista.objects.all()
        return Motorista.objects.filter(user=user)


# ---------------- Veículo ----------------
class VeiculoViewSet(viewsets.ModelViewSet):
    queryset = Veiculo.objects.all()
    serializer_class = VeiculoSerializer
    permission_classes = [IsAdminOrMotorista]  # ADMIN e MOTORISTA podem editar

    def get_queryset(self):
        user = self.request.user
        role_nome = getattr(user.role, "nome", "").upper()

        if role_nome == "ADMIN":
            return Veiculo.objects.all()
        elif role_nome == "MOTORISTA":
            return Veiculo.objects.filter(motorista__user=user)
        elif role_nome == "ENCARREGADO":
            # Encarregado só consulta veículos das rotas dos seus alunos
            return Veiculo.objects.filter(rotas__alunos__encarregado__user=user).distinct()
        return Veiculo.objects.none()


# ---------------- Rota ----------------
class RotaViewSet(viewsets.ModelViewSet):
    queryset = Rota.objects.all()
    serializer_class = RotaSerializer
    permission_classes = [IsAdminMotoristaOrEncarregado]  # regras específicas

    def get_queryset(self):
        user = self.request.user
        role_nome = getattr(user.role, "nome", "").upper()

        if role_nome == "ADMIN":
            return Rota.objects.all()
        elif role_nome == "MOTORISTA":
            return Rota.objects.filter(veiculo__motorista__user=user)
        elif role_nome == "ENCARREGADO":
            return Rota.objects.filter(alunos__encarregado__user=user).distinct()
        return Rota.objects.none()
