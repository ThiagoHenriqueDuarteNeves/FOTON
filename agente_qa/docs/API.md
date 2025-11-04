# API Documentation

## 📡 Backend API (FastAPI)

Base URL: `http://localhost:8000`

### Endpoints

#### 1. Health Check

```http
GET /
```

**Response** (200 OK):
```json
{
  "message": "Servidor rodando",
  "docs": "/docs"
}
```

---

#### 2. List Available LLM Models

```http
GET /api/models
```

**Description**: Retorna lista de modelos LLM disponíveis no LM Studio

**Response** (200 OK):
```json
{
  "models": [
    {
      "id": "model-name",
      "object": "model",
      "created": 1234567890,
      "owned_by": "owner"
    }
  ]
}
```

**Response** (500 Internal Server Error):
```json
{
  "detail": "Erro ao conectar ao LM Studio: ..."
}
```

---

#### 3. Start Agent Execution

```http
POST /api/agent/start
```

**Description**: Inicia execução do agente com configuração fornecida

**Request Body**:
```json
{
  "url": "https://example.com",
  "instructions": "Navegue até a página de login e faça login",
  "provider": "lmstudio",
  "provider_url": "http://localhost:1234",
  "api_key": "optional-api-key",
  "model": "llama-2-7b-chat",
  "max_steps": 50,
  "headless": true
}
```

**Parameters**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| url | string | Yes | URL inicial para navegação |
| instructions | string | Yes | Instruções para o agente |
| provider | string | Yes | Provedor LLM: `lmstudio`, `ollama`, `api_externa` |
| provider_url | string | Yes | URL do provedor LLM |
| api_key | string | No | API key para provedores externos |
| model | string | Yes | Nome do modelo LLM |
| max_steps | integer | No | Máximo de passos (padrão: 50) |
| headless | boolean | No | Executar browser em modo headless (padrão: true) |

**Response** (200 OK):
```json
{
  "status": "started",
  "message": "Agente iniciado com sucesso"
}
```

**Response** (400 Bad Request):
```json
{
  "detail": "Agente já está em execução"
}
```

**Response** (500 Internal Server Error):
```json
{
  "detail": "Erro ao iniciar agente: ..."
}
```

---

#### 4. Get Agent Status

```http
GET /api/agent/status
```

**Description**: Retorna status atual do agente

**Response** (200 OK):
```json
{
  "status": "running",
  "current_step": 5,
  "max_steps": 50,
  "last_action": "CLICK",
  "error": null
}
```

**Status Values**:
- `idle`: Agente não está executando
- `running`: Agente em execução
- `completed`: Execução concluída com sucesso
- `error`: Erro durante execução

---

#### 5. Test LLM Connection

```http
POST /api/test-llm
```

**Description**: Testa conexão com provedor LLM

**Request Body**:
```json
{
  "provider": "lmstudio",
  "provider_url": "http://localhost:1234",
  "api_key": "optional-api-key",
  "model": "llama-2-7b-chat"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Conexão com LLM bem-sucedida",
  "response": "Olá! Como posso ajudá-lo?"
}
```

**Response** (500 Internal Server Error):
```json
{
  "success": false,
  "message": "Erro ao conectar ao LLM: Connection refused"
}
```

---

### WebSocket

#### Real-time Logs

```javascript
ws://localhost:8000/ws
```

**Description**: Recebe logs em tempo real da execução do agente

**Connection**:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
  console.log('Connected to log stream');
};

ws.onmessage = (event) => {
  const log = JSON.parse(event.data);
  console.log(log);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Disconnected from log stream');
};
```

**Message Format**:
```json
{
  "timestamp": "2024-01-15T10:30:00",
  "level": "INFO",
  "message": "Executando ação: CLICK no seletor button.submit",
  "step": 5
}
```

**Log Levels**:
- `DEBUG`: Informações detalhadas de debug
- `INFO`: Informações gerais de execução
- `WARNING`: Avisos não críticos
- `ERROR`: Erros durante execução
- `CRITICAL`: Erros críticos que impedem continuação

---

## 🔐 Authentication

Atualmente, a API não requer autenticação. Para produção, considere implementar:

### Opção 1: API Key

```http
GET /api/agent/status
Authorization: Bearer YOUR_API_KEY
```

### Opção 2: JWT Token

```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "user",
  "password": "pass"
}
```

**Response**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

---

## 📊 Error Handling

### Standard Error Response

```json
{
  "detail": "Error message",
  "error_code": "ERROR_CODE",
  "timestamp": "2024-01-15T10:30:00"
}
```

### Error Codes

| Code | Description |
|------|-------------|
| `AGENT_RUNNING` | Tentativa de iniciar agente já em execução |
| `LLM_CONNECTION_ERROR` | Falha ao conectar com provedor LLM |
| `INVALID_PROVIDER` | Provedor LLM inválido |
| `BROWSER_ERROR` | Erro ao iniciar ou controlar browser |
| `VALIDATION_ERROR` | Erro de validação nos parâmetros |

---

## 🚀 Rate Limiting

Para proteger a API, considere implementar rate limiting:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/agent/start")
@limiter.limit("5/minute")
async def start_agent(...):
    ...
```

