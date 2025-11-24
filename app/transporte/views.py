from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from transporte.models import Motorista, Veiculo, Rota
from transporte.serializers import MotoristaSerializer, VeiculoSerializer, RotaSerializer
from transporte.permissions import IsAdmin, IsMotorista, IsResponsavel


class MotoristaViewSet(viewsets.ModelViewSet):
    queryset = Motorista.objects.all()
    serializer_class = MotoristaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role.nome == "Admin":
            return Motorista.objects.all()
        return Motorista.objects.filter(user=user)


class VeiculoViewSet(viewsets.ModelViewSet):
    queryset = Veiculo.objects.all()
    serializer_class = VeiculoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role.nome == "Admin":
            return Veiculo.objects.all()
        elif user.role.nome == "Motorista":
            return Veiculo.objects.filter(motorista__user=user)
        return Veiculo.objects.none()


class RotaViewSet(viewsets.ModelViewSet):
    queryset = Rota.objects.all()
    serializer_class = RotaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role.nome == "Admin":
            return Rota.objects.all()
        elif user.role.nome == "Motorista":
            return Rota.objects.filter(veiculo__motorista__user=user)
        elif user.role.nome == "Responsavel":
            return Rota.objects.filter(alunos__encarregado__user=user)
        return Rota.objects.none()
