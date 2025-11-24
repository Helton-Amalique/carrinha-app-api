from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from transporte.models import Veiculo, Motorista, Rota
from core.models import Aluno

User = get_user_model()

class TransporteViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Criar usuários
        self.admin_user = User.objects.create_user(email="admin@test.com", password="123", role_nome="Admin")
        self.motorista_user = User.objects.create_user(email="motorista@test.com", password="123", role_nome="Motorista")
        self.responsavel_user = User.objects.create_user(email="pai@test.com", password="123", role_nome="Responsavel")

        # Criar motorista
        self.motorista = Motorista.objects.create(user=self.motorista_user, telefone="123456789", ativo=True)

        # Criar veículo
        self.veiculo = Veiculo.objects.create(
            marca="Toyota", modelo="Hiace", matricula="ABC-1234",
            capacidade=10, motorista=self.motorista, ativo=True
        )

        # Criar rota
        self.rota = Rota.objects.create(
            nome="Rota 1", veiculo=self.veiculo,
            hora_partida="05:30", hora_chegada="07:00", ativo=True
        )

        # Criar aluno e vincular ao responsável
        self.aluno = Aluno.objects.create(nome="João", encarregado=self.responsavel_user)
        self.rota.alunos.add(self.aluno)

    def test_admin_can_list_all_veiculos(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get("/api/veiculos/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_motorista_can_only_see_his_veiculo(self):
        self.client.force_authenticate(user=self.motorista_user)
        response = self.client.get("/api/veiculos/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["motorista_nome"], self.motorista_user.nome)

    def test_responsavel_can_only_see_rotas_of_children(self):
        self.client.force_authenticate(user=self.responsavel_user)
        response = self.client.get("/api/rotas/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["nome"], "Rota 1")

    def test_motorista_inativo_cannot_be_assigned(self):
        self.motorista.ativo = False
        self.motorista.save()
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post("/api/veiculos/", {
            "marca": "Ford", "modelo": "Transit", "matricula": "XYZ-9999",
            "capacidade": 12, "motorista": self.motorista.id
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("motorista", response.data)

    def test_veiculo_inativo_cannot_be_used_in_rota(self):
        self.veiculo.ativo = False
        self.veiculo.save()
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post("/api/rotas/", {
            "nome": "Rota 2", "veiculo_id": self.veiculo.id,
            "hora_partida": "06:00", "hora_chegada": "07:30"
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("veiculo", response.data)

    def test_rota_cannot_exceed_capacity(self):
        # Criar mais alunos que a capacidade
        for i in range(15):
            aluno = Aluno.objects.create(nome=f"Aluno {i}", encarregado=self.responsavel_user)
            self.rota.alunos.add(aluno)

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(f"/api/rotas/{self.rota.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["total_alunos"] > self.veiculo.capacidade)
