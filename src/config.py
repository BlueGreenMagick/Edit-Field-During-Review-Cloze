import json
import copy
from typing import Any, Iterator

from aqt import mw


class ConfigManager:
    def __init__(self) -> None:
        self.load()

    def load(self) -> None:
        "Loads config from disk"
        self.config = mw.addonManager.getConfig(__name__)
        self.modified = False

    def save(self, force: bool = False) -> None:
        """Writes its config data to disk.
        If `force` is `False`, config is only written to disk if it was modified since last load."""
        if self.modified or force:
            mw.addonManager.writeConfig(__name__, self.config)
            self.modified = False

    def to_json(self) -> str:
        return json.dumps(self.config)

    def __getitem__(self, key: str) -> Any:
        "Returns a deep copy of the config. Modifying the returned object will not affect conf."
        return copy.deepcopy(self.config[key])

    def __setitem__(self, key: str, value: Any) -> None:
        "This function only modifies the internal config data. Call conf.write() to actually write to disk"
        self.config[key] = value
        self.modified = True

    def __iter__(self) -> Iterator:
        return iter(self.config)


def config_make_valid(conf: ConfigManager) -> None:
    # Once a boolean, Now a number.
    resize_conf = conf["resize_image_preserve_ratio"]
    if isinstance(resize_conf, bool):
        if resize_conf:
            conf["resize_image_preserve_ratio"] = 1
        else:
            conf["resize_image_preserve_ratio"] = 0

    sfmt = conf["z_special_formatting"]
    default_sfmt = {
        "removeformat": True,
        "strikethrough": True,
        "fontcolor": [True, "#00f"],
        "highlight": [False, "#00f"],
        "subscript": False,
        "superscript": False,
        "formatblock": [False, "pre"],
        "hyperlink": False,
        "unhyperlink": False,
        "unorderedlist": False,
        "orderedlist": False,
        "indent": False,
        "outdent": False,
        "justifyCenter": False,
        "justifyLeft": False,
        "justifyRight": False,
        "justifyFull": False,
    }

    # Remove wrong key.
    key_to_pop = []
    for key in sfmt:
        if key not in default_sfmt:
            key_to_pop.append(key)

    for key in key_to_pop:
        sfmt.pop(key)

    # Add keys on update / wrong deletion.
    for key in default_sfmt:
        if key not in sfmt:
            sfmt[key] = default_sfmt[key]

    conf["z_special_formatting"] = sfmt
    conf.save()
