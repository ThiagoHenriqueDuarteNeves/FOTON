# Guia de Segurança - Agente de QA Automatizado

## 🔒 Visão Geral

Este documento descreve as práticas de segurança implementadas no projeto e recomendações para uso seguro.

## 🛡️ Práticas Implementadas

### 1. Gerenciamento de Credenciais

#### ✅ Variáveis de Ambiente
```python
# Correto: Usar variáveis de ambiente
import os
api_key = os.getenv('LLM_API_KEY')

# Incorreto: Hardcoded
api_key = "sk-..."  # NUNCA FAÇA ISSO
```

#### ✅ Arquivo .env
- `.env` está no `.gitignore`
- `.env.example` serve como template
- Nunca commitar `.env` real

### 2. Sanitização de Logs

#### API Keys Mascaradas
```python
# agent/io.py
def log_api_key(key: str) -> str:
    if not key:
        return "N/A"
    return f"***{key[-4:]}" if len(key) > 4 else "***"
```

#### Dados Sensíveis
- Passwords nunca logados
- URLs sanitizadas (sem query params sensíveis)
- Dados pessoais mascarados

### 3. Validação de Inputs

#### Frontend
```javascript
// Validação de URL
const isValidUrl = (url) => {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
};
```

#### Backend
```python
from pydantic import BaseModel, HttpUrl

class AgentConfig(BaseModel):
    url: HttpUrl  # Validação automática
    max_passos: int = Field(gt=0, le=100)
```

### 4. Tratamento de Exceções

```python
try:
    result = risky_operation()
except SpecificException as e:
    logger.error(f"Error: {e}")
    # Não expor detalhes internos
    raise SafeException("Operation failed")
```

### 5. CORS (Backend)

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Específico
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 🚨 Checklist de Segurança

### Antes de Commitar
- [ ] Verificar se não há credenciais no código
- [ ] `.env` não está sendo commitado
- [ ] API keys não estão em variáveis hardcoded
- [ ] Logs não contêm dados sensíveis
- [ ] Screenshots não contêm informações confidenciais

### Configuração de Produção
- [ ] Usar HTTPS (não HTTP)
- [ ] Configurar CORS restritivo
- [ ] Usar secrets manager (AWS Secrets, Azure Key Vault)
- [ ] Habilitar rate limiting
- [ ] Implementar autenticação/autorização
- [ ] Configurar logging seguro
- [ ] Monitorar acessos suspeitos

### Dependências
- [ ] Executar `pip audit` regularmente
- [ ] Manter dependências atualizadas
- [ ] Verificar vulnerabilidades conhecidas
- [ ] Usar `requirements.txt` com versões fixas

## 🔐 Armazenamento de Secrets

### Desenvolvimento Local
```env
# .env (gitignored)
LLM_API_KEY=sk-...
DATABASE_URL=postgres://...
SECRET_KEY=...
```

### Produção (Recomendado)
```python
# Usar serviços de secrets management
import boto3

def get_secret(secret_name):
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    return response['SecretString']
```

## 🛑 O Que NÃO Fazer

### ❌ Hardcoded Credentials
```python
# NUNCA FAÇA ISSO
API_KEY = "sk-1234567890abcdef"
PASSWORD = "minhasenha123"
```

### ❌ Commitar Arquivos Sensíveis
```bash
# Arquivos que NUNCA devem ser commitados
.env
*.key
*.pem
credentials.json
secrets/
```

### ❌ Expor Detalhes de Erro
```python
# Incorreto
except Exception as e:
    return {"error": str(e)}  # Pode expor stack trace

# Correto
except Exception as e:
    logger.error(f"Internal error: {e}")
    return {"error": "An error occurred"}
```

### ❌ Logs Detalhados em Produção
```python
# Desenvolvimento
logger.debug(f"User data: {user_data}")

# Produção
logger.info("User operation completed")
```

## 🔍 Auditoria de Segurança

### Ferramentas Recomendadas

```bash
# Python
pip install safety
safety check

pip install bandit
bandit -r agent/

# Node.js
npm audit
npm audit fix
```

### Comandos Úteis

```bash
# Verificar secrets commitados
git log -p | grep -i "api_key\|password\|secret"

# Buscar padrões suspeitos
grep -r "password\s*=" --include="*.py"
grep -r "api_key\s*=" --include="*.py"
```

## 📊 Monitoramento

### Logs de Segurança

```python
# Log de acessos
logger.info(f"Access from IP: {request.client.host}")

# Log de tentativas suspeitas
logger.warning(f"Invalid API key attempt from {ip}")

# Log de erros
logger.error(f"Security exception: {sanitized_error}")
```

### Métricas a Monitorar
- Taxa de erros 401/403
- Tentativas de acesso não autorizado
- Uso anômalo de recursos
- Padrões de tráfego suspeitos

## 🆘 Resposta a Incidentes

### Se Credenciais Forem Expostas

1. **Imediato**
   - Revogar credenciais expostas
   - Gerar novas credenciais
   - Notificar equipe

2. **Investigação**
   - Identificar escopo do vazamento
   - Verificar logs de acesso
   - Documentar incidente

3. **Remediação**
   - Limpar histórico Git se necessário
   - Implementar controles adicionais
   - Atualizar documentação

### Comandos de Emergência

```bash
# Remover arquivo do histórico Git
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

# Forçar push (cuidado!)
git push origin --force --all
```

## 📚 Recursos Adicionais

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)
- [Node.js Security Best Practices](https://nodejs.org/en/docs/guides/security/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)

## 🤝 Contribuindo com Segurança

Se você encontrar uma vulnerabilidade:

1. **NÃO** abra uma issue pública
2. Entre em contato por email: security@exemplo.com
3. Forneça detalhes claros e reprodução
4. Aguarde resposta antes de divulgar

---

**Segurança é responsabilidade de todos! 🛡️**
