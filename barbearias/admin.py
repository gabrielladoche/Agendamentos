from django.contrib import admin
from django.urls import path
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Barbearia, Servico, Profissional, HorarioFuncionamento, Plano
from agendamentos.models import Agendamento
import csv

@admin.register(Barbearia)
class BarbeariaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'telefone', 'plano', 'ativa', 'usuario', 'criada_em']
    list_filter = ['ativa', 'plano', 'criada_em']
    search_fields = ['nome', 'telefone']
    prepopulated_fields = {'slug': ('nome',)}
    
    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('relatorios/', self.admin_site.admin_view(self.relatorios_view), name='barbearias_barbearia_relatorios'),
            path('<int:barbearia_id>/relatorio-mensal/', self.admin_site.admin_view(self.relatorio_mensal_view), name='barbearias_barbearia_relatorio_mensal'),
            path('<int:barbearia_id>/relatorio-csv/', self.admin_site.admin_view(self.relatorio_csv_view), name='barbearias_barbearia_relatorio_csv'),
        ]
        return my_urls + urls
    
    def relatorios_view(self, request):
        """View principal dos relatórios"""
        barbearias = Barbearia.objects.filter(ativa=True)
        return render(request, 'admin/barbearias/relatorios.html', {
            'title': 'Relatórios de Estabelecimentos',
            'barbearias': barbearias,
        })
    
    def relatorio_mensal_view(self, request):
        """View para relatório mensal específico de uma barbearia"""
        barbearia_id = request.resolver_match.kwargs['barbearia_id']
        barbearia = get_object_or_404(Barbearia, pk=barbearia_id)
        
        # Pegar parâmetros da URL
        ano = int(request.GET.get('ano', timezone.now().year))
        mes = int(request.GET.get('mes', timezone.now().month))
        
        # Data de início e fim do mês
        data_inicio = datetime(ano, mes, 1)
        if mes == 12:
            data_fim = datetime(ano + 1, 1, 1) - timedelta(days=1)
        else:
            data_fim = datetime(ano, mes + 1, 1) - timedelta(days=1)
        
        # Consultas para o relatório
        agendamentos_mes = Agendamento.objects.filter(
            barbearia=barbearia,
            data_hora__date__gte=data_inicio.date(),
            data_hora__date__lte=data_fim.date()
        )
        
        # Estatísticas gerais
        total_agendamentos = agendamentos_mes.count()
        agendamentos_concluidos = agendamentos_mes.filter(status='concluido').count()
        agendamentos_cancelados = agendamentos_mes.filter(status='cancelado').count()
        
        # Faturamento (apenas agendamentos concluídos)
        faturamento_total = agendamentos_mes.filter(status='concluido').aggregate(
            total=Sum('servico__preco')
        )['total'] or 0
        
        # Serviços mais populares
        servicos_populares = agendamentos_mes.values('servico__nome').annotate(
            quantidade=Count('id')
        ).order_by('-quantidade')[:5]
        
        # Profissionais mais procurados
        profissionais_populares = agendamentos_mes.values('profissional__nome').annotate(
            quantidade=Count('id')
        ).order_by('-quantidade')[:5]
        
        # Agendamentos por status
        agendamentos_por_status = agendamentos_mes.values('status').annotate(
            quantidade=Count('id')
        )
        
        # Agendamentos por dia do mês
        agendamentos_por_dia = []
        for dia in range(1, 32):
            try:
                data_dia = datetime(ano, mes, dia).date()
                if data_dia <= data_fim.date():
                    count = agendamentos_mes.filter(data_hora__date=data_dia).count()
                    agendamentos_por_dia.append({
                        'dia': dia,
                        'quantidade': count
                    })
            except ValueError:
                break
        
        context = {
            'title': f'Relatório Mensal - {barbearia.nome}',
            'barbearia': barbearia,
            'ano': ano,
            'mes': mes,
            'data_inicio': data_inicio,
            'data_fim': data_fim,
            'total_agendamentos': total_agendamentos,
            'agendamentos_concluidos': agendamentos_concluidos,
            'agendamentos_cancelados': agendamentos_cancelados,
            'faturamento_total': faturamento_total,
            'servicos_populares': servicos_populares,
            'profissionais_populares': profissionais_populares,
            'agendamentos_por_status': agendamentos_por_status,
            'agendamentos_por_dia': agendamentos_por_dia,
            'meses': [
                (1, 'Janeiro'), (2, 'Fevereiro'), (3, 'Março'), (4, 'Abril'),
                (5, 'Maio'), (6, 'Junho'), (7, 'Julho'), (8, 'Agosto'),
                (9, 'Setembro'), (10, 'Outubro'), (11, 'Novembro'), (12, 'Dezembro')
            ],
            'anos': range(2024, timezone.now().year + 2),
        }
        
        return render(request, 'admin/barbearias/relatorio_mensal.html', context)
    
    def relatorio_csv_view(self, request):
        """Exporta relatório em CSV"""
        barbearia_id = request.resolver_match.kwargs['barbearia_id']
        barbearia = get_object_or_404(Barbearia, pk=barbearia_id)
        
        ano = int(request.GET.get('ano', timezone.now().year))
        mes = int(request.GET.get('mes', timezone.now().month))
        
        data_inicio = datetime(ano, mes, 1)
        if mes == 12:
            data_fim = datetime(ano + 1, 1, 1) - timedelta(days=1)
        else:
            data_fim = datetime(ano, mes + 1, 1) - timedelta(days=1)
        
        agendamentos = Agendamento.objects.filter(
            barbearia=barbearia,
            data_hora__date__gte=data_inicio.date(),
            data_hora__date__lte=data_fim.date()
        ).order_by('data_hora')
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="relatorio_{barbearia.slug}_{ano}_{mes:02d}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Data/Hora', 'Cliente', 'Telefone', 'Email', 'Serviço', 'Profissional', 'Preço', 'Status'])
        
        for agendamento in agendamentos:
            writer.writerow([
                agendamento.data_hora.strftime('%d/%m/%Y %H:%M'),
                agendamento.nome_cliente,
                agendamento.telefone_cliente,
                agendamento.email_cliente or '',
                agendamento.servico.nome,
                agendamento.profissional.nome,
                f'R$ {agendamento.servico.preco}',
                agendamento.get_status_display()
            ])
        
        return response

