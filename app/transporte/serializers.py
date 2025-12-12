from rest_framework import serializers
from transporte.models import Veiculo, Rota
from core.models import Motorista, Aluno


class AlunoSerializer(serializers.ModelSerializer):
    user_nome = serializers.CharField(source='user.nome', read_only=True)

    class Meta:
        model = Aluno
        fields = ['id', 'user_nome', 'escola_dest', 'classe', 'ativo']


class MotoristaSerializer(serializers.ModelSerializer):
    user_nome = serializers.CharField(source='user.nome', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_role = serializers.CharField(source='user.role.nome', read_only=True)

    class Meta:
        model = Motorista
        fields = [
            'id', 'user', 'user_nome', 'user_email', 'user_role',
            'telefone', 'endereco', 'carta_nr', 'validade_da_carta',
            'ativo', 'criado_em', 'atualizado_em'
        ]
        read_only_fields = ['criado_em', 'atualizado_em']


class VeiculoSerializer(serializers.ModelSerializer):
    motorista_nome = serializers.CharField(source='motorista.user.nome', read_only=True)
    vagas_disponiveis = serializers.IntegerField(read_only=True)

    class Meta:
        model = Veiculo
        fields = [
            "id", "marca", "modelo", "matricula", "capacidade",
            "motorista", "motorista_nome", "vagas_disponiveis",
            "ativo", "criado_em", "atualizado_em"
        ]
        read_only_fields = ["vagas_disponiveis", "criado_em", "atualizado_em"]

    def validate(self, data):
        motorista = data.get('motorista')
        if motorista and not motorista.ativo:
            raise serializers.ValidationError(
                {'motorista': 'Nao e possivel atribuir um motorista inativo'}
            )
        return data


class RotaSerializer(serializers.ModelSerializer):
    motorista_detalhes = serializers.SerializerMethodField(read_only=True)
    veiculo_detalhes = serializers.SerializerMethodField(read_only=True)
    alunos = AlunoSerializer(many=True, read_only=True)
    total_alunos = serializers.SerializerMethodField(read_only=True)

    veiculo_id = serializers.PrimaryKeyRelatedField(
        queryset=Veiculo.objects.all(),
        source='veiculo',
        write_only=True,
        required=False
    )

    class Meta:
        model = Rota
        fields = [
            'id', 'nome', 'descricao', 'veiculo_id',
            'veiculo_detalhes', 'motorista_detalhes', 'total_alunos',
            'hora_partida', 'hora_chegada', 'ativo', 'criado_em', 'atualizado_em'
        ]
        read_only_fields = ['criado_em', 'atualizado_em']

    def get_veiculo_detalhes(self, obj):
        if obj.veiculo:
            return {
                'id': obj.veiculo.id,
                'modelo': obj.veiculo.modelo,
                'matricula': obj.veiculo.matricula,
                'capacidade': obj.veiculo.capacidade,
                'vagas_disponiveis': obj.veiculo.vagas_disponiveis
            }
        return None

    def get_motorista_detalhes(self, obj):
        if obj.veiculo and obj.veiculo.motorista:
            return {
                'id': obj.veiculo.motorista.id,
                'user_nome': obj.veiculo.motorista.user.nome,
                'user_email': obj.veiculo.motorista.user.email,
                'telefone': str(obj.veiculo.motorista.telefone)
            }
        return None

    def get_total_alunos(self, obj):
        return obj.alunos.count()

    def validate(self, data):
        veiculo = data.get('veiculo')
        if veiculo and not veiculo.motorista:
            raise serializers.ValidationError({'veiculo': 'O veículo selecionado não tem motorista.'})
        if veiculo and not veiculo.ativo:
            raise serializers.ValidationError({'veiculo': 'Não é possível criar rota com veículo inativo.'})

        hora_partida = data.get('hora_partida')
        hora_chegada = data.get('hora_chegada')
        if hora_partida and hora_chegada and hora_chegada <= hora_partida:
            raise serializers.ValidationError({'hora_chegada': 'Hora de chegada deve ser posterior à partida.'})
        return data

