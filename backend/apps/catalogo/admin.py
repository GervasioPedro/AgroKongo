from decimal import Decimal

from django.contrib import admin

from apps.catalogo.models import Produto, Safra


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ["nome", "categoria"]
    list_filter = ["categoria"]
    search_fields = ["nome"]


@admin.register(Safra)
class SafraAdmin(admin.ModelAdmin):
    list_display = ["id", "produto", "produtor", "quantidade_disponivel",
                    "preco_por_unidade", "status", "criado_em"]
    list_filter = ["status", "produto__categoria"]
    search_fields = ["produto__nome", "produtor__nome"]
    autocomplete_fields = ["produtor"]

    @admin.display(description="Valor estimado")
    def valor_estimado(self, obj):
        return obj.valor_estimado or Decimal("0.00")
