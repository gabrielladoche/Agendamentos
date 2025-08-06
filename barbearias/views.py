from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, Http404
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login, logout
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta
import csv

# Imports para PDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from io import BytesIO

from .models import Barbearia, Servico, Profissional, HorarioFuncionamento, Plano
from .forms import ServicoForm, ProfissionalForm, LoginBarbeiroForm, HorarioFuncionamentoForm, BarbeariaConfigForm
from agendamentos.models import Agendamento
from agendamentos.forms import AgendamentoForm
from agendamentos.utils import enviar_notificacao_novo_agendamento


# Helper function para verificar permissões do plano
def verificar_permissao_plano(barbearia, funcionalidade):
    """
    Verifica se a barbearia tem permissão para usar uma funcionalidade baseada no plano
    """
    if not barbearia.plano:
        return False  # Sem plano = sem acesso
    
    # Mapear funcionalidades
    permissoes = {
        'relatorios_basicos': barbearia.plano.relatorios_basicos,
        'relatorios_avancados': barbearia.plano.relatorios_avancados,
        'notificacoes_sms': barbearia.plano.notificacoes_sms,
        'integracao_google_calendar': barbearia.plano.integracao_google_calendar,
        'integracao_pagamento': barbearia.plano.integracao_pagamento,
        'personalizacao_completa': barbearia.plano.personalizacao_completa,
        'suporte_prioritario': barbearia.plano.suporte_prioritario,
    }
    
    return permissoes.get(funcionalidade, False)


