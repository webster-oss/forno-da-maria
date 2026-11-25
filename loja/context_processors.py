from .cart import resumo
from .models import Categoria

def loja(request):
    itens, total = resumo(request)
    return {"cart_count": sum(i["quantidade"] for i in itens), "cart_total": total, "categorias": Categoria.objects.all()}
