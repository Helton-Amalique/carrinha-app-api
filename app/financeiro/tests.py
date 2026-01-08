from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from financeiro.models import Pagamento, Mensalidade, Aluno

class PagamentoManagerTest(TestCase):
    def setUp(self):
        # Criar aluno e mensalidade
        self.aluno = Aluno.objects.create(nome="João")
        self.mensalidade = Mensalidade.objects.create(
            aluno=self.aluno,
            valor=Decimal("100.00"),
            status="EM_ABERTO"
        )

        # Criar pagamentos
        self.pagamento1 = Pagamento.all_objects.create(
            mensalidade=self.mensalidade,
            valor=Decimal("50.00"),
            data_pagamento=timezone.now().date(),
            metodo_pagamento="DINHEIRO",
            ativo=True
        )
        self.pagamento2 = Pagamento.all_objects.create(
            mensalidade=self.mensalidade,
            valor=Decimal("50.00"),
            data_pagamento=timezone.now().date(),
            metodo_pagamento="CARTAO",
            ativo=True
        )
        self.pagamento_inativo = Pagamento.all_objects.create(
            mensalidade=self.mensalidade,
            valor=Decimal("20.00"),
            data_pagamento=timezone.now().date(),
            metodo_pagamento="TRANSFERENCIA",
            ativo=False
        )

    def test_get_queryset_retorna_apenas_ativos(self):
        pagamentos = Pagamento.objects.all()
        self.assertEqual(pagamentos.count(), 2)
        self.assertNotIn(self.pagamento_inativo, pagamentos)

    def test_por_metodo(self):
        pagamentos_dinheiro = Pagamento.objects.por_metodo("DINHEIRO")
        self.assertIn(self.pagamento1, pagamentos_dinheiro)
        self.assertNotIn(self.pagamento2, pagamentos_dinheiro)

    def test_de_periodo(self):
        hoje = timezone.now().date()
        pagamentos_periodo = Pagamento.objects.de_periodo(hoje, hoje)
        self.assertEqual(pagamentos_periodo.count(), 2)

    def test_do_aluno(self):
        pagamentos_joao = Pagamento.objects.do_aluno(self.aluno)
        self.assertEqual(pagamentos_joao.count(), 2)

    def test_total_pago(self):
        total = Pagamento.objects.total_pago()
        self.assertEqual(total, Decimal("100.00"))  # apenas ativos

class AtualizarStatusMensalidadeSignalsTest(TestCase):
    def setup(self):
        self.aluno = Aluno.objects.create(nome="Maria Cossa")
        self.mensalidade = Mensalidade.objects.create(
            aluno=self.aluno,
            valor=Decimal("1200.00"),
            mes_referente=timezone.now().date(),
            data_vencimento=timezone.now().date() - timedelta(days=1),
            data_limite=timezone.now().date() + timedelta(days=5),
            status="PENDENTE"
            )

    def test_pagamento_total_atuali_pago(self):
        Pagamento.objects.create(
            mensalidade=self.mensalidade,
            valor=Decimal("1200.00"),
            metodo_pagamento="DINHEIRO"
        )
        self.mensalidade.refresh_from_db()
        self.assertEqual(self.mensalidade.status, "PAGO")

    def test_pagamento_parcial_atual(self):
        Pagamento.objects.create(
            mensalidade=self.mensalidade,
            valor=Decimal("600.00"),
            metodo_pagamento="CARTAO"
        )
        self.mensalidade.refresh_from_db()
        self.assertEqual(self.mensalidade.status, "PAGO PARCIAL")

    def test_sem_pagamento_atua(self):
        self.mensalidade.atualizar_status()
        self.mensalidade.refresh_from_db()
        self.assertEqual(self.mensalidade.status, "ATRASADO")

    def test_sem_pagamento_dentro_praso_mantem_pendente(self):
        mensalidade2 = Mensalidade.objects.create(
            aluno=self.aluno,
            valor=Decimal("2200.00"),
            mes_referente=timezone.now().date(),
            data_vencimento=timezone.now().date() + timedelta(days=10),
            data_limite=timezone.now().date() + timedelta(days=15),
            status="PENDENTE"
        )
        mensalidade2.atualizar_status()
        mensalidade2.refresh_from_db()
        self.assertEqual(mensalidade2.status, "PENDENTE")