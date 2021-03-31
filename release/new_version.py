import re
import sys
from pathlib import Path

version_string = sys.argv[1]
assert re.match(r"^(\d+).(\d+)$", version_string)

file_path = Path(__file__).resolve().parents[1] / "src" / "addon" / "VERSION"
file_path.write_text(version_string)
