import subprocess
import sys
from pathlib import Path


def main() -> None:
    try:
        app = Path(__file__).resolve().parent / "IH_Benchmark.py"
        cmd = [sys.executable, "-m", "streamlit", "run", str(app), *sys.argv[1:]]
        raise SystemExit(subprocess.call(cmd))
    except KeyboardInterrupt:
        return


if __name__ == "__main__":
    main()
