from src.mbulak_tools.events import exit_signal
from src.mybootstrap_core_itskovichanton.di import injector

from user_service.app import UserServiceApp


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
