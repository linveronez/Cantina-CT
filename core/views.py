import base64
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Count, F, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ClienteForm, ClienteUpdateForm, CreditoForm, ItemEstoqueForm, ItemForm, ItemPrecoForm
from .models import Cliente, Item, MovimentoCredito, Venda, VendaItem


ROLE_OWNER = "Dono"
ROLE_COORDINATOR = "Coordenador"
ROLE_ATTENDANT = "Atendente"


def user_role(user) -> str:
    if user.is_superuser:
        return ROLE_OWNER
    group = user.groups.first()
    return group.name if group else ROLE_ATTENDANT


def can_manage_credit(user) -> bool:
    return user_role(user) in {ROLE_OWNER, ROLE_COORDINATOR}


def can_manage_clients(user) -> bool:
    return user_role(user) in {ROLE_OWNER, ROLE_COORDINATOR}


def can_debit_credit(user) -> bool:
    return user_role(user) == ROLE_OWNER


def can_manage_items(user) -> bool:
    return user_role(user) in {ROLE_OWNER, ROLE_COORDINATOR}


def can_view_reports(user) -> bool:
    return user_role(user) == ROLE_OWNER


def role_context(request) -> dict:
    return {
        "role": user_role(request.user),
        "can_manage_clients": can_manage_clients(request.user),
        "can_manage_credit": can_manage_credit(request.user),
        "can_debit_credit": can_debit_credit(request.user),
        "can_manage_items": can_manage_items(request.user),
        "can_view_reports": can_view_reports(request.user),
    }


def owner_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not can_view_reports(request.user):
            messages.error(request, "Somente o perfil Dono acessa relatorios.")
            return redirect("dashboard")
        return view_func(request, *args, **kwargs)

    return wrapper


@login_required
def dashboard(request):
    hoje_total = Venda.objects.filter(criado_em__date__isnull=False).aggregate(total=Sum("total"))["total"] or 0
    context = {
        **role_context(request),
        "clientes_total": Cliente.objects.count(),
        "itens_total": Item.objects.filter(ativo=True).count(),
        "estoque_baixo_total": Item.objects.filter(ativo=True, estoque__lte=F("estoque_minimo")).count(),
        "vendas_total": hoje_total,
        "ultimas_vendas": Venda.objects.select_related("cliente", "atendente")[:6],
    }
    return render(request, "core/dashboard.html", context)


@login_required
def clientes(request):
    if request.method == "POST":
        if not can_manage_credit(request.user):
            messages.error(request, "Atendentes nao cadastram credito inicial.")
            return redirect("clientes")
        form = ClienteForm(request.POST, request.FILES)
        if form.is_valid():
            cliente = form.save(commit=False)
            cliente.credito = form.cleaned_data.get("credito_inicial") or Decimal("0.00")
            cliente.save()
            foto = decode_camera_photo(request.POST.get("foto_base64", ""))
            if foto:
                cliente.foto.save(f"cliente-{cliente.pk}.png", foto, save=True)
            if cliente.credito:
                MovimentoCredito.objects.create(
                    cliente=cliente,
                    usuario=request.user,
                    valor=cliente.credito,
                    tipo=MovimentoCredito.CREDITO,
                    observacao="Credito inicial",
                )
            messages.success(request, "Cliente cadastrado com sucesso.")
            return redirect("clientes")
    else:
        form = ClienteForm()

    context = {
        **role_context(request),
        "form": form,
        "credito_form": CreditoForm(),
        "clientes": Cliente.objects.all(),
    }
    return render(request, "core/clientes.html", context)


@login_required
@require_POST
def atualizar_cliente(request, cliente_id):
    if not can_manage_clients(request.user):
        messages.error(request, "Somente Dono ou Coordenador atualiza cadastro de cliente.")
        return redirect("clientes")

    cliente = get_object_or_404(Cliente, pk=cliente_id)
    form = ClienteUpdateForm(request.POST, request.FILES, instance=cliente)
    if form.is_valid():
        cliente = form.save(commit=False)
        foto = decode_camera_photo(request.POST.get("foto_base64", ""))
        if form.cleaned_data["remover_foto"] and cliente.foto:
            cliente.foto.delete(save=False)
            cliente.foto = None
        if foto:
            if cliente.foto:
                cliente.foto.delete(save=False)
            cliente.foto.save(f"cliente-{cliente.pk}.png", foto, save=False)
        if form.cleaned_data["remover_comprovante_pix"] and cliente.comprovante_pix:
            cliente.comprovante_pix.delete(save=False)
            cliente.comprovante_pix = None
        cliente.save()
        messages.success(request, "Cadastro do cliente atualizado.")
    else:
        messages.error(request, "Revise os dados do cadastro.")
    return redirect("clientes")


