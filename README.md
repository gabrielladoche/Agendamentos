# Sistema de Agendamento para Estabelecimentos

Sistema completo de agendamento desenvolvido em Django para barbearias e estabelecimentos similares, com gestão de planos de assinatura, controle de profissionais, relatórios e notificações automatizadas.

## 🚀 Funcionalidades

### 💼 Sistema de Planos de Assinatura
- **Plano Básico**: 1 profissional, 50 agendamentos/mês
- **Plano Intermediário**: Profissionais ilimitados, 200 agendamentos/mês, relatórios básicos
- **Plano Avançado**: Profissionais ilimitados, agendamentos ilimitados, relatórios avançados, integrações premium

### 👥 Gestão de Profissionais
- Controle automático de limites por plano
- Desativação automática quando excede limite do plano
- Estatísticas individuais de cada profissional

### 📅 Sistema de Agendamentos
- Interface pública para clientes agendarem
- Painel administrativo para gestão
- Verificação automática de disponibilidade
- Controle de horários de funcionamento

### 📊 Relatórios e Analytics
- Relatórios mensais em PDF e CSV
- Estatísticas de faturamento
- Serviços mais populares
- Análise de crescimento

### 🔔 Notificações
- Email automático para novos agendamentos
- Lembretes por email para clientes
- Sistema de notificações configurável

### 🎨 Personalização
- Sistema de temas (8 temas disponíveis)
- Configurações personalizáveis por estabelecimento
- Mini-site público para cada barbearia

## 🛠️ Tecnologias

- **Backend**: Django 5.2.4
- **Banco de Dados**: SQLite (produção preparada para MySQL)
- **Frontend**: HTML5, CSS3, JavaScript, Tailwind CSS
- **Relatórios**: ReportLab (PDF)
- **Email**: Django Email Framework
- **Autenticação**: Django Auth System

## 📋 Requisitos

### Dependências Python
```bash
Django==5.2.4
reportlab>=4.0.0
python-decouple>=3.8
```

### Requisitos do Sistema
- Python 3.8+
- SQLite3 (incluído no Python)
- Para produção: MySQL 8.0+ (preparado para migração)

## ⚙️ Instalação e Configuração

### 1. Clone o Repositório
```bash
git clone https://github.com/gabrielladoche/Agendamento-Estabelecimentos.git
cd Agendamento-Estabelecimentos
```

### 2. Ambiente Virtual
```bash
python -m venv venv

# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 4. Configurar Banco de Dados (SQLite)
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Criar Superusuário
```bash
python manage.py createsuperuser
```

### 6. Carregar Dados Iniciais
```bash
# Criar planos de assinatura
python manage.py shell
>>> from barbearias.models import Plano
>>> Plano.objects.create(nome="Básico", preco_mensal=29.90, max_profissionais=1, agendamentos_mes=50, ativo=True)
>>> Plano.objects.create(nome="Intermediário", preco_mensal=59.90, max_profissionais=0, agendamentos_mes=200, relatorios_basicos=True, ativo=True)
>>> Plano.objects.create(nome="Avançado", preco_mensal=99.90, max_profissionais=0, agendamentos_mes=0, relatorios_basicos=True, relatorios_avancados=True, integracao_pagamento=True, ativo=True)
>>> exit()
```

### 7. Executar Servidor
```bash
python manage.py runserver
```

O sistema estará disponível em: `http://127.0.0.1:8000`

## 🗄️ Banco de Dados

### Atual: SQLite
O sistema utiliza SQLite para desenvolvimento e testes:
- Arquivo: `db.sqlite3`
- Configuração automática
- Ideal para desenvolvimento e pequenos deployments

### Migração para MySQL (Preparado)
O sistema está preparado para migração para MySQL:

1. **Instalar driver MySQL**:
```bash
pip install mysqlclient
```

