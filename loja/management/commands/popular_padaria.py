from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from loja.models import Categoria, Produto


class Command(BaseCommand):
    help = "Cria categorias e produtos demonstrativos sem alterar produtos existentes."

    @transaction.atomic
    def handle(self, *args, **options):
        categorias = {slug: Categoria.objects.get_or_create(slug=slug, defaults={"nome": nome})[0] for slug, nome in [("paes", "Pães"), ("doces", "Doces e bolos"), ("salgados", "Salgados"), ("bebidas", "Bebidas"), ("combos", "Combos")]}
        produtos = [
            ("pao-frances", "Pão francês", "Casquinha crocante e miolo macio. Unidade de aproximadamente 50 g.", "1.20", 120, "paes", True),
            ("croissant", "Croissant de manteiga", "Massa folhada em camadas, assada até ficar dourada. Unidade.", "8.90", 32, "paes", True),
            ("pao-integral", "Pão integral de sementes", "Pão de forma com farinha integral e sementes. Peça de 450 g.", "16.90", 18, "paes", False),
            ("bolo-cenoura", "Bolo de cenoura", "Fatia generosa com cobertura de chocolate. Porção de 120 g.", "9.50", 24, "doces", True),
            ("pao-queijo", "Pão de queijo", "Tradicional e quentinho, com queijo de verdade. Porção de 5 unidades.", "7.90", 40, "salgados", True),
            ("sonho", "Sonho de creme", "Massa macia recheada com creme de baunilha e açúcar. Unidade.", "6.50", 25, "doces", False),
            ("cafe", "Café coado", "Café brasileiro passado na hora. Copo de 200 ml.", "4.50", 60, "bebidas", False),
            ("combo", "Café da manhã da Maria", "Dois pães franceses, porção de pão de queijo e dois cafés coados.", "18.90", 20, "combos", False),
        ]
        criados = 0
        for slug, nome, descricao, preco, estoque, categoria, destaque in produtos:
            _, novo = Produto.objects.get_or_create(slug=slug, defaults={"nome": nome, "descricao": descricao, "preco": Decimal(preco), "estoque": estoque, "categoria": categorias[categoria], "destaque": destaque, "imagem": slug})
            criados += novo
        self.stdout.write(self.style.SUCCESS(f"Padaria pronta: {criados} novos produtos; {Produto.objects.count()} produtos cadastrados."))
