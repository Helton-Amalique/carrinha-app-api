from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from core.views import (
    UserViewSet,
    EncarregadoViewSet,
    AlunoViewSet,
    MotoristaViewSet,
    RegisterView,
    # PasswordResetRequestView,
    # PasswordResetConfirmView,
)

# Router para os ViewSets
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'encarregados', EncarregadoViewSet, basename='encarregado')
router.register(r'alunos', AlunoViewSet, basename='aluno')
router.register(r'motoristas', MotoristaViewSet, basename='motorista')

urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegisterView.as_view(), name='register'),
    # path('password-reset/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    # path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('', include(router.urls)),
]
