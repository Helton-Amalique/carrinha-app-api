import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.core.exceptions import ValidationError
from core.models import User, Aluno, Encarregado, Motorista


@pytest.mark.django_db
class TestUserValidation:

    def test_user_admin_creation(self):
        user = User.objects.create_superuser(email="admin@test.com", nome="Admin User", password="password")
        assert user.role == "ADMIN"
        assert user.is_staff
        assert user.is_superuser


@pytest.mark.django_db
class TestAlunoEMotoristaValidacoes:

    @pytest.fixture
    def encarregado(self):
        user_enc = User.objects.create(
            email="encarregado@dominio.com",
            nome="Maria Encarregada",
            role="ENCARREGADO",
            salario=Decimal("0.00"),
        )
        return Encarregado.objects.create(
            user=user_enc,
            telefone="+258840000000",
            nrBI="123456789AB",
            endereco="Bairro Central",
        )

    # ----- Aluno -----

    def test_aluno_valido(self, encarregado):
        # 10 anos atrás
        nascimento = date.today().replace(year=date.today().year - 10)
        user_aluno = User.objects.create(
            email="aluno@dominio.com",
            nome="joao aluno",
            role="ALUNO",
            salario=Decimal("0.00"),
        )
        aluno = Aluno(
            user=user_aluno,
            encarregado=encarregado,
            data_nascimento=nascimento,
            nrBI="987654321CD",
            escola_dest="Escola 1",
            classe="5a",
            mensalidade=Decimal("1500.00"),
        )
        aluno.full_clean()  # não deve levantar erro
        aluno.save()
        assert aluno.idade >= 3
        # Normalização do nome e email do User aplicada no save()
        assert aluno.user.nome == "Joao Aluno"
        assert aluno.user.email == "aluno@dominio.com"

    def test_aluno_data_nascimento_futura_invalida(self, encarregado):
        futuro = date.today() + timedelta(days=1)
        user_aluno = User.objects.create(
            email="aluno2@dominio.com",
            nome="Ana Aluna",
            role="ALUNO",
        )
        aluno = Aluno(
            user=user_aluno,
            encarregado=encarregado,
            data_nascimento=futuro,
            nrBI="111222333EF",
            escola_dest="Escola 2",
            classe="3a",
        )
        with pytest.raises(ValidationError) as excinfo:
            aluno.full_clean()
        assert "data_nascimento" in excinfo.value.message_dict

    def test_aluno_idade_menor_que_3_invalida(self, encarregado):
        # 2 anos atrás
        nascimento = date.today().replace(year=date.today().year - 2)
        user_aluno = User.objects.create(
            email="aluno3@dominio.com",
            nome="Bebe",
            role="ALUNO",
        )
        aluno = Aluno(
            user=user_aluno,
            encarregado=encarregado,
            data_nascimento=nascimento,
            nrBI="222333444GH",
            escola_dest="Infantil",
            classe="Creche",
        )
        with pytest.raises(ValidationError) as excinfo:
            aluno.full_clean()
        assert "data_nascimento" in excinfo.value.message_dict

    # ----- Motorista -----

    def test_motorista_valido_maior_de_18(self):
        nascimento = date.today().replace(year=date.today().year - 30)
        user_motorista = User.objects.create(
            email="motorista@dominio.com",
            nome="Carlos Motorista",
            role="MOTORISTA",
        )
        motorista = Motorista(
            user=user_motorista,
            data_nascimento=nascimento,
            nrBI="333444555IJ",
            carta_conducao="ABC12345",
            telefone="+258850000000",
            endereco="Av. Principal",
        )
        motorista.full_clean()  # não deve levantar erro
        motorista.save()
        assert motorista.pk is not None

    def test_motorista_menor_de_18_invalido(self):
        # 16 anos atrás
        nascimento = date.today().replace(year=date.today().year - 16)
        user_motorista = User.objects.create(
            email="motorista2@dominio.com",
            nome="Jovem",
            role="MOTORISTA",
        )
        motorista = Motorista(
            user=user_motorista,
            data_nascimento=nascimento,
            nrBI="444555666KL",
            carta_conducao="XYZ98765",
            telefone="+258860000000",
            endereco="Rua Secundária",
        )
        # Espera ValidationError se você adicionou Motorista.clean() com regra de >= 18
        with pytest.raises(ValidationError):
            motorista.full_clean()
