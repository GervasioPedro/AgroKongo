from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from apps.accounts.models import SessaoAPI, Usuario


@admin.register(Usuario)
class UsuarioAdmin(DjangoUserAdmin):
    ordering = ["-criado_em"]
    list_display = ["nome", "telemovel", "email", "tipo", "conta_validada",
                    "rating_vendedor", "vendas_concluidas"]
    list_filter = ["tipo", "conta_validada", "provincia"]
    search_fields = ["nome", "telemovel", "email"]
    fieldsets = (
        (None, {"fields": ("telemovel", "password")}),
        ("Perfil", {"fields": ("nome", "email", "tipo", "foto_perfil",
                               "provincia", "municipio")}),
        ("Fiscal/Pagamentos", {"fields": ("nif", "iban", "saldo_disponivel")}),
        ("KYC", {"fields": ("documento_pdf", "perfil_completo", "conta_validada")}),
        ("Métricas", {"fields": ("rating_vendedor", "vendas_concluidas")}),
        ("Permissões", {"fields": ("is_active", "is_staff", "is_superuser",
                                   "groups", "user_permissions")}),
        ("Datas", {"fields": ("criado_em", "atualizado_em")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("nome", "telemovel", "tipo", "password1", "password2"),
        }),
    )
    readonly_fields = ["criado_em", "atualizado_em"]


@admin.register(SessaoAPI)
class SessaoAPIAdmin(admin.ModelAdmin):
    list_display = ["utilizador", "criado_em", "ultima_atividade", "ativa"]
    list_filter = ["ativa"]
    search_fields = ["utilizador__nome", "utilizador__telemovel"]
    readonly_fields = ["token", "criado_em", "ultima_atividade"]
