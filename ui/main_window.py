from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QTextEdit, QTableWidget, 
    QTableWidgetItem, QLabel, QPushButton, QHeaderView, QComboBox
)
from PyQt6.QtCore import Qt
import os
from core.config_loader import ConfigLoader

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.translations = self._load_translations()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self._init_ui_elements()
        self.retranslate_ui("en") # Set initial language to English

    def _load_translations(self):
        # Construct the path to the translations file
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'translations.yaml')
        return ConfigLoader.load_yaml(config_path)

    def _init_ui_elements(self):
        # Top layout for selectors
        top_layout = QHBoxLayout()

        # Language Selector
        self.language_label = QLabel("Language:")
        self.language_selector = QComboBox()
        if self.translations:
            self.language_selector.addItems(self.translations.keys())
        self.language_selector.currentTextChanged.connect(self.retranslate_ui)
        top_layout.addWidget(self.language_label)
        top_layout.addWidget(self.language_selector)
        top_layout.addStretch()

        # Mode Selector
        self.mode_label = QLabel()
        self.mode_selector = QComboBox()
        self.mode_selector.addItems(["fast", "accurate"])
        top_layout.addWidget(self.mode_label)
        top_layout.addWidget(self.mode_selector)
        
        self.main_layout.addLayout(top_layout)

        # Status Panel
        status_layout = QHBoxLayout()
        self.vts_status_label = QLabel()
        self.asr_status_label = QLabel()
        self.app_status_label = QLabel()
        status_layout.addWidget(self.vts_status_label)
        status_layout.addWidget(self.asr_status_label)
        status_layout.addWidget(self.app_status_label)
        self.main_layout.addLayout(status_layout)

        # Controls
        controls_layout = QHBoxLayout()
        self.start_button = QPushButton()
        self.stop_button = QPushButton()
        self.stop_button.setEnabled(False)
        controls_layout.addWidget(self.start_button)
        controls_layout.addWidget(self.stop_button)
        controls_layout.addStretch()
        self.main_layout.addLayout(controls_layout)

        # Transcription Log
        self.transcription_log = QTextEdit()
        self.transcription_log.setReadOnly(True)
        self.main_layout.addWidget(self.transcription_log)

        # Keyword Editor
        self.keyword_editor = QTableWidget()
        self.keyword_editor.setColumnCount(3)
        self.keyword_editor.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.main_layout.addWidget(self.keyword_editor)

    def retranslate_ui(self, language: str):
        # Get the dictionary for the selected language, fallback to 'en'
        lang_dict = self.translations.get(language, self.translations.get("en", {}))

        def tr(key, default_text=""):
            return lang_dict.get(key, default_text)

        self.setWindowTitle(tr("window_title", "VTS Voice Controller"))
        self.set_status(vts=tr("status_disconnected", "Disconnected"), asr="Idle", app="Stopped")
        self.mode_label.setText(tr("mode_label", "Recognition Mode:"))
        self.start_button.setText(tr("start_button", "Start Application"))
        self.stop_button.setText(tr("stop_button", "Stop Application"))
        self.transcription_log.setPlaceholderText(tr("transcription_placeholder", "Live Transcription Output..."))
        self.keyword_editor.setHorizontalHeaderLabels([
            tr("header_expression", "Expression Name"), 
            tr("header_keywords", "Keywords"), 
            tr("header_cooldown", "Cooldown (s)")
        ])
        self.language_label.setText(tr("language_label", "Language:"))

    def append_log(self, text: str):
        self.transcription_log.append(text)

    def set_status(self, vts: str = None, asr: str = None, app: str = None):
        if vts: self.vts_status_label.setText(f"VTS Status: {vts}")
        if asr: self.asr_status_label.setText(f"ASR Status: {asr}")
        if app: self.app_status_label.setText(f"App Status: {app}")

    def populate_keyword_editor(self, expressions: dict):
        self.keyword_editor.setRowCount(len(expressions))
        row = 0
        for exp_file, exp_data in expressions.items():
            self.keyword_editor.setItem(row, 0, QTableWidgetItem(exp_data.get('name', 'N/A')))
            self.keyword_editor.setItem(row, 1, QTableWidgetItem(", ".join(exp_data.get('keywords', []))))
            self.keyword_editor.setItem(row, 2, QTableWidgetItem(str(exp_data.get('cooldown_s', 'N/A'))))
            row += 1
