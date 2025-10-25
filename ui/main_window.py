from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QTextEdit, QTableWidget, 
    QTableWidgetItem, QLabel, QPushButton, QHeaderView, QComboBox, QGridLayout, QFrame
)
from PyQt6.QtGui import QIcon, QFont
from loguru import logger
from PyQt6.QtCore import Qt, QSize
import os
from core.config_loader import ConfigLoader

class MainWindow(QMainWindow):
    def __init__(self, config_path: str, initial_config: dict):
        super().__init__()

        self.config_path = config_path
        self.initial_config = initial_config

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
        self.mode_selector.addItems([self.tr("mode_fast"), self.tr("mode_accurate")])

        self.input_type_label = QLabel()
        self.input_type_selector = QComboBox()
        self.input_type_selector.addItems([self.tr("input_type_voice"), self.tr("input_type_emotion")])

        settings_layout.addWidget(self.language_label)
        settings_layout.addWidget(self.language_selector)
        settings_layout.addStretch()
        settings_layout.addWidget(self.mode_label)
        settings_layout.addWidget(self.mode_selector)
        settings_layout.addStretch()
        settings_layout.addWidget(self.input_type_label)
        settings_layout.addWidget(self.input_type_selector)
        
        grid_layout.addWidget(settings_frame, 0, 0, 1, 2)

        # Status Panel
        status_frame = QFrame()
        status_frame.setObjectName("statusFrame")
        status_layout = QHBoxLayout(status_frame)
        self.vts_status_label = QLabel()
        self.vts_status_label.setObjectName("vtsStatusLabel")
        self.asr_status_label = QLabel()
        self.asr_status_label.setObjectName("asrStatusLabel")
        self.app_status_label = QLabel()
        self.app_status_label.setObjectName("appStatusLabel")
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
        self.save_button = QPushButton()
        self.save_button.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'static', 'icons', 'save.svg'))) # Assuming a save.svg icon exists or will be created
        self.save_button.clicked.connect(self._save_keywords_to_config)
        
        controls_layout.addWidget(self.start_button)
        controls_layout.addWidget(self.stop_button)
        controls_layout.addWidget(self.save_button) # Add save button
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

    def retranslate_ui(self, language):
        self.setWindowTitle(self.tr("window_title"))
        self.app_status_label.setText(f"<b>{self.tr('status_app')}:</b> {self.tr('status_stopped')}")
        self.vts_status_label.setText(f"<b>{self.tr('status_vts')}:</b> {self.tr('status_disconnected')}")
        self.asr_status_label.setText(f"<b>{self.tr('status_asr')}:</b> {self.tr('status_idle')}")
        self.start_button.setText(self.tr("button_start"))
        self.stop_button.setText(self.tr("button_stop"))
        self.language_label.setText(self.tr("language_label"))
        self.mode_label.setText(self.tr("mode_label"))
        self.input_type_label.setText(self.tr("input_type_label"))
        # self.keyword_editor_group.setTitle(self.tr("keyword_editor_title")) # This element was removed
        self.save_button.setText(self.tr("button_save"))
        # self.log_group.setTitle(self.tr("log_title")) # This element was removed

        self.mode_selector.setItemText(0, self.tr("mode_fast"))
        self.mode_selector.setItemText(1, self.tr("mode_accurate"))
        self.input_type_selector.setItemText(0, self.tr("input_type_voice"))
        self.input_type_selector.setItemText(1, self.tr("input_type_emotion"))

    def append_log(self, text: str):
        self.transcription_log.append(text)

    def set_status(self, vts: str = None, asr: str = None, app: str = None):
        if vts: self.vts_status_label.setText(f"<b>{self.tr('status_vts')}:</b> {vts}")
        if asr: self.asr_status_label.setText(f"<b>{self.tr('status_asr')}:</b> {asr}")
        if app: self.app_status_label.setText(f"<b>{self.tr('status_app')}:</b> {app}")

    def _save_keywords_to_config(self):
        logger.info("--- UI: Save button clicked ---")
        updated_expressions = {}
        for row in range(self.keyword_editor.rowCount()):
            expression_name = self.keyword_editor.item(row, 0).text()
            keywords_str = self.keyword_editor.item(row, 1).text()
            cooldown_str = self.keyword_editor.item(row, 2).text()

            keywords = [k.strip() for k in keywords_str.split(',') if k.strip()]
            cooldown_s = int(cooldown_str) if cooldown_str.isdigit() else 0 # Default to 0 if not a valid number

            # Find the original expression key (exp_file) from the initial config
            # This assumes expression names are unique and match the 'name' field in config
            original_key = None
            for k, v in self.initial_config.get('expressions', {}).items():
                if v.get('name') == expression_name:
                    original_key = k
                    break
            
            if original_key:
                updated_expressions[original_key] = {
                    'name': expression_name,
                    'keywords': keywords,
                    'cooldown_s': cooldown_s
                }
            else:
                logger.warning(f"Could not find original key for expression: {expression_name}")

        # Load the current config to preserve other settings
        current_config = ConfigLoader.load_yaml(self.config_path)
        if current_config:
            current_config['expressions'] = updated_expressions
            ConfigLoader.save_yaml(self.config_path, current_config)
            logger.info("Keywords saved to vts_config.yaml")
            self.append_log(self.tr("keywords_saved_success", "Keywords saved successfully!"))
        else:
            logger.error("Failed to load current config for saving.")
            self.append_log(self.tr("keywords_save_error", "Error: Failed to save keywords."))

    def populate_keyword_editor(self, expressions: dict):
        self.keyword_editor.setRowCount(len(expressions))
        row = 0
        for exp_file, exp_data in expressions.items():
            self.keyword_editor.setItem(row, 0, QTableWidgetItem(exp_data.get('name', 'N/A')))
            self.keyword_editor.setItem(row, 1, QTableWidgetItem(", ".join(exp_data.get('keywords', []))))
            self.keyword_editor.setItem(row, 2, QTableWidgetItem(str(exp_data.get('cooldown_s', 'N/A'))))
            row += 1
