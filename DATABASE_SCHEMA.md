# 📊 Esquema do Banco de Dados SQLite

## Sistema de Agendamento para Estabelecimentos

Este documento apresenta a estrutura completa do banco de dados SQLite utilizado no sistema de agendamento.

---

## 📋 **Tabelas Principais do Sistema**

### 💎 **barbearias_plano**
**Planos de assinatura disponíveis no sistema**
```sql
├─ id (INTEGER) PRIMARY KEY              -- Identificador único
├─ nome (varchar(100))                   -- Nome do plano
├─ tipo (varchar(20))                    -- Tipo: basico/intermediario/avancado
├─ preco_mensal (decimal)                -- Preço mensal em reais
├─ max_profissionais (integer unsigned)  -- Máximo de profissionais (0=ilimitado)
├─ descricao (TEXT)                      -- Descrição do plano
├─ agendamento_online (bool)             -- Permite agendamento online
├─ gestao_agenda (bool)                  -- Gestão de agenda
├─ notificacoes_email (bool)             -- Notificações por email
├─ notificacoes_sms (bool)               -- Notificações por SMS
├─ integracao_google_calendar (bool)     -- Integração Google Calendar
├─ relatorios_basicos (bool)             -- Relatórios básicos
├─ relatorios_avancados (bool)           -- Relatórios avançados
├─ integracao_pagamento (bool)           -- Integração pagamentos
├─ personalizacao_completa (bool)        -- Personalização completa
├─ suporte_prioritario (bool)            -- Suporte prioritário
├─ ativo (bool)                          -- Plano ativo
├─ criado_em (datetime)                  -- Data de criação
```

### 🏪 **barbearias_barbearia**
**Estabelecimentos cadastrados no sistema**
```sql
├─ id (INTEGER) PRIMARY KEY          -- Identificador único
├─ nome (varchar(200))               -- Nome do estabelecimento
├─ endereco (TEXT)                   -- Endereço completo
├─ telefone (varchar(20))            -- Telefone de contato
├─ slug (varchar(200))               -- URL amigável (único)
├─ usuario_id (INTEGER)              -- FK: Usuário proprietário
├─ plano_id (INTEGER)                -- FK: Plano de assinatura
├─ ativa (bool)                      -- Status ativo/inativo
├─ tema (varchar(20))                -- Tema visual escolhido
├─ criada_em (datetime)              -- Data de criação
├─ email_notificacoes (varchar(254)) -- Email para notificações
```

### 👨‍💼 **barbearias_profissional**
**Profissionais que trabalham nos estabelecimentos**
```sql
├─ id (INTEGER) PRIMARY KEY    -- Identificador único
├─ nome (varchar(200))         -- Nome do profissional
├─ ativo (bool)                -- Status ativo/inativo
├─ criado_em (datetime)        -- Data de cadastro
├─ barbearia_id (bigint)       -- FK: Estabelecimento
```

### 💼 **barbearias_servico**
**Serviços oferecidos pelos estabelecimentos**
```sql
├─ id (INTEGER) PRIMARY KEY          -- Identificador único
├─ nome (varchar(200))               -- Nome do serviço
├─ preco (decimal)                   -- Preço do serviço
├─ duracao_minutos (integer unsigned)-- Duração em minutos
├─ ativo (bool)                      -- Status ativo/inativo
├─ criado_em (datetime)              -- Data de cadastro
├─ barbearia_id (bigint)             -- FK: Estabelecimento
```

### 📅 **agendamentos_agendamento**
**Agendamentos realizados pelos clientes**
```sql
├─ id (INTEGER) PRIMARY KEY     -- Identificador único
├─ nome_cliente (varchar(200))  -- Nome do cliente
├─ telefone_cliente (varchar(20))-- Telefone do cliente
├─ email_cliente (varchar(254)) -- Email do cliente
├─ data_hora (datetime)         -- Data e hora do agendamento
├─ status (varchar(20))         -- Status (agendado/confirmado/cancelado)
├─ observacoes (TEXT)           -- Observações especiais
├─ criado_em (datetime)         -- Data de criação do agendamento
├─ barbearia_id (bigint)        -- FK: Estabelecimento
├─ profissional_id (bigint)     -- FK: Profissional escolhido
├─ servico_id (bigint)          -- FK: Serviço contratado
├─ notificacao_enviada (bool)   -- Flag de notificação enviada
```

### 🕐 **barbearias_horariofuncionamento**
**Horários de funcionamento dos estabelecimentos**
```sql
├─ id (INTEGER) PRIMARY KEY -- Identificador único
├─ dia_semana (INTEGER)     -- Dia da semana (0-6)
├─ abertura (time)          -- Horário de abertura
├─ fechamento (time)        -- Horário de fechamento
├─ fechado (bool)           -- Se está fechado neste dia
├─ barbearia_id (bigint)    -- FK: Estabelecimento
```

---

## 🔐 **Tabelas de Autenticação Django**

### 👤 **auth_user**
**Usuários do sistema**
```sql
├─ id (INTEGER) PRIMARY KEY   -- Identificador único
├─ password (varchar(128))    -- Senha criptografada
├─ last_login (datetime)      -- Último login
├─ is_superuser (bool)        -- Super usuário
├─ username (varchar(150))    -- Nome de usuário (único)
├─ last_name (varchar(150))   -- Sobrenome
├─ email (varchar(254))       -- Email
├─ is_staff (bool)            -- Acesso ao admin
├─ is_active (bool)           -- Usuário ativo
├─ date_joined (datetime)     -- Data de cadastro
├─ first_name (varchar(150))  -- Primeiro nome
```

### 👥 **auth_group**
**Grupos de permissões**
```sql
├─ id (INTEGER) PRIMARY KEY -- Identificador único
├─ name (varchar(150))      -- Nome do grupo (único)
```

