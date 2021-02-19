from typing import Dict

from aqt import mw


def config_make_valid(config: Dict):
    changed = False

    # Once a boolean, Now a number.
    resize_conf = config["resize_image_preserve_ratio"]
    if isinstance(resize_conf, bool):
        if resize_conf:
            config["resize_image_preserve_ratio"] = 1
        else:
            config["resize_image_preserve_ratio"] = 0
        changed = True

    sfmt = config["z_special_formatting"]
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
            changed = True

    for key in key_to_pop:
        sfmt.pop(key)

    # Add keys on update / wrong deletion.
    for key in default_sfmt:
        if key not in sfmt:
            sfmt[key] = default_sfmt[key]
            changed = True

    if changed:
        mw.addonManager.writeConfig(__name__, config)
