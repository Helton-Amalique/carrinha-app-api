from django.contrib import admin
from datetime import date
from django.contrib import admin
from core.models import Aluno
from django.utils.html import format_html
from transporte.models import Veiculo, Rota
from core.models import Motorista, Encarregado
from core.admin_mixins.mixins import BaseAdmin


# ---------------- Motorista ----------------
# @admin.register(Motorista)
# class MotoristaAdmin(admin.ModelAdmin):
#     list_display = (
#         "id", "get_nome", "get_email", "telefone",
#         "carta_nr", "validade_carta_status", "ativo_badge", "criado_em"
#     )
#     list_filter = ("ativo", "validade_da_carta", "criado_em")
#     search_fields = ("user__nome", "user__email", "telefone", "carta_nr")
#     readonly_fields = ("criado_em", "atualizado_em")
#     date_hierarchy = "criado_em"
#     list_per_page = 25
#     ordering = ("-criado_em",)

#     fieldsets = (
#         ('Informações do Usuário', {'fields': ('user',)}),
#         ('Contato', {'fields': ('telefone', 'endereco')}),
#         ('Documentação', {'fields': ('carta_nr', 'validade_da_carta')}),
#         ('Status', {'fields': ('ativo', 'criado_em', 'atualizado_em')}),
#     )

#     def get_nome(self, obj):
#         return obj.user.nome if obj.user else '-'
#     get_nome.short_description = 'Nome'
#     get_nome.admin_order_field = 'user__nome'

#     def get_email(self, obj):
#         return obj.user.email if obj.user else '-'
#     get_email.short_description = 'Email'
#     get_email.admin_order_field = 'user__email'

#     def validade_carta_status(self, obj):
#         if obj.validade_da_carta < date.today():
#             return format_html('<span style="color: red;">⚠️ Expirada</span>')
#         return format_html('<span style="color: green;">✓ Válida</span>')
#     validade_carta_status.short_description = 'Status Carta'

#     def ativo_badge(self, obj):
#         return format_html(
#             '<span style="color: {};">{} {}</span>',
#             "green" if obj.ativo else "red",
#             "✓" if obj.ativo else "✗",
#             "Ativo" if obj.ativo else "Inativo"
#         )
#     ativo_badge.short_description = 'Status'

#     actions = ['ativar_motoristas', 'desativar_motoristas']

#     def ativar_motoristas(self, request, queryset):
#         count = queryset.update(ativo=True)
#         self.message_user(request, f'{count} motorista(s) ativado(s) com sucesso.')
#     ativar_motoristas.short_description = 'Ativar motoristas selecionados'

#     def desativar_motoristas(self, request, queryset):
#         count = queryset.update(ativo=False)
#         self.message_user(request, f'{count} motorista(s) desativado(s) com sucesso.')
#     desativar_motoristas.short_description = 'Desativar motoristas selecionados'


# ---------------- Veículo ----------------
@admin.register(Veiculo)
class VeiculoAdmin(admin.ModelAdmin):
    list_display = (
        "id", "modelo", "matricula", "marca", "capacidade",
        "get_motorista", "vagas_disponiveis", "ativo_badge", "criado_em"
    )
    list_filter = ("ativo", "motorista", "criado_em")
    search_fields = ("matricula", "modelo", "marca", "motorista__user__nome")
    readonly_fields = ("vagas_disponiveis", "criado_em", "atualizado_em")
    autocomplete_fields = ("motorista",)
    date_hierarchy = "criado_em"
    list_per_page = 25
    ordering = ("matricula",)

    fieldsets = (
        ('Informações do Veículo', {'fields': ('marca', 'modelo', 'matricula', 'capacidade')}),
        ('Motorista', {'fields': ('motorista',)}),
        ('Status', {'fields': ('ativo', 'vagas_disponiveis', 'criado_em', 'atualizado_em')}),
    )

    def get_motorista(self, obj):
        if obj.motorista:
            return obj.motorista.user.nome
        return format_html('<span style="color: orange;">Sem motorista</span>')
    get_motorista.short_description = 'Motorista'
    get_motorista.admin_order_field = 'motorista__user__nome'

    def ativo_badge(self, obj):
        return format_html(
            '<span style="color: {};">{} {}</span>',
            "green" if obj.ativo else "red",
            "✓" if obj.ativo else "✗",
            "Ativo" if obj.ativo else "Inativo"
        )
    ativo_badge.short_description = 'Status'

    actions = ['ativar_veiculos', 'desativar_veiculos']

    def ativar_veiculos(self, request, queryset):
        count = queryset.update(ativo=True)
        self.message_user(request, f'{count} veículo(s) ativado(s) com sucesso.')
    ativar_veiculos.short_description = 'Ativar veículos selecionados'

    def desativar_veiculos(self, request, queryset):
        count = queryset.update(ativo=False)
        self.message_user(request, f'{count} veículo(s) desativado(s) com sucesso.')
    desativar_veiculos.short_description = 'Desativar veículos selecionados'


