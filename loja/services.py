"""Regras de criação de pedidos e baixa transacional de estoque."""
from decimal import Decimal
from django.db import transaction
from django.db.models import F
from .models import ItemPedido, Pedido, Produto

TAXA_ENTREGA = Decimal("6.90")


class CarrinhoInvalido(ValueError):
    pass


@transaction.atomic
def criar_pedido(dados, carrinho):
    if not carrinho:
        raise CarrinhoInvalido("Seu carrinho está vazio.")
    produtos = {str(p.pk): p for p in Produto.objects.select_for_update().filter(pk__in=carrinho.keys())}
    if len(produtos) != len(carrinho):
        raise CarrinhoInvalido("Um produto foi removido. Revise seu carrinho.")
    subtotal = Decimal("0.00")
    for chave, quantidade in carrinho.items():
        p = produtos[chave]
        if not p.ativo or p.estoque < quantidade:
            raise CarrinhoInvalido(f"{p.nome}: estoque insuficiente. Revise seu carrinho.")
        subtotal += p.preco * quantidade
    taxa = TAXA_ENTREGA if dados["modalidade"] == Pedido.Modalidade.ENTREGA else Decimal("0.00")
    pedido = Pedido.objects.create(**dados, subtotal=subtotal, taxa_entrega=taxa, total=subtotal + taxa)
    for chave, quantidade in carrinho.items():
        produto = produtos[chave]
        # A condição evita estoque negativo também sob concorrência em bancos
        # que não oferecem bloqueio de linha, como SQLite.
        alterados = Produto.objects.filter(pk=produto.pk, ativo=True, estoque__gte=quantidade).update(estoque=F("estoque") - quantidade)
        if alterados != 1:
            raise CarrinhoInvalido(f"{produto.nome}: estoque alterado. Tente novamente.")
        ItemPedido.objects.create(pedido=pedido, produto=produto, nome=produto.nome, preco_unitario=produto.preco, quantidade=quantidade)
    return pedido
