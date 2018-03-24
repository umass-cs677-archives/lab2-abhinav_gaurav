import threading
from ..src.server import create_server

def run_thread(func, *_args):
    t = threading.Thread(target=func, args=_args)
    t.start()
    return t
