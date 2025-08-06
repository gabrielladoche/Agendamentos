from django.urls import path
from . import views

app_name = 'barbearias'

urlpatterns = [
    # URLs para estabelecimentos (nova área administrativa)
    path('estabelecimento/login/', views.login_estabelecimento, name='login_estabelecimento'),
    path('estabelecimento/logout/', views.logout_estabelecimento, name='logout_estabelecimento'),
    path('estabelecimento/dashboard/', views.dashboard_estabelecimento, name='dashboard_estabelecimento'),
    path('estabelecimento/relatorios/', views.relatorios_estabelecimento, name='relatorios_estabelecimento'),
    path('estabelecimento/relatorio-mensal/', views.relatorio_mensal_estabelecimento, name='relatorio_mensal_estabelecimento'),
    path('estabelecimento/exportar-csv/', views.exportar_csv_estabelecimento, name='exportar_csv_estabelecimento'),
    path('estabelecimento/agendamentos/', views.agendamentos_estabelecimento, name='agendamentos_estabelecimento'),
    
    # URLs públicas (existentes)
    path('', views.redirect_to_default, name='redirect_to_default'),
    path('<slug:slug>/', views.mini_site, name='mini_site'),
    path('<slug:slug>/agendar/', views.agendar, name='agendar'),
    path('<slug:slug>/consultar/', views.consultar_agendamentos_local, name='consultar_agendamentos_local'),
    path('<slug:slug>/agendamentos/<int:agendamento_id>/cancelar/', views.cancelar_agendamento_cliente, name='cancelar_agendamento_cliente'),
    path('<slug:slug>/api/horarios-disponiveis/', views.api_horarios_disponiveis, name='api_horarios_disponiveis'),
    path('<slug:slug>/api/dias-fechados/', views.api_dias_fechados, name='api_dias_fechados'),
    
    # URLs administrativas (protegidas por login próprio)
    path('<slug:slug>/admin/login/', views.admin_login, name='admin_login'),
    path('<slug:slug>/admin/logout/', views.admin_logout, name='admin_logout'),
    path('<slug:slug>/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('<slug:slug>/admin/servicos/', views.admin_servicos_lista, name='admin_servicos_lista'),
    path('<slug:slug>/admin/servicos/criar/', views.admin_servico_criar, name='admin_servico_criar'),
    path('<slug:slug>/admin/servicos/<int:servico_id>/editar/', views.admin_servico_editar, name='admin_servico_editar'),
    path('<slug:slug>/admin/servicos/<int:servico_id>/deletar/', views.admin_servico_deletar, name='admin_servico_deletar'),
    path('<slug:slug>/admin/agendamentos/', views.admin_agendamentos_lista, name='admin_agendamentos_lista'),
    path('<slug:slug>/admin/agendamentos/<int:agendamento_id>/status/', views.admin_agendamento_atualizar_status, name='admin_agendamento_atualizar_status'),
    path('<slug:slug>/admin/profissionais/', views.admin_profissionais_lista, name='admin_profissionais_lista'),
    path('<slug:slug>/admin/profissionais/criar/', views.admin_profissional_criar, name='admin_profissional_criar'),
    path('<slug:slug>/admin/profissionais/<int:profissional_id>/editar/', views.admin_profissional_editar, name='admin_profissional_editar'),
    path('<slug:slug>/admin/profissionais/<int:profissional_id>/deletar/', views.admin_profissional_deletar, name='admin_profissional_deletar'),
    path('<slug:slug>/admin/profissionais/<int:profissional_id>/agenda/', views.admin_agenda_profissional, name='admin_agenda_profissional'),
    path('<slug:slug>/admin/horarios/', views.admin_horarios_funcionamento, name='admin_horarios_funcionamento'),
    path('<slug:slug>/admin/configuracoes/', views.admin_configuracoes, name='admin_configuracoes'),
    path('<slug:slug>/admin/relatorios/', views.admin_relatorios, name='admin_relatorios'),
    path('<slug:slug>/admin/planos/', views.admin_planos, name='admin_planos'),
    path('<slug:slug>/admin/planos/<int:plano_id>/selecionar/', views.admin_selecionar_plano, name='admin_selecionar_plano'),
]
