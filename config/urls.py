from django.contrib import admin
from django.urls import include, path

urlpatterns = [path("admin/", admin.site.urls), path("", include("loja.urls"))]
admin.site.site_header = "Forno da Maria"
admin.site.site_title = "Gestão da padaria"
admin.site.index_title = "Produtos e pedidos"
