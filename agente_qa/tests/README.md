# Tests

Diretório contendo todos os testes do projeto.

## 📁 Estrutura

```
tests/
├── conftest.py              # Fixtures compartilhadas
├── __init__.py
├── test_*.py               # Testes com pytest
├── teste_*.py              # Testes legados
└── test_form.html          # Arquivo auxiliar de teste
```

## 🧪 Tipos de Testes

### Unit Tests
Testes de unidades individuais (funções, classes, módulos).

**Executar:**
```bash
pytest tests/ -m unit
```

### Integration Tests
Testes de integração entre componentes.

**Executar:**
```bash
pytest tests/ -m integration
```

### End-to-End Tests
Testes completos de fluxos do sistema.

**Executar:**
```bash
pytest tests/ -m e2e
```

## 🚀 Executando Testes

### Todos os testes
```bash
pytest
```

### Com cobertura
```bash
pytest --cov=agent --cov=backend
```

### Específico
```bash
pytest tests/test_llm.py
pytest tests/test_llm.py::test_specific_function
```

### Verbose
```bash
pytest -v
pytest -vv  # Extra verbose
```

### Com logs
```bash
pytest -s  # Show print statements
```

## 📊 Cobertura

Gerar relatório de cobertura HTML:
```bash
pytest --cov=agent --cov=backend --cov-report=html
```

Abrir relatório:
```bash
start htmlcov/index.html  # Windows
open htmlcov/index.html   # Mac
```

## 🏷️ Markers

Testes podem ser marcados para execução seletiva:

```python
@pytest.mark.unit
def test_something():
    pass

@pytest.mark.integration
def test_integration():
    pass

@pytest.mark.e2e
@pytest.mark.slow
def test_complete_flow():
    pass
```

**Executar apenas testes rápidos:**
```bash
pytest -m "not slow"
```

**Executar apenas testes de LLM:**
```bash
pytest -m llm
```

## 🔧 Fixtures Disponíveis

Veja `conftest.py` para lista completa de fixtures:

- `page` - Página do Playwright
- `browser_context` - Contexto do browser
- `mock_llm_provider` - Provider LLM mockado
- `sample_html` - HTML de exemplo
- `test_config` - Configuração de teste
- E mais...

## 📝 Convenções

1. **Naming**: Use `test_*.py` ou `*_test.py`
2. **Functions**: Prefixo `test_`
3. **Classes**: Prefixo `Test`
4. **Fixtures**: Nomes descritivos sem prefixo test_
5. **Markers**: Use markers apropriados

## 🐛 Debug

### Executar com debugger
```bash
pytest --pdb
```

### Parar no primeiro erro
```bash
pytest -x
```

### Reexecutar apenas falhas
```bash
pytest --lf  # last failed
pytest --ff  # failed first
```

## 📚 Recursos

- [Pytest Documentation](https://docs.pytest.org/)
- [Playwright Testing](https://playwright.dev/python/docs/test-runners)
- [Coverage.py](https://coverage.readthedocs.io/)
