"""
Точка входа user-service.

Запуск:
  python main.py
  (из каталога python/user-service или через IntelliJ Run Configuration)
"""

from __future__ import annotations

import sys
from pathlib import Path


def _bootstrap_sys_path() -> None:
    """
    Добавляет в sys.path корень монорепо и src сервиса.

    Нужно, чтобы работали импорты:
      - user_service.*          (python/user-service/src)
      - python.libs.*           (корень репозитория)
    Фреймворк mybootstrap_* уже лежит в site-packages/src.
    """
    service_dir = Path(__file__).resolve().parent          # .../python/user-service
    repo_root = service_dir.parents[1]                     # .../city-vibe
    service_src = service_dir / "src"                      # .../python/user-service/src

    for path in (repo_root, service_src):
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)


_bootstrap_sys_path()

from src.mbulak_tools.events import exit_signal  # noqa: E402
from src.mybootstrap_core_itskovichanton.di import injector  # noqa: E402

from user_service.app import UserServiceApp  # noqa: E402


def main() -> None:
    app = injector().inject(UserServiceApp)
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
