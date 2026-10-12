from decimal import Decimal

from django.conf import settings
from django.db import models
from django.urls import reverse


class Cliente(models.Model):
    nome = models.CharField(max_length=160)
    documento = models.CharField(max_length=60, blank=True)
    telefone = models.CharField(max_length=40, blank=True)
    foto = models.FileField(upload_to="clientes/", blank=True, null=True)
    credito = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    comprovante_pix = models.FileField(upload_to="pix/", blank=True, null=True)
    observacoes = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nome"]
        verbose_name = "cliente"
        verbose_name_plural = "clientes"

    def __str__(self) -> str:
        return self.nome

    def get_absolute_url(self) -> str:
        return reverse("clientes")


class Item(models.Model):
    nome = models.CharField(max_length=140)
    categoria = models.CharField(max_length=80, blank=True)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    estoque = models.PositiveIntegerField(default=0)
    estoque_minimo = models.PositiveIntegerField(default=5)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nome"]
        verbose_name = "item"
        verbose_name_plural = "itens"

    def __str__(self) -> str:
        return self.nome

    @property
    def estoque_baixo(self) -> bool:
        return self.ativo and self.estoque <= self.estoque_minimo


class Venda(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name="vendas")
    atendente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="vendas")
    total = models.DecimalField(max_digits=10, decimal_places=2)
    saldo_apos_venda = models.DecimalField(max_digits=10, decimal_places=2)
    foto = models.FileField(upload_to="vendas/", blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "venda"
        verbose_name_plural = "vendas"

    def __str__(self) -> str:
        return f"Venda #{self.pk} - {self.cliente}"


class VendaItem(models.Model):
    venda = models.ForeignKey(Venda, on_delete=models.CASCADE, related_name="itens")
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    quantidade = models.PositiveIntegerField()
    valor_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "item da venda"
        verbose_name_plural = "itens da venda"

    def __str__(self) -> str:
        return f"{self.quantidade}x {self.item}"


class MovimentoCredito(models.Model):
    CREDITO = "credito"
    DEBITO = "debito"
    VENDA = "venda"

    TIPOS = [
        (CREDITO, "Credito"),
        (DEBITO, "Retirada"),
        (VENDA, "Venda"),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="movimentos_credito")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="movimentos_credito")
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    tipo = models.CharField(max_length=20, choices=TIPOS)
    observacao = models.CharField(max_length=180, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "movimento de credito"
        verbose_name_plural = "movimentos de credito"

    def __str__(self) -> str:
        return f"{self.cliente} - {self.valor}"
