# Sistema de Cantina - Projeto Integrador

Eu desenvolvo este sistema web para controlar a operação de uma cantina institucional fictícia. A proposta resolve o cadastro de clientes, controle de crédito, cadastro de itens, registro de vendas, baixa de estoque, captura de foto no momento da venda e relatórios básicos para acompanhamento do dono.

## Minha proposta

Eu organizo o sistema em quatro áreas principais:

- Clientes: cadastro do acolhido/paciente, saldo de crédito e comprovante Pix opcional.
- Itens: cadastro dos produtos da cantina, preço, estoque e estoque mínimo.
- Vendas: seleção do cliente, seleção dos itens, cálculo automático, desconto do crédito e captura de foto pelo celular ou webcam.
- Relatórios: vendas recentes, itens mais vendidos, clientes em débito e lista de compras baseada em estoque baixo.

## Perfis de acesso

| Perfil | O que eu permito |
| --- | --- |
| Dono | Acesso total, incluindo relatórios e lista de compras. |
| Coordenador | Cadastro de clientes, créditos, itens e vendas. |
| Atendente | Registro de vendas. |

## Como eu executo localmente

```powershell
.venv\Scripts\python.exe manage.py migrate
.venv\Scripts\python.exe manage.py seed
.venv\Scripts\python.exe manage.py runserver
```

Depois eu acesso:

```text
http://127.0.0.1:8000
```

## Usuários iniciais

| Perfil | Usuário | Senha |
| --- | --- | --- |
| Dono | dono | 123456 |
| Coordenador | coordenador | 123456 |
| Atendente | atendente | 123456 |

## PWA e uso no celular

Eu preparo o sistema como PWA, com manifesto, service worker e layout responsivo. Assim, em um ambiente com HTTPS, o navegador do celular pode instalar o sistema como aplicativo e liberar a câmera do smartphone para capturar a foto da venda.

## Banco de dados e hospedagem

No desenvolvimento local eu uso SQLite para facilitar testes. Para hospedagem, deixo a configuração preparada para PostgreSQL por variáveis de ambiente:

- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_PORT`

Em produção, eu também devo configurar armazenamento persistente para fotos e comprovantes, como S3, Cloudinary, Supabase Storage ou Vercel Blob.

## Antes de subir no Git

Eu mantenho fora do repositório os arquivos locais de execução:

- `.venv/`
- `db.sqlite3`
- `media/`
- `staticfiles/`
- `.env`

Para preparar a versão que vai ao Git, eu verifico:

```powershell
.venv\Scripts\python.exe manage.py check
.venv\Scripts\python.exe manage.py collectstatic --noinput
```

O PWA já possui:

- `manifest.webmanifest`
- `service-worker.js`
- logo institucional da Recomeçar
- layout responsivo para notebook e celular

Para testar instalação como aplicativo no celular, eu devo publicar em ambiente com HTTPS. A câmera do navegador funciona de forma mais confiável em HTTPS ou em `localhost`.

## Marcadores para a entrega

- Eu apresento o problema: a cantina precisa controlar crédito, estoque e vendas por cliente.
- Eu justifico a solução: o sistema reduz registros manuais, facilita auditoria e gera relatórios básicos.
- Eu demonstro os perfis: atendente vende, coordenador controla crédito e estoque, dono acompanha relatórios.
- Eu demonstro uma venda: seleciono cliente, itens, capturo foto e finalizo.
- Eu mostro os impactos: saldo atualizado, estoque baixado, venda registrada e relatório alimentado.
