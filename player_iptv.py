import sys
import os
import json
import requests
import m3u8
import vlc
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QListWidgetItem, QFileDialog, QLineEdit,
    QStatusBar, QMessageBox, QComboBox, QSplitter, QSlider, QDialog,
    QFormLayout, QLabel, QTabWidget
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QKeyEvent

CONFIG_FILE = "config_xtream.json"

# Palavras-chave usadas para filtrar e isolar conteúdo adulto automaticamente
ADULT_KEYWORDS = ["adulto", "adults", "18+", "+18", "xxx", "erotico", "erotica", "for adult", "porn", "redlight"]


def is_adult_category(category_name):
    """Verifica se a categoria se enquadra em conteúdo adulto."""
    cat_lower = str(category_name).lower()
    return any(keyword in cat_lower for keyword in ADULT_KEYWORDS)


def save_xtream_config(url, username, password):
    """Salva as credenciais do Xtream Codes em um arquivo JSON local."""
    data = {
        "server_url": url,
        "username": username,
        "password": password
    }
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Erro ao salvar configurações: {e}")


def load_xtream_config():
    """Carrega as credenciais salvas do arquivo JSON local."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao ler configurações: {e}")
    return {"server_url": "", "username": "", "password": ""}


def format_time(ms):
    """Converte milissegundos no formato HH:MM:SS ou MM:SS."""
    if ms < 0:
        ms = 0
    seconds = int(ms / 1000)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


class XtreamLoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login Xtream Codes API")
        self.resize(400, 220)

        layout = QFormLayout(self)
        saved_config = load_xtream_config()

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("http://servidor.com:8080")
        self.url_input.setText(saved_config.get("server_url", ""))
        layout.addRow(QLabel("URL do Servidor:"), self.url_input)

        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Seu Usuário")
        self.user_input.setText(saved_config.get("username", ""))
        layout.addRow(QLabel("Usuário:"), self.user_input)

        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_input.setPlaceholderText("Sua Senha")
        self.pass_input.setText(saved_config.get("password", ""))
        layout.addRow(QLabel("Senha:"), self.pass_input)

        self.btn_login = QPushButton("🔑 Conectar")
        self.btn_login.clicked.connect(self.accept)
        layout.addRow(self.btn_login)

    def get_credentials(self):
        url = self.url_input.text().strip().rstrip('/')
        user = self.user_input.text().strip()
        password = self.pass_input.text().strip()
        return url, user, password


class XtreamLoaderWorker(QThread):
    finished = pyqtSignal(dict, str)

    def __init__(self, server_url, username, password):
        super().__init__()
        self.server_url = server_url
        self.username = username
        self.password = password

    def run(self):
        try:
            api_url = f"{self.server_url}/player_api.php"
            headers = {"User-Agent": "Mozilla/5.0"}

            result = {
                "live": [],
                "vod": [],
                "series": [],
                "adult": []
            }

            # 1. Busca Canais Ao Vivo
            resp_live = requests.get(api_url, params={"username": self.username, "password": self.password, "action": "get_live_streams"}, headers=headers, timeout=15)
            if resp_live.status_code == 200 and isinstance(resp_live.json(), list):
                for item in resp_live.json():
                    stream_id = item.get("stream_id")
                    name = item.get("name", "Canal sem nome")
                    group = str(item.get("category_id", "Ao Vivo"))
                    stream_url = f"{self.server_url}/live/{self.username}/{self.password}/{stream_id}.m3u8"
                    
                    data = {"name": name, "url": stream_url, "group": group, "type": "live"}
                    if is_adult_category(group) or is_adult_category(name):
                        result["adult"].append(data)
                    else:
                        result["live"].append(data)

            # 2. Busca VOD (Filmes e Cursos)
            resp_vod = requests.get(api_url, params={"username": self.username, "password": self.password, "action": "get_vod_streams"}, headers=headers, timeout=15)
            if resp_vod.status_code == 200 and isinstance(resp_vod.json(), list):
                for item in resp_vod.json():
                    stream_id = item.get("stream_id")
                    name = item.get("name", "Filme/Vídeo sem nome")
                    group = str(item.get("category_id", "Filmes & VOD"))
                    ext = item.get("container_extension", "mp4")
                    stream_url = f"{self.server_url}/movie/{self.username}/{self.password}/{stream_id}.{ext}"

                    data = {"name": name, "url": stream_url, "group": group, "type": "vod"}
                    if is_adult_category(group) or is_adult_category(name):
                        result["adult"].append(data)
                    else:
                        result["vod"].append(data)

            # 3. Busca Séries
            resp_series = requests.get(api_url, params={"username": self.username, "password": self.password, "action": "get_series"}, headers=headers, timeout=15)
            if resp_series.status_code == 200 and isinstance(resp_series.json(), list):
                for item in resp_series.json():
                    series_id = item.get("series_id")
                    name = item.get("name", "Série sem nome")
                    group = str(item.get("category_id", "Séries"))
                    stream_url = f"{self.server_url}/series/{self.username}/{self.password}/{series_id}.mp4"

                    data = {"name": name, "url": stream_url, "group": group, "type": "series"}
                    if is_adult_category(group) or is_adult_category(name):
                        result["adult"].append(data)
                    else:
                        result["series"].append(data)

            self.finished.emit(result, "")

        except Exception as e:
            self.finished.emit({}, f"Falha na conexão: {str(e)}")


def parse_m3u_robust(content, base_uri=""):
    channels_live = []
    channels_adult = []

    try:
        parsed = m3u8.loads(content, uri=base_uri)
        if parsed.segments:
            for segment in parsed.segments:
                url = segment.absolute_uri if segment.absolute_uri else segment.uri
                title = segment.title if segment.title else "Canal sem nome"
                group = "Geral"
                if hasattr(segment, 'custom_parser_values') and segment.custom_parser_values:
                    group = segment.custom_parser_values.get('group-title', 'Geral')

                data = {"name": title, "url": url, "group": group, "type": "live"}
                if is_adult_category(group) or is_adult_category(title):
                    channels_adult.append(data)
                else:
                    channels_live.append(data)

            if channels_live or channels_adult:
                return channels_live, channels_adult
    except Exception:
        pass

    lines = content.splitlines()
    current_name = "Canal sem nome"
    current_group = "Geral"

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("#EXTINF"):
            if "," in line:
                current_name = line.split(",")[-1].strip() or "Canal sem nome"
            if 'group-title="' in line:
                try:
                    current_group = line.split('group-title="')[1].split('"')[0]
                except IndexError:
                    current_group = "Geral"
        elif not line.startswith("#") and ("://" in line or line.endswith((".m3u8", ".ts", ".mp4", ".mkv"))):
            data = {
                "name": current_name,
                "url": line,
                "group": current_group,
                "type": "live"
            }
            if is_adult_category(current_group) or is_adult_category(current_name):
                channels_adult.append(data)
            else:
                channels_live.append(data)

            current_name = "Canal sem nome"
            current_group = "Geral"

    return channels_live, channels_adult


class IPTVPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Linux IPTV Player Pro - Live, On-Demand & Subtitles")
        self.resize(1180, 720)

        os.environ["VLC_VERBOSE"] = "-1"
        self.vlc_instance = vlc.Instance("--no-xlib", "--quiet")
        self.media_player = self.vlc_instance.media_player_new()

        self.channels_live = []
        self.channels_vod = []
        self.channels_series = []
        self.channels_adult = []

        self.filtered_channels = []
        self.current_index = -1
        self.last_credentials = None
        self.is_slider_user_dragging = False

        # Timer para progresso do vídeo e detecção de legendas
        self.timer = QTimer(self)
        self.timer.setInterval(500)
        self.timer.timeout.connect(self.update_video_progress)

        self.subtitle_timer = QTimer(self)
        self.subtitle_timer.setInterval(2000)
        self.subtitle_timer.timeout.connect(self.load_available_subtitles)

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Barra Superior
        top_bar = QHBoxLayout()

        self.btn_open_file = QPushButton("📁 Abrir Arquivo .m3u")
        self.btn_open_file.clicked.connect(self.open_file)
        top_bar.addWidget(self.btn_open_file)

        self.btn_xtream_login = QPushButton("🔐 Login Xtream Codes")
        self.btn_xtream_login.clicked.connect(self.open_xtream_dialog)
        top_bar.addWidget(self.btn_xtream_login)

        main_layout.addLayout(top_bar)

        # Splitter de Janelas
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Painel Esquerdo (Abas + Categorias + Lista)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()
        self.tabs.addTab(QWidget(), "📺 Ao Vivo")
        self.tabs.addTab(QWidget(), "🎬 Filmes & VOD")
        self.tabs.addTab(QWidget(), "🍿 Séries")
        self.tabs.addTab(QWidget(), "🔞 Adulto")
        self.tabs.currentChanged.connect(self.on_tab_changed)
        left_layout.addWidget(self.tabs)

        self.category_combo = QComboBox()
        self.category_combo.addItem("Todas as Categorias")
        self.category_combo.currentIndexChanged.connect(self.filter_channels)
        left_layout.addWidget(self.category_combo)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Buscar por nome...")
        self.search_input.textChanged.connect(self.filter_channels)
        left_layout.addWidget(self.search_input)

        self.channel_list = QListWidget()
        self.channel_list.itemDoubleClicked.connect(self.play_selected_item)
        left_layout.addWidget(self.channel_list)

        splitter.addWidget(left_panel)

        # Painel Direito (Player + Controles)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.video_frame = QWidget()
        self.video_frame.setStyleSheet("background-color: black;")
        right_layout.addWidget(self.video_frame, stretch=1)

        # Container do Slider de Tempo (On-Demand)
        self.progress_container = QWidget()
        progress_layout = QHBoxLayout(self.progress_container)
        progress_layout.setContentsMargins(5, 2, 5, 2)

        self.time_label = QLabel("00:00 / 00:00")
        progress_layout.addWidget(self.time_label)

        self.time_slider = QSlider(Qt.Orientation.Horizontal)
        self.time_slider.setRange(0, 1000)
        self.time_slider.sliderPressed.connect(self.on_slider_pressed)
        self.time_slider.sliderReleased.connect(self.on_slider_released)
        progress_layout.addWidget(self.time_slider)

        self.progress_container.hide()
        right_layout.addWidget(self.progress_container)

        # Barra de Controles de Mídia + Seleção de Legenda
        controls_bar = QHBoxLayout()

        self.btn_prev = QPushButton("⏮ Anterior")
        self.btn_prev.clicked.connect(self.play_prev)
        controls_bar.addWidget(self.btn_prev)

        self.btn_play_pause = QPushButton("⏯ Play/Pause")
        self.btn_play_pause.clicked.connect(self.toggle_play_pause)
        controls_bar.addWidget(self.btn_play_pause)

        self.btn_next = QPushButton("⏭ Próximo")
        self.btn_next.clicked.connect(self.play_next)
        controls_bar.addWidget(self.btn_next)

        # Seleção de Legendas
        self.subtitle_combo = QComboBox()
        self.subtitle_combo.addItem("💬 Legenda: Desativada", -1)
        self.subtitle_combo.currentIndexChanged.connect(self.change_subtitle)
        controls_bar.addWidget(self.subtitle_combo)

        self.btn_fullscreen = QPushButton("🔲 Tela Cheia")
        self.btn_fullscreen.clicked.connect(self.toggle_fullscreen)
        controls_bar.addWidget(self.btn_fullscreen)

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)
        self.volume_slider.setFixedWidth(100)
        self.volume_slider.valueChanged.connect(self.set_volume)
        controls_bar.addWidget(self.volume_slider)

        right_layout.addLayout(controls_bar)
        splitter.addWidget(right_panel)

        splitter.setSizes([340, 840])
        main_layout.addWidget(splitter)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Pronto.")

    def keyPressEvent(self, event: QKeyEvent):
        """Sai da tela cheia ao pressionar qualquer tecla (incluindo ESC)."""
        if self.isFullScreen():
            self.showNormal()
        else:
            super().keyPressEvent(event)

    def open_xtream_dialog(self):
        dialog = XtreamLoginDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            url, user, password = dialog.get_credentials()
            if not url or not user or not password:
                QMessageBox.warning(self, "Aviso", "Preencha todos os campos do Xtream Codes!")
                return

            self.last_credentials = (url, user, password)
            self.status_bar.showMessage("Carregando conteúdos...")
            self.worker = XtreamLoaderWorker(url, user, password)
            self.worker.finished.connect(self.on_xtream_loaded)
            self.worker.start()

    def on_xtream_loaded(self, result, error):
        if error:
            QMessageBox.critical(self, "Erro Xtream Codes", error)
            self.status_bar.showMessage("Falha no login Xtream Codes.")
        else:
            if self.last_credentials:
                save_xtream_config(*self.last_credentials)

            self.channels_live.extend(result.get("live", []))
            self.channels_vod.extend(result.get("vod", []))
            self.channels_series.extend(result.get("series", []))
            self.channels_adult.extend(result.get("adult", []))

            self.update_categories()
            self.filter_channels()

            self.status_bar.showMessage(f"Sucesso: {len(self.channels_live)} Ao Vivo, {len(self.channels_vod)} VOD, {len(self.channels_series)} Séries, {len(self.channels_adult)} Adulto.")

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar M3U", "", "Playlists (*.m3u *.m3u8 *.txt)")
        if file_path:
            try:
                content = ""
                for encoding in ['utf-8', 'latin-1', 'cp1252', 'utf-8-sig']:
                    try:
                        with open(file_path, 'r', encoding=encoding) as f:
                            content = f.read()
                        break
                    except UnicodeDecodeError:
                        continue

                live, adult = parse_m3u_robust(content)
                self.channels_live = live
                self.channels_adult = adult

                self.update_categories()
                self.filter_channels()
                self.status_bar.showMessage(f"Sucesso: {len(self.channels_live)} canais e {len(self.channels_adult)} adultos carregados!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Falha ao ler o arquivo: {e}")

    def get_current_source_list(self):
        idx = self.tabs.currentIndex()
        if idx == 0:
            return self.channels_live
        elif idx == 1:
            return self.channels_vod
        elif idx == 2:
            return self.channels_series
        else:
            return self.channels_adult

    def on_tab_changed(self, index):
        self.update_categories()
        self.filter_channels()

    def update_categories(self):
        self.category_combo.blockSignals(True)
        self.category_combo.clear()
        self.category_combo.addItem("Todas as Categorias")

        source_list = self.get_current_source_list()
        groups = sorted(list({ch.get('group', 'Geral') for ch in source_list}))
        for group in groups:
            self.category_combo.addItem(group)

        self.category_combo.blockSignals(False)

    def filter_channels(self):
        search = self.search_input.text().lower()
        selected_category = self.category_combo.currentText()
        source_list = self.get_current_source_list()

        self.filtered_channels = []
        self.channel_list.clear()

        for ch in source_list:
            matches_group = (selected_category == "Todas as Categorias") or (ch.get('group') == selected_category)
            matches_search = search in ch['name'].lower()

            if matches_group and matches_search:
                self.filtered_channels.append(ch)

        self.filtered_channels.sort(key=lambda x: x['name'].lower())

        for ch in self.filtered_channels:
            group_tag = f" [{ch['group']}]" if ch.get('group') else ""
            item = QListWidgetItem(f"{ch['name']}{group_tag}")
            self.channel_list.addItem(item)

    def play_channel_by_index(self, index):
        if 0 <= index < len(self.filtered_channels):
            self.current_index = index
            ch = self.filtered_channels[index]

            self.channel_list.setCurrentRow(index)

            win_id = int(self.video_frame.winId())
            if sys.platform.startswith("linux"):
                self.media_player.set_xwindow(win_id)

            media = self.vlc_instance.media_new(ch['url'])
            self.media_player.set_media(media)
            self.media_player.play()

            # Configura exibição de barra de progresso para On-Demand
            content_type = ch.get("type", "live")
            if content_type in ["vod", "series"]:
                self.progress_container.show()
                self.timer.start()
            else:
                self.progress_container.hide()
                self.timer.stop()

            # Dispara a busca de faixas de legenda
            self.subtitle_combo.blockSignals(True)
            self.subtitle_combo.clear()
            self.subtitle_combo.addItem("💬 Legenda: Desativada", -1)
            self.subtitle_combo.blockSignals(False)
            self.subtitle_timer.start()

            self.status_bar.showMessage(f"Reproduzindo: {ch['name']}")

    def load_available_subtitles(self):
        """Lê as faixas de legendas enviadas pela transmissão e preenche o ComboBox."""
        subtitles = self.media_player.video_get_spu_description()
        if subtitles:
            self.subtitle_combo.blockSignals(True)
            self.subtitle_combo.clear()
            self.subtitle_combo.addItem("💬 Legenda: Desativada", -1)

            for sub_id, name in subtitles:
                if sub_id != -1:
                    track_name = name.decode('utf-8', errors='ignore') if isinstance(name, bytes) else str(name)
                    self.subtitle_combo.addItem(f"💬 {track_name}", sub_id)

            self.subtitle_combo.blockSignals(False)
            self.subtitle_timer.stop()

    def change_subtitle(self, index):
        """Alterna a faixa de legenda do vídeo em tempo real."""
        sub_id = self.subtitle_combo.currentData()
        if sub_id is not None:
            self.media_player.video_set_spu(sub_id)

    def play_selected_item(self, item):
        row = self.channel_list.row(item)
        self.play_channel_by_index(row)

    def update_video_progress(self):
        if not self.media_player.is_playing() and not self.media_player.get_state() == vlc.State.Paused:
            return

        length = self.media_player.get_length()
        time_ms = self.media_player.get_time()

        if length > 0:
            self.time_label.setText(f"{format_time(time_ms)} / {format_time(length)}")

            if not self.is_slider_user_dragging:
                pos = int((time_ms / length) * 1000)
                self.time_slider.setValue(pos)

    def on_slider_pressed(self):
        self.is_slider_user_dragging = True

    def on_slider_released(self):
        self.is_slider_user_dragging = False
        val = self.time_slider.value()
        length = self.media_player.get_length()
        if length > 0:
            target_time = int((val / 1000.0) * length)
            self.media_player.set_time(target_time)

    def play_next(self):
        if self.filtered_channels and self.current_index < len(self.filtered_channels) - 1:
            self.play_channel_by_index(self.current_index + 1)

    def play_prev(self):
        if self.filtered_channels and self.current_index > 0:
            self.play_channel_by_index(self.current_index - 1)

    def toggle_play_pause(self):
        if self.media_player.is_playing():
            self.media_player.pause()
        else:
            self.media_player.play()

    def set_volume(self, value):
        self.media_player.audio_set_volume(value)

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def closeEvent(self, event):
        self.timer.stop()
        self.subtitle_timer.stop()
        self.media_player.stop()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    player = IPTVPlayer()
    player.show()
    sys.exit(app.exec())