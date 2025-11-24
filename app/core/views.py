from rest_framework import viewsets
from core.models import User, Cargo, Aluno, Encarregado, Motorista
from core.serializers import (
    UserSerializer,
    CargoSerializer,
    AlunoSerializer,
    EncarregadoSerializer,
    MotoristaSerializer,
)
from core.permissions import IsAdmin, IsOwnerOrReadOnly, IsEncarregadoOwner, IsAlunoOwner, IsMotoristaOwner


class CargoViewSet(viewsets.ModelViewSet):
    queryset = Cargo.objects.all()
    serializer_class = CargoSerializer
    permission_classes = [IsAdmin]  # apenas admin pode gerenciar cargos


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdmin, IsOwnerOrReadOnly]  # lista de classes


class EncarregadoViewSet(viewsets.ModelViewSet):
    queryset = Encarregado.objects.all()
    serializer_class = EncarregadoSerializer
    permission_classes = [IsAdmin, IsOwnerOrReadOnly]


class AlunoViewSet(viewsets.ModelViewSet):
    queryset = Aluno.objects.all()
    serializer_class = AlunoSerializer
    permission_classes = [IsAdmin, IsEncarregadoOwner, IsAlunoOwner]


class MotoristaViewSet(viewsets.ModelViewSet):
    queryset = Motorista.objects.all()
    serializer_class = MotoristaSerializer
    permission_classes = [IsAdmin, IsMotoristaOwner]
