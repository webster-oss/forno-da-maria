import uuid
from decimal import Decimal
from django.contrib import messages
from django.db import IntegrityError
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from .cart import MAX_QUANTIDADE, quantidades, resumo, salvar
from .forms import CheckoutForm
from .models import Categoria, Pedido, Produto
from .services import CarrinhoInvalido, TAXA_ENTREGA, criar_pedido


def home(request):
    return render(request, "loja/home.html", {"destaques": Produto.objects.filter(ativo=True, destaque=True).select_related("categoria")[:4]})


def catalogo(request):
    produtos = Produto.objects.filter(ativo=True).select_related("categoria")
    query = request.GET.get("q", "").strip()[:120]
    categoria_slug = request.GET.get("categoria", "").strip()
    categoria_atual = None
    if categoria_slug:
        categoria_atual = get_object_or_404(Categoria, slug=categoria_slug)
        produtos = produtos.filter(categoria=categoria_atual)
    if query:
        produtos = produtos.filter(Q(nome__icontains=query) | Q(descricao__icontains=query))
    return render(request, "loja/catalogo.html", {"produtos": produtos, "categoria_atual": categoria_atual, "query": query})


def carrinho(request):
    itens, total = resumo(request)
    return render(request, "loja/carrinho.html", {"itens": itens, "total": total})


def _quantidade(request):
    try:
        valor = int(request.POST.get("quantidade", "1"))
    except (ValueError, TypeError):
        return None
    return valor if 1 <= valor <= MAX_QUANTIDADE else None


@require_POST
def adicionar(request, produto_id):
    produto = get_object_or_404(Produto, pk=produto_id, ativo=True)
    quantidade = _quantidade(request)
    dados = quantidades(request)
    atual = dados.get(str(produto.pk), 0)
    if quantidade is None or atual + quantidade > min(produto.estoque, MAX_QUANTIDADE):
        messages.error(request, "Quantidade indisponível. Confira o estoque no cardápio.")
    else:
        dados[str(produto.pk)] = atual + quantidade
        salvar(request, dados)
        messages.success(request, f"{produto.nome} adicionado ao carrinho.")
    # Destinos fixos evitam redirecionamento externo por parâmetros do cliente.
    return redirect("loja:carrinho" if request.POST.get("origem") == "carrinho" else "loja:catalogo")


@require_POST
def atualizar(request, produto_id):
    produto = get_object_or_404(Produto, pk=produto_id, ativo=True)
    quantidade = _quantidade(request)
    if quantidade is None or quantidade > produto.estoque:
        messages.error(request, "Quantidade inválida ou maior que o estoque disponível.")
    else:
        dados = quantidades(request)
        dados[str(produto.pk)] = quantidade
        salvar(request, dados)
        messages.success(request, "Carrinho atualizado.")
    return redirect("loja:carrinho")


@require_POST
def remover(request, produto_id):
    dados = quantidades(request)
    dados.pop(str(produto_id), None)
    salvar(request, dados)
    messages.success(request, "Produto removido do carrinho.")
    return redirect("loja:carrinho")


def checkout(request):
    # Cada sessão mantém uma tentativa ativa e os pedidos que pode consultar.
    token = request.session.get("checkout_token")
    if not token:
        token = str(uuid.uuid4())
        request.session["checkout_token"] = token
    if request.method == "POST":
        posted_token = request.POST.get("checkout_token", "")
        autorizados = request.session.get("pedidos", [])
        try:
            existente = Pedido.objects.filter(checkout_token=uuid.UUID(posted_token), codigo__in=autorizados).first()
        except (ValueError, TypeError):
            existente = None
        if existente:
            return redirect("loja:pedido", codigo=existente.codigo)
    carrinho_antes = quantidades(request)
    itens, subtotal = resumo(request)
    carrinho_alterado = carrinho_antes != quantidades(request)
    if not itens:
        messages.info(request, "Adicione produtos antes de finalizar seu pedido.")
        return redirect("loja:catalogo")
    form = CheckoutForm(request.POST or None, initial={"checkout_token": token})
    if request.method == "POST" and form.is_valid():
        if carrinho_alterado:
            form.add_error(None, "Um item ficou indisponível. Revise o resumo e confirme novamente.")
        elif str(form.cleaned_data["checkout_token"]) != token:
            form.add_error(None, "Esta tentativa expirou. Recarregue a página e tente novamente.")
        else:
            try:
                novo_pedido = criar_pedido(form.cleaned_data, quantidades(request))
            except CarrinhoInvalido as exc:
                form.add_error(None, str(exc))
            except IntegrityError:
                form.add_error(None, "Este pedido já foi enviado. Consulte a confirmação na sessão original.")
            else:
                pedidos = request.session.get("pedidos", [])
                pedidos.append(str(novo_pedido.codigo))
                request.session["pedidos"] = pedidos[-30:]
                request.session.pop("checkout_token", None)
                salvar(request, {})
                return redirect("loja:pedido", codigo=novo_pedido.codigo)
    modalidade = form.data.get("modalidade", "retirada") if form.is_bound else "retirada"
    taxa = TAXA_ENTREGA if modalidade == "entrega" else Decimal("0.00")
    return render(request, "loja/checkout.html", {"form": form, "itens": itens, "subtotal": subtotal, "taxa_entrega": taxa, "total": subtotal + taxa, "valor_taxa_entrega": TAXA_ENTREGA})


def pedido(request, codigo):
    if str(codigo) not in request.session.get("pedidos", []):
        raise Http404("Pedido não encontrado")
    registro = get_object_or_404(Pedido.objects.prefetch_related("itens"), codigo=codigo)
    return render(request, "loja/pedido.html", {"pedido": registro, "itens": registro.itens.all()})
