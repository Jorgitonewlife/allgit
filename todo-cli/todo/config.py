"""Sistema de configuração: arquivo TOML + variáveis de ambiente.

Prioridade (maior para menor):
1. Variáveis de ambiente (TODO_*)
2. Arquivo de configuração (~/.config/todo/config.toml)
3. Valores padrão
"""

import os
import sys
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib as tomli
else:
    import tomli

import tomli_w

DEFAULT_CONFIG = {
    "storage": {
        "file_path": "~/.todo_cli_tasks.json",
    },
    "crm": {
        "file_path": "~/.todo_cli_crm.json",
    },
    "display": {
        "show_priority": True,
        "show_dates": False,
        "date_format": "%d/%m/%Y",
        "colors": True,
        "unicode": True,
    },
    "behavior": {
        "confirm_delete": True,
        "auto_save": True,
        "default_priority": "medium",
    },
    "editor": {
        "command": None,  # Ex: "code --wait", "vim", "notepad"
    },
}


class Config:
    """Gerencia configuração da aplicação."""

    def __init__(self, config_path: Path | None = None):
        self.config_path = config_path or self._default_config_path()
        self._data = DEFAULT_CONFIG.copy()
        self._load()

    def _default_config_path(self) -> Path:
        """Retorna caminho padrão do arquivo de configuração."""
        # XDG_CONFIG_HOME ou ~/.config
        config_home = os.environ.get("XDG_CONFIG_HOME")
        if config_home:
            return Path(config_home) / "todo" / "config.toml"
        return Path.home() / ".config" / "todo" / "config.toml"

    def _load(self) -> None:
        """Carrega configuração do arquivo TOML."""
        if self.config_path.exists():
            try:
                with open(self.config_path, "rb") as f:
                    file_config = tomli.load(f)
                self._deep_update(self._data, file_config)
            except Exception:
                # Se falhar, usa defaults
                pass

        # Sobrescreve com variáveis de ambiente
        self._apply_env_overrides()

    def _deep_update(self, base: dict, override: dict) -> None:
        """Atualiza dicionário recursivamente."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value

    def _apply_env_overrides(self) -> None:
        """Aplica variáveis de ambiente (prefixo TODO_)."""
        env_mapping = {
            "TODO_STORAGE_FILE": ("storage", "file_path"),
            "TODO_CRM_FILE": ("crm", "file_path"),
            "TODO_SHOW_PRIORITY": ("display", "show_priority"),
            "TODO_SHOW_DATES": ("display", "show_dates"),
            "TODO_DATE_FORMAT": ("display", "date_format"),
            "TODO_COLORS": ("display", "colors"),
            "TODO_UNICODE": ("display", "unicode"),
            "TODO_CONFIRM_DELETE": ("behavior", "confirm_delete"),
            "TODO_AUTO_SAVE": ("behavior", "auto_save"),
            "TODO_DEFAULT_PRIORITY": ("behavior", "default_priority"),
            "TODO_EDITOR_COMMAND": ("editor", "command"),
        }

        for env_var, (section, key) in env_mapping.items():
            value = os.environ.get(env_var)
            if value is not None:
                # Converte tipos
                if isinstance(self._data[section][key], bool):
                    value = value.lower() in ("1", "true", "yes", "on")
                elif isinstance(self._data[section][key], int):
                    value = int(value)
                self._data[section][key] = value

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Obtém valor de configuração."""
        return self._data.get(section, {}).get(key, default)

    def set(self, section: str, key: str, value: Any) -> None:
        """Define valor de configuração."""
        if section not in self._data:
            self._data[section] = {}
        self._data[section][key] = value

    def save(self) -> None:
        """Salva configuração no arquivo TOML."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Remove chaves com valor None (TOML não suporta None)
        def clean_none(d: dict) -> dict:
            result = {}
            for k, v in d.items():
                if v is None:
                    continue
                if isinstance(v, dict):
                    cleaned = clean_none(v)
                    if cleaned:  # Só adiciona se não ficou vazio
                        result[k] = cleaned
                else:
                    result[k] = v
            return result

        with open(self.config_path, "wb") as f:
            tomli_w.dump(clean_none(self._data), f)

    def get_storage_path(self) -> Path:
        """Retorna caminho do arquivo de storage expandido."""
        path_str = self.get("storage", "file_path", DEFAULT_CONFIG["storage"]["file_path"])
        return Path(path_str).expanduser()

    def get_crm_path(self) -> Path:
        """Retorna caminho do arquivo de storage do CRM expandido."""
        path_str = self.get("crm", "file_path", DEFAULT_CONFIG["crm"]["file_path"])
        return Path(path_str).expanduser()

    def get_display_config(self) -> dict:
        """Retorna configurações de exibição."""
        return self._data.get("display", {}).copy()

    def get_behavior_config(self) -> dict:
        """Retorna configurações de comportamento."""
        return self._data.get("behavior", {}).copy()

    def get_editor_command(self) -> str | None:
        """Retorna comando do editor externo."""
        return self.get("editor", "command")


# Instância global (singleton)
_config: Config | None = None


def get_config(config_path: Path | None = None) -> Config:
    """Retorna instância global de configuração."""
    global _config
    if _config is None or config_path is not None:
        _config = Config(config_path)
    return _config


def reset_config() -> None:
    """Reseta configuração global (útil para testes)."""
    global _config
    _config = None
