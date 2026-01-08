from django.urls import path, include
from rest_framework.routers import DefaultRouter
from financeiro.views import (
    MensalidadeViewSet,
    PagamentoViewSet,
    SalarioViewSet,
    FaturaViewSet,
    AlertaEnviadoViewSet,
    # FinceiroResumoViewSet,
)

router = DefaultRouter()
router.register(r"mensalidades", MensalidadeViewSet)
router.register(r"pagamentos", PagamentoViewSet)
router.register(r"salarios", SalarioViewSet)
router.register(r"faturas", FaturaViewSet)
router.register(r"alertas", AlertaEnviadoViewSet)
# router.register(r"resumo", FinceiroResumoViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
