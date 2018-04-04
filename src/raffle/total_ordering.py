import sys

sys.path.insert(0, "../")

import requests
import time
import config
import utils
import json
import threading
import prwlock

class TotalOrdering:
    def __init__(self, _pid):
        '''
        :param id: Server Address
        '''
        self.servers = []
        self.logical_id = 0
        self.pid = _pid
        self.queue = []
        self.__rwlock = prwlock.RWLock ()
        self.print_mutex = threading.RLock ()
        self.processed_reqs = []
        
    def compute_info(self):
        if self.servers != []:
            return

        self.servers = self.get_all_front_end_servers()
        self.pids = [i for i in range(len(self.servers))]
        self.greater_pids = dict()
        for pid in self.pids:
            cnt = 0
            for gpid in self.pids:
                if gpid > pid:
                    cnt += 1
            self.greater_pids[pid] = cnt

    def multicast_ordering(self):
        '''
        Every request to Front-end server is passed to this method.
        Implements the multicast total ordering.
        :return: ????
        '''                
        with self.__rwlock.writer_lock ():
            self.compute_info()
            # Step 1: set logical timestamp
            msg_id = self.logical_id
            self.logical_id += 1

        print self.servers
        # Step 2: Multicast acknowledgement of message to all front end
        for server in self.servers:
        # call API
            with self.__rwlock.writer_lock ():
                self.logical_id += 1
            s = 'http://' + server + '/multicastMsg/%d/%d/%d' % (self.logical_id, self.pid, msg_id)
            r = utils.run_thread (requests.get, s)
            
    def in_queue(self, msg_id, pid):
        for i in range(len(self.queue)):
                if self.queue[i][0] == int(msg_id) and self.queue[i][1] == int(pid):
                    return i
        return -1
    
    def multicastMsg(self, logical_id, pid, msg_id):
        '''
        API that receives the update message
        :return:
        '''
        
        with self.print_mutex:
            print "recevied multicast message at", self.pid, msg_id, pid, threading.currentThread()
        
        with self.__rwlock.writer_lock ():
            self.logical_id = max(int(logical_id), self.logical_id) + 1
            self.compute_info()
            idx = self.in_queue(msg_id, pid)
            if idx == -1:
                self.queue.append((int(msg_id), int(pid), set()))
            self.queue = sorted(self.queue, key=(lambda x: (x[0], x[1])))
        
        if self.greater_pids[self.pid] == 0:
            #Server with highest PID. Request has been processed and 
            #send ack to all previous PIDs
            for server in self.servers:
                if server != self.pid2server(self.pid):
                    with self.__rwlock.writer_lock ():
                        self.logical_id += 1
                    q = 'http://' + server + '/multicastAck/%d/%d/%d/%s' % (self.logical_id, int(pid), int(msg_id),
                                                                                      self.pid2server(self.pid))
                    r = utils.run_thread (requests.get, q)

        return json.dumps({"response": "success"})

    def multicastAck(self, logical_id, pid, msg_id, server_pid):
        '''

        :param logical_id:
        :param pid:
        :param server_pid:
        :return:
        '''
        idx = -1
        
        is_set_full = False
        with self.__rwlock.writer_lock ():
            self.compute_info()
            idx = self.in_queue(msg_id, pid)
            if idx == -1:
                self.queue.append((int(msg_id), int(pid), set([server_pid])))
            else:
                self.logical_id = max(int(logical_id), self.logical_id) + 1
                self.queue[idx][2].add(server_pid)  # received acknowledgment from server
            
            self.queue = sorted(self.queue, key=(lambda x: (x[0], x[1])))
                
                
            if len(self.queue[0][2]) == self.greater_pids[self.pid]:
                is_set_full = True
                
        if is_set_full:
            for pid in self.pids:
                if pid < self.pid:
                    with self.__rwlock.writer_lock():
                        self.logical_id += 1
                    w = 'http://' + self.pid2server(pid) + '/multicastAck/%d/%d/%d/%s' % (
                        int(self.logical_id), int(pid), int(msg_id), "127.0.0.1:%d" % self.pid2server(self.pid))
                    r = utils.run_thread (requests.get, w)

        return json.dumps({"response": "success"})

    def pid2server(self, pid):
        return '127.0.0.1:%d' % (6000 + pid)

    def get_all_processed_reqs(self):
        with self.__rwlock.writer_lock():
            processed_reqs = [(x[0], x[1]) for x in self.queue]
            self.queue = []
            return processed_reqs
    
    def clearReqQueue(self):
        with self.__rwlock.writer_lock():
            self.queue = []
        return json.dumps({"response":"success"})
        
class Raffle (TotalOrdering):
    def __init__ (self, _pid, raffleLength):
        TotalOrdering.__init__(self, _pid)
        self.__raffleLength = raffleLength
        
    def chooseRaffleWinner(self, rand_winner):
        processed_reqs = self.get_all_processed_reqs()
        all_hundreth_reqs = []
        for i,x in enumerate(processed_reqs):
            if i%self.__raffleLength == 0:
                all_hundreth_reqs += [x]
        if len(all_hundreth_reqs) == 0:
            return json.dumps({"response": "success", "winner":"No Winner Yet"})
            
        idx = int(float(rand_winner)*len(all_hundreth_reqs))
        return json.dumps({"response":"success", "winner":str(all_hundreth_reqs[idx])})
