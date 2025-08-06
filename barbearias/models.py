from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from decimal import Decimal

class Plano(models.Model):
    TIPOS_PLANO = [
        ('basico', 'Básico'),
        ('intermediario', 'Intermediário'),
        ('avancado', 'Avançado'),
    ]
    
    nome = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPOS_PLANO, unique=True)
    preco_mensal = models.DecimalField(max_digits=8, decimal_places=2)
    max_profissionais = models.PositiveIntegerField(help_text="Número máximo de profissionais permitidos (0 = ilimitado)")
    descricao = models.TextField()
    
    # Funcionalidades do plano
    agendamento_online = models.BooleanField(default=True)
    gestao_agenda = models.BooleanField(default=True)
    notificacoes_email = models.BooleanField(default=True)
    notificacoes_sms = models.BooleanField(default=False)
    integracao_google_calendar = models.BooleanField(default=False)
    relatorios_basicos = models.BooleanField(default=False)
    relatorios_avancados = models.BooleanField(default=False)
    integracao_pagamento = models.BooleanField(default=False)
    personalizacao_completa = models.BooleanField(default=False)
    suporte_prioritario = models.BooleanField(default=False)
    
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.nome} - R$ {self.preco_mensal}/mês"
    
    class Meta:
        verbose_name = "Plano"
        verbose_name_plural = "Planos"
        ordering = ['preco_mensal']

class Barbearia(models.Model):
    TEMAS_CHOICES = [
        ('classico', 'Clássico (Azul e Branco)'),
        ('moderno', 'Moderno (Preto e Dourado)'),
        ('elegante', 'Elegante (Cinza e Verde)'),
        ('vibrante', 'Vibrante (Roxo e Rosa)'),
        ('rustico', 'Rústico (Marrom e Laranja)'),
        ('minimalista', 'Minimalista (Branco e Preto)'),
        ('tropical', 'Tropical (Verde e Azul)'),
        ('vintage', 'Vintage (Sépia e Bege)'),
    ]
    
    nome = models.CharField(max_length=200)
    endereco = models.TextField()
    telefone = models.CharField(max_length=20)
    email_notificacoes = models.EmailField(blank=True, null=True, help_text="Email para receber notificações de novos agendamentos")
    slug = models.SlugField(unique=True, max_length=200)
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    plano = models.ForeignKey(Plano, on_delete=models.PROTECT, null=True, blank=True, help_text="Plano de assinatura do estabelecimento")
    ativa = models.BooleanField(default=True)
    tema = models.CharField(max_length=20, choices=TEMAS_CHOICES, default='classico', help_text="Tema visual do estabelecimento")
    criada_em = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)
    
    def pode_adicionar_profissional(self):
        """Verifica se pode adicionar mais profissionais baseado no plano"""
        if not self.plano:
            return False  # Sem plano = sem permissão para adicionar
        
        if self.plano.max_profissionais == 0:
            return True  # 0 = ilimitado
        
        profissionais_ativos = self.profissionais.filter(ativo=True).count()
        return profissionais_ativos < self.plano.max_profissionais
    
    def profissionais_restantes(self):
        """Retorna quantos profissionais ainda podem ser adicionados"""
        if not self.plano:
            return 0  # Sem plano = sem vagas
            
        if self.plano.max_profissionais == 0:
            return "Ilimitado"
        
        profissionais_ativos = self.profissionais.filter(ativo=True).count()
        restantes = self.plano.max_profissionais - profissionais_ativos
        return max(0, restantes)
    
    def excede_limite_profissionais(self):
        """Verifica se o número atual de profissionais excede o limite do plano"""
        if not self.plano:
            return True  # Sem plano = sempre excede
            
        if self.plano.max_profissionais == 0:
            return False  # Ilimitado = nunca excede
        
        profissionais_ativos = self.profissionais.filter(ativo=True).count()
        return profissionais_ativos > self.plano.max_profissionais
    
    def aplicar_limite_profissionais(self):
        """Desativa profissionais em excesso para respeitar o limite do plano"""
        if not self.plano or self.plano.max_profissionais == 0:
            return 0  # Sem plano ou ilimitado
        
        profissionais_ativos = self.profissionais.filter(ativo=True).order_by('-id')
        total_ativos = profissionais_ativos.count()
        limite = self.plano.max_profissionais
        
        if total_ativos > limite:
            # Desativar os profissionais mais recentes (excesso)
            excesso = total_ativos - limite
            profissionais_excesso = profissionais_ativos[:excesso]
            
            for profissional in profissionais_excesso:
                profissional.ativo = False
                profissional.save()
            
            return excesso
        
        return 0
    
    def __str__(self):
        return self.nome
    
    class Meta:
        verbose_name = "Estabelecimento"
        verbose_name_plural = "Estabelecimentos"

class Servico(models.Model):
    nome = models.CharField(max_length=200)
    preco = models.DecimalField(max_digits=8, decimal_places=2)
    duracao_minutos = models.PositiveIntegerField(help_text="Duração do serviço em minutos")
    barbearia = models.ForeignKey(Barbearia, on_delete=models.CASCADE, related_name='servicos')
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.nome} - {self.barbearia.nome}"
    
    class Meta:
        verbose_name = "Serviço"
        verbose_name_plural = "Serviços"

class Profissional(models.Model):
    nome = models.CharField(max_length=200)
    barbearia = models.ForeignKey(Barbearia, on_delete=models.CASCADE, related_name='profissionais')
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.nome} - {self.barbearia.nome}"
    
    class Meta:
        verbose_name = "Profissional"
        verbose_name_plural = "Profissionais"


class HorarioFuncionamento(models.Model):
    DIAS_DA_SEMANA = [
        (0, 'Segunda-feira'),
        (1, 'Terça-feira'),
        (2, 'Quarta-feira'),
        (3, 'Quinta-feira'),
        (4, 'Sexta-feira'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]

    barbearia = models.ForeignKey(Barbearia, on_delete=models.CASCADE, related_name='horarios_funcionamento')
    dia_semana = models.IntegerField(choices=DIAS_DA_SEMANA, unique=False)
    abertura = models.TimeField(null=True, blank=True)
    fechamento = models.TimeField(null=True, blank=True)
    fechado = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Horário de Funcionamento"
        verbose_name_plural = "Horários de Funcionamento"
        unique_together = ('barbearia', 'dia_semana')
        ordering = ['dia_semana']

    def __str__(self):
        dia = self.get_dia_semana_display()
        if self.fechado:
            return f"{dia} - Fechado"
        return f"{dia} - {self.abertura.strftime('%H:%M')} às {self.fechamento.strftime('%H:%M')}"
