from rest_framework import viewsets, filters
from core.models import User, Aluno, Encarregado, Motorista
from core.serializers import (
    UserSerializer,
    AlunoSerializer,
    EncarregadoSerializer,
    MotoristaSerializer,
)
from core.permissions import (
    IsAdmin,
    IsOwnerOrAdmin,
    IsEncarregadoOwner,
    IsAlunoOwner,
    IsMotoristaOwner,
)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    # Permite admin OU dono (sem leitura pública)
    permission_classes = [IsAdmin | IsOwnerOrAdmin]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["email", "nome", "role"]
    ordering_fields = ["nome", "email", "role"]


class EncarregadoViewSet(viewsets.ModelViewSet):
    queryset = Encarregado.objects.select_related("user").all()
    serializer_class = EncarregadoSerializer
    permission_classes = [IsAdmin | IsOwnerOrAdmin]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["user__nome", "user__email", "nrBI", "telefone"]
    ordering_fields = ["user__nome", "nrBI", "telefone"]


class AlunoViewSet(viewsets.ModelViewSet):
    queryset = Aluno.objects.select_related("user", "encarregado").all()
    serializer_class = AlunoSerializer
    permission_classes = [IsAdmin | IsEncarregadoOwner | IsAlunoOwner]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["user__nome", "user__email", "escola_dest", "classe", "nrBI"]
    ordering_fields = ["user__nome", "classe", "mensalidade"]


class MotoristaViewSet(viewsets.ModelViewSet):
    queryset = Motorista.objects.select_related("user").all()
    serializer_class = MotoristaSerializer
    permission_classes = [IsAdmin | IsMotoristaOwner]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["user__nome", "user__email", "nrBI", "carta_conducao", "telefone"]
    ordering_fields = ["user__nome", "nrBI", "carta_conducao"]
