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
        # TODO: check initialization and Lock needed. Never Decreases!!!
        self.servers = []  # TODO: need to be initialized

        self.logical_id = 0
        self.pid = _pid
        self.queue = []
        self.__rwlock = prwlock.RWLock ()
        self.print_mutex = threading.RLock ()
        self.processed_reqs = []
        self.cv = threading.Condition ()
        
    def compute_info(self):
        if self.servers != []:
            return

        self.servers = self.get_all_front_end_servers()
        self.pids = [0, 1]  # TODO: self.get_all_pids()
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
        #print "multicase_ordering of server ", self.pid2server(self.pid), threading.currentThread ()        
        with self.__rwlock.writer_lock ():
            self.compute_info()
            # Step 1: set logical timestamp
            msg_id = self.logical_id
            #self.queue.append((int(msg_id), int(self.pid), set()))
            #sorted(self.queue, key=(lambda x: (x[0], x[1])))
            self.logical_id += 1

        print self.servers
        # Step 2: Multicast acknowledgement of message to all front end
        for server in self.servers:
        # call API       # TODO the server itself receives so greater_pids should have count + 1
            #print "sending multicastMsg to ", server, self.logical_id, self.pid
            with self.__rwlock.writer_lock ():
                self.logical_id += 1
            s = 'http://' + server + '/multicastMsg/%d/%d/%d' % (self.logical_id, self.pid, msg_id)
            r = utils.run_thread (requests.get, s)
            #utils.check_response_for_failure(r.text)
        
    def in_queue(self, msg_id, pid):
        for i in range(len(self.queue)):
                if self.queue[i][0] == int(msg_id) and self.queue[i][1] == int(pid):
                    return i
        return -1
    
    def in_list(self, l, msg_id, pid):
        for i in range(len(l)):
                if l[i][0] == int(msg_id) and l[i][1] == int(pid):
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
            # Step 3: Insert in local queue the message that is received
            idx = self.in_queue(msg_id, pid)
            if idx == -1 and self.in_list(self.processed_reqs, msg_id, pid) == -1:
                self.queue.append((int(msg_id), int(pid), set()))
            self.queue = sorted(self.queue, key=(lambda x: (x[0], x[1])))
        
            #with self.print_mutex:
            #    print "Pid", self.pid, "Queue", self.queue, "greater_pids", self.greater_pids
        
        # Step 4: Message delivered check if head is acknowledged by all
            #if self.greater_pids[self.pid] == 0:  ## I am the biggest server
            #    self.processed_reqs.append (self.queue.pop(0))
        
        if self.greater_pids[self.pid] == 0:
            # Step 5: Send Acknowledgement
            with self.print_mutex:
                print "PID", self.pid, "servers:", self.servers
            for server in self.servers:
                if server != self.pid2server(self.pid):
                    with self.__rwlock.writer_lock ():
                        self.logical_id += 1
                    q = 'http://' + server + '/multicastAck/%d/%d/%d/%s' % (self.logical_id, int(pid), int(msg_id),
                                                                                      "127.0.0.1:%d" % (
                                                                                          6000 + self.pid))
                    r = utils.run_thread (requests.get, q)  # TODO: Change this pid to server conversion

        return json.dumps({"response": "success"})

    def multicastAck(self, logical_id, pid, msg_id, server_pid):
        '''

        :param logical_id:
        :param pid:
        :param server_pid:
        :return:
        '''

        with self.print_mutex:
            print "muticastAck (%s, %s, %s, %s)"%(logical_id, msg_id, pid, server_pid), " at ", self.pid
        idx = -1
        
        is_set_full = False
        with self.__rwlock.writer_lock ():
            self.compute_info()
            idx = self.in_queue(msg_id, pid)
            if idx == -1:
                # Step 3: Insert in local queue the message that is received
                self.queue.append((int(msg_id), int(pid), set([server_pid])))
            else:
                self.logical_id = max(int(logical_id), self.logical_id) + 1
                self.queue[idx][2].add(server_pid)  # received acknowledgment from server
            
            self.queue = sorted(self.queue, key=(lambda x: (x[0], x[1])))
                
            with self.print_mutex:
                print "queue for pid ", self.pid, self.queue
                
            #if len(self.queue[0][2]) == self.greater_pids[self.pid]:
            #    e = self.queue.pop(0)
            #    self.processed_reqs.append (e)
            #    msg_id, pid, _ = e
                is_set_full = True
                
        with self.print_mutex:
            print "POPPED ELEMENTS FOR ", self.pid, "WWW", self.processed_reqs
            
        if is_set_full:
            for pid in self.pids:
                if pid < self.pid:
                    with self.__rwlock.writer_lock():
                        self.logical_id += 1
                    w = 'http://' + self.pid2server(pid) + '/multicastAck/%d/%d/%d/%s' % (
                        int(self.logical_id), int(pid), int(msg_id), "127.0.0.1:%d" % (
                            6000 + self.pid))
                    
                    r = utils.run_thread (requests.get, w)  # TODO create dictionary pid2server

        return json.dumps({"response": "success"})

    def pid2server(self, pid):
        return '127.0.0.1:%d' % (6000 + pid)

    def get_all_processed_reqs(self):
        with self.__rwlock.writer_lock():
            self.processed_reqs = [(x[0], x[1]) for x in self.queue]
            self.queue = []
            
        return self.processed_reqs
