from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core.views import UserViewSet, EncarregadoViewSet, AlunoViewSet, MotoristaViewSet

# Cria o roteador padrão
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'encarregados', EncarregadoViewSet, basename='encarregado')
router.register(r'alunos', AlunoViewSet, basename='aluno')
router.register(r'motoristas', MotoristaViewSet, basename='motorista')

urlpatterns = [
    path('api/', include(router.urls)),
]