@login_required
@require_POST
def ajustar_credito(request):
    if not can_manage_credit(request.user):
        messages.error(request, "Somente Dono ou Coordenador ajusta credito.")
        return redirect("clientes")

    form = CreditoForm(request.POST)
    if form.is_valid():
        cliente = get_object_or_404(Cliente, pk=form.cleaned_data["cliente_id"])
        valor = form.cleaned_data["valor"]
        tipo = form.cleaned_data["tipo"]
        if tipo == MovimentoCredito.DEBITO and not can_debit_credit(request.user):
            messages.error(request, "Somente o perfil Dono pode retirar credito por correcao.")
            return redirect("clientes")
        valor_final = valor if tipo == MovimentoCredito.CREDITO else -valor
        cliente.credito += valor_final
        cliente.save(update_fields=["credito", "atualizado_em"])
        MovimentoCredito.objects.create(
            cliente=cliente,
            usuario=request.user,
            valor=valor_final,
            tipo=tipo,
            observacao=form.cleaned_data["observacao"],
        )
        messages.success(request, "Credito atualizado.")
    else:
        messages.error(request, "Revise o valor informado.")
    return redirect("clientes")


@login_required
def itens(request):
    if request.method == "POST":
        if not can_manage_items(request.user):
            messages.error(request, "Somente Dono ou Coordenador cadastra itens.")
            return redirect("itens")
        form = ItemForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Item cadastrado com sucesso.")
            return redirect("itens")
    else:
        form = ItemForm(initial={"ativo": True, "estoque_minimo": 5})

    itens_query = Item.objects.all()
    busca = request.GET.get("busca", "").strip()
    categoria = request.GET.get("categoria", "").strip()
    if busca:
        itens_query = itens_query.filter(nome__icontains=busca)
    if categoria:
        itens_query = itens_query.filter(categoria=categoria)

    categorias = (
        Item.objects.exclude(categoria="")
        .values_list("categoria", flat=True)
        .distinct()
        .order_by("categoria")
    )

    context = {
        **role_context(request),
        "form": form,
        "itens": itens_query,
        "busca": busca,
        "categoria_selecionada": categoria,
        "categorias": categorias,
    }
    return render(request, "core/itens.html", context)


@login_required
@require_POST
def atualizar_preco_item(request, item_id):
    if not can_manage_items(request.user):
        messages.error(request, "Somente Dono ou Coordenador altera itens.")
        return redirect("itens")

    item = get_object_or_404(Item, pk=item_id)
    form = ItemPrecoForm(request.POST)
    if form.is_valid():
        item.preco = form.cleaned_data["preco"]
        item.save(update_fields=["preco", "atualizado_em"])
        messages.success(request, f"Preço de {item.nome} atualizado.")
    else:
        messages.error(request, "Informe um preço válido.")
    return redirect("itens")


@login_required
@require_POST
def atualizar_estoque_item(request, item_id):
    if not can_manage_items(request.user):
        messages.error(request, "Somente Dono ou Coordenador altera estoque.")
        return redirect("itens")

    item = get_object_or_404(Item, pk=item_id)
    form = ItemEstoqueForm(request.POST)
    if form.is_valid():
        item.estoque = form.cleaned_data["estoque"]
        item.save(update_fields=["estoque", "atualizado_em"])
        messages.success(request, f"Estoque de {item.nome} atualizado.")
    else:
        messages.error(request, "Informe uma quantidade válida.")
    return redirect("itens")


@login_required
@require_POST
def excluir_item(request, item_id):
    if not can_manage_items(request.user):
        messages.error(request, "Somente Dono ou Coordenador exclui itens.")
        return redirect("itens")

    item = get_object_or_404(Item, pk=item_id)
    if item.vendaitem_set.exists():
        item.ativo = False
        item.save(update_fields=["ativo", "atualizado_em"])
        messages.success(request, f"{item.nome} foi desativado para preservar o histórico de vendas.")
    else:
        nome = item.nome
        item.delete()
        messages.success(request, f"{nome} foi excluído.")
    return redirect("itens")


