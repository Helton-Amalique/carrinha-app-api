import pytest
from core.models import User, Cargo, Aluno, Encarregado, Motorista


@pytest.mark.django_db
def test_criar_perfil_aluno_signal():
    cargo_aluno = Cargo.objects.create(nome="ALUNO", salario_padrao=0)
    user = User.objects.create_user(email="aluno@test.com", nome="Joao Mateus", role=cargo_aluno, password="123456")
    assert Aluno.objects.filter(user=user).exists()
    assert user.perfil_aluno is not None


@pytest.mark.django_db
def test_criar_perfil_encarregado_signal():
    cargo_encarregado = Cargo.objects.create(nome="ENCARREGADO", salario_padrao=0)
    user = User.objects.create_user(email="enc@test.com", nome="Maria Julia", role=cargo_encarregado, password="7894561")
    assert Encarregado.objects.filter(user=user).exists()
    assert user.perfil_encarregado is not None


@pytest.mark.django_db
def test_criar_perfil_motorista_signal():
    cargo_motorista = Cargo.objects.create(nome="MOTORISTA", salario_padrao=0)
    user = User.objects.create_user(email="motor@test.com", nome="Carlos Mosquita", role=cargo_motorista, password="64598319")
    assert Motorista.objects.filter(user=user).exists()
    assert user.perfil_motorista is not None
