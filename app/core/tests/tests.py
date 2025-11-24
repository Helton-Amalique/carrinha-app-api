import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from core.models import User, Cargo, Aluno, Encarregado, Motorista


@pytest.mark.django_db
class TestCargoModel:

    def test_cargo_valido(self):
        cargo = Cargo(nome="Motorista", salario_padrao=Decimal("5000.00"))
        cargo.full_clean()  # não deve levantar erro
        cargo.save()
        assert Cargo.objects.count() == 1

    def test_salario_negativo_invalido(self):
        cargo = Cargo(nome="Motorista", salario_padrao=Decimal("-100.00"))
        with pytest.raises(ValidationError) as excinfo:
            cargo.full_clean()
        assert "salario_padrao" in excinfo.value.message_dict

    def test_nome_vazio_invalido(self):
        cargo = Cargo(nome="   ", salario_padrao=Decimal("1000.00"))
        with pytest.raises(ValidationError) as excinfo:
            cargo.full_clean()
        assert "nome" in excinfo.value.message_dict

    def test_salario_none_invalido(self):
        cargo = Cargo(nome="Motorista", salario_padrao=None)
        with pytest.raises(ValidationError) as excinfo:
            cargo.full_clean()
        assert "salario_padrao" in excinfo.value.message_dict

    def test_nome_unico(self):
        Cargo.objects.create(nome="Motorista", salario_padrao=Decimal("1000.00"))
        cargo2 = Cargo(nome="Motorista", salario_padrao=Decimal("2000.00"))
        with pytest.raises(ValidationError):
            cargo2.full_clean()


@pytest.mark.django_db
class TestAlunoEMotoristaValidacoes:

    @pytest.fixture
    def cargos(self):
        cargo_aluno = Cargo.objects.create(nome="ALUNO", salario_padrao=Decimal("0.00"))
        cargo_encarregado = Cargo.objects.create(nome="ENCARREGADO", salario_padrao=Decimal("0.00"))
        cargo_motorista = Cargo.objects.create(nome="MOTORISTA", salario_padrao=Decimal("0.00"))
        return {
            "aluno": cargo_aluno,
            "encarregado": cargo_encarregado,
            "motorista": cargo_motorista,
        }

    @pytest.fixture
    def encarregado(self, cargos):
        user_enc = User.objects.create(
            email="encarregado@dominio.com",
            nome="Maria Encarregada",
            role=cargos["encarregado"],
            salario=Decimal("0.00"),
        )
        return Encarregado.objects.create(
            user=user_enc,
            telefone="+258840000000",
            nrBI="123456789AB",
            endereco="Bairro Central",
        )

    # ----- Aluno -----

    def test_aluno_valido(self, cargos, encarregado):
        # 10 anos atrás
        nascimento = date.today().replace(year=date.today().year - 10)
        user_aluno = User.objects.create(
            email="aluno@dominio.com",
            nome="joao aluno",
            role=cargos["aluno"],
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

    def test_aluno_data_nascimento_futura_invalida(self, cargos, encarregado):
        futuro = date.today() + timedelta(days=1)
        user_aluno = User.objects.create(
            email="aluno2@dominio.com",
            nome="Ana Aluna",
            role=cargos["aluno"],
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

    def test_aluno_idade_menor_que_3_invalida(self, cargos, encarregado):
        # 2 anos atrás
        nascimento = date.today().replace(year=date.today().year - 2)
        user_aluno = User.objects.create(
            email="aluno3@dominio.com",
            nome="Bebe",
            role=cargos["aluno"],
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

    def test_motorista_valido_maior_de_18(self, cargos):
        nascimento = date.today().replace(year=date.today().year - 30)
        user_motorista = User.objects.create(
            email="motorista@dominio.com",
            nome="Carlos Motorista",
            role=cargos["motorista"],
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

    def test_motorista_menor_de_18_invalido(self, cargos):
        # 16 anos atrás
        nascimento = date.today().replace(year=date.today().year - 16)
        user_motorista = User.objects.create(
            email="motorista2@dominio.com",
            nome="Jovem",
            role=cargos["motorista"],
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