# Views para estabelecimentos (área administrativa própria)
def login_estabelecimento(request):
    """View de login para estabelecimentos"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Verificar se o usuário tem uma barbearia associada
            try:
                barbearia = Barbearia.objects.get(usuario=user, ativa=True)
                login(request, user)
                return redirect('barbearias:dashboard_estabelecimento')
            except Barbearia.DoesNotExist:
                messages.error(request, 'Este usuário não está associado a um estabelecimento ativo.')
        else:
            messages.error(request, 'Usuário ou senha incorretos.')
    
    return render(request, 'barbearias/login_estabelecimento.html')


def logout_estabelecimento(request):
    """View de logout para estabelecimentos"""
    logout(request)
    messages.success(request, 'Logout realizado com sucesso.')
    return redirect('barbearias:login_estabelecimento')


@login_required
def dashboard_estabelecimento(request):
    """Dashboard principal do estabelecimento"""
    try:
        barbearia = Barbearia.objects.get(usuario=request.user, ativa=True)
    except Barbearia.DoesNotExist:
        messages.error(request, 'Estabelecimento não encontrado.')
        return redirect('barbearias:login_estabelecimento')
    
    # Estatísticas rápidas do mês atual
    hoje = timezone.now().date()
    inicio_mes = hoje.replace(day=1)
    
    agendamentos_mes = Agendamento.objects.filter(
        barbearia=barbearia,
        data_hora__date__gte=inicio_mes
    )
    
    estatisticas = {
        'total_mes': agendamentos_mes.count(),
        'confirmados_mes': agendamentos_mes.filter(status='confirmado').count(),
        'concluidos_mes': agendamentos_mes.filter(status='concluido').count(),
        'hoje': Agendamento.objects.filter(
            barbearia=barbearia,
            data_hora__date=hoje
        ).count(),
        'faturamento_mes': agendamentos_mes.filter(status='concluido').aggregate(
            total=Sum('servico__preco')
        )['total'] or 0
    }
    
    # Próximos agendamentos
    proximos_agendamentos = Agendamento.objects.filter(
        barbearia=barbearia,
        data_hora__gte=timezone.now(),
        status__in=['agendado', 'confirmado']
    ).order_by('data_hora')[:10]
    
    context = {
        'barbearia': barbearia,
        'estatisticas': estatisticas,
        'proximos_agendamentos': proximos_agendamentos,
    }
    
    return render(request, 'barbearias/dashboard_estabelecimento.html', context)


@login_required
def relatorios_estabelecimento(request):
    """View de relatórios para o estabelecimento"""
    try:
        barbearia = Barbearia.objects.get(usuario=request.user, ativa=True)
    except Barbearia.DoesNotExist:
        messages.error(request, 'Estabelecimento não encontrado.')
        return redirect('barbearias:login_estabelecimento')
    
    # Verificar se tem acesso a relatórios
    if not verificar_permissao_plano(barbearia, 'relatorios_basicos'):
        messages.error(
            request, 
            '🚫 Relatórios não disponíveis no seu plano atual. '
            'Faça upgrade para acessar relatórios.'
        )
        return redirect('barbearias:dashboard_estabelecimento')
    
    return render(request, 'barbearias/relatorios_estabelecimento.html', {
        'barbearia': barbearia,
    })


@login_required
def relatorio_mensal_estabelecimento(request):
    """View para relatório mensal do estabelecimento"""
    try:
        barbearia = Barbearia.objects.get(usuario=request.user, ativa=True)
    except Barbearia.DoesNotExist:
        messages.error(request, 'Estabelecimento não encontrado.')
        return redirect('barbearias:login_estabelecimento')
    
    # Verificar se tem acesso a relatórios
    if not verificar_permissao_plano(barbearia, 'relatorios_basicos'):
        messages.error(
            request, 
            '🚫 Relatórios não disponíveis no seu plano atual. '
            'Faça upgrade para acessar relatórios.'
        )
        return redirect('barbearias:dashboard_estabelecimento')
    
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
    servicos_populares = agendamentos_mes.values('servico__nome', 'servico__preco').annotate(
        quantidade=Count('id'),
        faturamento=Sum('servico__preco')
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
    
    # Comparação com mês anterior
    if mes == 1:
        mes_anterior = 12
        ano_anterior = ano - 1
    else:
        mes_anterior = mes - 1
        ano_anterior = ano
    
    data_inicio_anterior = datetime(ano_anterior, mes_anterior, 1)
    if mes_anterior == 12:
        data_fim_anterior = datetime(ano_anterior + 1, 1, 1) - timedelta(days=1)
    else:
        data_fim_anterior = datetime(ano_anterior, mes_anterior + 1, 1) - timedelta(days=1)
    
    agendamentos_mes_anterior = Agendamento.objects.filter(
        barbearia=barbearia,
        data_hora__date__gte=data_inicio_anterior.date(),
        data_hora__date__lte=data_fim_anterior.date()
    ).count()
    
    # Calcular crescimento
    if agendamentos_mes_anterior > 0:
        crescimento = ((total_agendamentos - agendamentos_mes_anterior) / agendamentos_mes_anterior) * 100
    else:
        crescimento = 100 if total_agendamentos > 0 else 0
    
    context = {
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
        'crescimento': round(crescimento, 1),
        'agendamentos_mes_anterior': agendamentos_mes_anterior,
        'meses': [
            (1, 'Janeiro'), (2, 'Fevereiro'), (3, 'Março'), (4, 'Abril'),
            (5, 'Maio'), (6, 'Junho'), (7, 'Julho'), (8, 'Agosto'),
            (9, 'Setembro'), (10, 'Outubro'), (11, 'Novembro'), (12, 'Dezembro')
        ],
        'anos': range(2024, timezone.now().year + 2),
    }
    
    return render(request, 'barbearias/relatorio_mensal_estabelecimento.html', context)


@login_required
def exportar_csv_estabelecimento(request):
    """Exporta relatório em CSV para o estabelecimento"""
    try:
        barbearia = Barbearia.objects.get(usuario=request.user, ativa=True)
    except Barbearia.DoesNotExist:
        raise Http404("Estabelecimento não encontrado")
    
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
    
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="relatorio_{barbearia.slug}_{ano}_{mes:02d}.csv"'
    
    # Adicionar BOM para Excel reconhecer UTF-8
    response.write('\ufeff')
    
    writer = csv.writer(response)
    writer.writerow([
        'Data/Hora', 'Cliente', 'Telefone', 'Email', 'Serviço', 
        'Profissional', 'Preço (R$)', 'Status', 'Observações'
    ])
    
    for agendamento in agendamentos:
        writer.writerow([
            agendamento.data_hora.strftime('%d/%m/%Y %H:%M'),
            agendamento.nome_cliente,
            agendamento.telefone_cliente,
            agendamento.email_cliente or '',
            agendamento.servico.nome,
            agendamento.profissional.nome,
            f'{agendamento.servico.preco}',
            agendamento.get_status_display(),
            agendamento.observacoes or ''
        ])
    
    return response


@login_required
def agendamentos_estabelecimento(request):
    """Lista de agendamentos do estabelecimento"""
    try:
        barbearia = Barbearia.objects.get(usuario=request.user, ativa=True)
    except Barbearia.DoesNotExist:
        messages.error(request, 'Estabelecimento não encontrado.')
        return redirect('barbearias:login_estabelecimento')
    
    # Filtros
    data_filtro = request.GET.get('data')
    status_filtro = request.GET.get('status')
    profissional_filtro = request.GET.get('profissional')
    
    agendamentos = Agendamento.objects.filter(barbearia=barbearia)
    
    if data_filtro:
        try:
            data_obj = datetime.strptime(data_filtro, '%Y-%m-%d').date()
            agendamentos = agendamentos.filter(data_hora__date=data_obj)
        except ValueError:
            pass
    
    if status_filtro:
        agendamentos = agendamentos.filter(status=status_filtro)
    
    if profissional_filtro:
        agendamentos = agendamentos.filter(profissional_id=profissional_filtro)
    
    agendamentos = agendamentos.order_by('-data_hora')
    
    # Profissionais para o filtro
    profissionais = Profissional.objects.filter(barbearia=barbearia, ativo=True)
    
    context = {
        'barbearia': barbearia,
        'agendamentos': agendamentos,
        'profissionais': profissionais,
        'status_choices': Agendamento.STATUS_CHOICES,
        'filtros': {
            'data': data_filtro,
            'status': status_filtro,
            'profissional': profissional_filtro,
        }
    }
    
    return render(request, 'barbearias/agendamentos_estabelecimento.html', context)


# Views existentes do mini site (mantidas)
def get_default_barbearia():
    """Retorna a barbearia padrão configurada"""
    try:
        default_slug = getattr(settings, 'DEFAULT_BARBEARIA_SLUG', None)
        if default_slug:
            return Barbearia.objects.get(slug=default_slug, ativa=True)
    except Barbearia.DoesNotExist:
        pass
    
    # Se não encontrar o padrão, pega o primeiro ativo
    return Barbearia.objects.filter(ativa=True).first()


def redirect_to_default(request):
    """Redireciona para o estabelecimento padrão"""
    try:
        # Tenta usar o slug padrão configurado
        default_slug = getattr(settings, 'DEFAULT_BARBEARIA_SLUG', None)
        if default_slug:
            barbearia = Barbearia.objects.get(slug=default_slug, ativa=True)
            return redirect('barbearias:mini_site', slug=default_slug)
    except Barbearia.DoesNotExist:
        pass
    
    # Se não encontrar o padrão, pega o primeiro ativo
    try:
        primeira_barbearia = Barbearia.objects.filter(ativa=True).first()
        if primeira_barbearia:
            return redirect('barbearias:mini_site', slug=primeira_barbearia.slug)
    except:
        pass
    
    # Se não houver nenhuma barbearia ativa, mostra página de erro
    return render(request, 'barbearias/no_barbearia.html', status=404)

def consultar_agendamentos_local(request, slug):
    """Consulta de agendamentos de uma barbearia específica"""
    barbearia = get_object_or_404(Barbearia, slug=slug, ativa=True)
    
    agendamentos = []
    telefone = None
    
    if request.method == 'POST':
        telefone = request.POST.get('telefone', '').strip()
        if telefone:
            agendamentos = Agendamento.objects.filter(
                barbearia=barbearia,  # Filtra apenas por esta barbearia
                telefone_cliente__icontains=telefone,
                data_hora__gte=timezone.now() - timedelta(days=30)
            ).order_by('-data_hora')
    elif request.method == 'GET' and request.GET.get('telefone'):
        # Para preservar telefone após redirecionamento
        telefone = request.GET.get('telefone', '').strip()
        if telefone:
            agendamentos = Agendamento.objects.filter(
                barbearia=barbearia,
                telefone_cliente__icontains=telefone,
                data_hora__gte=timezone.now() - timedelta(days=30)
            ).order_by('-data_hora')
    
    context = {
        'barbearia': barbearia,
        'agendamentos': agendamentos,
        'telefone': telefone,
    }
    return render(request, 'barbearias/consultar_agendamentos.html', context)

@login_required
def painel_admin_default(request):
    """Painel administrativo da barbearia padrão"""
    barbearia = get_default_barbearia()
    if not barbearia:
        return render(request, 'barbearias/no_barbearia.html')
    
    # Verifica se o usuário tem permissão para esta barbearia
    if barbearia.usuario != request.user:
        messages.error(request, 'Você não tem permissão para acessar esta barbearia.')
        return redirect('admin:index')
    
    # Estatísticas básicas
    hoje = timezone.now().date()
    agendamentos_hoje = Agendamento.objects.filter(
        barbearia=barbearia,
        data_hora__date=hoje
    ).count()
    
    agendamentos_pendentes = Agendamento.objects.filter(
        barbearia=barbearia,
        status='agendado',
        data_hora__gte=timezone.now()
    ).count()
    
    # Próximos agendamentos
    proximos_agendamentos = Agendamento.objects.filter(
        barbearia=barbearia,
        data_hora__gte=timezone.now(),
        status__in=['agendado', 'confirmado']
    )[:10]
    
    context = {
        'barbearia': barbearia,
        'agendamentos_hoje': agendamentos_hoje,
        'agendamentos_pendentes': agendamentos_pendentes,
        'proximos_agendamentos': proximos_agendamentos,
    }
    return render(request, 'barbearias/painel_admin.html', context)

def mini_site(request, slug):
    """Mini site público da barbearia"""
    barbearia = get_object_or_404(Barbearia, slug=slug, ativa=True)
    servicos = barbearia.servicos.filter(ativo=True)
    profissionais = barbearia.profissionais.filter(ativo=True)
    
    context = {
        'barbearia': barbearia,
        'servicos': servicos,
        'profissionais': profissionais,
    }
    return render(request, 'barbearias/mini_site.html', context)

def agendar(request, slug):
    """Formulário de agendamento público"""
    barbearia = get_object_or_404(Barbearia, slug=slug, ativa=True)
    
    if request.method == 'POST':
        form = AgendamentoForm(request.POST, barbearia=barbearia)
        if form.is_valid():
            agendamento = form.save(commit=False)
            agendamento.barbearia = barbearia
            try:
                agendamento.save()
                
                # Enviar notificação para o estabelecimento
                try:
                    resultado = enviar_notificacao_novo_agendamento(agendamento)
                    if resultado:
                        print(f"✅ Notificação enviada com sucesso para agendamento #{agendamento.id}")
                        messages.success(request, f'Agendamento realizado com sucesso! Uma notificação foi enviada para {barbearia.nome}.')
                    else:
                        print(f"❌ Falha ao enviar notificação para agendamento #{agendamento.id}")
                        if not barbearia.email_notificacoes:
                            messages.success(request, 'Agendamento realizado com sucesso!')
                        else:
                            messages.warning(request, 'Agendamento realizado, mas houve problema ao enviar notificação ao estabelecimento.')
                except Exception as e:
                    print(f"🚨 Erro ao enviar notificação: {str(e)}")
                    messages.warning(request, 'Agendamento realizado, mas houve problema ao enviar notificação ao estabelecimento.')
                
                return redirect('barbearias:mini_site', slug=slug)
            except Exception as e:
                messages.error(request, f'Erro ao realizar agendamento: {str(e)}')
    else:
        form = AgendamentoForm(barbearia=barbearia)
    
    context = {
        'barbearia': barbearia,
        'form': form,
    }
    return render(request, 'barbearias/agendar.html', context)

@login_required
def painel_admin(request, slug):
    """Painel administrativo da barbearia"""
    try:
        barbearia = get_object_or_404(Barbearia, slug=slug, usuario=request.user)
    except:
        messages.error(request, 'Você não tem permissão para acessar esta barbearia.')
        return redirect('admin:index')
    
    # Estatísticas básicas
    hoje = timezone.now().date()
    agendamentos_hoje = Agendamento.objects.filter(
        barbearia=barbearia,
        data_hora__date=hoje
    ).count()
    
    agendamentos_pendentes = Agendamento.objects.filter(
        barbearia=barbearia,
        status='agendado',
        data_hora__gte=timezone.now()
    ).count()
    
    # Próximos agendamentos
    proximos_agendamentos = Agendamento.objects.filter(
        barbearia=barbearia,
        data_hora__gte=timezone.now(),
        status__in=['agendado', 'confirmado']
    )[:10]
    
    context = {
        'barbearia': barbearia,
        'agendamentos_hoje': agendamentos_hoje,
        'agendamentos_pendentes': agendamentos_pendentes,
        'proximos_agendamentos': proximos_agendamentos,
    }
    return render(request, 'barbearias/painel_admin.html', context)

def consultar_agendamentos(request):
    """Consulta de agendamentos por telefone"""
    agendamentos = []
    telefone = None
    
    if request.method == 'POST':
        telefone = request.POST.get('telefone', '').strip()
        if telefone:
            agendamentos = Agendamento.objects.filter(
                telefone_cliente__icontains=telefone,
                data_hora__gte=timezone.now() - timedelta(days=30)  # Últimos 30 dias
            ).order_by('-data_hora')
    
    context = {
        'agendamentos': agendamentos,
        'telefone': telefone,
    }
    return render(request, 'barbearias/consultar_agendamentos.html', context)

# ===== VIEWS ADMINISTRATIVAS =====

def barbeiro_required(view_func):
    """Decorator que verifica se o barbeiro está logado e tem acesso à barbearia"""
    def _wrapped_view(request, slug, *args, **kwargs):
        # Verificar se está logado
        if not request.user.is_authenticated:
            messages.info(request, 'Faça login para acessar a área administrativa.')
            return redirect('barbearias:admin_login', slug=slug)
        
        # Verificar se tem acesso à barbearia
        try:
            barbearia = Barbearia.objects.get(slug=slug, ativa=True)
            if barbearia.usuario != request.user:
                messages.error(request, 'Você não tem permissão para acessar esta barbearia.')
                logout(request)
                return redirect('barbearias:admin_login', slug=slug)
        except Barbearia.DoesNotExist:
            messages.error(request, 'Barbearia não encontrada.')
            return redirect('barbearias:redirect_to_default')
        
        return view_func(request, slug, *args, **kwargs)
    return _wrapped_view

def admin_login(request, slug):
    """Login específico para barbeiros"""
    # Verificar se a barbearia existe
    try:
        barbearia = Barbearia.objects.get(slug=slug, ativa=True)
    except Barbearia.DoesNotExist:
        messages.error(request, 'Barbearia não encontrada.')
        return redirect('barbearias:redirect_to_default')
    
    # Se já está logado e tem acesso, redirecionar
    if request.user.is_authenticated:
        if barbearia.usuario == request.user:
            return redirect('barbearias:admin_dashboard', slug=slug)
        else:
            # Logado com usuário errado, fazer logout
            logout(request)
    
    if request.method == 'POST':
        form = LoginBarbeiroForm(request.POST, slug=slug, request=request)
        if form.is_valid():
            user = form.cleaned_data['user']
            login(request, user)
            messages.success(request, f'Bem-vindo, {user.first_name or user.username}!')
            return redirect('barbearias:admin_dashboard', slug=slug)
    else:
        form = LoginBarbeiroForm(slug=slug, request=request)
    
    context = {
        'form': form,
        'barbearia': barbearia,
    }
    # Garantir que o contexto de request está sendo passado corretamente
    return render(request, 'barbearias/admin/login.html', context)

def admin_logout(request, slug):
    """Logout para barbeiros"""
    logout(request)
    messages.success(request, 'Você saiu da área administrativa.')
    return redirect('barbearias:mini_site', slug=slug)

@barbeiro_required
def admin_dashboard(request, slug):
    """Dashboard administrativo da barbearia"""
    barbearia = Barbearia.objects.get(slug=slug, ativa=True)
    
    # Verificar se excede o limite de profissionais
    if barbearia.excede_limite_profissionais():
        if barbearia.plano:
            messages.error(
                request,
                f'🚨 ATENÇÃO: Você tem {barbearia.profissionais.filter(ativo=True).count()} profissionais ativos, '
                f'mas seu plano {barbearia.plano.nome} permite apenas {barbearia.plano.max_profissionais}. '
                f'Desative alguns profissionais ou faça upgrade do plano para regularizar sua situação.'
            )
        else:
            messages.error(
                request,
                f'🚨 ATENÇÃO: Você precisa escolher um plano para usar o sistema. '
                f'Selecione um plano que comporte seus {barbearia.profissionais.filter(ativo=True).count()} profissionais.'
            )
    
    # Estatísticas básicas
    hoje = timezone.now().date()
    agendamentos_hoje = Agendamento.objects.filter(
        barbearia=barbearia,
        data_hora__date=hoje
    ).count()
    
    agendamentos_pendentes = Agendamento.objects.filter(
        barbearia=barbearia,
        status='agendado',
        data_hora__gte=timezone.now()
    ).count()
    
    total_servicos = barbearia.servicos.filter(ativo=True).count()
    total_profissionais = barbearia.profissionais.filter(ativo=True).count()
    
    # Próximos agendamentos
    proximos_agendamentos = Agendamento.objects.filter(
        barbearia=barbearia,
        data_hora__gte=timezone.now(),
        status__in=['agendado', 'confirmado']
    )[:5]
    
    context = {
        'barbearia': barbearia,
        'agendamentos_hoje': agendamentos_hoje,
        'agendamentos_pendentes': agendamentos_pendentes,
        'total_servicos': total_servicos,
        'total_profissionais': total_profissionais,
        'proximos_agendamentos': proximos_agendamentos,
        'excede_limite_profissionais': barbearia.excede_limite_profissionais(),
    }
    return render(request, 'barbearias/admin/dashboard.html', context)

@barbeiro_required
def admin_servicos_lista(request, slug):
    """Lista de serviços para administração"""
    barbearia = Barbearia.objects.get(slug=slug, ativa=True)
    servicos = barbearia.servicos.all().order_by('nome')
    
    context = {
        'barbearia': barbearia,
        'servicos': servicos,
    }
    return render(request, 'barbearias/admin/servicos_lista.html', context)

@barbeiro_required
def admin_servico_criar(request, slug):
    """Criar novo serviço"""
    barbearia = Barbearia.objects.get(slug=slug, ativa=True)
    
    if request.method == 'POST':
        form = ServicoForm(request.POST)
        if form.is_valid():
            servico = form.save(commit=False)
            servico.barbearia = barbearia
            servico.save()
            messages.success(request, 'Serviço criado com sucesso!')
            return redirect('barbearias:admin_servicos_lista', slug=slug)
    else:
        form = ServicoForm()
    
    context = {
        'barbearia': barbearia,
        'form': form,
        'titulo': 'Criar Serviço',
        'botao': 'Criar Serviço'
    }
    return render(request, 'barbearias/admin/servico_form.html', context)

@barbeiro_required
def admin_servico_editar(request, slug, servico_id):
    """Editar serviço existente"""
    barbearia = Barbearia.objects.get(slug=slug, ativa=True)
    servico = get_object_or_404(Servico, id=servico_id, barbearia=barbearia)
    
    if request.method == 'POST':
        form = ServicoForm(request.POST, instance=servico)
        if form.is_valid():
            form.save()
            messages.success(request, 'Serviço atualizado com sucesso!')
            return redirect('barbearias:admin_servicos_lista', slug=slug)
    else:
        form = ServicoForm(instance=servico)
    
    context = {
        'barbearia': barbearia,
        'servico': servico,
        'form': form,
        'titulo': 'Editar Serviço',
        'botao': 'Salvar Alterações',
    }
    return render(request, 'barbearias/admin/servico_form.html', context)

@barbeiro_required
def admin_servico_deletar(request, slug, servico_id):
    """Deletar serviço"""
    barbearia = Barbearia.objects.get(slug=slug, ativa=True)
    servico = get_object_or_404(Servico, id=servico_id, barbearia=barbearia)
    
    if request.method == 'POST':
        servico.delete()
        messages.success(request, 'Serviço deletado com sucesso!')
        return redirect('barbearias:admin_servicos_lista', slug=slug)
    
    context = {
        'barbearia': barbearia,
        'servico': servico,
    }
    return render(request, 'barbearias/admin/servico_deletar.html', context)

@barbeiro_required
def admin_agendamentos_lista(request, slug):
    """Lista de agendamentos da barbearia"""
    barbearia = Barbearia.objects.get(slug=slug, ativa=True)
    
    # Filtros
    data_filtro = request.GET.get('data', '')
    status_filtro = request.GET.get('status', '')
    profissional_filtro = request.GET.get('profissional', '')
    
    # Query base
    agendamentos = Agendamento.objects.filter(barbearia=barbearia)
    
    # Aplicar filtros
    if data_filtro:
        try:
            from datetime import datetime
            data = datetime.strptime(data_filtro, '%Y-%m-%d').date()
            agendamentos = agendamentos.filter(data_hora__date=data)
        except ValueError:
            pass
    
    if status_filtro:
        agendamentos = agendamentos.filter(status=status_filtro)
    
    if profissional_filtro:
        try:
            profissional_id = int(profissional_filtro)
            agendamentos = agendamentos.filter(profissional_id=profissional_id)
        except (ValueError, TypeError):
            pass
    
    # Se não houver filtro de data, mostrar apenas agendamentos dos próximos 30 dias
    if not data_filtro:
        from datetime import date, timedelta
        hoje = date.today()
        data_limite = hoje + timedelta(days=30)
        agendamentos = agendamentos.filter(
            data_hora__date__gte=hoje,
            data_hora__date__lte=data_limite
        )
    
    # Ordenar por data/hora
    agendamentos = agendamentos.order_by('data_hora')
    
    # Para os filtros no template
    profissionais = barbearia.profissionais.filter(ativo=True)
    status_choices = Agendamento.STATUS_CHOICES
    
    context = {
        'barbearia': barbearia,
        'agendamentos': agendamentos,
        'profissionais': profissionais,
        'status_choices': status_choices,
        'data_filtro': data_filtro,
        'status_filtro': status_filtro,
        'profissional_filtro': profissional_filtro,
    }
    return render(request, 'barbearias/admin/agendamentos_lista.html', context)

@barbeiro_required
def admin_agendamento_atualizar_status(request, slug, agendamento_id):
    """Atualizar status de um agendamento"""
    barbearia = Barbearia.objects.get(slug=slug, ativa=True)
    agendamento = get_object_or_404(Agendamento, id=agendamento_id, barbearia=barbearia)
    
    if request.method == 'POST':
        novo_status = request.POST.get('status')
        if novo_status in dict(Agendamento.STATUS_CHOICES):
            status_anterior = agendamento.status
            agendamento.status = novo_status
            agendamento.save()
            
            status_nome = dict(Agendamento.STATUS_CHOICES)[novo_status]
            messages.success(request, f'Agendamento de {agendamento.nome_cliente} atualizado para "{status_nome}".')
            
            # Enviar email de confirmação para o cliente quando status mudar para "confirmado"
            if novo_status == 'confirmado' and status_anterior != 'confirmado':
                from agendamentos.utils import enviar_confirmacao_agendamento_cliente
                if enviar_confirmacao_agendamento_cliente(agendamento):
                    messages.success(request, f'Email de confirmação enviado para {agendamento.nome_cliente}!')
                else:
                    if agendamento.email_cliente:
                        messages.warning(request, f'Falha ao enviar email para {agendamento.email_cliente}. Verifique as configurações.')
                    else:
                        messages.info(request, 'Cliente não possui email cadastrado. Email não enviado.')
        else:
            messages.error(request, 'Status inválido.')
    
    return redirect('barbearias:admin_agendamentos_lista', slug=slug)

@barbeiro_required
def admin_profissionais_lista(request, slug):
    """Lista de profissionais para administração"""
    barbearia = Barbearia.objects.get(slug=slug, ativa=True)
    profissionais = barbearia.profissionais.all().order_by('nome')
    
    context = {
        'barbearia': barbearia,
        'profissionais': profissionais,
    }
    return render(request, 'barbearias/admin/profissionais_lista.html', context)

@barbeiro_required
def admin_profissional_criar(request, slug):
    """Criar novo profissional"""
    barbearia = Barbearia.objects.get(slug=slug, ativa=True)
    
    # Verificar se pode adicionar mais profissionais baseado no plano
    if not barbearia.pode_adicionar_profissional():
        if barbearia.plano:
            messages.error(
                request, 
                f'🚫 Limite de profissionais atingido! Seu plano {barbearia.plano.nome} permite apenas '
                f'{barbearia.plano.max_profissionais} profissional(es). '
                f'Faça upgrade do seu plano para adicionar mais profissionais.'
            )
        else:
            messages.error(
                request, 
                '🚫 Você precisa escolher um plano para adicionar profissionais.'
            )
        return redirect('barbearias:admin_planos', slug=slug)
    
    if request.method == 'POST':
        form = ProfissionalForm(request.POST)
        if form.is_valid():
            profissional = form.save(commit=False)
            profissional.barbearia = barbearia
            profissional.save()
            messages.success(request, 'Profissional criado com sucesso!')
            return redirect('barbearias:admin_profissionais_lista', slug=slug)
    else:
        form = ProfissionalForm()
    
    context = {
        'barbearia': barbearia,
        'form': form,
        'titulo': 'Criar Profissional',
        'botao': 'Criar Profissional'
    }
    return render(request, 'barbearias/admin/profissional_form.html', context)

@barbeiro_required
def admin_profissional_editar(request, slug, profissional_id):
    """Editar profissional existente"""
    barbearia = Barbearia.objects.get(slug=slug, ativa=True)
    profissional = get_object_or_404(Profissional, id=profissional_id, barbearia=barbearia)
    
    if request.method == 'POST':
        form = ProfissionalForm(request.POST, instance=profissional)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profissional atualizado com sucesso!')
            return redirect('barbearias:admin_profissionais_lista', slug=slug)
    else:
        form = ProfissionalForm(instance=profissional)
    
    # Calcular estatísticas do profissional
    agendamentos_pendentes = profissional.agendamento_set.filter(status='agendado').count()
    agendamentos_concluidos = profissional.agendamento_set.filter(status='concluido').count()
    
    context = {
        'barbearia': barbearia,
        'profissional': profissional,
        'form': form,
        'titulo': 'Editar Profissional',
        'botao': 'Salvar Alterações',
        'agendamentos_pendentes': agendamentos_pendentes,
        'agendamentos_concluidos': agendamentos_concluidos,
    }
    return render(request, 'barbearias/admin/profissional_form.html', context)

@barbeiro_required
def admin_profissional_deletar(request, slug, profissional_id):
    barbearia = get_object_or_404(Barbearia, slug=slug, ativa=True)
    profissional = get_object_or_404(Profissional, id=profissional_id, barbearia=barbearia)

    # Se o profissional tiver agendamentos, não permitir a exclusão
    if profissional.agendamento_set.exists():
        messages.error(request, 'Não é possível deletar um profissional que já possui agendamentos.')
        return redirect('barbearias:admin_profissionais_lista', slug=slug)

    if request.method == 'POST':
        profissional.delete()
        messages.success(request, 'Profissional deletado com sucesso!')
        return redirect('barbearias:admin_profissionais_lista', slug=slug)

    context = {
        'barbearia': barbearia,
        'profissional': profissional,
    }
    return render(request, 'barbearias/admin/profissional_deletar.html', context)

def cancelar_agendamento_cliente(request, slug, agendamento_id):
    """Cancelar agendamento pelo cliente"""
    barbearia = get_object_or_404(Barbearia, slug=slug, ativa=True)
    agendamento = get_object_or_404(Agendamento, id=agendamento_id, barbearia=barbearia)
    
    if request.method == 'POST':
        telefone = request.POST.get('telefone', '').strip()
        
        # Verificar se o telefone corresponde ao agendamento
        if not telefone or agendamento.telefone_cliente != telefone:
            messages.error(request, 'Telefone não corresponde ao agendamento.')
            return redirect('barbearias:consultar_agendamentos_local', slug=slug)
        
        # Verificar se o agendamento pode ser cancelado
        if agendamento.status not in ['agendado', 'confirmado']:
            messages.error(request, 'Este agendamento não pode ser cancelado.')
            return redirect('barbearias:consultar_agendamentos_local', slug=slug)
        
        # Verificar se não está muito próximo da data/hora do agendamento
        from datetime import datetime, timedelta
        agora = timezone.now()
        limite_cancelamento = agendamento.data_hora - timedelta(hours=2)  # 2 horas antes
        
        if agora > limite_cancelamento:
            messages.error(request, 'Não é possível cancelar agendamentos com menos de 2 horas de antecedência.')
            return redirect('barbearias:consultar_agendamentos_local', slug=slug)
        
        # Cancelar o agendamento
        agendamento.status = 'cancelado'
        agendamento.save()
        
        messages.success(request, f'Agendamento de {agendamento.data_hora.strftime("%d/%m/%Y às %H:%M")} foi cancelado com sucesso.')
        
        # Redirecionar de volta para consulta mantendo o telefone
        from django.http import HttpResponseRedirect
        from django.urls import reverse
        url = reverse('barbearias:consultar_agendamentos_local', kwargs={'slug': slug})
        return HttpResponseRedirect(f"{url}?telefone={telefone}")
    
    return redirect('barbearias:consultar_agendamentos_local', slug=slug)

@require_http_methods(["GET"])
def api_horarios_disponiveis(request, slug):
    """API para consultar horários disponíveis de um profissional"""
    barbearia = get_object_or_404(Barbearia, slug=slug, ativa=True)
    
    profissional_id = request.GET.get('profissional_id')
    data_str = request.GET.get('data')
    servico_id = request.GET.get('servico_id')
    
    if not all([profissional_id, data_str, servico_id]):
        return JsonResponse({
            'erro': 'Parâmetros obrigatórios: profissional_id, data, servico_id'
        }, status=400)
    
    try:
        profissional = get_object_or_404(Profissional, id=profissional_id, barbearia=barbearia, ativo=True)
        servico = get_object_or_404(Servico, id=servico_id, barbearia=barbearia, ativo=True)
        
        # Converter string de data para objeto date
        from datetime import datetime
        data = datetime.strptime(data_str, '%Y-%m-%d').date()
        
        # Verificar se a barbearia está fechada no dia da semana
        dia_semana = data.weekday()
        horario_funcionamento = HorarioFuncionamento.objects.filter(barbearia=barbearia, dia_semana=dia_semana).first()
        
        if horario_funcionamento and horario_funcionamento.fechado:
            return JsonResponse({
                'horarios': [],
                'profissional': profissional.nome,
                'servico': servico.nome,
                'duracao': servico.duracao_minutos,
                'data': data_str,
                'mensagem': 'O estabelecimento está fechado neste dia.'
            })

        # Obter horários de funcionamento configurados
        horario_inicio = '08:00'  # Padrão
        horario_fim = '18:00'     # Padrão
        
        if horario_funcionamento and not horario_funcionamento.fechado:
            if horario_funcionamento.abertura and horario_funcionamento.fechamento:
                horario_inicio = horario_funcionamento.abertura.strftime('%H:%M')
                horario_fim = horario_funcionamento.fechamento.strftime('%H:%M')

        # Obter horários disponíveis
        horarios = Agendamento.obter_horarios_disponiveis(
            profissional=profissional,
            data=data,
            duracao_minutos=servico.duracao_minutos,
            horario_inicio=horario_inicio,
            horario_fim=horario_fim
        )
        
        return JsonResponse({
            'horarios': horarios,
            'profissional': profissional.nome,
            'servico': servico.nome,
            'duracao': servico.duracao_minutos,
            'data': data_str
        })
        
    except ValueError as e:
        return JsonResponse({'erro': 'Formato de data inválido. Use YYYY-MM-DD'}, status=400)
    except Exception as e:
        return JsonResponse({'erro': str(e)}, status=500)

def api_dias_fechados(request, slug):
    """API para obter dias da semana em que a barbearia está fechada"""
    barbearia = get_object_or_404(Barbearia, slug=slug, ativa=True)
    
    # Buscar horários de funcionamento onde fechado=True
    horarios_fechados = HorarioFuncionamento.objects.filter(
        barbearia=barbearia, 
        fechado=True
    ).values_list('dia_semana', flat=True)
    
    return JsonResponse({
        'dias_fechados': list(horarios_fechados)
    })

@barbeiro_required
def admin_agenda_profissional(request, slug, profissional_id):
    """Visualizar agenda de um profissional específico"""
    barbearia = Barbearia.objects.get(slug=slug, ativa=True)
    profissional = get_object_or_404(Profissional, id=profissional_id, barbearia=barbearia)
    
    # Data selecionada (default hoje)
    data_str = request.GET.get('data', timezone.now().date().strftime('%Y-%m-%d'))
    try:
        from datetime import datetime
        data_selecionada = datetime.strptime(data_str, '%Y-%m-%d').date()
    except ValueError:
        data_selecionada = timezone.now().date()
    
    # Buscar agendamentos do profissional para a data
    agendamentos = Agendamento.objects.filter(
        profissional=profissional,
        data_hora__date=data_selecionada,
        status__in=['agendado', 'confirmado']
    ).order_by('data_hora')
    
    # Gerar horários do dia baseado no horário de funcionamento
    from datetime import datetime, time, timedelta
    horarios_dia = []
    
    # Obter horário de funcionamento configurado
    dia_semana = data_selecionada.weekday()
    horario_funcionamento = HorarioFuncionamento.objects.filter(barbearia=barbearia, dia_semana=dia_semana).first()
    
    # Definir horários padrão ou usar os configurados
    hora_inicio = time(8, 0)   # 8:00 padrão
    hora_fim = time(18, 0)     # 18:00 padrão
    
    # Se estabelecimento fechado no dia, não mostrar horários
    estabelecimento_fechado = False
    if horario_funcionamento and horario_funcionamento.fechado:
        estabelecimento_fechado = True
    elif horario_funcionamento and not horario_funcionamento.fechado:
        if horario_funcionamento.abertura and horario_funcionamento.fechamento:
            hora_inicio = horario_funcionamento.abertura
            hora_fim = horario_funcionamento.fechamento
    
    if not estabelecimento_fechado:
        hora_atual = datetime.combine(data_selecionada, hora_inicio)
        hora_limite = datetime.combine(data_selecionada, hora_fim)
        
        while hora_atual <= hora_limite:
            # Verificar se há agendamento neste horário
            agendamento_neste_horario = None
            for agendamento in agendamentos:
                inicio_agendamento = agendamento.data_hora
                fim_agendamento = inicio_agendamento + timedelta(minutes=agendamento.servico.duracao_minutos)
                
                if inicio_agendamento <= hora_atual < fim_agendamento:
                    agendamento_neste_horario = agendamento
                    break
            
            horarios_dia.append({
                'hora': hora_atual.strftime('%H:%M'),
                'datetime': hora_atual,
                'agendamento': agendamento_neste_horario,
                'disponivel': agendamento_neste_horario is None
            })
            
            hora_atual += timedelta(minutes=30)  # Intervalos de 30 minutos
    
    context = {
        'barbearia': barbearia,
        'profissional': profissional,
        'data_selecionada': data_selecionada,
        'horarios_dia': horarios_dia,
        'agendamentos': agendamentos,
        'estabelecimento_fechado': estabelecimento_fechado,
        'horario_funcionamento': horario_funcionamento,
    }
    return render(request, 'barbearias/admin/agenda_profissional.html', context)

@barbeiro_required
def admin_horarios_funcionamento(request, slug):
    """Gerenciar horários de funcionamento da barbearia"""
    barbearia = get_object_or_404(Barbearia, slug=slug, usuario=request.user, ativa=True)

    # Obter ou criar instâncias de HorarioFuncionamento para cada dia da semana
    horarios_existentes = {h.dia_semana: h for h in HorarioFuncionamento.objects.filter(barbearia=barbearia)}
    
    # Criar uma lista de formulários, um para cada dia da semana
    forms = []
    for dia_num, dia_nome in HorarioFuncionamento.DIAS_DA_SEMANA:
        instance = horarios_existentes.get(dia_num)
        initial_data = {'dia_semana': dia_num} # Garante que o dia da semana esteja no formulário
        
        if request.method == 'POST':
            # Para cada dia, precisamos de um prefixo único para o formset
            form = HorarioFuncionamentoForm(request.POST, instance=instance, prefix=f'dia_{dia_num}')
        else:
            form = HorarioFuncionamentoForm(instance=instance, initial=initial_data, prefix=f'dia_{dia_num}')
        
        forms.append({'dia_nome': dia_nome, 'form': form})

    if request.method == 'POST':
        all_forms_valid = True
        forms_to_process = []

        # Criar uma cópia mutável de request.POST
        post_data = request.POST.copy()

        for dia_num, dia_nome in HorarioFuncionamento.DIAS_DA_SEMANA:
            instance = horarios_existentes.get(dia_num)
            
            # Garantir que dia_semana esteja em post_data para este formulário
            post_data[f'dia_{dia_num}-dia_semana'] = str(dia_num) # Converte para string para o POST data

            form = HorarioFuncionamentoForm(post_data, instance=instance, prefix=f'dia_{dia_num}')
            forms_to_process.append(form)

        for form in forms_to_process:
            if form.is_valid():
                fechado = form.cleaned_data['fechado']
                abertura = form.cleaned_data['abertura']
                fechamento = form.cleaned_data['fechamento']

                if fechado:
                    # Se fechado, garantir que abertura e fechamento sejam None
                    form.cleaned_data['abertura'] = None
                    form.cleaned_data['fechamento'] = None
                elif not abertura or not fechamento:
                    # Se não está fechado, mas faltam horários, é um erro
                    form.add_error('abertura', "Obrigatório se não estiver fechado.")
                    form.add_error('fechamento', "Obrigatório se não estiver fechado.")
                    all_forms_valid = False
                elif abertura and fechamento and abertura >= fechamento:
                    form.add_error('fechamento', "Deve ser depois do horário de abertura.")
                    all_forms_valid = False
            else:
                all_forms_valid = False
        
        if all_forms_valid:
            for form in forms_to_process:
                # Salvar apenas se o formulário for válido após todas as validações
                horario = form.save(commit=False)
                horario.barbearia = barbearia
                horario.dia_semana = form.cleaned_data['dia_semana']
                horario.abertura = form.cleaned_data['abertura']
                horario.fechamento = form.cleaned_data['fechamento']
                horario.save()
            messages.success(request, 'Horários de funcionamento atualizados com sucesso!')
            return redirect('barbearias:admin_horarios_funcionamento', slug=slug)
        else:
            messages.error(request, 'Por favor, corrija os erros nos horários.')

        # Re-renderizar formulários com erros
        forms = []
        for dia_num, dia_nome in HorarioFuncionamento.DIAS_DA_SEMANA:
            instance = horarios_existentes.get(dia_num)
            # Passar post_data para o formulário para que ele mantenha os valores submetidos
            form = HorarioFuncionamentoForm(post_data, instance=instance, prefix=f'dia_{dia_num}')
            forms.append({'dia_nome': dia_nome, 'form': form})

    context = {
        'barbearia': barbearia,
        'forms': forms,
    }
    return render(request, 'barbearias/admin/horarios_funcionamento.html', context)

@barbeiro_required
def admin_configuracoes(request, slug):
    """Configurações da barbearia"""
    barbearia = get_object_or_404(Barbearia, slug=slug, usuario=request.user, ativa=True)
    
    # Verificar se tem permissão para alterar tema (plano avançado)
    pode_alterar_tema = verificar_permissao_plano(barbearia, 'personalizacao_completa')
    
    if request.method == 'POST':
        form = BarbeariaConfigForm(request.POST, instance=barbearia)
        if form.is_valid():
            # Se não tem permissão para alterar tema, manter o tema atual
            if not pode_alterar_tema and 'tema' in form.changed_data:
                messages.error(request, 'Seu plano atual não permite alteração de tema. Faça upgrade para o plano Avançado.')
                form.instance.tema = barbearia.tema  # Restaurar tema original
            
            form.save()
            messages.success(request, 'Configurações atualizadas com sucesso!')
            return redirect('barbearias:admin_configuracoes', slug=slug)
    else:
        form = BarbeariaConfigForm(instance=barbearia)
    
    context = {
        'barbearia': barbearia,
        'form': form,
        'pode_alterar_tema': pode_alterar_tema,
    }
    return render(request, 'barbearias/admin/configuracoes.html', context)

@barbeiro_required
def admin_relatorios(request, slug):
    """Página de relatórios para download"""
    barbearia = get_object_or_404(Barbearia, slug=slug, usuario=request.user, ativa=True)
    
    # Verificar se tem acesso a relatórios
    if not verificar_permissao_plano(barbearia, 'relatorios_basicos'):
        messages.error(
            request, 
            '🚫 Relatórios não disponíveis no seu plano atual. '
            'Faça upgrade para o Plano Intermediário ou Avançado para acessar relatórios.'
        )
        return redirect('barbearias:admin_planos', slug=slug)
    
    # Se foi solicitado download
    if request.GET.get('download'):
        mes_inicio = int(request.GET.get('mes_inicio', timezone.now().month))
        ano_inicio = int(request.GET.get('ano_inicio', timezone.now().year))
        mes_fim = int(request.GET.get('mes_fim', timezone.now().month))
        ano_fim = int(request.GET.get('ano_fim', timezone.now().year))
        formato = request.GET.get('formato', 'pdf')  # pdf ou csv
        
        # Calcular datas de início e fim
        data_inicio = datetime(ano_inicio, mes_inicio, 1)
        
        # Data fim: último dia do mês final
        if mes_fim == 12:
            data_fim = datetime(ano_fim + 1, 1, 1) - timedelta(days=1)
        else:
            data_fim = datetime(ano_fim, mes_fim + 1, 1) - timedelta(days=1)
        
        # Buscar agendamentos no período
        agendamentos = Agendamento.objects.filter(
            barbearia=barbearia,
            data_hora__date__gte=data_inicio.date(),
            data_hora__date__lte=data_fim.date()
        ).order_by('data_hora')
        
        # Gerar nome do arquivo
        if data_inicio.year == data_fim.year and data_inicio.month == data_fim.month:
            # Mesmo mês
            periodo_nome = data_inicio.strftime('%m-%Y')
        else:
            # Período entre meses
            periodo_nome = f"{data_inicio.strftime('%m-%Y')}_a_{data_fim.strftime('%m-%Y')}"
        
        if formato == 'pdf':
            return gerar_relatorio_pdf(barbearia, agendamentos, data_inicio, data_fim, periodo_nome)
        else:
            return gerar_relatorio_csv(barbearia, agendamentos, periodo_nome)
    
    # Mostrar página de seleção
    meses_nomes = [
        'Janeiro', 'Fevereiro', 'Março', 'Abril',
        'Maio', 'Junho', 'Julho', 'Agosto',
        'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ]
    
    context = {
        'barbearia': barbearia,
        'meses': [
            (1, 'Janeiro'), (2, 'Fevereiro'), (3, 'Março'), (4, 'Abril'),
            (5, 'Maio'), (6, 'Junho'), (7, 'Julho'), (8, 'Agosto'),
            (9, 'Setembro'), (10, 'Outubro'), (11, 'Novembro'), (12, 'Dezembro')
        ],
        'anos': range(2024, timezone.now().year + 2),
        'ano_atual': timezone.now().year,
        'mes_atual': timezone.now().month,
        'mes_atual_nome': meses_nomes[timezone.now().month - 1],
    }
    return render(request, 'barbearias/admin/relatorios.html', context)


def gerar_relatorio_pdf(barbearia, agendamentos, data_inicio, data_fim, periodo_nome):
    """Gera relatório em PDF"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    
    # Estilo customizado para título
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1,  # Centralizado
        textColor=colors.darkblue
    )
    
    # Estilo para subtítulos
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.darkgreen
    )
    
    story = []
    
    # Título
    story.append(Paragraph(f"Relatório de Agendamentos", title_style))
    story.append(Paragraph(f"{barbearia.nome}", styles['Heading2']))
    
    # Período
    if data_inicio.month == data_fim.month and data_inicio.year == data_fim.year:
        periodo_texto = data_inicio.strftime('%B de %Y')
    else:
        periodo_texto = f"{data_inicio.strftime('%B de %Y')} até {data_fim.strftime('%B de %Y')}"
    
    story.append(Paragraph(f"Período: {periodo_texto}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Estatísticas gerais
    total_agendamentos = agendamentos.count()
    agendamentos_concluidos = agendamentos.filter(status='concluido').count()
    agendamentos_cancelados = agendamentos.filter(status='cancelado').count()
    faturamento_total = agendamentos.filter(status='concluido').aggregate(
        total=Sum('servico__preco')
    )['total'] or 0
    
    story.append(Paragraph("📊 Resumo Geral", subtitle_style))
    
    # Tabela de resumo
    dados_resumo = [
        ['Métrica', 'Valor'],
        ['Total de Agendamentos', str(total_agendamentos)],
        ['Agendamentos Concluídos', str(agendamentos_concluidos)],
        ['Agendamentos Cancelados', str(agendamentos_cancelados)],
        ['Faturamento Total', f'R$ {faturamento_total:.2f}'],
    ]
    
    tabela_resumo = Table(dados_resumo, colWidths=[3*inch, 2*inch])
    tabela_resumo.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(tabela_resumo)
    story.append(Spacer(1, 20))
    
    # Tabela de agendamentos
    story.append(Paragraph("📅 Lista de Agendamentos", subtitle_style))
    
    if agendamentos.exists():
        # Cabeçalho da tabela
        dados_agendamentos = [
            ['Data/Hora', 'Cliente', 'Telefone', 'Serviço', 'Profissional', 'Preço', 'Status']
        ]
        
        # Dados dos agendamentos
        for agendamento in agendamentos:
            dados_agendamentos.append([
                agendamento.data_hora.strftime('%d/%m/%Y %H:%M'),
                agendamento.nome_cliente,
                agendamento.telefone_cliente,
                agendamento.servico.nome,
                agendamento.profissional.nome,
                f'R$ {agendamento.servico.preco:.2f}',
                agendamento.get_status_display()
            ])
        
        # Criar tabela
        tabela_agendamentos = Table(dados_agendamentos, colWidths=[1.2*inch, 1.5*inch, 1*inch, 1.2*inch, 1.2*inch, 0.8*inch, 1*inch])
        tabela_agendamentos.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(tabela_agendamentos)
    else:
        story.append(Paragraph("Nenhum agendamento encontrado no período selecionado.", styles['Normal']))
    
    # Rodapé
    story.append(Spacer(1, 30))
    story.append(Paragraph(f"Relatório gerado em {timezone.now().strftime('%d/%m/%Y às %H:%M')}", styles['Normal']))
    
    # Gerar PDF
    doc.build(story)
    
    # Retornar resposta
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="relatorio_{barbearia.slug}_{periodo_nome}.pdf"'
    
    return response


def gerar_relatorio_csv(barbearia, agendamentos, periodo_nome):
    """Gera relatório em CSV"""
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="relatorio_{barbearia.slug}_{periodo_nome}.csv"'
    
    # Adicionar BOM para Excel reconhecer UTF-8
    response.write('\ufeff')
    
    writer = csv.writer(response)
    writer.writerow([
        'Data/Hora', 'Cliente', 'Telefone', 'Email', 'Serviço', 
        'Profissional', 'Preço (R$)', 'Status', 'Observações'
    ])
    
    for agendamento in agendamentos:
        writer.writerow([
            agendamento.data_hora.strftime('%d/%m/%Y %H:%M'),
            agendamento.nome_cliente,
            agendamento.telefone_cliente,
            agendamento.email_cliente or '',
            agendamento.servico.nome,
            agendamento.profissional.nome,
            f'{agendamento.servico.preco}',
            agendamento.get_status_display(),
            agendamento.observacoes or ''
        ])
    
    return response


# DEMONSTRAÇÃO DO SISTEMA DE TEMAS

def admin_demo_temas(request, slug):
    """Demo dos temas disponíveis"""
    barbearia = get_object_or_404(Barbearia, slug=slug, ativa=True)
    
    temas_info = {
        "classico": {"nome": "Clássico", "desc": "Azul e Branco - Profissional"},
        "moderno": {"nome": "Moderno", "desc": "Preto e Dourado - Elegante"},
        "elegante": {"nome": "Elegante", "desc": "Cinza e Verde - Natural"},
        "vibrante": {"nome": "Vibrante", "desc": "Roxo e Rosa - Criativo"},
        "rustico": {"nome": "Rústico", "desc": "Marrom e Laranja - Acolhedor"},
        "minimalista": {"nome": "Minimalista", "desc": "Branco e Preto - Clean"},
        "tropical": {"nome": "Tropical", "desc": "Verde e Azul - Relaxante"},
        "vintage": {"nome": "Vintage", "desc": "Sépia e Bege - Nostálgico"}
    }
    
    context = {"barbearia": barbearia, "temas_info": temas_info}
    return render(request, "barbearias/admin/demo_temas.html", context)


# SISTEMA DE PLANOS

@barbeiro_required
def admin_planos(request, slug):
    """Página de seleção de planos"""
    barbearia = get_object_or_404(Barbearia, slug=slug, ativa=True)
    
    # Buscar todos os planos ativos
    planos = Plano.objects.filter(ativo=True).order_by('preco_mensal')
    
    # Verificar se excede limite atual
    profissionais_ativos = barbearia.profissionais.filter(ativo=True).count()
    excede_limite = barbearia.excede_limite_profissionais()
    
    # Adicionar warnings para planos que não comportam os profissionais atuais
    for plano in planos:
        plano.pode_selecionar = True
        plano.warning_profissionais = None
        
        if plano.max_profissionais > 0 and profissionais_ativos > plano.max_profissionais:
            excesso = profissionais_ativos - plano.max_profissionais
            plano.warning_profissionais = f"⚠️ Você tem {profissionais_ativos} profissionais, mas este plano permite apenas {plano.max_profissionais}. {excesso} profissional(es) será(ão) automaticamente desativado(s)."
    
    context = {
        'barbearia': barbearia,
        'planos': planos,
        'plano_atual': barbearia.plano,
        'profissionais_ativos': profissionais_ativos,
        'excede_limite': excede_limite,
    }
    return render(request, 'barbearias/admin/planos.html', context)

@barbeiro_required
def admin_selecionar_plano(request, slug, plano_id):
    """Selecionar um plano para a barbearia"""
    barbearia = get_object_or_404(Barbearia, slug=slug, ativa=True)
    plano = get_object_or_404(Plano, id=plano_id, ativo=True)
    
    # Verificar se há profissionais em excesso
    profissionais_ativos_antes = barbearia.profissionais.filter(ativo=True).count()
    
    # Atualizar o plano
    plano_anterior = barbearia.plano
    barbearia.plano = plano
    barbearia.save()
    
    # Aplicar limite de profissionais (desativar excesso)
    profissionais_desativados = barbearia.aplicar_limite_profissionais()
    
    # Mensagens de feedback
    if profissionais_desativados > 0:
        messages.warning(
            request,
            f'✅ Plano alterado para {plano.nome}! '
            f'⚠️ {profissionais_desativados} profissional(es) foram automaticamente desativados '
            f'para respeitar o limite de {plano.max_profissionais} profissionais do plano {plano.nome}. '
            f'Você pode reativá-los fazendo upgrade para um plano superior.'
        )
    else:
        messages.success(
            request,
            f'✅ Plano alterado com sucesso para {plano.nome}!'
        )
    
    return redirect('barbearias:admin_planos', slug=slug)

