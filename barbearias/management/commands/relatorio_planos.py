from django.core.management.base import BaseCommand
from barbearias.models import Barbearia, Plano, Profissional

class Command(BaseCommand):
    help = 'Mostra relatório detalhado dos planos e compliance'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('📊 RELATÓRIO DE PLANOS E COMPLIANCE'))
        self.stdout.write('='*60)
        
        # Estatísticas gerais
        total_barbearias = Barbearia.objects.filter(ativa=True).count()
        barbearias_sem_plano = Barbearia.objects.filter(ativa=True, plano__isnull=True).count()
        barbearias_fora_limite = 0
        
        for barbearia in Barbearia.objects.filter(ativa=True):
            if barbearia.excede_limite_profissionais():
                barbearias_fora_limite += 1
        
        self.stdout.write(f'📈 VISÃO GERAL:')
        self.stdout.write(f'   Total de Barbearias Ativas: {total_barbearias}')
        self.stdout.write(f'   Barbearias sem Plano: {barbearias_sem_plano}')
        self.stdout.write(f'   Barbearias fora do limite: {barbearias_fora_limite}')
        self.stdout.write('')
        
        # Detalhes por plano
        self.stdout.write('💎 DISTRIBUIÇÃO POR PLANO:')
        for plano in Plano.objects.filter(ativo=True).order_by('preco_mensal'):
            count = Barbearia.objects.filter(plano=plano, ativa=True).count()
            receita_mensal = count * plano.preco_mensal
            
            self.stdout.write(
                f'   {plano.nome} (R$ {plano.preco_mensal}): {count} barbearia(s) '
                f'= R$ {receita_mensal:.2f}/mês'
            )
        
        # Sem plano
        sem_plano = Barbearia.objects.filter(plano__isnull=True, ativa=True).count()
        if sem_plano > 0:
            self.stdout.write(f'   Sem Plano: {sem_plano} barbearia(s) = R$ 0.00/mês')
        
        self.stdout.write('')
        
        # Receita total
        receita_total = 0
        for plano in Plano.objects.filter(ativo=True):
            count = Barbearia.objects.filter(plano=plano, ativa=True).count()
            receita_total += count * plano.preco_mensal
        
        self.stdout.write(
            self.style.SUCCESS(f'💰 RECEITA MENSAL TOTAL: R$ {receita_total:.2f}')
        )
        self.stdout.write('')
        
        # Detalhes de cada barbearia
        self.stdout.write('🏪 DETALHES POR BARBEARIA:')
        for barbearia in Barbearia.objects.filter(ativa=True).order_by('nome'):
            profissionais_ativos = barbearia.profissionais.filter(ativo=True).count()
            profissionais_inativos = barbearia.profissionais.filter(ativo=False).count()
            
            if barbearia.plano:
                plano_info = f'{barbearia.plano.nome} (R$ {barbearia.plano.preco_mensal})'
                limite = barbearia.plano.max_profissionais if barbearia.plano.max_profissionais > 0 else '∞'
                status_compliance = '✅' if not barbearia.excede_limite_profissionais() else '🚨'
            else:
                plano_info = 'SEM PLANO'
                limite = 'N/A'
                status_compliance = '🚨'
            
            self.stdout.write(f'   {status_compliance} {barbearia.nome}:')
            self.stdout.write(f'      Plano: {plano_info}')
            self.stdout.write(f'      Profissionais: {profissionais_ativos} ativos, {profissionais_inativos} inativos (limite: {limite})')
            
            if barbearia.excede_limite_profissionais():
                self.stdout.write(
                    self.style.ERROR(f'      ⚠️  FORA DO LIMITE!')
                )
            
            self.stdout.write('')
        
        # Recomendações
        self.stdout.write('🎯 RECOMENDAÇÕES:')
        
        if barbearias_sem_plano > 0:
            self.stdout.write(
                self.style.WARNING(
                    f'   • {barbearias_sem_plano} barbearia(s) precisam escolher um plano'
                )
            )
        
        if barbearias_fora_limite > 0:
            self.stdout.write(
                self.style.ERROR(
                    f'   • {barbearias_fora_limite} barbearia(s) estão fora do limite do plano'
                )
            )
        
        if barbearias_sem_plano == 0 and barbearias_fora_limite == 0:
            self.stdout.write(
                self.style.SUCCESS('   • Todas as barbearias estão em compliance! 🎉')
            )
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('📋 Relatório concluído!'))
