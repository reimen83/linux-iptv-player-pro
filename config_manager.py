import json
import os
from PyQt6.QtCore import QSettings

CONFIG_FILE = "config_xtream.json"
ORG_NAME = "reimen83"
APP_NAME = "linux-iptv-player-pro"


def save_xtream_config(url, username, password):
    """Salva as credenciais do Xtream Codes usando QSettings.

    Faz migração do arquivo legado config_xtream.json quando existir.
    """
    try:
        settings = QSettings(ORG_NAME, APP_NAME)
        settings.setValue("server_url", url)
        settings.setValue("username", username)
        settings.setValue("password", password)
        settings.sync()

        try:
            if os.path.exists(CONFIG_FILE):
                os.remove(CONFIG_FILE)
        except Exception:
            pass
    except Exception as e:
        print(f"Erro ao salvar configurações com QSettings: {e}")


def load_xtream_config():
    """Carrega as credenciais salvas. Primeiro tenta QSettings e depois migra do JSON antigo."""
    try:
        settings = QSettings(ORG_NAME, APP_NAME)
        server_url = settings.value("server_url", "") or ""
        username = settings.value("username", "") or ""
        password = settings.value("password", "") or ""

        if not (server_url or username or password) and os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                server_url = data.get("server_url", "")
                username = data.get("username", "")
                password = data.get("password", "")
                save_xtream_config(server_url, username, password)
            except Exception as e:
                print(f"Erro ao migrar configurações antigas: {e}")

        return {"server_url": server_url, "username": username, "password": password}
    except Exception as e:
        print(f"Erro ao ler configurações: {e}")
        return {"server_url": "", "username": "", "password": ""}
