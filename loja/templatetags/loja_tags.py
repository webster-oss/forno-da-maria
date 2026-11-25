from decimal import Decimal, InvalidOperation
from django import template
register = template.Library()

@register.filter
def moeda(valor):
    try:
        texto = f"{Decimal(valor):,.2f}"
    except (InvalidOperation, TypeError, ValueError):
        return "R$ 0,00"
    return "R$ " + texto.replace(",", "_").replace(".", ",").replace("_", ".")
