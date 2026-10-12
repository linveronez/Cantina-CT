from django import template

register = template.Library()


@register.filter
def br_money(value):
    amount = value or 0
    formatted = f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"
