import uuid
from decimal import Decimal
from django.core.validators import MinValueValidator
from django.db import models


class Categoria(models.Model):
    nome = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ["nome"]
        verbose_name = "categoria"
        verbose_name_plural = "categorias"

    def __str__(self):
        return self.nome


class Produto(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name="produtos")
    nome = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    descricao = models.TextField(max_length=600)
    preco = models.DecimalField("preço", max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    estoque = models.PositiveIntegerField(default=0)
    ativo = models.BooleanField(default=True)
    destaque = models.BooleanField(default=False)
    imagem = models.SlugField(help_text="Nome da ilustração SVG em static/loja/img, sem a extensão.")

    class Meta:
        ordering = ["nome"]
        constraints = [models.CheckConstraint(condition=models.Q(preco__gt=0), name="produto_preco_positivo")]

    def __str__(self):
        return self.nome


class Pedido(models.Model):
    class Modalidade(models.TextChoices):
        RETIRADA = "retirada", "Retirada na padaria"
        ENTREGA = "entrega", "Entrega em casa"

    class Status(models.TextChoices):
        RECEBIDO = "recebido", "Recebido"
        PREPARANDO = "preparando", "Em preparo"
        PRONTO = "pronto", "Pronto para retirada ou entrega"
        CONCLUIDO = "concluido", "Concluído"

    codigo = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    checkout_token = models.UUIDField(unique=True, editable=False)
    nome = models.CharField(max_length=120)
    telefone = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    modalidade = models.CharField(max_length=10, choices=Modalidade.choices)
    endereco = models.CharField("endereço", max_length=300, blank=True)
    observacoes = models.TextField("observações", max_length=600, blank=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    taxa_entrega = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.RECEBIDO)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-criado_em"]

    @property
    def numero(self):
        return str(self.codigo).split("-")[0].upper()

    def __str__(self):
        return f"{self.numero} - {self.nome}"


class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="itens")
    produto = models.ForeignKey(Produto, on_delete=models.SET_NULL, null=True, blank=True)
    nome = models.CharField(max_length=120)
    preco_unitario = models.DecimalField(max_digits=8, decimal_places=2)
    quantidade = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        verbose_name = "item do pedido"
        verbose_name_plural = "itens do pedido"
        constraints = [models.CheckConstraint(condition=models.Q(quantidade__gt=0), name="item_quantidade_positiva")]

    @property
    def subtotal(self):
        return self.preco_unitario * self.quantidade

    def __str__(self):
        return f"{self.quantidade} x {self.nome}"
