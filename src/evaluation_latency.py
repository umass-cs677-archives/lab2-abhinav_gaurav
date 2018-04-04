import commands
import threading
import sys
import re


class EvaluationThread(threading.Thread):
    def __init__(self, func, *args):
        threading.Thread.__init__(self)
        self.func = func
        self.args = args

    def run(self):
        self.retval = self.func(*self.args)


def run_thread(func, *_args):
    t = EvaluationThread(func, *_args)
    t.start()
    return t


def run_command(command):
    return run_thread(commands.getoutput, command)


n_clients = int(sys.argv[1])
n_requests = 100

client_type = "pull"
if (client_type == "pull"):
    clients_process = []
    for i in range(0, n_clients):
        clients_process.append(
            run_command(
                "python client_pull.py --dispatcher_ip_addr 127.0.0.1 --dispatcher_port 5000 --num_requests %d" % (
                n_requests)))

    print "Clients Data:"
    times = {"getScore": 0, "getMedalTally": 0}
    for p in clients_process:
        p.join()
        print p.retval
        times["getScore"] += float(re.findall(r'each getScore.+?(\d*\.\d+|\d)+', p.retval)[0])
        times["getMedalTally"] += float(re.findall(r'each getMedalTally.+?(\d*\.\d+|\d)+', p.retval)[0])

    print "Average Time taken to process getScore request", times["getScore"] / n_clients, "sec"
    print "Average Time taken to process getMedalTally request", times["getMedalTally"] / n_clients, "sec"
