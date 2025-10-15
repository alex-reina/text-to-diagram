"""Console entry point that shells out to the Streamlit UI."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Sequence


def main(argv: Sequence[str] | None = None) -> int:
    """Invoke `streamlit run streamlit_app.py` with optional passthrough args."""

    project_root = Path(__file__).resolve().parent.parent
    app_path = project_root / "streamlit_app.py"
    cmd = ["streamlit", "run", str(app_path)]
    if argv:
        cmd.extend(argv)
    try:
        return subprocess.call(cmd)
    except FileNotFoundError as exc:  # streamlit CLI missing
        print(f"Failed to invoke Streamlit: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