---

## 📈 Monitoring & Metrics

### Prometheus Metrics

Adicione métricas para monitoramento:

```python
from prometheus_client import Counter, Histogram, Gauge

# Contadores
agent_executions = Counter('agent_executions_total', 'Total execuções do agente')
llm_requests = Counter('llm_requests_total', 'Total requisições ao LLM')
errors = Counter('errors_total', 'Total de erros', ['type'])

# Histogramas
execution_duration = Histogram('execution_duration_seconds', 'Duração das execuções')
llm_response_time = Histogram('llm_response_time_seconds', 'Tempo de resposta do LLM')

# Gauges
active_agents = Gauge('active_agents', 'Número de agentes ativos')
```

**Endpoint**:
```http
GET /metrics
```

---

## 🧪 API Testing

### Using curl

```bash
# Test health check
curl http://localhost:8000/

# List models
curl http://localhost:8000/api/models

# Start agent
curl -X POST http://localhost:8000/api/agent/start \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "instructions": "Navegue até a página de contato",
    "provider": "lmstudio",
    "provider_url": "http://localhost:1234",
    "model": "llama-2-7b-chat"
  }'

# Get status
curl http://localhost:8000/api/agent/status
```

### Using Python

```python
import requests

# Start agent
response = requests.post('http://localhost:8000/api/agent/start', json={
    'url': 'https://example.com',
    'instructions': 'Navegue até a página de contato',
    'provider': 'lmstudio',
    'provider_url': 'http://localhost:1234',
    'model': 'llama-2-7b-chat',
    'max_steps': 30
})

print(response.json())

# Monitor status
import time
while True:
    status = requests.get('http://localhost:8000/api/agent/status').json()
    print(f"Status: {status['status']} - Step: {status.get('current_step', 0)}")
    
    if status['status'] in ['completed', 'error', 'idle']:
        break
    
    time.sleep(2)
```

### Using JavaScript/Fetch

```javascript
// Start agent
fetch('http://localhost:8000/api/agent/start', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    url: 'https://example.com',
    instructions: 'Navegue até a página de contato',
    provider: 'lmstudio',
    provider_url: 'http://localhost:1234',
    model: 'llama-2-7b-chat'
  })
})
.then(response => response.json())
.then(data => console.log(data));

// Get status
fetch('http://localhost:8000/api/agent/status')
  .then(response => response.json())
  .then(data => console.log(data));
```

---

## 📝 API Changelog

### Version 1.0.0 (2024-01-15)

**Added**:
- Initial API release
- Agent execution endpoints
- WebSocket log streaming
- LLM model listing
- Connection testing

**Changed**:
- N/A

**Deprecated**:
- N/A

**Removed**:
- N/A

**Fixed**:
- N/A

**Security**:
- Added CORS support

---

## 🔮 Future Endpoints

### Planned Features

```http
# Agent history
GET /api/agent/history
GET /api/agent/history/{execution_id}

# Screenshots
GET /api/agent/screenshots
GET /api/agent/screenshots/{step}

# Configuration presets
GET /api/presets
POST /api/presets
GET /api/presets/{preset_id}
DELETE /api/presets/{preset_id}

# User management
POST /api/auth/register
POST /api/auth/login
GET /api/users/me
PUT /api/users/me

# Webhooks
POST /api/webhooks
GET /api/webhooks
DELETE /api/webhooks/{webhook_id}
```

---

## 📚 Additional Resources

- **OpenAPI/Swagger**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **GitHub**: [Link to repository]
- **Support**: [Link to issues]

---

**API em constante evolução - feedback é sempre bem-vindo! 🚀**
