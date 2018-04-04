import threading


def run_thread(func, *_args):
    t = threading.Thread(target=func, args=_args)
    t.start()
    return t
