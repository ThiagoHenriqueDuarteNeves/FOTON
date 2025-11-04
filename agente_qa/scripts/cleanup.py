#!/usr/bin/env python3
"""
Script para limpar arquivos temporários, logs e cache.
Uso: python scripts/cleanup.py [--all]
"""

import os
import shutil
import argparse
from pathlib import Path

def get_size_mb(path):
    """Retorna tamanho em MB de um arquivo ou diretório"""
    if os.path.isfile(path):
        return os.path.getsize(path) / (1024 * 1024)
    
    total = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            if os.path.exists(filepath):
                total += os.path.getsize(filepath)
    
    return total / (1024 * 1024)

def clean_logs():
    """Limpa arquivos de log"""
    print("\n🧹 Limpando logs...")
    
    logs_dir = Path('logs')
    if not logs_dir.exists():
        print("  ℹ️  Diretório 'logs' não encontrado")
        return 0
    
    total_size = 0
    count = 0
    
    for log_file in logs_dir.glob('*.log'):
        size = get_size_mb(log_file)
        total_size += size
        log_file.unlink()
        count += 1
        print(f"  ✅ Removido: {log_file.name} ({size:.2f} MB)")
    
    print(f"  📊 Total: {count} arquivo(s), {total_size:.2f} MB liberados")
    return total_size

def clean_screenshots():
    """Limpa screenshots"""
    print("\n🧹 Limpando screenshots...")
    
    prints_dir = Path('prints')
    if not prints_dir.exists():
        print("  ℹ️  Diretório 'prints' não encontrado")
        return 0
    
    total_size = 0
    count = 0
    
    for img_file in prints_dir.glob('*.png'):
        size = get_size_mb(img_file)
        total_size += size
        img_file.unlink()
        count += 1
        print(f"  ✅ Removido: {img_file.name} ({size:.2f} MB)")
    
    print(f"  📊 Total: {count} arquivo(s), {total_size:.2f} MB liberados")
    return total_size

def clean_pycache():
    """Limpa arquivos __pycache__"""
    print("\n🧹 Limpando __pycache__...")
    
    total_size = 0
    count = 0
    
    for pycache in Path('.').rglob('__pycache__'):
        size = get_size_mb(pycache)
        total_size += size
        shutil.rmtree(pycache)
        count += 1
        print(f"  ✅ Removido: {pycache}")
    
    print(f"  📊 Total: {count} diretório(s), {total_size:.2f} MB liberados")
    return total_size

def clean_pytest_cache():
    """Limpa cache do pytest"""
    print("\n🧹 Limpando .pytest_cache...")
    
    pytest_cache = Path('.pytest_cache')
    if not pytest_cache.exists():
        print("  ℹ️  .pytest_cache não encontrado")
        return 0
    
    size = get_size_mb(pytest_cache)
    shutil.rmtree(pytest_cache)
    print(f"  ✅ Removido .pytest_cache ({size:.2f} MB)")
    
    return size

def clean_node_modules():
    """Limpa node_modules (CUIDADO!)"""
    print("\n🧹 Limpando node_modules...")
    
    node_modules = Path('frontend/node_modules')
    if not node_modules.exists():
        print("  ℹ️  node_modules não encontrado")
        return 0
    
    size = get_size_mb(node_modules)
    print(f"  ⚠️  Isso irá remover {size:.2f} MB")
    response = input("  Tem certeza? (s/n): ")
    
    if response.lower() != 's':
        print("  ❌ Cancelado")
        return 0
    
    shutil.rmtree(node_modules)
    print(f"  ✅ Removido node_modules ({size:.2f} MB)")
    print("  💡 Lembre-se de executar 'npm install' antes de rodar o frontend")
    
    return size

def clean_frontend_build():
    """Limpa build do frontend"""
    print("\n🧹 Limpando build do frontend...")
    
    dist_dir = Path('frontend/dist')
    if not dist_dir.exists():
        print("  ℹ️  frontend/dist não encontrado")
        return 0
    
    size = get_size_mb(dist_dir)
    shutil.rmtree(dist_dir)
    print(f"  ✅ Removido frontend/dist ({size:.2f} MB)")
    
    return size

def main():
    parser = argparse.ArgumentParser(description='Limpa arquivos temporários do projeto')
    parser.add_argument('--all', action='store_true', help='Limpa tudo, incluindo node_modules')
    args = parser.parse_args()
    
    print("=" * 60)
    print("🧹 Limpeza do Projeto - Agente de QA")
    print("=" * 60)
    
    total_freed = 0
    
    # Limpezas padrão
    total_freed += clean_logs()
    total_freed += clean_screenshots()
    total_freed += clean_pycache()
    total_freed += clean_pytest_cache()
    total_freed += clean_frontend_build()
    
    # Limpeza completa
    if args.all:
        total_freed += clean_node_modules()
    
    print("\n" + "=" * 60)
    print(f"✅ Limpeza concluída! Total liberado: {total_freed:.2f} MB")
    print("=" * 60)

if __name__ == '__main__':
    main()
