from django.urls import path, include
from rest_framework.routers import DefaultRouter
from transporte.views import MotoristaViewSet, VeiculoViewSet, RotaViewSet

# Cria o router e registra os ViewSets
router = DefaultRouter()
router.register(r'motoristas', MotoristaViewSet, basename='motorista')
router.register(r'veiculos', VeiculoViewSet, basename='veiculo')
router.register(r'rotas', RotaViewSet, basename='rota')

urlpatterns = [
    path('', include(router.urls)),
]