### 🔑 **auth_permission**
**Permissões do sistema**
```sql
├─ id (INTEGER) PRIMARY KEY     -- Identificador único
├─ content_type_id (INTEGER)    -- FK: Tipo de conteúdo
├─ codename (varchar(100))      -- Código da permissão
├─ name (varchar(255))          -- Nome da permissão
```

### 🔗 **auth_group_permissions**
**Relacionamento grupos e permissões**
```sql
├─ id (INTEGER) PRIMARY KEY -- Identificador único
├─ group_id (INTEGER)       -- FK: Grupo
├─ permission_id (INTEGER)  -- FK: Permissão
```

### 👤🔗 **auth_user_groups**
**Relacionamento usuários e grupos**
```sql
├─ id (INTEGER) PRIMARY KEY -- Identificador único
├─ user_id (INTEGER)        -- FK: Usuário
├─ group_id (INTEGER)       -- FK: Grupo
```

### 👤🔑 **auth_user_user_permissions**
**Permissões específicas dos usuários**
```sql
├─ id (INTEGER) PRIMARY KEY  -- Identificador único
├─ user_id (INTEGER)         -- FK: Usuário
├─ permission_id (INTEGER)   -- FK: Permissão
```

---

## 🛠️ **Tabelas do Sistema Django**

### 📦 **django_content_type**
**Tipos de conteúdo do Django**
```sql
├─ id (INTEGER) PRIMARY KEY  -- Identificador único
├─ app_label (varchar(100))  -- Nome da aplicação
├─ model (varchar(100))      -- Nome do modelo
```

### 🗃️ **django_migrations**
**Migrações aplicadas**
```sql
├─ id (INTEGER) PRIMARY KEY -- Identificador único
├─ app (varchar(255))       -- Nome da aplicação
├─ name (varchar(255))      -- Nome da migração
├─ applied (datetime)       -- Data de aplicação
```

### 📝 **django_admin_log**
**Log de ações do admin**
```sql
├─ id (INTEGER) PRIMARY KEY        -- Identificador único
├─ object_id (TEXT)                -- ID do objeto alterado
├─ object_repr (varchar(200))      -- Representação do objeto
├─ action_flag (smallint unsigned) -- Tipo de ação
├─ change_message (TEXT)           -- Mensagem da alteração
├─ content_type_id (INTEGER)       -- FK: Tipo de conteúdo
├─ user_id (INTEGER)               -- FK: Usuário
├─ action_time (datetime)          -- Data/hora da ação
```

### 🔐 **django_session**
**Sessões ativas**
```sql
├─ session_key (varchar(40)) PRIMARY KEY -- Chave da sessão
├─ session_data (TEXT)                   -- Dados da sessão
├─ expire_date (datetime)                -- Data de expiração
```

### 🔢 **sqlite_sequence**
**Sequências automáticas do SQLite**
```sql
├─ name ()  -- Nome da tabela
├─ seq ()   -- Próximo valor da sequência
```

---

## 🎨 **Temas Disponíveis**

O sistema suporta 8 temas visuais na tabela `barbearias_barbearia.tema`:

- 🔵 **classico** - Azul e Branco (Profissional)
- 🟡 **moderno** - Preto e Dourado (Elegante)
- 🟢 **elegante** - Cinza e Verde (Natural)
- 🟣 **vibrante** - Roxo e Rosa (Criativo)
- 🟠 **rustico** - Marrom e Laranja (Acolhedor)
- ⚫ **minimalista** - Branco e Preto (Clean)
- 🌊 **tropical** - Verde e Azul (Relaxante)
- 🤎 **vintage** - Sépia e Bege (Nostálgico)

---

## 🔗 **Relacionamentos Principais**

```
auth_user (1) ←→ (1) barbearias_barbearia
barbearias_plano (1) ←→ (N) barbearias_barbearia
barbearias_barbearia (1) ←→ (N) barbearias_profissional
barbearias_barbearia (1) ←→ (N) barbearias_servico
barbearias_barbearia (1) ←→ (N) barbearias_horariofuncionamento
barbearias_barbearia (1) ←→ (N) agendamentos_agendamento
barbearias_profissional (1) ←→ (N) agendamentos_agendamento
barbearias_servico (1) ←→ (N) agendamentos_agendamento
```

---

## 📊 **Estatísticas do Schema**

- **Total de Tabelas:** 17
- **Tabelas do Sistema:** 6
- **Tabelas de Autenticação:** 6
- **Tabelas do Django:** 5
- **Campos com Foreign Key:** 13
- **Campos Primary Key:** 17

---

## 💎 **Planos de Assinatura**

O sistema oferece 3 planos de assinatura:

### 🔵 **Plano Básico - R$ 49,00/mês**
- ✅ Agendamento online
- ✅ Gestão de agenda 
- ✅ Notificações por email
- ✅ 1 profissional
- ❌ Integração Google Calendar
- ❌ Relatórios
- ❌ SMS

### 🟡 **Plano Intermediário - R$ 89,00/mês** ⭐ *Recomendado*
- ✅ Todas do Básico
- ✅ Profissionais ilimitados
- ✅ Integração Google Calendar
- ✅ Relatórios básicos
- ❌ SMS
- ❌ Pagamentos

### 🟣 **Plano Avançado - R$ 149,00/mês** 💎 *Premium*
- ✅ Todas as funcionalidades
- ✅ Notificações SMS
- ✅ Relatórios avançados
- ✅ Integração pagamentos
- ✅ Personalização completa
- ✅ Suporte prioritário

---

*Documento gerado automaticamente em {{ date }}*
*Sistema de Agendamento para Estabelecimentos v1.0*
