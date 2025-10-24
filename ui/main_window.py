from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QTextEdit, QTableWidget, 
    QTableWidgetItem, QLabel, QPushButton, QHeaderView, QComboBox, QGridLayout, QFrame
)
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtCore import Qt, QSize
import os
from core.config_loader import ConfigLoader

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.translations = self._load_translations()
        self._load_stylesheet()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self._init_ui_elements()
        self.retranslate_ui("en") # Set initial language to English

    def _load_translations(self):
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'translations.yaml')
        return ConfigLoader.load_yaml(config_path)

    def _load_stylesheet(self):
        stylesheet_path = os.path.join(os.path.dirname(__file__), 'static', 'styles.qss')
        try:
            with open(stylesheet_path, "r") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print("Stylesheet not found.")

    def _init_ui_elements(self):
        # Main grid layout
        grid_layout = QGridLayout()
        self.main_layout.addLayout(grid_layout)

        # Settings Panel
        settings_frame = QFrame()
        settings_frame.setObjectName("settingsFrame")
        settings_layout = QHBoxLayout(settings_frame)

        self.language_label = QLabel()
        self.language_selector = QComboBox()
        if self.translations:
            self.language_selector.addItems(self.translations.keys())

        self.mode_label = QLabel()
        self.mode_selector = QComboBox()
        self.mode_selector.addItems(["fast", "accurate"])

        settings_layout.addWidget(self.language_label)
        settings_layout.addWidget(self.language_selector)
        settings_layout.addStretch()
        settings_layout.addWidget(self.mode_label)
        settings_layout.addWidget(self.mode_selector)
        
        grid_layout.addWidget(settings_frame, 0, 0, 1, 2)

        # Status Panel
        status_frame = QFrame()
        status_frame.setObjectName("statusFrame")
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
        controls_frame.setObjectName("controlsFrame")
        controls_layout = QHBoxLayout(controls_frame)
        self.start_button = QPushButton()
        self.start_button.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'static', 'icons', 'start.svg')))
        self.stop_button = QPushButton()
        self.stop_button.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'static', 'icons', 'stop.svg')))
        self.stop_button.setEnabled(False)
        controls_layout.addWidget(self.start_button)
        controls_layout.addWidget(self.stop_button)
        controls_layout.addStretch()
        grid_layout.addWidget(controls_frame, 2, 0, 1, 2)

        # Transcription Log
        self.transcription_log = QTextEdit()
        self.transcription_log.setReadOnly(True)
        grid_layout.addWidget(self.transcription_log, 3, 0, 1, 1)

        # Keyword Editor
        self.keyword_editor = QTableWidget()
        self.keyword_editor.setColumnCount(3)
        self.keyword_editor.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        grid_layout.addWidget(self.keyword_editor, 3, 1, 1, 1)

    def retranslate_ui(self, language: str):
        lang_dict = self.translations.get(language, self.translations.get("en", {}))

        def tr(key, default_text=""):
            return lang_dict.get(key, default_text)

        self.setWindowTitle(tr("window_title", "VTS Voice Controller"))
        self.set_status(vts=tr("status_disconnected", "Disconnected"), asr="Idle", app="Stopped")
        self.mode_label.setText(tr("mode_label", "Recognition Mode:"))
        self.start_button.setText(tr("start_button", "Start"))
        self.stop_button.setText(tr("stop_button", "Stop"))
        self.transcription_log.setPlaceholderText(tr("transcription_placeholder", "Live Transcription Output..."))
        self.keyword_editor.setHorizontalHeaderLabels([
            tr("header_expression", "Expression Name"), 
            tr("header_keywords", "Keywords"), 
            tr("header_cooldown", "Cooldown (s)")
        ])
        self.language_label.setText(tr("language_label", "Language:"))
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), 'static', 'icons', 'app_icon.svg')))


    def append_log(self, text: str):
        self.transcription_log.append(text)

    def set_status(self, vts: str = None, asr: str = None, app: str = None):
        if vts: self.vts_status_label.setText(f"VTS: {vts}")
        if asr: self.asr_status_label.setText(f"ASR: {asr}")
        if app: self.app_status_label.setText(f"App: {app}")

    def populate_keyword_editor(self, expressions: dict):
        self.keyword_editor.setRowCount(len(expressions))
        row = 0
        for exp_file, exp_data in expressions.items():
            self.keyword_editor.setItem(row, 0, QTableWidgetItem(exp_data.get('name', 'N/A')))
            self.keyword_editor.setItem(row, 1, QTableWidgetItem(", ".join(exp_data.get('keywords', []))))
            self.keyword_editor.setItem(row, 2, QTableWidgetItem(str(exp_data.get('cooldown_s', 'N/A'))))
            row += 1
