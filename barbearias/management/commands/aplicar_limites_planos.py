from django.core.management.base import BaseCommand
from barbearias.models import Barbearia

class Command(BaseCommand):
    help = 'Aplica os limites de profissionais baseado nos planos das barbearias'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostra o que seria feito sem fazer alterações',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write(self.style.WARNING('🔍 Verificando limites de planos...'))
        
        barbearias = Barbearia.objects.filter(ativa=True)
        total_processadas = 0
        total_desativados = 0
        
        for barbearia in barbearias:
            if barbearia.excede_limite_profissionais():
                profissionais_ativos = barbearia.profissionais.filter(ativo=True).count()
                
                if barbearia.plano:
                    limite = barbearia.plano.max_profissionais
                    excesso = profissionais_ativos - limite
                    
                    self.stdout.write(
                        self.style.ERROR(
                            f'🚨 {barbearia.nome}: {profissionais_ativos} profissionais ativos, '
                            f'limite do plano {barbearia.plano.nome}: {limite} '
                            f'(excesso: {excesso})'
                        )
                    )
                    
                    if not dry_run:
                        desativados = barbearia.aplicar_limite_profissionais()
                        total_desativados += desativados
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'✅ {desativados} profissionais desativados em {barbearia.nome}'
                            )
                        )
                    else:
                        total_desativados += excesso
                        self.stdout.write(
                            self.style.WARNING(
                                f'⚠️  [DRY RUN] {excesso} profissionais seriam desativados'
                            )
                        )
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f'🚨 {barbearia.nome}: {profissionais_ativos} profissionais ativos, '
                            f'mas SEM PLANO DEFINIDO!'
                        )
                    )
                
                total_processadas += 1
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ {barbearia.nome}: Dentro do limite '
                        f'({barbearia.profissionais.filter(ativo=True).count()} profissionais)'
                    )
                )
        
        self.stdout.write('\n' + '='*50)
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'📊 RESUMO (DRY RUN):\n'
                    f'   - Barbearias verificadas: {barbearias.count()}\n'
                    f'   - Barbearias fora do limite: {total_processadas}\n'
                    f'   - Profissionais que seriam desativados: {total_desativados}'
                )
            )
            self.stdout.write(
                self.style.WARNING(
                    '\n💡 Execute sem --dry-run para aplicar as alterações'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'📊 RESUMO:\n'
                    f'   - Barbearias verificadas: {barbearias.count()}\n'
                    f'   - Barbearias corrigidas: {total_processadas}\n'
                    f'   - Profissionais desativados: {total_desativados}'
                )
            )
            
        self.stdout.write(self.style.SUCCESS('\n🎯 Operação concluída!'))
