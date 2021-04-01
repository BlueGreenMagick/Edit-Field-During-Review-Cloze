from pathlib import Path

from .config import conf


class Version:
    def __init__(self) -> None:
        self.load()

    def load(self) -> None:
        self.major = conf["version.major"]
        self.minor = conf["version.minor"]

    def __eq__(self, other: str) -> bool:  # type: ignore
        ver = other.split(".")
        return self.major == ver[0] and self.minor == ver[1]

    def __gt__(self, other: str) -> bool:
        ver = other.split(".")
        return self.major > ver[0] or (self.major == ver[0] and self.minor > ver[1])

    def __lt__(self, other: str) -> bool:
        ver = other.split(".")
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


# Save current version
file_path = Path(__file__).parent / "VERSION"
version_string = file_path.read_text()
conf["version.major"] = version_string.split(".")[0]
conf["version.minor"] = version_string.split(".")[1]
