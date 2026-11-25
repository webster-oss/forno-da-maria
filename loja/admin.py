from django.contrib import admin
from .models import Categoria, ItemPedido, Pedido, Produto


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ["nome", "slug"]
    prepopulated_fields = {"slug": ("nome",)}


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ["nome", "categoria", "preco", "estoque", "ativo", "destaque"]
    list_filter = ["categoria", "ativo", "destaque"]
    list_editable = ["preco", "estoque", "ativo", "destaque"]
    search_fields = ["nome", "descricao"]
    prepopulated_fields = {"slug": ("nome",)}


class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    fields = ["nome", "preco_unitario", "quantidade", "subtotal"]
    readonly_fields = fields
    extra = 0
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ["numero", "nome", "modalidade", "total", "status", "criado_em"]
    list_filter = ["status", "modalidade", "criado_em"]
    search_fields = ["nome", "telefone", "codigo"]
    readonly_fields = ["codigo", "checkout_token", "nome", "telefone", "email", "modalidade", "endereco", "observacoes", "subtotal", "taxa_entrega", "total", "criado_em"]
    fields = readonly_fields + ["status"]
    inlines = [ItemPedidoInline]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
