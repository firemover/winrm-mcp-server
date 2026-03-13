#!/usr/bin/env python3
"""
WinRM MCP Server (Linux-friendly, single file)

Инструменты:
- winrm_run_ps(hostname, command)
- winrm_run_cmd(hostname, command)
- winrm_get_services(hostname)
- winrm_get_disks(hostname)
- winrm_restart_service(hostname, service_name)
- winrm_get_eventlog(hostname, log_name="System", newest=50)

Креды берутся из переменных окружения:
- WINRM_USERNAME
- WINRM_PASSWORD
- WINRM_DOMAIN (опционально)

Зависимости (pip):
- mcp
- pywinrm
"""

import os
from typing import Dict, Any

import winrm
from mcp.server.fastmcp import FastMCP


mcp = FastMCP("WinRM Server")

WINRM_TIMEOUT = 30


def _get_env_credentials() -> Dict[str, str]:
    username = os.getenv("WINRM_USERNAME")
    password = os.getenv("WINRM_PASSWORD")
    domain = os.getenv("WINRM_DOMAIN", "")

    if not username or not password:
        raise RuntimeError(
            "WINRM_USERNAME and WINRM_PASSWORD must be set in environment "
            "for WinRM MCP server."
        )

    # Если указан домен и юзер без домена — собираем DOMAIN\\user
    if domain and "\\" not in username and "@" not in username:
        username = f"{domain}\\{username}"

    return {"username": username, "password": password}


def _make_session(hostname: str) -> winrm.Session:
    creds = _get_env_credentials()
    return winrm.Session(
        f"http://{hostname}:5985/wsman",
        auth=(creds["username"], creds["password"]),
        transport="ntlm",
        operation_timeout_sec=WINRM_TIMEOUT,
        read_timeout_sec=WINRM_TIMEOUT + 5,
    )


def _format_result(result: winrm.Response) -> Dict[str, Any]:
    return {
        "status": result.status_code,
        "stdout": result.std_out.decode("utf-8", errors="replace"),
        "stderr": result.std_err.decode("utf-8", errors="replace"),
    }


@mcp.tool()
def winrm_run_ps(hostname: str, command: str) -> dict:
    """Выполнить PowerShell на удалённом Windows‑хосте через WinRM."""
    try:
        session = _make_session(hostname)
        result = session.run_ps(command)
        return _format_result(result)
    except (winrm.exceptions.WinRMError, OSError, RuntimeError) as e:
        return {
            "error": "WinRM PowerShell execution failed",
            "details": str(e),
        }


@mcp.tool()
def winrm_run_cmd(hostname: str, command: str) -> dict:
    """Выполнить CMD‑команду на удалённом Windows‑хосте через WinRM."""
    try:
        session = _make_session(hostname)
        result = session.run_cmd(command)
        return _format_result(result)
    except (winrm.exceptions.WinRMError, OSError, RuntimeError) as e:
        return {
            "error": "WinRM CMD execution failed",
            "details": str(e),
        }


@mcp.tool()
def winrm_get_services(hostname: str) -> dict:
    """Получить список служб на Windows‑хосте."""
    ps = (
        "Get-Service | "
        "Select-Object Name, DisplayName, Status, StartType | "
        "Sort-Object Name | ConvertTo-Json -Compress"
    )
    return winrm_run_ps(hostname, ps)


@mcp.tool()
def winrm_get_disks(hostname: str) -> dict:
    """Получить информацию о дисках на Windows‑хосте."""
    ps = (
        "Get-WmiObject -Class Win32_LogicalDisk | "
        "Select-Object DeviceID, "
        "@{Name='SizeGB';Expression={[math]::Round($_.Size/1GB,2)}}, "
        "@{Name='FreeGB';Expression={[math]::Round($_.FreeSpace/1GB,2)}} | "
        "ConvertTo-Json -Compress"
    )
    return winrm_run_ps(hostname, ps)


@mcp.tool()
def winrm_restart_service(hostname: str, service_name: str) -> dict:
    """Перезапустить службу на Windows‑хосте."""
    ps = (
        f"Try {{ Restart-Service -Name '{service_name}' -Force -ErrorAction Stop; "
        "Write-Output '{\"status\":\"restarted\"}' }} "
        "Catch {{ Write-Error $_.Exception.Message; Exit 1 }}"
    )
    return winrm_run_ps(hostname, ps)


@mcp.tool()
def winrm_get_eventlog(
    hostname: str, log_name: str = "System", newest: int = 50
) -> dict:
    """Получить последние события из журнала Windows."""
    ps = (
        f"Get-EventLog -LogName '{log_name}' -Newest {newest} | "
        "Select-Object TimeGenerated, EntryType, Source, EventID, Message | "
        "ConvertTo-Json -Compress"
    )
    return winrm_run_ps(hostname, ps)


def main():
    """Точка входа MCP‑сервера."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

