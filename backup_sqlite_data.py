#!/usr/bin/env python3
"""
Script para fazer backup dos dados SQLite antes da migração para MySQL
"""
import os
import sys
import django
import json
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'barbearia_system.settings')

# Temporariamente usar SQLite para backup
import tempfile
from django.conf import settings

# Backup da configuração atual
current_db_config = settings.DATABASES['default'].copy()

# Configurar SQLite temporariamente para backup
settings.DATABASES['default'] = {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': settings.BASE_DIR / 'db.sqlite3',
}

django.setup()

from django.contrib.auth.models import User
from barbearias.models import Barbearia, Plano, Servico, Profissional, HorarioFuncionamento
from agendamentos.models import Agendamento

def backup_data():
    """Faz backup de todos os dados em JSON"""
    backup_data = {
        'timestamp': datetime.now().isoformat(),
        'users': [],
        'planos': [],
        'barbearias': [],
        'servicos': [],
        'profissionais': [],
        'horarios': [],
        'agendamentos': []
    }
    
    print("📦 Fazendo backup dos dados SQLite...")
    
    # Backup Users
    for user in User.objects.all():
        backup_data['users'].append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'date_joined': user.date_joined.isoformat() if user.date_joined else None,
        })
    
    # Backup Planos
    for plano in Plano.objects.all():
        backup_data['planos'].append({
            'id': plano.id,
            'nome': plano.nome,
            'tipo': plano.tipo,
            'preco_mensal': str(plano.preco_mensal),
            'max_profissionais': plano.max_profissionais,
            'descricao': plano.descricao,
            'agendamento_online': plano.agendamento_online,
            'gestao_agenda': plano.gestao_agenda,
            'notificacoes_email': plano.notificacoes_email,
            'notificacoes_sms': plano.notificacoes_sms,
            'integracao_google_calendar': plano.integracao_google_calendar,
            'relatorios_basicos': plano.relatorios_basicos,
            'relatorios_avancados': plano.relatorios_avancados,
            'integracao_pagamento': plano.integracao_pagamento,
            'personalizacao_completa': plano.personalizacao_completa,
            'suporte_prioritario': plano.suporte_prioritario,
            'ativo': plano.ativo,
            'criado_em': plano.criado_em.isoformat() if plano.criado_em else None,
        })
    
    # Backup Barbearias
    for barbearia in Barbearia.objects.all():
        backup_data['barbearias'].append({
            'id': barbearia.id,
            'nome': barbearia.nome,
            'endereco': barbearia.endereco,
            'telefone': barbearia.telefone,
            'email_notificacoes': barbearia.email_notificacoes,
            'slug': barbearia.slug,
            'usuario_id': barbearia.usuario_id,
            'plano_id': barbearia.plano_id if barbearia.plano else None,
            'ativa': barbearia.ativa,
            'tema': barbearia.tema,
            'criada_em': barbearia.criada_em.isoformat() if barbearia.criada_em else None,
        })
    
    # Backup Serviços
    for servico in Servico.objects.all():
        backup_data['servicos'].append({
            'id': servico.id,
            'nome': servico.nome,
            'preco': str(servico.preco),
            'duracao_minutos': servico.duracao_minutos,
            'barbearia_id': servico.barbearia_id,
            'ativo': servico.ativo,
            'criado_em': servico.criado_em.isoformat() if servico.criado_em else None,
        })
    
    # Backup Profissionais
    for prof in Profissional.objects.all():
        backup_data['profissionais'].append({
            'id': prof.id,
            'nome': prof.nome,
            'barbearia_id': prof.barbearia_id,
            'ativo': prof.ativo,
            'criado_em': prof.criado_em.isoformat() if prof.criado_em else None,
        })
    
    # Backup Horários de Funcionamento
    for horario in HorarioFuncionamento.objects.all():
        backup_data['horarios'].append({
            'id': horario.id,
            'barbearia_id': horario.barbearia_id,
            'dia_semana': horario.dia_semana,
            'abertura': horario.abertura.strftime('%H:%M:%S') if horario.abertura else None,
            'fechamento': horario.fechamento.strftime('%H:%M:%S') if horario.fechamento else None,
            'fechado': horario.fechado,
        })
    
    # Backup Agendamentos
    for agend in Agendamento.objects.all():
        backup_data['agendamentos'].append({
            'id': agend.id,
            'nome_cliente': agend.nome_cliente,
            'telefone_cliente': agend.telefone_cliente,
            'email_cliente': agend.email_cliente,
            'data_hora': agend.data_hora.isoformat() if agend.data_hora else None,
            'servico_id': agend.servico_id,
            'profissional_id': agend.profissional_id,
            'barbearia_id': agend.barbearia_id,
            'status': agend.status,
            'observacoes': agend.observacoes,
            'notificacao_enviada': agend.notificacao_enviada,
            'criado_em': agend.criado_em.isoformat() if agend.criado_em else None,
        })
    
    # Salvar backup
    backup_file = 'sqlite_backup.json'
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Backup salvo em: {backup_file}")
    print(f"📊 Dados salvos:")
    print(f"   - {len(backup_data['users'])} usuários")
    print(f"   - {len(backup_data['planos'])} planos")
    print(f"   - {len(backup_data['barbearias'])} barbearias")
    print(f"   - {len(backup_data['servicos'])} serviços")
    print(f"   - {len(backup_data['profissionais'])} profissionais")
    print(f"   - {len(backup_data['horarios'])} horários")
    print(f"   - {len(backup_data['agendamentos'])} agendamentos")

if __name__ == '__main__':
    backup_data()