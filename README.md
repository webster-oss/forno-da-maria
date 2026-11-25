# Forno da Maria

Aplicação web de uma padaria fictícia, desenvolvida em Django para a atividade de Desenvolvimento de Aplicação Web do IESB.

**Repositório do projeto:** [webster-oss/forno-da-maria](https://github.com/webster-oss/forno-da-maria)

**Discente:** Webster Alencar  
**Docentes:** Francisco e William

O cliente consulta o cardápio, monta um carrinho e registra um pedido para retirada ou entrega. A diretora administra categorias, produtos, estoque e situação dos pedidos pelo Django Admin. O pedido é uma reserva acadêmica: não existe cobrança eletrônica nem operação de uma padaria real.

## Executar no Windows

Requisitos: Python 3.12 ou superior compatível com Django 5.2 e conexão à internet na primeira instalação. A execução foi verificada com Python 3.12.14 e Django 5.2.19.

Extraia o ZIP e abra um terminal na pasta que contém `manage.py`. Execute:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe manage.py migrate
.venv\Scripts\python.exe manage.py popular_padaria
.venv\Scripts\python.exe manage.py runserver
```

Abra **http://127.0.0.1:8000/**. O arquivo `INICIAR.bat` automatiza os mesmos comandos, sem precisar ativar o ambiente virtual. O cadastro inicial pode ser executado novamente: preserva os registros já existentes.

No Linux ou macOS, use `python3 -m venv .venv` e substitua `.venv\Scripts\python.exe` por `.venv/bin/python`.

## Administrar a padaria

Em outro terminal, crie sua própria conta:

```powershell
.venv\Scripts\python.exe manage.py createsuperuser
```

Acesse **http://127.0.0.1:8000/admin/**. Nenhum usuário ou senha vem cadastrado no projeto entregue. O administrador pode cadastrar categorias e produtos, alterar estoque e acompanhar pedidos. Os valores dos itens do pedido são preservados mesmo se o preço do produto mudar depois.

## Funcionalidades

- Página inicial com destaques e explicação do pedido.
- Cardápio com pesquisa por nome/descrição e filtro por categoria.
- Carrinho por sessão com alteração de quantidade e remoção.
- Finalização com nome, telefone, e-mail opcional e observações.
- Retirada sem taxa ou entrega com taxa demonstrativa fixa de R$ 6,90 e endereço obrigatório.
- Confirmação com código, itens, modalidade e total calculado no servidor.
- Validação de estoque na finalização e redução dentro de uma transação.
- Proteção contra criação duplicada ao reenviar o mesmo checkout.
- Consulta de confirmação limitada à sessão que efetuou o pedido.
- Painel administrativo com autenticação do Django.
- Layout responsivo, imagens SVG locais e navegação por teclado.

Os dados, produtos e preços iniciais são fictícios. O site não envia e-mail ou WhatsApp, não processa pagamentos e não calcula distância, frete real ou prazo de entrega. O formulário não deve receber dados pessoais reais durante a apresentação acadêmica.

## Organização do projeto

```text
config/                  configurações, rotas globais, WSGI e ASGI
loja/models.py           categorias, produtos, pedidos e itens
loja/forms.py            validação dos dados do comprador
loja/cart.py             leitura e cálculo do carrinho em sessão
loja/services.py         criação transacional do pedido
loja/views.py            fluxo HTTP e respostas renderizadas
loja/urls.py             rotas da loja
loja/admin.py            administração de dados
loja/templates/          páginas HTML com templates Django
loja/static/             CSS, JavaScript e ilustrações SVG
loja/management/commands/popular_padaria.py
loja/migrations/         histórico do esquema do banco
loja/tests.py            testes automatizados
requirements.txt        dependências de execução
```

O padrão MVT separa os dados (`models`), o fluxo (`views`) e a apresentação (`templates`). Os arquivos estáticos não dependem de CDN. O banco SQLite é criado por `migrate`; não há banco com pedidos ou credenciais no ZIP.

## Validar

```powershell
.venv\Scripts\python.exe manage.py check
.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.venv\Scripts\python.exe manage.py test
```

Os testes verificam o cálculo do pedido, taxas, validação, proteção do estoque, envio duplicado e isolamento das sessões. Para conferir visualmente, percorra início, cardápio, carrinho, finalização e confirmação; depois abra `/admin/` com sua conta. Reduza a largura do navegador para conferir o uso em celular.

## Publicação do código no GitHub

1. O repositório destinado ao projeto foi criado em [webster-oss/forno-da-maria](https://github.com/webster-oss/forno-da-maria). Os comandos abaixo documentam o envio dos arquivos por Git.
2. Na pasta do projeto, execute os comandos abaixo com acesso autorizado à conta.

```powershell
git init
git add .
git commit -m "Implementa padaria em Django e documentacao"
git branch -M main
git remote add origin https://github.com/webster-oss/forno-da-maria.git
git push -u origin main
```

3. Após o envio, confira que os arquivos aparecem na aba Code e que a visibilidade permite ao professor acessá-los. Use **https://github.com/webster-oss/forno-da-maria** como URL de entrega do código.
4. Anexe o relatório PDF à atividade acadêmica. Uma cópia do relatório acompanha o código na pasta `docs/`.

Caso já exista um repositório, confira `git remote -v` e ajuste a origem antes do push. Nunca publique `.env`, senhas, chaves ou o banco de dados. O `.gitignore` já exclui esses arquivos. O endereço local `127.0.0.1` é apenas para executar a aplicação e não substitui a URL de hospedagem do código.

## Hospedagem da aplicação

O enunciado exige hospedagem do código; disponibilizar o site em um servidor público é uma etapa adicional. GitHub Pages não executa Django. Para executar o aplicativo em um servidor Python/Linux, instale as dependências, configure as variáveis de ambiente, aplique as migrações, execute `collectstatic` e use um servidor WSGI:

```bash
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py popular_padaria
python manage.py collectstatic --noinput
python manage.py check --deploy
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 1
```

Use `DEBUG=false`, uma `SECRET_KEY` longa gerada fora do código, o domínio correto em `ALLOWED_HOSTS` e as origens HTTPS em `CSRF_TRUSTED_ORIGINS`. As variáveis devem ser configuradas no ambiente do servidor. O arquivo `.env.example` é apenas uma referência; o projeto não carrega `.env` automaticamente.

Para esta versão acadêmica, mantenha SQLite em um volume persistente com um único processo de aplicação. Para uma padaria em produção com concorrência elevada, adote PostgreSQL, backups, infraestrutura HTTPS e testes de carga. O servidor `runserver` serve apenas para desenvolvimento.

## Referências

- Django Software Foundation. [Documentação Django 5.2](https://docs.djangoproject.com/en/5.2/).
- Django Software Foundation. [Tutorial oficial](https://docs.djangoproject.com/en/5.2/intro/tutorial01/).
- Django Software Foundation. [Checklist de implantação](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/).
- GitHub Docs. [Adicionar código local ao GitHub](https://docs.github.com/pt/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github).

Consulta em 25 de novembro de 2026. O relatório da entrega descreve as telas e as decisões de implementação desta aplicação.
