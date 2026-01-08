from django.contrib import admin
from financeiro.models import Mensalidade, Pagamento, Salario, Fatura, AlertaEnviado


@admin.register(Mensalidade)
class MensalidadeAdmin(admin.ModelAdmin):
    list_display = (
        "aluno",
        "mes_referente",
        "valor",
        "status",
        "data_vencimento",
        "data_limite",
        "valor_atualizado",
        "total_pago",
        "valor_devido",
    )
    list_filter = ("status", "data_vencimento", "data_limite")
    search_fields = ("aluno__nome",)
    date_hierarchy = "data_vencimento"
    # readonly_fields = ("valor_atualizado",)
    # # readonly_fields = ("valor_atualizado", "total_pago", "valor_devido")
    # def mostrar_valor_atualizado():
    #     return obj.valor_atualizado
    # mostrar_valor_atualizado.short_description = "Valor atualizado"


@admin.register(Pagamento)
class PagamentoAdmin(admin.ModelAdmin):
    list_display = (
        "mensalidade",
        "valor",
        "metodo_pagamento",
        "data_pagamento",
    )
    list_filter = ("metodo_pagamento", "data_pagamento")
    search_fields = ("mensalidade__aluno__nome",)


@admin.register(Salario)
class SalarioAdmin(admin.ModelAdmin):
    list_display = (
        "funcionario",
        "mes_referente",
        "valor",
        "status",
        "recibo_gerado",
    )
    list_filter = ("status", "mes_referente")
    search_fields = ("funcionario__username", "funcionario__email")


@admin.register(Fatura)
class FaturaAdmin(admin.ModelAdmin):
    list_display = (
        "descricao",
        "valor",
        "data_emissao",
        "data_vencimento",
        "status",
        "recibo_gerado",
        "email_destinatario",
    )
    list_filter = ("status", "data_emissao", "data_vencimento")
    search_fields = ("descricao", "email_destinatario")


@admin.register(AlertaEnviado)
class AlertaEnviadoAdmin(admin.ModelAdmin):
    list_display = (
        "encarregado",
        "tipo",
        "status",
        "email",
        "enviado_em",
        "alunos_count",
    )
    list_filter = ("status", "tipo", "enviado_em")
    search_fields = ("encarregado__user__email", "mensagem")

    def alunos_count(self, obj):
        return obj.alunos.count()
    alunos_count.short_description = "Qtd Alunos"
