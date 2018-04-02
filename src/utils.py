import json
from collections import namedtuple
import time
import threading

games = ['Luge', 'Stone Curling', 'Stone Skating']
teams = ['Gaul', 'Rome']
medals = ["Bronze", "Silver", "Gold"]

team_idx = dict(zip(teams, range(len(teams))))
game_idx = dict(zip(games, range(len(games))))


def json_to_object(json_str):
    """Parse JSON into an object with attributes corresponding to dict keys."""
    x = json.loads(json_str,
                   object_hook=lambda d: namedtuple('X', d.keys())(*d.values()))
    return x


def check_response_for_failure(r):
    obj = json_to_object(r)
    if obj.response == "failure":
        raise Exception("Request Failed. Reason '%s'" % obj.message)

    return obj


def timeit(func, *args, **kwargs):
    t1 = time.clock()
    ret = func(*args, **kwargs)
    t2 = time.clock()
    return (t2 - t1), ret


def create_address(ip, port):
    return "http://" + str(ip) + ":" + str(port)

def run_thread(func, *_args):
    t = threading.Thread(target=func, args=_args)
    t.start()
    return t
