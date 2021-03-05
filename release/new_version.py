import re
import sys
import simplejson
from pathlib import Path

version_string = sys.argv[1]
match = re.compile(r"(\d+).(\d+)").search(version_string)
major_version = match.group(1)
minor_version = match.group(2)

json_path = Path(__file__).resolve().parents[1] / "src" / "config.json"
with json_path.open('r') as f:
    config = simplejson.load(f)
with json_path.open('w') as f:
    config["version"] = {
        "major": major_version,
        "minor": minor_version
    }
    simplejson.dump(config, f, indent=2)
