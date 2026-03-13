## WinRM MCP Server (Python)

Этот репозиторий содержит MCP‑сервер для управления Windows‑хостами по WinRM.

### Требования

- Python 3.10+
- Зависимости: `mcp`, `pywinrm`

### Переменные окружения

- `WINRM_USERNAME`
- `WINRM_PASSWORD`
- `WINRM_DOMAIN` (опционально)

### Запуск как скрипт

```bash
pip install mcp pywinrm
export WINRM_USERNAME="DOMAIN\\user"
export WINRM_PASSWORD="password"
export WINRM_DOMAIN="DOMAIN"
python win_mcp_server.py
```

### Установка как пакет

Этот репозиторий также поддерживает установку через `pip` (см. `pyproject.toml`):

```bash
pip install .
winrm-mcp-server
```

