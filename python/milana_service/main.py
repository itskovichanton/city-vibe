"""Точка входа milana-service — NL→places/search агент (DeepSeek)."""

from __future__ import annotations

import sys
from pathlib import Path


def _bootstrap_sys_path() -> None:
    service_dir = Path(__file__).resolve().parent
    repo_root = service_dir.parents[1]
    service_src = service_dir / "src"
    for path in (repo_root, service_src):
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)


_bootstrap_sys_path()

from src.mbulak_tools.events import exit_signal  # noqa: E402
from src.mybootstrap_core_itskovichanton.di import injector  # noqa: E402

from python.milana_service.src.milana_service.app import MilanaServiceApp  # noqa: E402


def main() -> None:
    app = injector().inject(MilanaServiceApp)
    app.run()


def quit_handler(signo, _frame):
    print("Interrupted by %d, shutting down" % signo)
    exit_signal.set()


if __name__ == "__main__":
    import signal

    for sig in ("TERM", "HUP", "INT"):
        sig_name = "SIG" + sig
        if hasattr(signal, sig_name):
            sig_obj = getattr(signal, sig_name)
            if sig_obj:
                signal.signal(sig_obj, quit_handler)
    main()
