import json
import copy
from typing import Any, Callable, Dict, Iterator, List, Optional

import aqt
from aqt import mw
from aqt.qt import *
from aqt.utils import tooltip, showText


class InvalidConfigValueError(Exception):
    def __init__(self, key: str, expected: str, value: Any):
        self.key = key
        self.expected = expected
        self.value = value

    def __str__(self) -> str:
        return f"For config: {self.key}\nexpected value is: {self.expected}\nbut instead encountered: {self.value}"


class ConfigManager:
    def __init__(self) -> None:
        self.config_window: Optional[ConfigWindow] = None
        self.config_tabs: List[Callable] = []
        self._config: Optional[Dict] = None
        addon_dir = mw.addonManager.addonFromModule(__name__)
        self._default = mw.addonManager.addonConfigDefaults(addon_dir)
        self.load()

    def load(self) -> None:
        "Loads config from disk"
        self._config = mw.addonManager.getConfig(__name__)
        self.modified = False

    def save(self, force: bool = False) -> None:
        """Writes its config data to disk.
        If `force` is `False`, config is only written to disk if it was modified since last load."""
        if self.modified or force:
            mw.addonManager.writeConfig(__name__, self._config)
            self.modified = False

    def load_defaults(self) -> None:
        "call .save() afterwards to restore defaults."
        self._config = copy.deepcopy(self._default)
        self.modified = False

    def to_json(self) -> str:
        return json.dumps(self._config)

    def get_from_dict(self, dict_obj: dict, key: str) -> Any:
        "Raises KeyError if config doesn't exist"
        levels = key.split('.')
        return_val = dict_obj
        for level in levels:
            if isinstance(return_val, list):
                level = int(level)
            return_val = return_val[level]
        return return_val

    def copy(self) -> str:
        return copy.deepcopy(self._config)

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self.get_from_dict(self._config, key)
        except KeyError:
            return default

    def get_default_value(self, key: str) -> Any:
        return self.get_from_dict(self._default, key)

    def set(self, key: str, value: Any) -> None:
        self.modified = True
        levels = key.split('.')
        conf_obj = self._config
        for i in range(len(levels) - 1):
            level = levels[i]
            if isinstance(conf_obj, list):
                level = int(level)
            try:
                conf_obj = conf_obj[level]
            except KeyError:
                conf_obj[level] = {}
                conf_obj = conf_obj[level]
        conf_obj[levels[-1]] = value

    def __getitem__(self, key: str) -> Any:
        "Returns a deep copy of the config. Modifying the returned object will not affect conf."
        return self.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        "This function only modifies the internal config data. Call conf.save() to actually write to disk"
        self.set(key, value)

    def __iter__(self) -> Iterator:
        return iter(self._config)

    # Config Window
    def use_custom_window(self) -> None:
        def open_config() -> bool:
            config_window = ConfigWindow(self)
            for tab in self.config_tabs:
                tab(config_window)
            config_window.on_open()
            config_window.exec_()
            self.config_window = config_window
            return True
        mw.addonManager.setConfigAction(__name__, open_config)

    def add_config_tab(self, tab: Callable[["ConfigWindow"], None]) -> None:
        self.config_tabs.append(tab)


