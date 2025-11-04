# Scripts

Scripts utilitários para facilitar o desenvolvimento e manutenção do projeto.

## 📜 Scripts Disponíveis

### 🚀 start_servers.py

Inicia backend (FastAPI) e frontend (React) simultaneamente.

**Uso:**
```bash
python scripts/start_servers.py
```

**O que faz:**
- ✅ Verifica se as portas 8000 e 3000 estão disponíveis
- ✅ Inicia backend na porta 8000
- ✅ Inicia frontend na porta 3000
- ✅ Mantém ambos rodando em janelas separadas (Windows)
- ✅ Permite parar ambos com Ctrl+C

**URLs:**
- Backend: http://localhost:8000
- Backend Docs: http://localhost:8000/docs
- Frontend: http://localhost:3000

---

### 🧹 cleanup.py

Limpa arquivos temporários, cache e logs.

**Uso:**
```bash
# Limpeza padrão (logs, cache, screenshots, build)
python scripts/cleanup.py

# Limpeza completa (inclui node_modules)
python scripts/cleanup.py --all
```

**O que remove:**
- 📝 `logs/*.log` - Arquivos de log
- 📸 `prints/*.png` - Screenshots
- 🐍 `__pycache__/` - Cache Python
- 🧪 `.pytest_cache/` - Cache de testes
- 📦 `frontend/dist/` - Build do frontend
- 🗂️ `frontend/node_modules/` (apenas com --all)

**Segurança:**
- Pede confirmação antes de remover node_modules
- Mostra tamanho dos arquivos removidos
- Exibe resumo final

---

### 🏥 health_check.py

Verifica a saúde do sistema e dependências.

**Uso:**
```bash
python scripts/health_check.py
```

**O que verifica:**
- 🐍 Versão do Python (>= 3.8)
- 📦 Virtual environment ativo
- 📚 Dependências Python instaladas
- 🌐 Browsers do Playwright
- 📦 Node.js e npm
- ⚛️ Dependências do frontend
- 🔐 Arquivo .env
- 📁 Estrutura de diretórios
- 🔌 Conectividade do backend
- 🤖 Provedores LLM (LM Studio, Ollama)

**Status possíveis:**
- ✅ Passou: Sistema OK
- ⚠️ Aviso: Funciona mas pode melhorar
- ❌ Problema: Requer ação

**Retorna:**
- Exit code 0: Sistema saudável
- Exit code 1: Problemas encontrados

---

## 🔧 Criando Novos Scripts

Siga estas convenções:

### Template Básico

```python
#!/usr/bin/env python3
"""
Script para [descrição].
Uso: python scripts/nome_script.py [argumentos]
"""

import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description='Descrição do script')
    parser.add_argument('--option', help='Descrição da opção')
    args = parser.parse_args()
    
    print("=" * 60)
    print("🔧 Nome do Script")
    print("=" * 60)
    
    # Implementação
    
    print("\n✅ Concluído!")

if __name__ == '__main__':
    main()
```

### Boas Práticas

1. **Shebang**: Sempre inicie com `#!/usr/bin/env python3`
2. **Docstring**: Descreva o propósito e uso
3. **Argumentos**: Use `argparse` para opções CLI
4. **Feedback**: Use emojis e cores para clareza
5. **Segurança**: Peça confirmação para ações destrutivas
6. **Resumo**: Mostre relatório final
7. **Exit Code**: Retorne 0 (sucesso) ou 1 (erro)

### Emojis Recomendados

- ✅ Sucesso
- ❌ Erro
- ⚠️ Aviso
- ℹ️ Informação
- 🚀 Início/Execução
- 🧹 Limpeza
- 🏥 Health Check
- 🔧 Configuração
- 📊 Estatísticas
- 💡 Dica

---

## 📚 Exemplos de Uso

### Workflow Típico de Desenvolvimento

```bash
# 1. Verificar saúde do sistema
python scripts/health_check.py

# 2. Limpar arquivos antigos
python scripts/cleanup.py

# 3. Iniciar servidores
python scripts/start_servers.py
```

### Antes de Commit

```bash
# Limpar temporários
python scripts/cleanup.py

# Verificar sistema
python scripts/health_check.py

# Rodar testes
pytest
```

### Deploy/Produção

```bash
# Limpeza completa
python scripts/cleanup.py --all

# Reinstalar dependências
pip install -r requirements.txt
cd frontend && npm install && cd ..

# Verificar
python scripts/health_check.py

# Build frontend
cd frontend && npm run build && cd ..
```

---

## 🎯 Scripts Futuros (Planejados)

- `backup.py` - Backup de logs e configurações
- `migrate.py` - Migração de dados/configurações
- `deploy.py` - Deploy automatizado
- `benchmark.py` - Testes de performance
- `generate_docs.py` - Gerar documentação
- `update_deps.py` - Atualizar dependências

---

## 💡 Dicas

1. **Adicione scripts ao PATH** para acesso rápido
2. **Crie aliases** no PowerShell/Bash
3. **Automatize com cron/Task Scheduler** se necessário
4. **Documente** novos scripts neste README

---

**Scripts facilitam a vida! Use-os! 🚀**
