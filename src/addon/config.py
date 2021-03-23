import json
import copy
from typing import Any, Dict, Iterator, Optional

import aqt
from aqt import mw
from aqt.qt import *
from aqt.utils import tooltip


class ConfigManager:
    def __init__(self) -> None:
        self.config_window: Optional[ConfigWindow] = None
        self._config: Optional[Dict] = None
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
        self._config = mw.addonManager.addonConfigDefaults(__name__)
        self.modified = False

    def to_json(self) -> str:
        return json.dumps(self._config)

    def __getitem__(self, key: str) -> Any:
        "Returns a deep copy of the config. Modifying the returned object will not affect conf."
        return copy.deepcopy(self._config[key])

    def __setitem__(self, key: str, value: Any) -> None:
        "This function only modifies the internal config data. Call conf.save() to actually write to disk"
        self._config[key] = value
        self.modified = True

    def __iter__(self) -> Iterator:
        return iter(self._config)

    # Config Window
    def enable_config_window(self) -> "ConfigWindow":
        self.config_window = ConfigWindow(self)
        config_window = self.config_window

        def open_config() -> bool:
            config_window.exec_()
            return True
        mw.addonManager.setConfigAction(__name__, open_config)

        return config_window


class ConfigWindow(QDialog):
    def __init__(self, config: ConfigManager) -> None:
        QDialog.__init__(self, mw, Qt.Window)  # type: ignore
        self.config = config
        self.mgr = mw.addonManager
        self.setWindowTitle("Config for Edit Field During Review (Cloze)")
        self.setup()

    def setup(self) -> None:
        self.main_layout = QVBoxLayout(self)
        main_layout = self.main_layout
        self.setLayout(main_layout)

        self.main_tab = QTabWidget()
        main_tab = self.main_tab
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

    def addTab(self, name: str, widget: QWidget) -> None:
        self.main_tab.addTab(widget, name)

    def on_save(self) -> None:
        self.config.save()
        self.close()

    def on_cancel(self) -> None:
        self.close()

    def on_reset(self) -> None:
        # TODO: warn user before loading default
        self.config.load_defaults()
        self.config.save()
        self.close()
        tooltip("Restored Defaults")

    def on_advanced(self) -> None:
        aqt.addons.ConfigEditor(self, __name__, self.config._config).exec_()
        self.close()

    def closeEvent(self, evt: QCloseEvent) -> None:
        # Discard the contents when clicked cancel,
        # and also in case the window was clicked without clicking any of the buttons
        self.config.load()
        evt.accept()


def config_make_valid(conf: ConfigManager) -> None:
    # Once a boolean, Now a number.
    resize_conf = conf["resize_image_preserve_ratio"]
    if isinstance(resize_conf, bool):
        if resize_conf:
            conf["resize_image_preserve_ratio"] = 1
        else:
            conf["resize_image_preserve_ratio"] = 0
    conf.save()
