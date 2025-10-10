from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QTextEdit, QTableWidget, 
    QTableWidgetItem, QLabel, QPushButton, QHeaderView, QComboBox
)
from PyQt6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self._init_ui_elements()
        self.retranslate_ui("en") # Set initial language to English

    def _init_ui_elements(self):
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
        self.mode_label = QLabel()
        self.mode_selector = QComboBox()
        self.mode_selector.addItems(["fast", "accurate"])
        controls_layout.addWidget(self.start_button)
        controls_layout.addWidget(self.stop_button)
        controls_layout.addStretch()
        controls_layout.addWidget(self.mode_label)
        controls_layout.addWidget(self.mode_selector)
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
        # In the future, this could load text from a language file
        if language == "en":
            self.setWindowTitle("VTS Voice Controller")
            self.set_status(vts="Disconnected", asr="Idle", app="Stopped") # Set initial text
            self.mode_label.setText("Recognition Mode:")
            self.start_button.setText("Start Application")
            self.stop_button.setText("Stop Application")
            self.transcription_log.setPlaceholderText("Live Transcription Output...")
            self.keyword_editor.setHorizontalHeaderLabels(["Expression Name", "Keywords", "Cooldown (s)"])

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