# ---------------- Inline de Alunos em Rotas ----------------
class AlunoInline(admin.TabularInline):
    model = Rota.alunos.through
    extra = 0
    autocomplete_fields = ("aluno",)
    verbose_name = "Aluno"
    verbose_name_plural = "Alunos"


# ---------------- Rota ----------------
@admin.register(Rota)
class RotaAdmin(BaseAdmin):
    list_display = (
        "id", "nome", "get_veiculo", "get_motorista",
        "hora_partida", "hora_chegada", "total_alunos", "ativo_badge", "criado_em"
    )
    list_filter = ("ativo", "veiculo", "criado_em")
    search_fields = ("nome", "descricao", "veiculo__matricula", "veiculo__modelo")
    readonly_fields = ("total_alunos", "get_motorista", "criado_em", "atualizado_em")
    autocomplete_fields = ("veiculo",)
    inlines = [AlunoInline]
    date_hierarchy = "criado_em"
    list_per_page = 25
    ordering = ("nome",)

    fieldsets = (
        ('Informações da Rota', {'fields': ('nome', 'descricao')}),
        ('Veículo e Horários', {'fields': ('veiculo', 'hora_partida', 'hora_chegada')}),
        ('Estatísticas', {'fields': ('get_motorista', 'total_alunos')}),
        ('Status', {'fields': ('ativo', 'criado_em', 'atualizado_em')}),
    )

    def get_veiculo(self, obj):
        return f"{obj.veiculo.modelo} - {obj.veiculo.matricula}"
    get_veiculo.short_description = 'Veículo'
    get_veiculo.admin_order_field = 'veiculo__modelo'

    def get_motorista(self, obj):
        if obj.veiculo and obj.veiculo.motorista:
            return obj.veiculo.motorista.user.nome
        return '-'
    get_motorista.short_description = 'Motorista'

    def total_alunos(self, obj):
        count = obj.alunos.count()
        capacidade = obj.veiculo.capacidade if obj.veiculo else 0
        if capacidade == 0:
            return "-"
        percentual = (count / capacidade) * 100
        if count > capacidade:
            return format_html('<span style="color: red;">{} / {} ({}%) ⚠️</span>', count, capacidade, round(percentual))
        return format_html('<span style="color: green;">{} / {} ({}%)</span>', count, capacidade, round(percentual))

        # return format_html(
        # '<div style="width:100px; border:1px solid #ccc;">'
        # '<div style="width:{}%; background-color:{}; text-align:center; color:white;">{}%</div>'
        # '</div>',
        # percentual, color, percentual
    total_alunos.short_description = 'Alunos (Ocupação)'

    def ativo_badge(self, obj):
        return format_html(
            '<span style="color: {};">{} {}</span>',
            "green" if obj.ativo else "red",
            "✓" if obj.ativo else "✗",
            "Ativa" if obj.ativo else "Inativa"
        )
    ativo_badge.short_description = 'Status'

    actions = ['ativar_rotas', 'desativar_rotas']

    def ativar_rotas(self, request, queryset):
        count = queryset.update(ativo=True)
        self.message_user(request, f'{count} rota(s) ativada(s) com sucesso.')
    ativar_rotas.short_description = 'Ativar rotas selecionadas'

    def desativar_rotas(self, request, queryset):
        count = queryset.update(ativo=False)
        self.message_user(request, f'{count} rota(s) desativada(s) com sucesso')
    desativar_rotas.short_description = 'Desativar rotas selecionadas'


class CartaExpiradaFilter(admin.SimpleListFilter):
    carta = "Carta Expirada"
    parameter_name = "carta_expirada"

    def lookups(self, request, model_admin):
        return [("sim", "Expirada"), ("nao", "Válida")]

    def queryset(self, request, queryset):
        if self.value() == "sim":
            return queryset.filter(validade_da_carta__lt=date.today())
        if self.value() == "nao":
            return queryset.filter(validade_da_carta__gte=date.today())

