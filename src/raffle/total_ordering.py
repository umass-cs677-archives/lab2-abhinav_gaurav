import sys

sys.path.insert(0, "../")

import requests
import time
import config
import utils
import json
import threading

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
        self.__mutex = threading.RLock()

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
        print "multicase_ordering"
        self.__mutex.acquire ()
        self.compute_info()
        # Step 1: set logical timestamp
        self.logical_id += 1  # TODO: take max this is a bug
        msg_id = self.logical_id
        self.__mutex.release ()

        print self.servers
        # Step 2: Multicast acknowledgement of message to all front end
        for server in self.servers:
            # call API       # TODO the server itself receives so greater_pids should have count + 1
            print "sending multicastMsg to ", server, self.logical_id, self.pid
            self.__mutex.acquire()
            self.logical_id += 1
            self.__mutex.release()
            r = requests.get('http://' + server + '/multicastMsg/%d/%d/%d' % (self.logical_id, self.pid, msg_id))
            print r.text
            utils.check_response_for_failure(r.text)

    def multicastMsg(self, logical_id, pid, msg_id):
        '''
        API that receives the update message
        :return:
        '''
        print "recevied multicast message at", self.pid, msg_id, pid, threading.currentThread()
        self.__mutex.acquire ()
        self.logical_id = max(int(logical_id), self.logical_id)+1
        self.compute_info()
        # Step 3: Insert in local queue the message that is received
        self.queue.append((int(msg_id), int(pid), set()))
        sorted(self.queue, key=(lambda x: (x[0], x[1])))

        # Step 4: Message delivered check if head is acknowledged by all
        self.__mutex.release()

        if self.greater_pids[self.pid] == 0:  ## I am the biggest server
            self.__mutex.acquire()
            print "###############################", self.pid, self.queue
            self.queue.pop(0)  # TODO
            self.__mutex.release()
            # Step 5: Send Acknowledgement
            for server in self.servers:
                if server != self.pid2server(self.pid):
                    self.__mutex.acquire()
                    self.logical_id += 1
                    self.__mutex.release()
                    r = requests.get('http://' + server + '/multicastAck/%d/%d/%d/%s' % (self.logical_id, int(pid), int(msg_id),
                                                                                      "127.0.0.1:%d" % (
                                                                                          6000 + self.pid)))  # TODO: Change this pid to server conversion

        return json.dumps({"response": "success"})

    def multicastAck(self, logical_id, pid, msg_id, server_pid):
        '''

        :param logical_id:
        :param pid:
        :param server_pid:
        :return:
        '''


        idx = -1
        #while idx == -1:
        #self.__mutex.acquire()
        #tie.sleep(1)
        for i in range(len(self.queue)):
            if self.queue[i][0] == int(msg_id) and self.queue[i][1] == int(pid):
                idx = i
                break
        #self.__mutex.release()

        # if (idx == -1):
        #     utils.run_thread (requests.get, 'http://' + self.pid2server(int(pid)) + '/multicastAck/%d/%d/%d/%s' % (int(logical_id), int(pid), int(msg_id), self.pid2server(int(pid))))
        #     return

        print "#############index", idx, msg_id, pid, self.pid, threading.currentThread()
        self.__mutex.acquire()
        self.logical_id = max(int(logical_id), self.logical_id) + 1
        self.__mutex.release()
        print self.pid, self.queue
        elem = self.queue[idx]
        elem_id, elem_pid, elem_set = elem
        elem_set.add(server_pid)  # received acknowledgment from server
        #self.__mutex.release ()
        print "Greater pids", self.greater_pids
        if len(self.queue[0][2]) == self.greater_pids[self.pid]:
            self.__mutex.acquire()
            self.queue.pop(0)
            self.__mutex.release()
            for pid in self.pids:
                if pid < self.pid:
                    self.__mutex.acquire()
                    self.logical_id += 1
                    self.__mutex.release()
                    r = requests.get('http://' + self.pid2server(pid) + '/multicastAck/%d/%d/%d/%s' % (
                        int(self.logical_id), int(pid), int(msg_id), "127.0.0.1:%d" % (
                            6000 + self.pid)))  # TODO create dictionary pid2server

        return json.dumps({"response": "success"})

    def pid2server(self, pid):
        return '127.0.0.1:%d' % (6000 + pid)