class ConfigWindow(QDialog):
    def __init__(self, conf: ConfigManager) -> None:
        QDialog.__init__(self, mw, Qt.Window)  # type: ignore
        self.conf = conf
        self.mgr = mw.addonManager
        self.setWindowTitle("Config for Edit Field During Review (Cloze)")
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.widget_updates: List[Callable[[], None]] = []
        self._on_save_hook: List[Callable[[], None]] = []
        self.setup()

    def setup(self) -> None:
        self.main_layout = QVBoxLayout()
        main_layout = self.main_layout
        self.setLayout(main_layout)

        self.main_tab = QTabWidget()
        main_tab = self.main_tab
        main_tab.setFocusPolicy(Qt.StrongFocus)
        main_layout.addWidget(main_tab)
        self.setup_buttons()

    def setup_buttons(self) -> None:
        btn_box = QHBoxLayout()

        advanced_btn = QPushButton("Advanced")
        advanced_btn.clicked.connect(self.on_advanced)
        btn_box.addWidget(advanced_btn)

        reset_btn = QPushButton("Restore Defaults")
        reset_btn.clicked.connect(self.on_reset)
        btn_box.addWidget(reset_btn)

        btn_box.addStretch(1)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.on_cancel)
        btn_box.addWidget(cancel_btn)

        save_btn = QPushButton("Save")
        save_btn.setDefault(True)
        save_btn.setShortcut("Ctrl+Return")
        save_btn.clicked.connect(self.on_save)
        btn_box.addWidget(save_btn)

        self.main_layout.addLayout(btn_box)

    def update_widgets(self) -> None:
        try:
            for widget_update in self.widget_updates:
                widget_update()
        except InvalidConfigValueError as e:
            advanced = self.advanced_window()
            dial, bbox = showText(
                "Invalid Config. Please fix the following issue in the advanced config editor. \n\n"
                + str(e),
                title="Invalid Config"
                parent=advanced,
                run=False)
            button = QPushButton("Quit Config")
            bbox.addButton(button, QDialogButtonBox.DestructiveRole)
            bbox.button(QDialogButtonBox.Close).setDefault(True)

            def quit() -> None:
                dial.close()
                advanced.close()
                self.widget_updates = []
                self.close()

            button.clicked.connect(quit)
            dial.show()
            advanced.exec_()
            self.conf.load()
            self.update_widgets()

    def on_open(self) -> None:
        self.update_widgets()

    def on_save(self) -> None:
        for hook in self._on_save_hook:
            hook()
        self.conf.save()
        self.close()

    def on_cancel(self) -> None:
        self.close()

    def on_reset(self) -> None:
        self.conf.load_defaults()
        self.update_widgets()
        tooltip("Press save to save changes")

    def on_advanced(self) -> None:
        self.advanced_window().exec_()
        self.conf.load()
        self.update_widgets()

    def advanced_window(self) -> aqt.addons.ConfigEditor:
        return aqt.addons.ConfigEditor(self, __name__, self.conf._config)

    def closeEvent(self, evt: QCloseEvent) -> None:
        # Discard the contents when clicked cancel,
        # and also in case the window was clicked without clicking any of the buttons
        self.conf.load()
        evt.accept()

    # Add Widgets

    def add_tab(self, name: str, widget: QWidget = None) -> "ConfigTab":
        tab = ConfigTab(self)
        self.main_tab.addTab(tab, name)
        return tab

    def execute_on_save(self, hook: Callable[[], None]) -> None:
        self._on_save_hook.append(hook)


class ConfigTab(QWidget):
    def __init__(self, window: ConfigWindow):
        QWidget.__init__(self, window)
        self.config_window = window
        self.conf = self.config_window.conf
        self.widget_updates = window.widget_updates

    def hlayout(self) -> "ConfigLayout":
        layout = ConfigLayout(self, QBoxLayout.LeftToRight)
        self.setLayout(layout)
        return layout

    def vlayout(self) -> "ConfigLayout":
        layout = ConfigLayout(self, QBoxLayout.TopToBottom)
        self.setLayout(layout)
        return layout


