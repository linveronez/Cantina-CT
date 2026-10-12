from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Cria perfis e usuarios iniciais do sistema."

    def handle(self, *args, **options):
        users = [
            ("Dono", "dono", "123456", True),
            ("Coordenador", "coordenador", "123456", False),
            ("Atendente", "atendente", "123456", False),
        ]
        for group_name, username, password, is_staff in users:
            group, _ = Group.objects.get_or_create(name=group_name)
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": group_name,
                    "is_staff": is_staff,
                    "is_superuser": group_name == "Dono",
                },
            )
            if created:
                user.set_password(password)
            user.is_staff = is_staff
            user.groups.set([group])
            user.save()
            status = "criado" if created else "atualizado"
            self.stdout.write(self.style.SUCCESS(f"Usuario {username} {status}."))
