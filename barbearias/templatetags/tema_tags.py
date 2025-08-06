from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag
def tema_data_attr(barbearia):
    """Retorna o atributo data-tema baseado no tema da barbearia"""
    if barbearia and hasattr(barbearia, 'tema'):
        return mark_safe(f'data-tema="{barbearia.tema}"')
    return mark_safe('data-tema="classico"')

@register.simple_tag
def tema_css_vars(barbearia):
    """Retorna as variáveis CSS do tema como inline styles"""
    temas_config = {
        'classico': {
            'primaria': '#3B82F6',
            'secundaria': '#1E40AF',
            'acento': '#60A5FA',
            'fundo': '#F8FAFC',
            'card': '#FFFFFF',
            'texto': '#1F2937',
            'texto_claro': '#6B7280',
        },
        'moderno': {
            'primaria': '#F59E0B',
            'secundaria': '#111827',
            'acento': '#FCD34D',
            'fundo': '#111827',
            'card': '#1F2937',
            'texto': '#F9FAFB',
            'texto_claro': '#D1D5DB',
        },
        'elegante': {
            'primaria': '#059669',
            'secundaria': '#374151',
            'acento': '#34D399',
            'fundo': '#F3F4F6',
            'card': '#FFFFFF',
            'texto': '#374151',
            'texto_claro': '#6B7280',
        },
        'vibrante': {
            'primaria': '#8B5CF6',
            'secundaria': '#7C3AED',
            'acento': '#F472B6',
            'fundo': '#FAF5FF',
            'card': '#FFFFFF',
            'texto': '#581C87',
            'texto_claro': '#7C2D92',
        },
        'rustico': {
            'primaria': '#EA580C',
            'secundaria': '#92400E',
            'acento': '#FB923C',
            'fundo': '#FEF3E2',
            'card': '#FFFFFF',
            'texto': '#92400E',
            'texto_claro': '#C2410C',
        },
        'minimalista': {
            'primaria': '#000000',
            'secundaria': '#374151',
            'acento': '#6B7280',
            'fundo': '#FFFFFF',
            'card': '#F9FAFB',
            'texto': '#111827',
            'texto_claro': '#6B7280',
        },
        'tropical': {
            'primaria': '#0891B2',
            'secundaria': '#059669',
            'acento': '#06B6D4',
            'fundo': '#ECFEFF',
            'card': '#FFFFFF',
            'texto': '#155E75',
            'texto_claro': '#0891B2',
        },
        'vintage': {
            'primaria': '#A16207',
            'secundaria': '#78716C',
            'acento': '#D97706',
            'fundo': '#FEF7ED',
            'card': '#FFFBEB',
            'texto': '#78716C',
            'texto_claro': '#A8A29E',
        }
    }
    
    tema = 'classico'  # padrão
    if barbearia and hasattr(barbearia, 'tema'):
        tema = barbearia.tema
    
    config = temas_config.get(tema, temas_config['classico'])
    
    styles = []
    for key, value in config.items():
        css_var = key.replace('_', '-')
        styles.append(f'--cor-{css_var}: {value}')
    
    return mark_safe(f'style="{"; ".join(styles)}"')

@register.filter
def tema_class(value, tema_class):
    """Adiciona classes CSS baseadas no tema"""
    return f"{value} tema-{tema_class}"

@register.simple_tag
def preview_tema(tema_nome):
    """Retorna uma div de preview para seleção de tema"""
    temas_info = {
        'classico': {'cor': '#3B82F6', 'nome': 'Clássico', 'desc': 'Azul e Branco'},
        'moderno': {'cor': '#F59E0B', 'nome': 'Moderno', 'desc': 'Preto e Dourado'},
        'elegante': {'cor': '#059669', 'nome': 'Elegante', 'desc': 'Cinza e Verde'},
        'vibrante': {'cor': '#8B5CF6', 'nome': 'Vibrante', 'desc': 'Roxo e Rosa'},
        'rustico': {'cor': '#EA580C', 'nome': 'Rústico', 'desc': 'Marrom e Laranja'},
        'minimalista': {'cor': '#000000', 'nome': 'Minimalista', 'desc': 'Branco e Preto'},
        'tropical': {'cor': '#0891B2', 'nome': 'Tropical', 'desc': 'Verde e Azul'},
        'vintage': {'cor': '#A16207', 'nome': 'Vintage', 'desc': 'Sépia e Bege'},
    }
    
    info = temas_info.get(tema_nome, temas_info['classico'])
    
    return mark_safe(f'''
        <div class="tema-preview" data-tema="{tema_nome}">
            <div class="preview-circle" style="background-color: {info['cor']}"></div>
            <div class="preview-info">
                <span class="preview-nome">{info['nome']}</span>
                <span class="preview-desc">{info['desc']}</span>
            </div>
        </div>
    ''')