@login_required
def vendas(request):
    if request.method == "POST":
        return criar_venda(request)

    context = {
        **role_context(request),
        "clientes": Cliente.objects.all(),
        "itens": Item.objects.filter(ativo=True, estoque__gt=0),
    }
    return render(request, "core/vendas.html", context)


def criar_venda(request):
    cliente = get_object_or_404(Cliente, pk=request.POST.get("cliente"))
    itens_selecionados = request.POST.getlist("itens")
    if not itens_selecionados:
        messages.error(request, "Selecione pelo menos um item para vender.")
        return redirect("vendas")

    with transaction.atomic():
        itens = Item.objects.select_for_update().filter(pk__in=itens_selecionados, ativo=True)
        linhas = []
        total = Decimal("0.00")
        for item in itens:
            quantidade = int(request.POST.get(f"quantidade_{item.pk}", "1") or 1)
            quantidade = max(1, min(quantidade, item.estoque))
            subtotal = item.preco * quantidade
            total += subtotal
            linhas.append((item, quantidade, subtotal))

        if not linhas:
            messages.error(request, "Os itens selecionados nao estao disponiveis.")
            return redirect("vendas")

        cliente.credito -= total
        cliente.save(update_fields=["credito", "atualizado_em"])
        venda = Venda.objects.create(
            cliente=cliente,
            atendente=request.user,
            total=total,
            saldo_apos_venda=cliente.credito,
        )
        foto = decode_camera_photo(request.POST.get("foto_base64", ""))
        if foto:
            venda.foto.save(f"venda-{venda.pk}.png", foto, save=True)

        for item, quantidade, subtotal in linhas:
            VendaItem.objects.create(
                venda=venda,
                item=item,
                quantidade=quantidade,
                valor_unitario=item.preco,
                subtotal=subtotal,
            )
            item.estoque -= quantidade
            item.save(update_fields=["estoque", "atualizado_em"])

        MovimentoCredito.objects.create(
            cliente=cliente,
            usuario=request.user,
            valor=-total,
            tipo=MovimentoCredito.VENDA,
            observacao=f"Venda #{venda.pk}",
        )

    messages.success(request, "Venda registrada com sucesso.")
    return redirect("relatorios" if can_view_reports(request.user) else "vendas")


def decode_camera_photo(data_url: str) -> ContentFile | None:
    prefix = "data:image/png;base64,"
    if not data_url.startswith(prefix):
        return None
    return ContentFile(base64.b64decode(data_url[len(prefix):]))


@login_required
@owner_required
def relatorios(request):
    context = {
        **role_context(request),
        "vendas": Venda.objects.select_related("cliente", "atendente")[:50],
        "itens_mais_vendidos": (
            VendaItem.objects.values(nome=F("item__nome"))
            .annotate(quantidade=Sum("quantidade"), receita=Sum("subtotal"))
            .order_by("-quantidade")[:10]
        ),
        "lista_compras": Item.objects.filter(ativo=True, estoque__lte=F("estoque_minimo")).order_by("estoque"),
        "clientes_devedores": Cliente.objects.filter(credito__lt=0).order_by("credito"),
        "vendas_por_cliente": (
            Venda.objects.values(nome=F("cliente__nome"))
            .annotate(total=Sum("total"), quantidade=Count("id"))
            .order_by("-total")[:10]
        ),
    }
    return render(request, "core/relatorios.html", context)


def manifest(request):
    return JsonResponse(
        {
            "name": "Sistema de Cantina",
            "short_name": "Cantina",
            "start_url": "/",
            "display": "standalone",
            "background_color": "#f5f8ff",
            "theme_color": "#1d4ed8",
            "icons": [
                {"src": staticfiles_storage.url("core/recomecar-mark.svg"), "sizes": "any", "type": "image/svg+xml"},
            ],
        }
    )


def service_worker(request):
    content = """
const CACHE_NAME = 'cantina-pwa-v1';
const APP_SHELL = ['/', '/static/core/styles.css', '/static/core/app.js', '/offline/'];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(APP_SHELL)));
});

self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key)))));
});

self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;
  event.respondWith(fetch(event.request).catch(() => caches.match(event.request).then(response => response || caches.match('/offline/'))));
});
"""
    return HttpResponse(content, content_type="application/javascript")


def offline(request):
    return render(request, "core/offline.html")
