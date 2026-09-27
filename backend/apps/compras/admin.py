from django.contrib import admin

from apps.compras.models import Comprovativo, HistoricoStatus, Transacao


class HistoricoInline(admin.TabularInline):
    model = HistoricoStatus
    extra = 0
    can_delete = False
    readonly_fields = ["status_anterior", "status_novo", "data_mudanca", "observacao"]
    ordering = ["data_mudanca"]


@admin.register(Transacao)
class TransacaoAdmin(admin.ModelAdmin):
    list_display = ["fatura_ref", "produto_nome", "comprador", "vendedor",
                    "valor_total_pago", "status", "criado_em"]
    list_filter = ["status"]
    search_fields = ["fatura_ref", "comprador__nome", "vendedor__nome"]
    autocomplete_fields = ["comprador", "vendedor"]
    inlines = [HistoricoInline]
    readonly_fields = ["fatura_ref", "comissao_plataforma",
                       "valor_liquido_vendedor", "criado_em", "atualizado_em"]

    @admin.display(description="Produto")
    def produto_nome(self, obj):
        return obj.safra.produto.nome


@admin.register(HistoricoStatus)
class HistoricoStatusAdmin(admin.ModelAdmin):
    list_display = ["transacao", "status_anterior", "status_novo", "data_mudanca"]
    list_filter = ["status_novo"]
    search_fields = ["transacao__fatura_ref"]


@admin.register(Comprovativo)
class ComprovativoAdmin(admin.ModelAdmin):
    list_display = ["id", "transacao", "enviado_por", "validado", "enviado_em"]
    list_filter = ["validado"]
