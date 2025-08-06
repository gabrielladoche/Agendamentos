#!/usr/bin/env python3
"""
Script para restaurar os dados do backup SQLite no MySQL
EXECUTE ESTE SCRIPT APÓS CONFIGURAR O MySQL
"""
import os
import sys
import django
import json
from decimal import Decimal
from datetime import datetime, time

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'barbearia_system.settings')
django.setup()

from django.contrib.auth.models import User
from barbearias.models import Barbearia, Plano, Servico, Profissional, HorarioFuncionamento
from agendamentos.models import Agendamento

def restore_data():
    """Restaura todos os dados do backup JSON para MySQL"""
    
    # Ler backup
    try:
        with open('sqlite_backup.json', 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
    except FileNotFoundError:
        print("❌ Arquivo sqlite_backup.json não encontrado!")
        print("Execute primeiro: python3 backup_sqlite_data.py")
        return
    
    print("📦 Restaurando dados do backup no MySQL...")
    print(f"📅 Backup de: {backup_data['timestamp']}")
    
    # Limpar dados existentes (cuidado!)
    print("⚠️  Limpando dados existentes...")
    Agendamento.objects.all().delete()
    HorarioFuncionamento.objects.all().delete()
    Profissional.objects.all().delete()
    Servico.objects.all().delete()
    Barbearia.objects.all().delete()
    Plano.objects.all().delete()
    User.objects.all().delete()
    
    # Restaurar Users
    print("👤 Restaurando usuários...")
    for user_data in backup_data['users']:
        user = User.objects.create_user(
            username=user_data['username'],
            email=user_data['email'],
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
        )
        user.is_staff = user_data['is_staff']
        user.is_superuser = user_data['is_superuser']
        if user_data['date_joined']:
            user.date_joined = datetime.fromisoformat(user_data['date_joined'])
        user.save()
        
        # Definir senha padrão para usuários restaurados
        if user.is_superuser:
            user.set_password('admin123')  # Senha para superusuários
        else:
            user.set_password('123456')   # Senha padrão
        user.save()
    
    # Restaurar Planos
    print("💎 Restaurando planos...")
    for plano_data in backup_data['planos']:
        plano = Plano(
            nome=plano_data['nome'],
            tipo=plano_data['tipo'],
            preco_mensal=Decimal(plano_data['preco_mensal']),
            max_profissionais=plano_data['max_profissionais'],
            descricao=plano_data['descricao'],
            agendamento_online=plano_data['agendamento_online'],
            gestao_agenda=plano_data['gestao_agenda'],
            notificacoes_email=plano_data['notificacoes_email'],
            notificacoes_sms=plano_data['notificacoes_sms'],
            integracao_google_calendar=plano_data['integracao_google_calendar'],
            relatorios_basicos=plano_data['relatorios_basicos'],
            relatorios_avancados=plano_data['relatorios_avancados'],
            integracao_pagamento=plano_data['integracao_pagamento'],
            personalizacao_completa=plano_data['personalizacao_completa'],
            suporte_prioritario=plano_data['suporte_prioritario'],
            ativo=plano_data['ativo']
        )
        if plano_data['criado_em']:
            plano.criado_em = datetime.fromisoformat(plano_data['criado_em'])
        plano.save()
    
    # Restaurar Barbearias
    print("🏪 Restaurando barbearias...")
    for barbearia_data in backup_data['barbearias']:
        usuario = User.objects.get(id=barbearia_data['usuario_id'])
        plano = None
        if barbearia_data['plano_id']:
            plano = Plano.objects.get(id=barbearia_data['plano_id'])
        
        barbearia = Barbearia(
            nome=barbearia_data['nome'],
            endereco=barbearia_data['endereco'],
            telefone=barbearia_data['telefone'],
            email_notificacoes=barbearia_data['email_notificacoes'],
            slug=barbearia_data['slug'],
            usuario=usuario,
            plano=plano,
            ativa=barbearia_data['ativa'],
            tema=barbearia_data['tema']
        )
        if barbearia_data['criada_em']:
            barbearia.criada_em = datetime.fromisoformat(barbearia_data['criada_em'])
        barbearia.save()
    
    # Restaurar Serviços
    print("✂️  Restaurando serviços...")
    for servico_data in backup_data['servicos']:
        barbearia = Barbearia.objects.get(id=servico_data['barbearia_id'])
        servico = Servico(
            nome=servico_data['nome'],
            preco=Decimal(servico_data['preco']),
            duracao_minutos=servico_data['duracao_minutos'],
            barbearia=barbearia,
            ativo=servico_data['ativo']
        )
        if servico_data['criado_em']:
            servico.criado_em = datetime.fromisoformat(servico_data['criado_em'])
        servico.save()
    
    # Restaurar Profissionais
    print("👨‍💼 Restaurando profissionais...")
    for prof_data in backup_data['profissionais']:
        barbearia = Barbearia.objects.get(id=prof_data['barbearia_id'])
        prof = Profissional(
            nome=prof_data['nome'],
            barbearia=barbearia,
            ativo=prof_data['ativo']
        )
        if prof_data['criado_em']:
            prof.criado_em = datetime.fromisoformat(prof_data['criado_em'])
        prof.save()
    
    # Restaurar Horários
    print("⏰ Restaurando horários de funcionamento...")
    for horario_data in backup_data['horarios']:
        barbearia = Barbearia.objects.get(id=horario_data['barbearia_id'])
        horario = HorarioFuncionamento(
            barbearia=barbearia,
            dia_semana=horario_data['dia_semana'],
            fechado=horario_data['fechado']
        )
        if horario_data['abertura']:
            horario.abertura = time.fromisoformat(horario_data['abertura'])
        if horario_data['fechamento']:
            horario.fechamento = time.fromisoformat(horario_data['fechamento'])
        horario.save()
    
    # Restaurar Agendamentos
    print("📅 Restaurando agendamentos...")
    for agend_data in backup_data['agendamentos']:
        servico = Servico.objects.get(id=agend_data['servico_id'])
        profissional = Profissional.objects.get(id=agend_data['profissional_id'])
        barbearia = Barbearia.objects.get(id=agend_data['barbearia_id'])
        
        agend = Agendamento(
            nome_cliente=agend_data['nome_cliente'],
            telefone_cliente=agend_data['telefone_cliente'],
            email_cliente=agend_data['email_cliente'],
            servico=servico,
            profissional=profissional,
            barbearia=barbearia,
            status=agend_data['status'],
            observacoes=agend_data['observacoes'],
            notificacao_enviada=agend_data['notificacao_enviada']
        )
        if agend_data['data_hora']:
            agend.data_hora = datetime.fromisoformat(agend_data['data_hora'])
        if agend_data['criado_em']:
            agend.criado_em = datetime.fromisoformat(agend_data['criado_em'])
        agend.save()
    
    print("✅ Restauração concluída!")
    print(f"📊 Dados restaurados:")
    print(f"   - {len(backup_data['users'])} usuários")
    print(f"   - {len(backup_data['planos'])} planos")
    print(f"   - {len(backup_data['barbearias'])} barbearias")
    print(f"   - {len(backup_data['servicos'])} serviços")
    print(f"   - {len(backup_data['profissionais'])} profissionais")
    print(f"   - {len(backup_data['horarios'])} horários")
    print(f"   - {len(backup_data['agendamentos'])} agendamentos")
    print("")
    print("🔑 Senhas dos usuários:")
    print("   - Superusuários: admin123")
    print("   - Outros usuários: 123456")

if __name__ == '__main__':
    restore_data()