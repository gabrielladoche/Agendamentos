#!/usr/bin/env python3
"""
Script para testar o envio de email de confirmação quando o estabelecimento confirma um agendamento.
"""

import os
import django
from datetime import datetime, timedelta
from django.utils import timezone

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'barbearia_system.settings')
django.setup()

from agendamentos.models import Agendamento
from agendamentos.utils import enviar_confirmacao_agendamento_cliente
from barbearias.models import Barbearia, Servico, Profissional

def testar_funcionalidade():
    """Testa a funcionalidade completa de confirmação com envio de email"""
    
    print("=" * 60)
    print("🧪 TESTE - CONFIRMAÇÃO DE AGENDAMENTO COM EMAIL")
    print("=" * 60)
    
    # 1. Buscar agendamentos pendentes
    agendamentos_pendentes = Agendamento.objects.filter(status='agendado')
    
    if not agendamentos_pendentes.exists():
        print("❌ Nenhum agendamento pendente encontrado.")
        print("   Criando um agendamento de teste...")
        
        # Criar agendamento de teste
        barbearia = Barbearia.objects.first()
        servico = Servico.objects.filter(barbearia=barbearia).first()
        profissional = Profissional.objects.filter(barbearia=barbearia).first()
        
        if not all([barbearia, servico, profissional]):
            print("❌ Dados necessários não encontrados no banco")
            return False
            
        # Data para amanhã
        amanha = timezone.now().date() + timedelta(days=1)
        data_hora = timezone.make_aware(
            datetime.combine(amanha, datetime.strptime('15:30', '%H:%M').time())
        )
        
        agendamento = Agendamento.objects.create(
            nome_cliente='João Silva',
            telefone_cliente='(11) 98765-4321',
            email_cliente='gabriel.ladoche@outlook.com',  # Substitua pelo seu email
            servico=servico,
            profissional=profissional,
            barbearia=barbearia,
            data_hora=data_hora,
            status='agendado',
            observacoes='Teste de confirmação por email'
        )
        
        print(f"✅ Agendamento de teste criado:")
        print(f"   ID: #{agendamento.id}")
        print(f"   Cliente: {agendamento.nome_cliente}")
        print(f"   Email: {agendamento.email_cliente}")
        print(f"   Data/Hora: {agendamento.data_hora.strftime('%d/%m/%Y %H:%M')}")
        print()
        
        agendamentos_pendentes = [agendamento]
    
    # 2. Simular confirmação pelo estabelecimento
    agendamento = agendamentos_pendentes[0]
    
    print(f"📋 AGENDAMENTO SELECIONADO PARA TESTE:")
    print(f"   ID: #{agendamento.id}")
    print(f"   Cliente: {agendamento.nome_cliente}")
    print(f"   Status Atual: {agendamento.get_status_display()}")
    print(f"   Email Cliente: {agendamento.email_cliente}")
    print(f"   Estabelecimento: {agendamento.barbearia.nome}")
    print()
    
    # 3. Confirmar agendamento
    print("⏳ Confirmando agendamento...")
    status_anterior = agendamento.status
    agendamento.status = 'confirmado'
    agendamento.save()
    
    print(f"✅ Status atualizado de '{status_anterior}' para '{agendamento.status}'")
    print()
    
    # 4. Enviar email de confirmação
    print("📧 Enviando email de confirmação para o cliente...")
    
    try:
        resultado = enviar_confirmacao_agendamento_cliente(agendamento)
        
        if resultado:
            print("✅ EMAIL ENVIADO COM SUCESSO! 🎉")
            print(f"   Destinatário: {agendamento.email_cliente}")
            print(f"   Assunto: Agendamento Confirmado - {agendamento.barbearia.nome}")
            print()
            print("📱 O cliente receberá:")
            print("   • Confirmação de que o agendamento foi aceito")
            print("   • Detalhes completos do agendamento")
            print("   • Informações do estabelecimento")
            print("   • Instruções importantes")
            print("   • Template HTML responsivo e bonito")
        else:
            print("❌ Falha ao enviar email")
            if not agendamento.email_cliente:
                print("   Motivo: Cliente não possui email cadastrado")
            else:
                print("   Motivo: Erro de configuração SMTP ou outro problema")
        
    except Exception as e:
        print(f"❌ Erro durante envio: {str(e)}")
        return False
    
    print()
    print("=" * 60)
    print("✅ TESTE CONCLUÍDO!")
    print("=" * 60)
    print()
    print("🔄 Como usar na prática:")
    print("1. Cliente faz agendamento (status: 'agendado')")
    print("2. Dono acessa admin e confirma agendamento")
    print("3. Sistema muda status para 'confirmado'")
    print("4. Email automático é enviado para o cliente")
    print("5. Cliente recebe confirmação por email")
    
    return True

if __name__ == "__main__":
    testar_funcionalidade()