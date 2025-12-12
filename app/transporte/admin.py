from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.utils.html import format_html
from datetime import date
import csv
from django.http import HttpResponse

from transporte.models import Veiculo, Rota
from core.models import Motorista


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

    # Ações customizadas
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
    verbose_name = "Aluno"
    verbose_name_plural = "Alunos"


# ---------------- Rota ----------------
@admin.register(Rota)
class RotaAdmin(admin.ModelAdmin):
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
    total_alunos.short_description = 'Alunos (Ocupação)'

    def ativo_badge(self, obj):
        return format_html(
            '<span style="color: {};">{} {}</span>',
            "green" if obj.ativo else "red",
            "✓" if obj.ativo else "✗",
            "Ativa" if obj.ativo else "Inativa"
        )
    ativo_badge.short_description = 'Status'

    # Ações customizadas
    actions = ['ativar_rotas', 'desativar_rotas', 'exportar_alunos']

    def ativar_rotas(self, request, queryset):
        count = queryset.update(ativo=True)
        self.message_user(request, f'{count} rota(s) ativada(s) com sucesso.')
    ativar_rotas.short_description = 'Ativar rotas selecionadas'

    def desativar_rotas(self, request, queryset):
        count = queryset.update(ativo=False)
        self.message_user(request, f'{count} rota(s) desativada(s) com sucesso')
    desativar_rotas.short_description = 'Desativar rotas selecionadas'

    def exportar_alunos(self, request, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="alunos_rota.csv"'
        writer = csv.writer(response)
        writer.writerow(["Rota", "Aluno", "Email", "Encarregado"])
        for rota in queryset:
            for aluno in rota.alunos.all():
                writer.writerow([
                    rota.nome,
                    aluno.user.nome,
                    aluno.user.email,
                    aluno.encarregado.user.nome if aluno.encarregado else "-"
                ])
        return response
    exportar_alunos.short_description = "Exportar lista de alunos"

# # ---------------- Motorista ----------------
# class CartaExpiradaFilter(admin.SimpleListFilter):
#     title = "Carta Expirada"
#     parameter_name = "carta_expirada"

#     def lookups(self, request, model_admin):
#         return [("sim", "Expirada"), ("nao", "Válida")]

#     def queryset(self, request, queryset):
#         if self.value() == "sim":
#             return queryset.filter(validade_da_carta__lt=date.today())
#         if self.value() == "nao":
#             return queryset.filter(validade_da_carta__gte=date.today())


# @admin.register(Motorista)
# class MotoristaAdmin(admin.ModelAdmin):
#     list_display = ("id", "user", "nrBI", "carta_conducao", "telefone", "ativo")
#     list_filter = ("ativo", CartaExpiradaFilter)
#     search_fields = ("user__nome", "user__email", "nrBI", "carta_conducao")
#     ordering = ("user__nome",)