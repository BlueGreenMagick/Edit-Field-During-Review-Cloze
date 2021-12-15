import os

from aqt import mw
from aqt.utils import showText

from .ankiaddonconfig import ConfigManager


conf = ConfigManager()


class Version:
    def __init__(self) -> None:
        self.load()

    def load(self) -> None:
        self.major = conf["version.major"]
        self.minor = conf["version.minor"]
        # v6.x has string version
        if isinstance(self.major, str):
            self.major = int(self.major)
        if isinstance(self.minor, str):
            self.major = int(self.minor)

    def __eq__(self, other: str) -> bool:  # type: ignore
        ver = [int(i) for i in other.split(".")]
        return self.major == ver[0] and self.minor == ver[1]

    def __gt__(self, other: str) -> bool:
        ver = [int(i) for i in other.split(".")]
        return self.major > ver[0] or (self.major == ver[0] and self.minor > ver[1])

    def __lt__(self, other: str) -> bool:
        ver = [int(i) for i in other.split(".")]
        return self.major < ver[0] or (self.major == ver[0] and self.minor < ver[1])

    def __ge__(self, other: str) -> bool:
        return self == other or self > other

    def __le__(self, other: str) -> bool:
        return self == other or self < other


version = Version()


# Initial installation have config version of -1.-1
# Versions before 6.0 will have config version of 0.0
# However if the user hasn't edited their config, it will show up as -1.-1


def distinguish_initial_install() -> None:
    if not version == "-1.-1":
        return
    if conf.get("undo", None):
        conf["version.major"] = 0
        conf["version.minor"] = 0
        conf.save()
        version.load()


distinguish_initial_install()


# Make config compatible when upgrading from older version


def change_resize_image_preserve_ratio() -> None:
    resize_conf = conf["resize_image_preserve_ratio"]
    if not isinstance(resize_conf, bool):
        return

    if resize_conf:
        conf["resize_image_preserve_ratio"] = 1
    else:
        conf["resize_image_preserve_ratio"] = 0
    conf.save()


change_resize_image_preserve_ratio()


def change_special_formatting() -> None:
    if not "z_special_formatting" in conf:
        return
    for key in conf["z_special_formatting"]:
        opts = conf["z_special_formatting"][key]
        if isinstance(opts, list):
            enabled = opts[0]
            arg = opts[1]
        else:
            enabled = opts
            arg = None
        conf[f"special_formatting.{key}.enabled"] = enabled
        if arg is not None:
            conf[f"special_formatting.{key}.arg"] = {
                "type": "color" if key in ["fontcolor", "highlight"] else "text",
                "value": arg,
            }

    del conf["z_special_formatting"]
    conf.save()


change_special_formatting()


def remove_undo() -> None:
    if not "undo" in conf:
        return
    del conf["undo"]
    conf.save()


remove_undo()


def initial_tutorial() -> None:
    tutorial = "<br>".join(
        [
            "<center><h3>Edit Field During Review (Cloze)",
            "How to Use</h3></center>"
            "<h4>Initial Setup</h4>"
            "1. Open the add-on config and go to the <i>Fields</i> tab.",
            "2. For each note type, <i>check</i> the fields you want editable.",
            "3. Remember to do this whenever you add or modify a note type!",
            "4. And it's done! Now you can <b>Ctrl + Click</b> on the field content to edit it.",
        ]
    )
    showText(tutorial, type="html", title="Add-on Tutorial")


if version == "-1.-1":
    initial_tutorial()

# Save current version
version_string = os.environ.get("EFDRC_VERSION")
if not version_string:
    addon_dir = mw.addonManager.addonFromModule(__name__)
    meta = mw.addonManager.addonMeta(addon_dir)
    version_string = meta["human_version"]

conf["version.major"] = int(version_string.split(".")[0])
conf["version.minor"] = int(version_string.split(".")[1])
conf.save()
