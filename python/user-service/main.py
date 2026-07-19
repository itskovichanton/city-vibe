from src.mbulak_tools.events import exit_signal
from src.mybootstrap_core_itskovichanton.di import injector


def main() -> None:
    app = injector().inject(PaasAdminApp)
    app.run()


def quit(signo, _frame):
    print("Interrupted by %d, shutting down" % signo)
    exit_signal.set()


if __name__ == '__main__':
    import signal

    for sig in ('TERM', 'HUP', 'INT'):
        sig_name = 'SIG' + sig
        if hasattr(signal, sig_name):
            sig = getattr(signal, sig_name)
            if sig:
                signal.signal(sig, quit)
    main()