@admin.register(Plano)
class PlanoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'tipo', 'preco_mensal', 'max_profissionais', 'ativo']
    list_filter = ['tipo', 'ativo']
    search_fields = ['nome', 'tipo']
    readonly_fields = ['criado_em']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'tipo', 'preco_mensal', 'max_profissionais', 'descricao', 'ativo')
        }),
        ('Funcionalidades', {
            'fields': (
                'agendamento_online', 'gestao_agenda', 
                'notificacoes_email', 'notificacoes_sms',
                'integracao_google_calendar', 'relatorios_basicos', 'relatorios_avancados',
                'integracao_pagamento', 'personalizacao_completa', 'suporte_prioritario'
            )
        }),
        ('Metadados', {
            'fields': ('criado_em',)
        }),
    )

@admin.register(Servico)
class ServicoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'barbearia', 'preco', 'duracao_minutos', 'ativo']
    list_filter = ['barbearia', 'ativo']
    search_fields = ['nome', 'barbearia__nome']

@admin.register(Profissional)
class ProfissionalAdmin(admin.ModelAdmin):
    list_display = ['nome', 'barbearia', 'ativo', 'criado_em']
    list_filter = ['barbearia', 'ativo']
    search_fields = ['nome', 'barbearia__nome']

@admin.register(HorarioFuncionamento)
class HorarioFuncionamentoAdmin(admin.ModelAdmin):
    list_display = ['barbearia', 'dia_semana', 'abertura', 'fechamento', 'fechado']
    list_filter = ['barbearia', 'dia_semana', 'fechado']
    search_fields = ['barbearia__nome']