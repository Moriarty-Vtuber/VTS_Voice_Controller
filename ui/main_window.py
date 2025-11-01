from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QTextEdit, QTableWidget,
    QTableWidgetItem, QLabel, QPushButton, QHeaderView, QComboBox, QGridLayout, QFrame
)
from loguru import logger
import os
from core.config_loader import ConfigLoader


class MainWindow(QMainWindow):
    def __init__(self, config_path: str, initial_config: dict):
        super().__init__()

        self.config_path = config_path
        self.initial_config = initial_config
        self.current_language = "en"

        self.setMinimumSize(800, 600)

        self.translations = self._load_translations()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self._init_ui_elements()
        self.retranslate_ui(self.current_language)

    def _load_translations(self):
        try:
            config_path = os.path.join(os.path.dirname(
                __file__), '..', 'config', 'translations.yaml')
            return ConfigLoader.load_yaml(config_path)
        except Exception as e:
            logger.error(f"Failed to load translations: {e}")
            return {}

    def _init_ui_elements(self):
        grid_layout = QGridLayout()
        self.main_layout.addLayout(grid_layout)

        # Settings Panel
        settings_frame = QFrame()
        settings_layout = QHBoxLayout(settings_frame)
        self.language_label = QLabel()
        self.language_selector = QComboBox()
        if self.translations:
            self.language_selector.addItems(self.translations.keys())
        self.mode_label = QLabel()
        self.mode_selector = QComboBox()
        self.microphone_label = QLabel()
        self.microphone_selector = QComboBox()
        settings_layout.addWidget(self.language_label)
        settings_layout.addWidget(self.language_selector)
        settings_layout.addStretch()
        settings_layout.addWidget(self.mode_label)
        settings_layout.addWidget(self.mode_selector)
        settings_layout.addStretch()
        settings_layout.addWidget(self.microphone_label)
        settings_layout.addWidget(self.microphone_selector)
        grid_layout.addWidget(settings_frame, 0, 0, 1, 2)

        # Status Panel
        status_frame = QFrame()
        status_layout = QHBoxLayout(status_frame)
        self.vts_status_label = QLabel()
        self.asr_status_label = QLabel()
        self.app_status_label = QLabel()
        status_layout.addWidget(self.vts_status_label)
        status_layout.addWidget(self.asr_status_label)
        status_layout.addWidget(self.app_status_label)
        grid_layout.addWidget(status_frame, 1, 0, 1, 2)

        # Controls
        controls_frame = QFrame()
        controls_layout = QHBoxLayout(controls_frame)
        self.start_button = QPushButton()
        self.stop_button = QPushButton()
        self.stop_button.setEnabled(False)
        self.save_button = QPushButton()
        self.save_button.clicked.connect(self._save_keywords_to_config)
        controls_layout.addWidget(self.start_button)
        controls_layout.addWidget(self.stop_button)
        controls_layout.addWidget(self.save_button)
        controls_layout.addStretch()
        grid_layout.addWidget(controls_frame, 2, 0, 1, 2)

        # Transcription Log
        self.transcription_log = QTextEdit()
        self.transcription_log.setReadOnly(True)
        grid_layout.addWidget(self.transcription_log, 3, 0, 1, 1)

        # Keyword Editor
        self.keyword_editor = QTableWidget()
        self.keyword_editor.setColumnCount(3)
        self.keyword_editor.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)
        grid_layout.addWidget(self.keyword_editor, 3, 1, 1, 1)

        grid_layout.setRowStretch(3, 1)

    def tr(self, key, default_text=""):
        return self.translations.get(self.current_language, {}).get(key, default_text)

    def retranslate_ui(self, language):
        self.current_language = language
        self.setWindowTitle(
            self.tr("window_title", "VTube Studio Voice Controller"))
        self.app_status_label.setText(
            f"<b>{self.tr('status_app', 'App')}:</b> {self.tr('status_stopped', 'Stopped')}")
        self.vts_status_label.setText(
            f"<b>{self.tr('status_vts', 'VTS')}:</b> {self.tr('status_disconnected', 'Disconnected')}")
        self.asr_status_label.setText(
            f"<b>{self.tr('status_asr', 'ASR')}:</b> {self.tr('status_idle', 'Idle')}")
        self.start_button.setText(self.tr("button_start", "Start"))
        self.stop_button.setText(self.tr("button_stop", "Stop"))
        self.language_label.setText(self.tr("language_label", "Language:"))
        self.mode_label.setText(self.tr("mode_label", "Mode:"))
        self.microphone_label.setText(
            self.tr("microphone_label", "Microphone:"))
        self.save_button.setText(self.tr("button_save", "Save Keywords"))
        self.mode_selector.clear()
        self.mode_selector.addItems(
            [self.tr("mode_fast", "Fast"), self.tr("mode_accurate", "Accurate")])
        self.keyword_editor.setHorizontalHeaderLabels([self.tr("header_expression", "Expression"), self.tr(
            "header_keywords", "Keywords"), self.tr("header_cooldown", "Cooldown (s)")])

    def append_log(self, text: str):
        self.transcription_log.append(text)

    def set_status(self, vts: str = None, asr: str = None, app: str = None):
        if vts is not None:
            self.vts_status_label.setText(
                f"<b>{self.tr('status_vts', 'VTS')}:</b> {vts}")
        if asr is not None:
            self.asr_status_label.setText(
                f"<b>{self.tr('status_asr', 'ASR')}:</b> {asr}")
        if app is not None:
            self.app_status_label.setText(
                f"<b>{self.tr('status_app', 'App')}:</b> {app}")

    def _save_keywords_to_config(self):
        logger.info("--- UI: Save button clicked ---")
        updated_expressions = {}
        for row in range(self.keyword_editor.rowCount()):
            expression_name = self.keyword_editor.item(row, 0).text()
            keywords_str = self.keyword_editor.item(row, 1).text()
            cooldown_str = self.keyword_editor.item(row, 2).text()
            keywords = [k.strip()
                        for k in keywords_str.split(',') if k.strip()]
            cooldown_s = int(cooldown_str) if cooldown_str.isdigit() else 0
            original_key = next((k for k, v in self.initial_config.get(
                'expressions', {}).items() if v.get('name') == expression_name), None)
            if original_key:
                updated_expressions[original_key] = {
                    'name': expression_name, 'keywords': keywords, 'cooldown_s': cooldown_s}

        current_config = ConfigLoader.load_yaml(self.config_path)
        if current_config:
            current_config['expressions'] = updated_expressions
            ConfigLoader.save_yaml(self.config_path, current_config)
            self.append_log(self.tr("keywords_saved_success",
                            "Keywords saved successfully!"))
        else:
            self.append_log(self.tr("keywords_save_error",
                            "Error: Failed to save keywords."))

    def populate_keyword_editor(self, expressions: dict):
        self.keyword_editor.clearContents()
        self.keyword_editor.setRowCount(len(expressions))
        self.keyword_editor.setHorizontalHeaderLabels([self.tr("header_expression", "Expression"), self.tr(
            "header_keywords", "Keywords"), self.tr("header_cooldown", "Cooldown (s)")])
        for i, (exp_file, exp_data) in enumerate(expressions.items()):
            self.keyword_editor.setItem(
                i, 0, QTableWidgetItem(exp_data.get('name', 'N/A')))
            self.keyword_editor.setItem(i, 1, QTableWidgetItem(
                ", ".join(exp_data.get('keywords', []))))
            self.keyword_editor.setItem(i, 2, QTableWidgetItem(
                str(exp_data.get('cooldown_s', 'N/A'))))
