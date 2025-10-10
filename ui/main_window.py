from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QTextEdit, QTableWidget, 
    QTableWidgetItem, QLabel, QPushButton, QHeaderView, QComboBox
)
from PyQt6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VTS Voice Controller")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self._init_status_panel()
        self._init_controls()
        self._init_transcription_log()
        self._init_keyword_editor()

    def _init_status_panel(self):
        status_layout = QHBoxLayout()
        self.vts_status_label = QLabel("VTS Status: Disconnected")
        self.asr_status_label = QLabel("ASR Status: Idle")
        self.app_status_label = QLabel("App Status: Stopped")

        status_layout.addWidget(self.vts_status_label)
        status_layout.addWidget(self.asr_status_label)
        status_layout.addWidget(self.app_status_label)
        self.main_layout.addLayout(status_layout)

    def _init_controls(self):
        controls_layout = QHBoxLayout()
        self.start_button = QPushButton("Start Application")
        self.stop_button = QPushButton("Stop Application")
        self.stop_button.setEnabled(False)

        self.mode_selector = QComboBox()
        self.mode_selector.addItems(["fast", "accurate"])

        controls_layout.addWidget(self.start_button)
        controls_layout.addWidget(self.stop_button)
        controls_layout.addWidget(QLabel("Recognition Mode:"))
        controls_layout.addWidget(self.mode_selector)
        self.main_layout.addLayout(controls_layout)

    def _init_transcription_log(self):
        self.transcription_log = QTextEdit()
        self.transcription_log.setReadOnly(True)
        self.transcription_log.setPlaceholderText("Live Transcription Output...")
        self.main_layout.addWidget(self.transcription_log)

    def _init_keyword_editor(self):
        self.keyword_editor = QTableWidget()
        self.keyword_editor.setColumnCount(3)
        self.keyword_editor.setHorizontalHeaderLabels(["Expression Name", "Keywords", "Cooldown (s)"])
        self.keyword_editor.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.main_layout.addWidget(self.keyword_editor)

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
