from rest_framework.routers import DefaultRouter
from core.views import (UserViewSet, CargoViewSet, AlunoViewSet, EncarregadoViewSet, MotoristaViewSet)

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'cargos', CargoViewSet)
router.register(r'encarregados', EncarregadoViewSet)
router.register(r'alunos', AlunoViewSet)
router.register(r'motoristas', MotoristaViewSet)

urlpatterns = router.urls
