from django import template
from barbearias.models import Barbearia

register = template.Library()

@register.filter
def tem_permissao_plano(barbearia, funcionalidade):
    """
    Template filter para verificar se a barbearia tem permissão para usar uma funcionalidade
    Uso: {% if barbearia|tem_permissao_plano:"relatorios_basicos" %}
    """
    if not barbearia or not barbearia.plano:
        return False
    
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

@register.simple_tag
def nome_plano_atual(barbearia):
    """
    Template tag para obter o nome do plano atual
    Uso: {% nome_plano_atual barbearia %}
    """
    if not barbearia or not barbearia.plano:
        return "Nenhum plano"
    return barbearia.plano.nome

@register.filter
def pode_adicionar_profissional(barbearia):
    """
    Template filter para verificar se pode adicionar mais profissionais
    Uso: {% if barbearia|pode_adicionar_profissional %}
    """
    if not barbearia:
        return False
    return barbearia.pode_adicionar_profissional()
