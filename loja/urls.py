from django.urls import path
from . import views
app_name = "loja"
urlpatterns = [
    path("", views.home, name="home"),
    path("cardapio/", views.catalogo, name="catalogo"),
    path("carrinho/", views.carrinho, name="carrinho"),
    path("carrinho/adicionar/<int:produto_id>/", views.adicionar, name="adicionar"),
    path("carrinho/atualizar/<int:produto_id>/", views.atualizar, name="atualizar"),
    path("carrinho/remover/<int:produto_id>/", views.remover, name="remover"),
    path("finalizar/", views.checkout, name="checkout"),
    path("pedido/<uuid:codigo>/", views.pedido, name="pedido"),
]
