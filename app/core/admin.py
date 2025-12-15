from django.contrib import admin
from core.models import User, Encarregado, Aluno, Motorista
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("id", "email", "nome", "role", "salario", "is_active", "is_staff", "is_superuser")
    list_filter = ("role", "is_active", "is_staff", "is_superuser")
    search_fields = ("email", "nome")
    ordering = ("email",)
    readonly_fields = ("data_criacao", "data_atualizacao")
    fieldsets = (
        (None, {"fields": ("email", "nome", "password")}),
        ("Cargo e Salário", {"fields": ("role", "salario")}),
        ("Permissões", {"fields": ("is_active", "is_staff", "is_superuser")}),
        ("Datas", {"fields": ("last_login", "data_criacao", "data_atualizacao")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "nome", "role", "password1", "password2"),
        }),
    )
    search_help_text = "Pesquise por email ou nome"


class AlunoInline(admin.TabularInline):
    model= Aluno
    extra = 1
    readonly_fields = ("get_email",)
    # list_display = ("id", "user", "get_email", "encarregado", "escola_dest", "classe", "mensalidade", "ativo")

    def get_email(self, obj):
        return obj.user.email if obj.user else "-"
    get_email.short_description = "Email"

@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "get_email", "encarregado", "escola_dest", "classe", "mensalidade", "idade", "ativo")
    search_fields = ("user__nome", "user__email", "escola_dest", "classe", "nrBI")
    list_filter = ("ativo", "classe", "escola_dest")
    ordering = ("user__nome",)
    list_select_related = ("user", "encarregado")
    readonly_fields = ("criado_em", "atualizado_em")
    autocomplete_fields = ("user", "encarregado")
    search_help_text = "Pesquise por nome, email, escola ou BI"

    def get_email(self, obj):
        return obj.user.email if obj.user else "-"
    get_email.short_description = "Email"
    get_email.admin_order_field = "user__email"

    def idade(self, obj):
        return obj.idade
    idade.short_description = "Idade"
    # class AlunoAdmin(admin.ModelAdmin):
    #     list_display = ("id", "user", "get_email", "encarregado", "escola_dest", "classe", "mensalidade", "ativo")
    #     search_fields = ("user__nome", "user__email", "escola_dest", "classe", "nrBI")
    #     list_filter = ("ativo", "classe", "escola_dest")

    #     ordering = ("user__nome",)
    #     list_select_related = ("user", "encarregado")

    #     def get_email(self, obj):
    #         return obj.user.email if obj.user else "-"
    #     get_email.short_description = "Email"
    #     get_email.admin_order_field = "user__email"


@admin.register(Encarregado)
class EncarregadoAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "get_email", "telefone", "nrBI", "ativo")
    search_fields = ("user__nome", "user__email", "nrBI", "telefone")
    list_filter = ("ativo",)
    ordering = ("user__nome",)
    inlines = [AlunoInline]
    list_select_related = ("user",)

    def get_email(self, obj):
        return obj.user.email if obj.user else "-"
    get_email.short_description = "Email"
    get_email.admin_order_field = "user__email"



@admin.register(Motorista)
class MotoristaAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "get_email", "nrBI", "carta_conducao", "telefone", "ativo")
    search_fields = ("user__nome", "user__email", "nrBI", "carta_conducao", "telefone")
    list_filter = ("ativo",)
    ordering = ("user__nome",)
    list_select_related = ("user",)

    def get_email(self, obj):
        return obj.user.email if obj.user else "-"
    get_email.short_description = "Email"
    get_email.admin_order_field = "user__email"
