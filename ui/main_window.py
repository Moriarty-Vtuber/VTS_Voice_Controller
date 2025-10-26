from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QTextEdit, QTableWidget, 
    QTableWidgetItem, QLabel, QPushButton, QHeaderView, QComboBox, QGridLayout, QFrame, QSizePolicy
)
from PyQt6.QtGui import QIcon, QFont
from loguru import logger
from PyQt6.QtCore import Qt, QSize
import os
from core.config_loader import ConfigLoader
from inputs.emotion_detector import EMOTION_LABELS # Keep import for _init_ui_elements

class MainWindow(QMainWindow):
    EMOTION_LABELS = EMOTION_LABELS # Make it a class attribute

    def __init__(self, config_path: str, initial_config: dict):
        super().__init__()

        self.config_path = config_path
        self.initial_config = initial_config

        self.setMinimumSize(800, 600) # Set a reasonable minimum size for the window

        self.translations = self._load_translations()
        # self._load_stylesheet() # Temporarily commented out for debugging

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

        self.microphone_label = QLabel()
        self.microphone_selector = QComboBox()

        self.webcam_label = QLabel()
        self.webcam_selector = QComboBox()

        settings_layout.addWidget(self.language_label)
        settings_layout.addWidget(self.language_selector)
        settings_layout.addStretch()
        settings_layout.addWidget(self.mode_label)
        settings_layout.addWidget(self.mode_selector)
        settings_layout.addStretch()
        settings_layout.addWidget(self.input_type_label)
        settings_layout.addWidget(self.input_type_selector)
        settings_layout.addStretch()
        settings_layout.addWidget(self.microphone_label)
        settings_layout.addWidget(self.microphone_selector)
        settings_layout.addStretch()
        settings_layout.addWidget(self.webcam_label)
        settings_layout.addWidget(self.webcam_selector)
        
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

        self.save_emotion_button = QPushButton()
        self.save_emotion_button.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'static', 'icons', 'save.svg')))
        self.save_emotion_button.clicked.connect(self._save_emotion_mappings_to_config)
        
        controls_layout.addWidget(self.start_button)
        controls_layout.addWidget(self.stop_button)
        controls_layout.addWidget(self.save_button) # Add save button
        controls_layout.addWidget(self.save_emotion_button) # Add save emotion button
        controls_layout.addStretch()
        grid_layout.addWidget(controls_frame, 2, 0, 1, 2)

        # Transcription Log
        self.transcription_log = QTextEdit()
        self.transcription_log.setReadOnly(True)
        self.transcription_log.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        grid_layout.addWidget(self.transcription_log, 3, 0, 1, 1)

        # Keyword Editor
        self.keyword_editor = QTableWidget()
        self.keyword_editor.setColumnCount(3)
        self.keyword_editor.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.keyword_editor.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        grid_layout.addWidget(self.keyword_editor, 3, 1, 1, 1)

        # Emotion Mapping Editor
        self.emotion_editor_frame = QFrame()
        self.emotion_editor_frame.setObjectName("emotionEditorFrame")
        self.emotion_editor_layout = QGridLayout(self.emotion_editor_frame)
        self.emotion_editor_labels = {}
        self.emotion_editor_comboboxes = {}

        # Import EMOTION_LABELS from emotion_detector
        # from inputs.emotion_detector import EMOTION_LABELS # Removed

        for i, emotion in enumerate(self.EMOTION_LABELS):
            label = QLabel(emotion.capitalize() + ":")
            combo_box = QComboBox()
            combo_box.setMinimumSize(100, 25) # Explicitly set a minimum size
            self.emotion_editor_labels[emotion] = label
            self.emotion_editor_comboboxes[emotion] = combo_box
            self.emotion_editor_layout.addWidget(label, i, 0)
            self.emotion_editor_layout.addWidget(combo_box, i, 1)
            
            logger.debug(f"Emotion ComboBox {emotion}: FocusPolicy={combo_box.focusPolicy()}")

            # Use a nested function to capture 'emotion' correctly
            def create_connection(current_emotion):
                def on_index_changed(index):
                    self._emotion_mapping_changed(current_emotion, index)
                return on_index_changed

            combo_box.currentIndexChanged.connect(create_connection(emotion))

            if emotion == "neutral": # Install event filter on the 'neutral' combobox for debugging
                combo_box.installEventFilter(self)
                # Temporary button to show popup programmatically
                self.show_popup_button = QPushButton("Show Neutral Popup")
                self.show_popup_button.clicked.connect(lambda: self.emotion_editor_comboboxes["neutral"].showPopup())
                self.emotion_editor_layout.addWidget(self.show_popup_button, i, 2) # Add next to the combobox
        
        logger.debug(f"Emotion editor comboboxes after initialization: {self.emotion_editor_comboboxes}")

        # Temporary button for testing interactivity
        self.test_button = QPushButton("Test Button")
        self.test_button.clicked.connect(lambda: logger.info("Test Button Clicked!"))
        self.emotion_editor_layout.addWidget(self.test_button, len(EMOTION_LABELS), 0, 1, 2)

        grid_layout.addWidget(self.emotion_editor_frame, 4, 0, 1, 2) # Place below keyword editor, spanning both columns
        self.emotion_editor_frame.setMinimumHeight(200)
        self.emotion_editor_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        grid_layout.setRowStretch(4, 1) # Give this row a stretch factor to make it expand


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
        self.microphone_label.setText(self.tr("microphone_label"))
        self.webcam_label.setText(self.tr("webcam_label"))
        # self.keyword_editor_group.setTitle(self.tr("keyword_editor_title")) # This element was removed
        self.save_button.setText(self.tr("button_save"))
        self.save_emotion_button.setText(self.tr("button_save_emotion_mappings"))
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

    def _save_emotion_mappings_to_config(self):
        logger.info("--- UI: Save Emotion Mappings button clicked ---")
        updated_emotion_mappings = {}
        # from inputs.emotion_detector import EMOTION_LABELS # Re-import to ensure access # Removed

        for emotion in self.EMOTION_LABELS:
            combo_box = self.emotion_editor_comboboxes.get(emotion)
            if combo_box:
                selected_expression = combo_box.currentText()
                # Save 'null' if 'None' or empty string is selected
                updated_emotion_mappings[emotion] = selected_expression if selected_expression not in ["None", ""] else "null"

        current_config = ConfigLoader.load_yaml(self.config_path)
        if current_config:
            current_config['emotion_mappings'] = updated_emotion_mappings
            ConfigLoader.save_yaml(self.config_path, current_config)
            logger.info("Emotion mappings saved to vts_config.yaml")
            self.append_log(self.tr("emotion_mappings_saved_success", "Emotion mappings saved successfully!"))
        else:
            logger.error("Failed to load current config for saving emotion mappings.")
            self.append_log(self.tr("emotion_mappings_save_error", "Error: Failed to save emotion mappings."))

    def populate_keyword_editor(self, expressions: dict):
        self.keyword_editor.setRowCount(len(expressions))
        row = 0
        for exp_file, exp_data in expressions.items():
            self.keyword_editor.setItem(row, 0, QTableWidgetItem(exp_data.get('name', 'N/A')))
            self.keyword_editor.setItem(row, 1, QTableWidgetItem(", ".join(exp_data.get('keywords', []))))
            self.keyword_editor.setItem(row, 2, QTableWidgetItem(str(exp_data.get('cooldown_s', 'N/A'))))
            row += 1

    def populate_emotion_editor(self, emotion_mappings: dict, available_vts_expressions: list):
        logger.debug(f"Populating emotion editor with {len(available_vts_expressions)} VTS expressions.")

        # Clear existing items and add a "None" option
        for emotion in self.EMOTION_LABELS:
            combo_box = self.emotion_editor_comboboxes.get(emotion)
            if combo_box is not None:
                try:
                    combo_box.clear()
                    combo_box.addItem("None") # Option to not trigger any expression
                    if available_vts_expressions:
                        combo_box.addItems(available_vts_expressions)
                except Exception as e:
                    print(f"[ERROR] Exception while populating combobox for emotion '{emotion}': {e}")

            # Set current selection based on config
            mapped_expression = emotion_mappings.get(emotion)
            if mapped_expression and mapped_expression != "null":
                index = combo_box.findText(mapped_expression)
                if index != -1:
                    combo_box.setCurrentIndex(index)
                else:
                    logger.warning(f"Mapped expression '{mapped_expression}' for emotion '{emotion}' not found in VTS expressions.")
                    combo_box.setCurrentText("None") # Fallback to None if not found
            else:
                combo_box.setCurrentText("None") # Default to None if not mapped or explicitly null

    def _emotion_mapping_changed(self, emotion: str, index: int):
        combo_box = self.emotion_editor_comboboxes.get(emotion)
        if combo_box:
            selected_expression = combo_box.itemText(index)
            logger.info(f"Emotion mapping changed: {emotion} -> {selected_expression}")

    def eventFilter(self, obj, event):
        from PyQt6.QtCore import QEvent
        if obj in self.emotion_editor_comboboxes.values(): # Check if the object is one of our comboboxes
            logger.debug(f"Event Filter: Object={obj.objectName() if obj.objectName() else obj.__class__.__name__}, Event Type={event.type().name}")
            if event.type() == QEvent.Type.MouseButtonPress:
                logger.debug(f"Event Filter: MouseButtonPress detected on {obj.objectName() if obj.objectName() else obj.__class__.__name__}")
            elif event.type() == QEvent.Type.MouseButtonRelease:
                logger.debug(f"Event Filter: MouseButtonRelease detected on {obj.objectName() if obj.objectName() else obj.__class__.__name__}")
            elif event.type() == QEvent.Type.HoverEnter:
                logger.debug(f"Event Filter: HoverEnter detected on {obj.objectName() if obj.objectName() else obj.__class__.__name__}")
            elif event.type() == QEvent.Type.HoverLeave:
                logger.debug(f"Event Filter: HoverLeave detected on {obj.objectName() if obj.objectName() else obj.__class__.__name__}")
        return super().eventFilter(obj, event)
