"""Testes das regras de pedido, segurança e navegação da padaria."""
import uuid
from decimal import Decimal
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from .forms import CheckoutForm
from .models import Categoria, ItemPedido, Pedido, Produto
from .services import CarrinhoInvalido, criar_pedido


@override_settings(STORAGES={"default": {"BACKEND": "django.core.files.storage.FileSystemStorage"}, "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}})
class PadariaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.categoria = Categoria.objects.create(nome="Pães", slug="paes")
        cls.produto = Produto.objects.create(categoria=cls.categoria, nome="Pão francês", slug="pao-frances", descricao="Pão fresco", preco=Decimal("1.20"), estoque=10, imagem="pao-frances", destaque=True)
        cls.outro = Produto.objects.create(categoria=cls.categoria, nome="Croissant", slug="croissant", descricao="Massa folhada", preco=Decimal("8.90"), estoque=2, imagem="croissant")

    def preparar_checkout(self, client=None, quantidade=2):
        client = client or self.client
        token = str(uuid.uuid4())
        session = client.session
        session["carrinho"] = {str(self.produto.pk): quantidade}
        session["checkout_token"] = token
        session.save()
        return {"nome": "Maria da Silva", "telefone": "(61) 99999-1234", "email": "maria@example.com", "modalidade": "retirada", "endereco": "", "observacoes": "", "checkout_token": token}

    def test_home_e_catalogo(self):
        self.assertContains(self.client.get(reverse("loja:home")), "Pão francês")
        resposta = self.client.get(reverse("loja:catalogo"), {"q": "Croissant", "categoria": "paes"})
        self.assertEqual(list(resposta.context["produtos"]), [self.outro])

    def test_categoria_inexistente_retorna_404(self):
        self.assertEqual(self.client.get(reverse("loja:catalogo"), {"categoria": "ausente"}).status_code, 404)

    def test_busca_sem_resultados(self):
        resposta = self.client.get(reverse("loja:catalogo"), {"q": "produto inexistente"})
        self.assertEqual(len(resposta.context["produtos"]), 0)

    def test_carrinho_adiciona_atualiza_remove(self):
        self.client.post(reverse("loja:adicionar", args=[self.produto.pk]), {"quantidade": 2})
        self.assertEqual(self.client.session["carrinho"][str(self.produto.pk)], 2)
        self.client.post(reverse("loja:atualizar", args=[self.produto.pk]), {"quantidade": 3})
        resposta = self.client.get(reverse("loja:carrinho"))
        self.assertEqual(resposta.context["total"], Decimal("3.60"))
        self.client.post(reverse("loja:remover", args=[self.produto.pk]))
        self.assertEqual(self.client.session["carrinho"], {})

    def test_carrinho_rejeita_quantidades_invalidas_e_estoque_excedido(self):
        for quantidade in ("abc", "0", "-1", "999", "1.5", "11"):
            with self.subTest(quantidade=quantidade):
                resposta = self.client.post(reverse("loja:adicionar", args=[self.produto.pk]), {"quantidade": quantidade})
                self.assertEqual(resposta.status_code, 302)
                self.assertNotIn(str(self.produto.pk), self.client.session.get("carrinho", {}))

    def test_adicoes_acumuladas_respeitam_estoque(self):
        self.client.post(reverse("loja:adicionar", args=[self.produto.pk]), {"quantidade": 8})
        self.client.post(reverse("loja:adicionar", args=[self.produto.pk]), {"quantidade": 3})
        self.assertEqual(self.client.session["carrinho"][str(self.produto.pk)], 8)

    def test_mutacoes_exigem_post(self):
        for nome in ("adicionar", "atualizar", "remover"):
            self.assertEqual(self.client.get(reverse(f"loja:{nome}", args=[self.produto.pk])).status_code, 405)

    def test_mutacao_exige_csrf(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post(reverse("loja:adicionar", args=[self.produto.pk]), {"quantidade": 1}).status_code, 403)

    def test_parametro_next_nao_redireciona_para_fora(self):
        resposta = self.client.post(reverse("loja:adicionar", args=[self.produto.pk]), {"quantidade": 1, "next": "https://externo.example"})
        self.assertEqual(resposta.url, reverse("loja:catalogo"))

    def test_checkout_retira_estoque_e_ignora_preco_do_cliente(self):
        dados = self.preparar_checkout()
        dados.update({"total": "0.01", "preco": "0.01", "taxa_entrega": "999"})
        resposta = self.client.post(reverse("loja:checkout"), dados)
        pedido = Pedido.objects.get()
        self.assertEqual(resposta.url, reverse("loja:pedido", args=[pedido.codigo]))
        self.assertEqual(pedido.total, Decimal("2.40"))
        self.assertEqual(pedido.taxa_entrega, Decimal("0.00"))
        self.assertEqual(pedido.itens.get().preco_unitario, Decimal("1.20"))
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.estoque, 8)
        self.assertEqual(self.client.session["carrinho"], {})

    def test_entrega_calcula_taxa_no_servidor(self):
        dados = self.preparar_checkout()
        dados.update({"modalidade": "entrega", "endereco": "Rua das Flores, 25, Centro"})
        self.client.post(reverse("loja:checkout"), dados)
        pedido = Pedido.objects.get()
        self.assertEqual(pedido.taxa_entrega, Decimal("6.90"))
        self.assertEqual(pedido.total, Decimal("9.30"))

    def test_entrega_exige_endereco_e_telefone_valido(self):
        dados = self.preparar_checkout()
        dados.update({"modalidade": "entrega", "telefone": "123", "endereco": ""})
        resposta = self.client.post(reverse("loja:checkout"), dados)
        self.assertIn("telefone", resposta.context["form"].errors)
        self.assertIn("endereco", resposta.context["form"].errors)
        self.assertFalse(Pedido.objects.exists())

    def test_reenvio_idempotente_nao_duplica_pedido(self):
        dados = self.preparar_checkout()
        primeiro = self.client.post(reverse("loja:checkout"), dados)
        segundo = self.client.post(reverse("loja:checkout"), dados)
        self.assertEqual(primeiro.url, segundo.url)
        self.assertEqual(Pedido.objects.count(), 1)
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.estoque, 8)

    def test_token_estrangeiro_rejeitado(self):
        dados = self.preparar_checkout()
        dados["checkout_token"] = str(uuid.uuid4())
        resposta = self.client.post(reverse("loja:checkout"), dados)
        self.assertTrue(resposta.context["form"].non_field_errors())
        self.assertFalse(Pedido.objects.exists())

    def test_outra_sessao_nao_consulta_confirmacao(self):
        self.client.post(reverse("loja:checkout"), self.preparar_checkout())
        pedido = Pedido.objects.get()
        url = reverse("loja:pedido", args=[pedido.codigo])
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(Client().get(url).status_code, 404)

    def test_estoque_alterado_impede_checkout(self):
        dados = self.preparar_checkout(quantidade=3)
        Produto.objects.filter(pk=self.produto.pk).update(estoque=1)
        resposta = self.client.post(reverse("loja:checkout"), dados)
        self.assertTrue(resposta.context["form"].non_field_errors())
        self.assertFalse(Pedido.objects.exists())
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.estoque, 1)

    def test_produto_inativo_nao_pode_ser_comprado(self):
        self.produto.ativo = False
        self.produto.save()
        self.assertEqual(self.client.post(reverse("loja:adicionar", args=[self.produto.pk]), {"quantidade": 1}).status_code, 404)
        dados = CheckoutForm(self.preparar_checkout()).data
        with self.assertRaises(CarrinhoInvalido):
            criar_pedido({**dados, "checkout_token": uuid.uuid4()}, {str(self.produto.pk): 1})
        self.assertFalse(Pedido.objects.exists())

    def test_falha_ao_gravar_item_reverte_pedido_e_estoque(self):
        form = CheckoutForm(self.preparar_checkout())
        self.assertTrue(form.is_valid())
        with patch("loja.services.ItemPedido.objects.create", side_effect=RuntimeError("falha simulada")):
            with self.assertRaises(RuntimeError):
                criar_pedido(form.cleaned_data, {str(self.produto.pk): 2})
        self.assertFalse(Pedido.objects.exists())
        self.assertFalse(ItemPedido.objects.exists())
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.estoque, 10)

    def test_produto_removido_rejeita_carrinho(self):
        form = CheckoutForm(self.preparar_checkout())
        self.assertTrue(form.is_valid())
        with self.assertRaises(CarrinhoInvalido):
            criar_pedido(form.cleaned_data, {"999999": 2})

    def test_carrinho_remove_item_inativo_sem_bloquear_itens_validos(self):
        dados = self.preparar_checkout()
        session = self.client.session
        session["carrinho"][str(self.outro.pk)] = 1
        session.save()
        Produto.objects.filter(pk=self.outro.pk).update(ativo=False)
        self.client.get(reverse("loja:carrinho"))
        self.assertEqual(self.client.session["carrinho"], {str(self.produto.pk): 2})
        self.client.post(reverse("loja:checkout"), dados)
        self.assertEqual(Pedido.objects.count(), 1)

    def test_carrinho_remove_item_excluido(self):
        self.preparar_checkout()
        session = self.client.session
        session["carrinho"][str(self.outro.pk)] = 1
        session.save()
        self.outro.delete()
        resposta = self.client.get(reverse("loja:carrinho"))
        self.assertEqual(len(resposta.context["itens"]), 1)
        self.assertEqual(self.client.session["carrinho"], {str(self.produto.pk): 2})

    def test_checkout_pede_revisao_quando_item_fica_indisponivel(self):
        dados = self.preparar_checkout()
        session = self.client.session
        session["carrinho"][str(self.outro.pk)] = 1
        session.save()
        Produto.objects.filter(pk=self.outro.pk).update(ativo=False)
        resposta = self.client.post(reverse("loja:checkout"), dados)
        self.assertTrue(resposta.context["form"].non_field_errors())
        self.assertFalse(Pedido.objects.exists())

    def test_snapshot_do_item_preserva_historico(self):
        self.client.post(reverse("loja:checkout"), self.preparar_checkout())
        Produto.objects.filter(pk=self.produto.pk).update(nome="Nome alterado", preco=Decimal("99.00"))
        item = ItemPedido.objects.get()
        self.assertEqual(item.nome, "Pão francês")
        self.assertEqual(item.subtotal, Decimal("2.40"))

    def test_admin_exige_login_e_lista_pedidos(self):
        resposta = self.client.get(reverse("admin:loja_pedido_changelist"))
        self.assertEqual(resposta.status_code, 302)
        admin = get_user_model().objects.create_superuser("gestora", "gestora@example.com", "senha-forte-de-teste-123")
        self.client.force_login(admin)
        self.assertEqual(self.client.get(reverse("admin:loja_pedido_changelist")).status_code, 200)
