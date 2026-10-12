from django.contrib import admin

from .models import Cliente, Item, MovimentoCredito, Venda, VendaItem


class VendaItemInline(admin.TabularInline):
    model = VendaItem
    extra = 0
    readonly_fields = ["item", "quantidade", "valor_unitario", "subtotal"]


@admin.register(Venda)
class VendaAdmin(admin.ModelAdmin):
    list_display = ["id", "cliente", "atendente", "total", "saldo_apos_venda", "criado_em"]
    list_filter = ["criado_em", "atendente"]
    search_fields = ["cliente__nome", "atendente__username"]
    inlines = [VendaItemInline]


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ["nome", "documento", "telefone", "credito", "atualizado_em"]
    search_fields = ["nome", "documento", "telefone"]


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ["nome", "categoria", "preco", "estoque", "estoque_minimo", "ativo"]
    list_filter = ["ativo", "categoria"]
    search_fields = ["nome", "categoria"]


@admin.register(MovimentoCredito)
class MovimentoCreditoAdmin(admin.ModelAdmin):
    list_display = ["cliente", "usuario", "valor", "tipo", "criado_em"]
    list_filter = ["tipo", "criado_em"]
    search_fields = ["cliente__nome", "usuario__username"]
