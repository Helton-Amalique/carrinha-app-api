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


@pytest.mark.django_db
def test_nao_criar_perfil_para_admin():
    cargo_admin = Cargo.objects.create(nome="ADMIN", salario_padrao=0)
    user = User.objects.create_user(email="admin@test.com", nome="Super Admin", role=cargo_admin, password="admin123")
    # Não deve criar perfil de aluno/encarregado/motorista
    assert not hasattr(user, "perfil_aluno")
    assert not hasattr(user, "perfil_encarregado")
    assert not hasattr(user, "perfil_motorista")


@pytest.mark.django_db
def test_signal_nao_duplica_perfil():
    cargo_motorista = Cargo.objects.create(nome="MOTORISTA", salario_padrao=0)
    user = User.objects.create_user(email="motor2@test.com", nome="Carlos Motorista", role=cargo_motorista, password="123456")
    # Chamando save novamente não deve criar duplicado
    user.save()
    assert Motorista.objects.filter(user=user).count() == 1
