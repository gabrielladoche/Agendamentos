#!/usr/bin/env python3
"""
Script para limpar o banco MySQL e recriar do zero
"""
import pymysql
from django.conf import settings
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'barbearia_system.settings')
django.setup()

# Obter configurações do banco
db_config = settings.DATABASES['default']

def reset_database():
    """Remove todas as tabelas e recria o banco"""
    print("🔄 Conectando ao MySQL...")
    
    try:
        # Conectar ao MySQL (sem especificar banco para poder removê-lo)
        connection = pymysql.connect(
            host=db_config['HOST'],
            user=db_config['USER'],
            password=db_config['PASSWORD'],
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with connection:
            cursor = connection.cursor()
            
            # Dropar o banco se existir
            print(f"🗑️  Removendo banco '{db_config['NAME']}'...")
            cursor.execute(f"DROP DATABASE IF EXISTS `{db_config['NAME']}`")
            
            # Recriar o banco
            print(f"🆕 Criando banco '{db_config['NAME']}'...")
            cursor.execute(f"CREATE DATABASE `{db_config['NAME']}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            
            print("✅ Banco recriado com sucesso!")
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False
    
    return True

if __name__ == '__main__':
    print("⚠️  ATENÇÃO: Este script irá APAGAR TODOS os dados do banco MySQL!")
    print(f"Banco: {db_config['NAME']} em {db_config['HOST']}")
    
    if reset_database():
        print("\n🚀 Agora execute:")
        print("python3 manage.py migrate")
        print("python3 restore_mysql_data.py")
    else:
        print("\n❌ Falha na operação")