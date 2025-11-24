from rest_framework import serializers
from financeiro.models import Mensalidade, Pagamento, Salario, Fatura, AlertaEnviado

class PagamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pagamento
        fields = ['id', 'mensalidade', 'valor', 'data_pagamento', 'metodo_pagamento', 'observacao']

class MensalidadeSerializer(serializers.ModelSerializer):
    aluno = serializers.StringRelatedField()
    pagamentos = PagamentoSerializer(many=True, read_only=True)
    total_pago = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    valor_devido = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    valor_atualizado = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    dias_atraso = serializers.IntegerField(read_only=True)

    # class Meta:
    #     model = Mensalidade
    #     fields = ['id', 'aluno', 'valor', 'mes_referente', 'data_vencimento', 'data_limite', 'taxa_atraso', 'obs', 'recibo_gerado', 'status', 'data_pagamento', 'pagamentos', 'total_pago', 'valor_devido', 'valor_atualizado', 'dias_atraso',]

    class Meta:
        model = Mensalidade
        fields = [
            'id', 'aluno', 'valor', 'mes_referente', 'data_vencimento', 'data_limite',
            'taxa_atraso', 'obs', 'recibo_gerado', 'status', 'data_pagamento',
            'pagamentos', 'total_pago', 'valor_devido', 'valor_atualizado', 'dias_atraso',
    ]

    def get_total_pago(self, obj):
        return obj.total_pago

    def get_valor_devido(self, obj):
        return obj.valor_devido

    def get_valor_atualizado(self, obj):
        return obj.valor_atualizado

    def get_dias_atraso(self, obj):
        return obj.dias_atraso


class SalarioSerializer(serializers.ModelSerializer):
    # funcionario = serializers.PrimaryKeyRelatedField(queryset=Funcionario.objects.all())
    funcionario = serializers.StringRelatedField()
    class Meta:
        model = Salario
        fields = ['id', 'funcionario', 'valor', 'mes_referente' ,'obs', 'recibo_gerado', 'status', 'data_pagamento',]


class FaturaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fatura
        # fields = '__all__'
        fields = ['id', 'descricao', 'valor', 'data_emissao' ,'data_vencimento', 'obs', 'recibo_gerado', 'email_destinatario' ,'status', 'data_pagamento',]


class AlertaEnviadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlertaEnviado
        fields = ['id', 'encarregado', 'alunos', 'tipo' ,'email', 'mensagem', 'enviado_em', 'status',]


class RelatorioFinanceiroSerializer(serializers.Serializer):
    ano = serializers.IntegerField()
    mes = serializers.IntegerField()
    receitas = serializers.DecimalField(max_digits=12, decimal_places=2)
    despesas = serializers.DecimalField(max_digits=12, decimal_places=2)
    saldo_liquido = serializers.DecimalField(max_digits=12, decimal_places=2)
