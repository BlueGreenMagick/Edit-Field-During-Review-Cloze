from typing import Callable, List, TYPE_CHECKING

import aqt
from aqt import mw
from aqt.qt import *
from aqt.utils import tooltip, showText

from .errors import InvalidConfigValueError

if TYPE_CHECKING:
    from .manager import ConfigManager


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
                title="Invalid Config",
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