class ConfigLayout(QBoxLayout):
    def __init__(self, parent: QObject, direction: QBoxLayout.Direction):
        QBoxLayout.__init__(self, direction)
        self.conf = parent.conf
        self.config_window = parent.config_window
        self.widget_updates = parent.widget_updates

    def label(self, label: str, bold: bool = False, size: int = 0) -> QLabel:
        label_widget = QLabel(label)
        if bold or size:
            font = QFont()
            if bold:
                font.setBold(True)
            if size:
                font.setPixelSize(size)
            label_widget.setFont(font)

        self.addWidget(label_widget)
        return label_widget

    # Config Input Widgets

    def checkbox(self, key: str, label: str = "") -> QCheckBox:
        "For boolean config"
        checkbox = QCheckBox()

        def update() -> None:
            value = self.conf.get(key)
            if not isinstance(value, bool):
                raise InvalidConfigValueError(key, "boolean", value)
            checkbox.setChecked(value)
        self.widget_updates.append(update)

        if label:
            checkbox.setText(label)
        checkbox.stateChanged.connect(
            lambda s: self.conf.set(key, s == Qt.Checked))
        self.addWidget(checkbox)
        return checkbox

    def dropdown(self, key: str, labels: list, values: list) -> QComboBox:
        combobox = QComboBox()
        combobox.insertItems(0, labels)

        def update() -> None:
            conf = self.conf
            try:
                val = conf.get(key)
                index = values.index(val)
            except:
                raise InvalidConfigValueError(
                    key, "any value in list " + str(values), val)
            combobox.setCurrentIndex(index)
        self.widget_updates.append(update)

        combobox.currentIndexChanged.connect(
            lambda idx: self.conf.set(key, values[idx]))
        self.addWidget(combobox)
        return combobox

    def text_input(self, key: str) -> QLineEdit:
        "For string config"
        line_edit = QLineEdit()

        def update() -> None:
            val = self.conf.get(key)
            if not isinstance(val, str):
                raise InvalidConfigValueError(key, "string", val)
            line_edit.setText(val)
        self.widget_updates.append(update)

        line_edit.textChanged.connect(
            lambda text: self.conf.set(key, text))
        self.addWidget(line_edit)
        return line_edit

    def color_input(self, key: str) -> QPushButton:
        "For hex color config"
        button = QPushButton()
        button.setFixedWidth(25)
        button.setFixedHeight(25)

        color_dialog = QColorDialog(self.config_window)

        def set_color(rgb: str) -> None:
            button.setStyleSheet(
                "QPushButton{ background-color: \"%s\"; border: none; border-radius: 3px}" % rgb
            )
            color = QColor()
            color.setNamedColor(rgb)
            if not color.isValid():
                raise InvalidConfigValueError(key, "rgb hex color string", rgb)
            color_dialog.setCurrentColor(color)

        def update() -> None:
            value = self.conf.get(key)
            set_color(value)

        def save(color: QColor) -> None:
            rgb = color.name(QColor.HexRgb)
            self.conf.set(key, rgb)
            set_color(rgb)

        self.widget_updates.append(update)
        color_dialog.colorSelected.connect(lambda color: save(color))
        button.clicked.connect(lambda _: color_dialog.exec_())

        self.addWidget(button)
        return button

    # Layout widgets

    def space(self, space: int = 1) -> None:
        self.addSpacing(space)

    def stretch(self, factor: int = 0) -> None:
        self.addStretch(factor)

    def hlayout(self) -> "ConfigLayout":
        layout = ConfigLayout(self, QBoxLayout.LeftToRight)
        self.addLayout(layout)
        return layout

    def vlayout(self) -> "ConfigLayout":
        layout = ConfigLayout(self, QBoxLayout.TopToBottom)
        self.addLayout(layout)
        return layout

    def scroll_layout(self, horizontal: bool = True, vertical: bool = True) -> "ConfigLayout":
        layout = ConfigLayout(self, QBoxLayout.TopToBottom)
        inner_widget = QWidget()
        inner_widget.setLayout(layout)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(inner_widget)
        scroll.setSizePolicy(
            QSizePolicy.Expanding if horizontal else QSizePolicy.Minimum,
            QSizePolicy.Expanding if vertical else QSizePolicy.Minimum,
        )
        self.addWidget(scroll)
        return layout


def config_make_valid(conf: ConfigManager) -> None:
    # Once a boolean, Now a number.
    resize_conf = conf["resize_image_preserve_ratio"]
    if isinstance(resize_conf, bool):
        if resize_conf:
            conf["resize_image_preserve_ratio"] = 1
        else:
            conf["resize_image_preserve_ratio"] = 0
    conf.save()
