import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from financeiro.models import Mensalidade, Pagamento, Salario, Fatura, Despesa, AlertaEnviado
from alunos.models import Aluno, Encarregado

User = get_user_model()

@pytest.mark.django_db
class TestMensalidade:
    def setup_method(self):
        self.user = User.objects.create_user(email="aluno@test.com", password="123", nome="Aluno Teste", role="ALUNO")
        self.aluno = Aluno.objects.create(user=self.user)
        self.mensalidade = Mensalidade.objects.create(
            aluno=self.aluno,
            valor=Decimal("100.00"),
            mes_referente=date(2025, 11, 1),
            data_vencimento=date.today() - timedelta(days=5),
            data_limite=date.today() + timedelta(days=5),
        )

    def test_status_atrasado(self):
        self.mensalidade.atualizar_status()
        assert self.mensalidade.status == "ATRASADO"

    def test_pagamento_parcial(self):
        Pagamento.objects.create(mensalidade=self.mensalidade, valor=Decimal("50.00"))
        self.mensalidade.atualizar_status()
        assert self.mensalidade.status == "PAGO PARCIAL"

    def test_pagamento_total(self):
        Pagamento.objects.create(mensalidade=self.mensalidade, valor=Decimal("100.00"))
        self.mensalidade.atualizar_status()
        assert self.mensalidade.status == "PAGO"
        assert self.mensalidade.data_pagamento is not None


@pytest.mark.django_db
class TestSalario:
    def setup_method(self):
        self.funcionario = User.objects.create_user(email="func@test.com", password="123", nome="Funcionario", role="FUNCIONARIO")
        self.salario = Salario.objects.create(
            funcionario=self.funcionario,
            valor=Decimal("500.00"),
            mes_referente=date(2025, 11, 1),
            status="PENDENTE"
        )

    def test_salario_pendente(self):
        assert Salario.objects.pendentes().count() == 1

    def test_salario_pago_dispara_recibo(self):
        self.salario.status = "PAGO"
        self.salario.save()
        assert self.salario.recibo_gerado is True


@pytest.mark.django_db
class TestFatura:
    def setup_method(self):
        self.fatura = Fatura.objects.create(
            descricao="Serviço extra",
            valor=Decimal("200.00"),
            data_emissao=date.today(),
            data_vencimento=date.today() + timedelta(days=10),
            email_destinatario="cliente@test.com",
            status="PENDENTE"
        )

    def test_fatura_pendente(self):
        assert Fatura.objects.pendentes().count() == 1

    def test_fatura_pago_dispara_recibo(self):
        self.fatura.status = "PAGO"
        self.fatura.save()
        assert self.fatura.recibo_gerado is True


@pytest.mark.django_db
class TestDespesa:
    def test_despesa_total(self):
        Despesa.objects.create(descricao="Combustível", categoria="COMBUSTIVEL", valor=Decimal("300.00"))
        Despesa.objects.create(descricao="Manutenção", categoria="MANUTENCAO", valor=Decimal("200.00"))
        total = Despesa.objects.total_despesas()
        assert total == Decimal("500.00")


@pytest.mark.django_db
class TestAPIResumo:
    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email="admin@test.com", password="123", nome="Admin", role="ADMINISTRADOR")
        self.client.force_authenticate(user=self.user)

    def test_resumo_endpoint(self):
        response = self.client.get("/api/financeiro/resumo/")
        assert response.status_code == 200
        data = response.json()
        assert "mensalidade" in data
        assert "pagamento" in data
        assert "salarios" in data
        assert "fatura" in data
        assert "despesas" in data

    def test_evolucao_endpoint(self):
        response = self.client.get("/api/financeiro/evolucao/?ano=2025")
        assert response.status_code == 200
        data = response.json()
        assert "evolucao" in data
        assert len(data["evolucao"]) == 12
