"""Carrinho: a sessão guarda somente IDs e quantidades; preços vêm do banco."""
from decimal import Decimal
from django.contrib import messages
from .models import Produto

CART_KEY = "carrinho"
MAX_QUANTIDADE = 99


def quantidades(request):
    raw = request.session.get(CART_KEY, {})
    if not isinstance(raw, dict):
        return {}
    return {str(k): v for k, v in raw.items() if str(k).isdigit() and isinstance(v, int) and not isinstance(v, bool) and 1 <= v <= MAX_QUANTIDADE}


def salvar(request, dados):
    request.session[CART_KEY] = dados
    request.session.modified = True


def resumo(request):
    dados = quantidades(request)
    produtos = list(Produto.objects.filter(pk__in=dados.keys(), ativo=True).select_related("categoria"))
    validos = {str(p.pk): dados[str(p.pk)] for p in produtos}
    if validos != request.session.get(CART_KEY, {}):
        salvar(request, validos)
        messages.info(request, "Um produto indisponível foi removido do carrinho. Revise os itens antes de finalizar.")
    itens = [{"produto": p, "quantidade": dados[str(p.pk)], "subtotal": p.preco * dados[str(p.pk)]} for p in produtos]
    total = sum((item["subtotal"] for item in itens), Decimal("0.00"))
    return itens, total
