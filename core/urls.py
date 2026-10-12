from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("clientes/", views.clientes, name="clientes"),
    path("clientes/<int:cliente_id>/atualizar/", views.atualizar_cliente, name="atualizar_cliente"),
    path("clientes/credito/", views.ajustar_credito, name="ajustar_credito"),
    path("itens/", views.itens, name="itens"),
    path("itens/<int:item_id>/preco/", views.atualizar_preco_item, name="atualizar_preco_item"),
    path("itens/<int:item_id>/estoque/", views.atualizar_estoque_item, name="atualizar_estoque_item"),
    path("itens/<int:item_id>/excluir/", views.excluir_item, name="excluir_item"),
    path("vendas/", views.vendas, name="vendas"),
    path("relatorios/", views.relatorios, name="relatorios"),
    path("manifest.webmanifest", views.manifest, name="manifest"),
    path("service-worker.js", views.service_worker, name="service_worker"),
    path("offline/", views.offline, name="offline"),
]
