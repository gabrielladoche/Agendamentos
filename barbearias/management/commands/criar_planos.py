from django.core.management.base import BaseCommand
from barbearias.models import Plano
from decimal import Decimal

class Command(BaseCommand):
    help = 'Cria os planos padrão do sistema'

    def handle(self, *args, **options):
        # Plano Básico
        plano_basico, created = Plano.objects.get_or_create(
            tipo='basico',
            defaults={
                'nome': 'Básico',
                'preco_mensal': Decimal('49.00'),
                'max_profissionais': 1,
                'descricao': 'Ideal para estabelecimentos pequenos com um profissional',
                'agendamento_online': True,
                'gestao_agenda': True,
                'notificacoes_email': True,
                'notificacoes_sms': False,
                'integracao_google_calendar': False,
                'relatorios_basicos': False,
                'relatorios_avancados': False,
                'integracao_pagamento': False,
                'personalizacao_completa': False,
                'suporte_prioritario': False,
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Plano Básico criado: {plano_basico}')
            )
        else:
            self.stdout.write(f'Plano Básico já existe: {plano_basico}')

        # Plano Intermediário
        plano_intermediario, created = Plano.objects.get_or_create(
            tipo='intermediario',
            defaults={
                'nome': 'Intermediário',
                'preco_mensal': Decimal('89.00'),
                'max_profissionais': 0,  # Ilimitado
                'descricao': 'Recomendado para estabelecimentos com múltiplos profissionais',
                'agendamento_online': True,
                'gestao_agenda': True,
                'notificacoes_email': True,
                'notificacoes_sms': False,
                'integracao_google_calendar': True,
                'relatorios_basicos': True,
                'relatorios_avancados': False,
                'integracao_pagamento': False,
                'personalizacao_completa': False,
                'suporte_prioritario': False,
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Plano Intermediário criado: {plano_intermediario}')
            )
        else:
            self.stdout.write(f'Plano Intermediário já existe: {plano_intermediario}')

        # Plano Avançado
        plano_avancado, created = Plano.objects.get_or_create(
            tipo='avancado',
            defaults={
                'nome': 'Avançado',
                'preco_mensal': Decimal('149.00'),
                'max_profissionais': 0,  # Ilimitado
                'descricao': 'Premium com todas as funcionalidades para estabelecimentos grandes',
                'agendamento_online': True,
                'gestao_agenda': True,
                'notificacoes_email': True,
                'notificacoes_sms': True,
                'integracao_google_calendar': True,
                'relatorios_basicos': True,
                'relatorios_avancados': True,
                'integracao_pagamento': True,
                'personalizacao_completa': True,
                'suporte_prioritario': True,
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Plano Avançado criado: {plano_avancado}')
            )
        else:
            self.stdout.write(f'Plano Avançado já existe: {plano_avancado}')

        self.stdout.write(
            self.style.SUCCESS('✅ Todos os planos foram verificados/criados com sucesso!')
        )