2. **Configurar settings.py**:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'agendamento_db',
        'USER': 'seu_usuario',
        'PASSWORD': 'sua_senha',
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
}
```

3. **Executar migrações**:
```bash
python manage.py migrate
```

## 📁 Estrutura do Projeto

```
Agendamento-Estabelecimentos/
├── barbearia_system/          # Configurações principais do Django
├── barbearias/                # App principal - gestão de estabelecimentos
│   ├── models.py             # Modelos (Barbearia, Plano, Profissional, etc.)
│   ├── views.py              # Views e lógica de negócio
│   ├── forms.py              # Formulários
│   ├── admin.py              # Interface administrativa
│   ├── management/commands/   # Comandos personalizados
│   └── migrations/           # Migrações do banco
├── agendamentos/             # App de agendamentos
│   ├── models.py             # Modelo Agendamento
│   ├── forms.py              # Formulários de agendamento
│   ├── utils.py              # Utilitários (email, etc.)
│   └── management/commands/   # Comandos de notificação
├── templates/                # Templates HTML
│   ├── barbearias/          # Templates de barbearias
│   ├── agendamentos/        # Templates de agendamentos
│   └── emails/              # Templates de email
├── static/                   # Arquivos estáticos (CSS, JS, imagens)
├── db.sqlite3               # Banco de dados SQLite
└── manage.py                # Comando principal Django
```

## 🔧 Comandos Úteis

### Gestão de Planos
```bash
# Aplicar limites de profissionais automaticamente
python manage.py aplicar_limites_planos

# Relatório de conformidade dos planos
python manage.py relatorio_planos
```

### Notificações
```bash
# Enviar notificações diárias
python manage.py enviar_notificacoes

# Testar sistema de notificação
python manage.py testar_notificacao
```

### Testes
```bash
# Testar agendamento
python manage.py testar_agendamento
```

## 🌐 URLs Principais

### Público
- `/` - Redirecionamento para estabelecimento padrão
- `/{slug}/` - Mini-site público da barbearia
- `/{slug}/agendar/` - Formulário de agendamento
- `/{slug}/consultar/` - Consulta de agendamentos por telefone

### Administrativo
- `/{slug}/admin/` - Painel administrativo
- `/{slug}/admin/dashboard/` - Dashboard principal
- `/{slug}/admin/planos/` - Gestão de planos
- `/{slug}/admin/profissionais/` - Gestão de profissionais
- `/{slug}/admin/servicos/` - Gestão de serviços
- `/{slug}/admin/agendamentos/` - Lista de agendamentos
- `/{slug}/admin/relatorios/` - Relatórios e exports

## 💳 Sistema de Planos

### Plano Básico (R$ 29,90/mês)
- ✅ 1 profissional
- ✅ 50 agendamentos/mês
- ✅ Interface básica

### Plano Intermediário (R$ 59,90/mês)
- ✅ Profissionais ilimitados
- ✅ 200 agendamentos/mês
- ✅ Relatórios básicos
- ✅ Exportação PDF/CSV

### Plano Avançado (R$ 99,90/mês)
- ✅ Profissionais ilimitados
- ✅ Agendamentos ilimitados
- ✅ Relatórios avançados
- ✅ Integrações premium
- ✅ Suporte prioritário

## 🔒 Segurança

- Autenticação obrigatória para áreas administrativas
- Validação de permissões por estabelecimento
- Controle de acesso baseado em planos
- Sanitização de dados de entrada
- Proteção CSRF habilitada

## 📧 Configuração de Email

Configure as variáveis de ambiente para notificações:

```python
# settings.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'seu-smtp-host'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'seu-email'
EMAIL_HOST_PASSWORD = 'sua-senha'
DEFAULT_FROM_EMAIL = 'sistema@seudomain.com'
```

## 🚀 Deploy e Produção

### Preparação para MySQL
1. Configurar servidor MySQL
2. Atualizar `DATABASES` no settings
3. Instalar `mysqlclient`
4. Executar migrações
5. Configurar backup automático

### Configurações de Produção
```python
DEBUG = False
ALLOWED_HOSTS = ['seudominio.com']
STATIC_ROOT = '/path/to/static/'
MEDIA_ROOT = '/path/to/media/'
```

## 📝 Logs e Monitoramento

- Logs de agendamento em `server.log`
- Logs de notificação automática
- Monitoramento de conformidade de planos

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para detalhes.

## 📞 Suporte

Para suporte técnico ou dúvidas:
- Email: suporte@seudomain.com
- Issues: [GitHub Issues](https://github.com/gabrielladoche/Agendamento-Estabelecimentos/issues)

## 🗓️ Roadmap

- [ ] Interface mobile responsiva
- [ ] Integração com WhatsApp
- [ ] Sistema de pagamento online
- [ ] API REST completa
- [ ] Aplicativo mobile
- [ ] Integração com Google Calendar
- [ ] Sistema de avaliações
- [ ] Multi-idioma

---

Desenvolvido com ❤️ para facilitar o gerenciamento de estabelecimentos e melhorar a experiência dos clientes.
