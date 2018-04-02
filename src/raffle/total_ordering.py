import sys

sys.path.insert(0, "../")

import requests
import time
import config
import utils
import json


class TotalOrdering:
    def __init__(self, server_id, _pid):
        '''
        :param id: Server Address
        '''
        self.id = server_id
        # TODO: check initialization and Lock needed. Never Decreases!!!
        self.servers = []  # TODO: need to be initialized

        self.logical_id = 0
        self.pid = _pid
        self.queue = []


    def compute_info(self):
        self.servers = self.get_all_servers()
        self.pids = self.get_all_pids()
        self.idx = self.servers.index(self.id)
        self.greater_pids = dict()
        for pid in self.pids:
            cnt = 0
            for gpid in self.pids:
                if gpid >= pid:
                    cnt += 1
            self.greater_pids[pid] = cnt


    def multicast_ordering(self, *args):
        '''
        Every request to Front-end server is passed to this method.
        Implements the multicast total ordering.
        :return: ????
        '''

        #Step 1: set logical timestamp
        self.logical_id += 1

        #Step 2: Multicast it to all front end
        for server in self.servers:
            #call API       # TODO the server itself receives so greater_pids should have count + 1
            r = requests.get('http://' + server + '/multicastMsg/%d/%d' % (self.logical_id, self.pid))
            utils.check_response_for_failure(r.text)


    def multicastMsg(self, logical_id, pid):
        '''
        API that receives the update message
        :return:
        '''
        #Step 3: Insert in local queue the message that is received
        self.queue.append((logical_id, pid, set()))
        sorted(self.queue)

        #Step 4: Message delivered
        # check if head is acknowledged by all
        head = self.queue[0]
        head_id, head_pid, head_set = head
        if self.greater_pids[self.pid] == 1:    ## I am the biggest server
            self.queue.pop(0)   #TODO
            self.send_acknowledgement(logical_id, pid)


    def multicastAck(self, logical_id, pid, server_pid):
        '''

        :param logical_id:
        :param pid:
        :param server_pid:
        :return:
        '''

        idx = self.queue.index(logical_id, pid)   # TODO make key
        elem = self.queue[idx]
        elem_id, elem_pid, elem_set = elem

        elem_set.add(server_pid)    # received acknowledgment from server

        if len(elem_set) == self.greater_pids[pid]:
            for pid in self.pids:
                if pid < self.pid:
                    r = requests.get('http://' + self.pid2server + '/receiveMulticastAck/%d/%d' % (logical_id, pid)))     # TODO create dictionary pid2server

    def receiveMulticastAck(self, logical_id, pid):
        '''

        :param logical_id:
        :param pid:
        :return:
        '''
        self.queue.pop(0)
        self.send_acknowledgement(logical_id, pid)


    def send_acknowledgement(self, logical_id, pid):
        #Step 5: Send Acknowledgement
        for server in self.servers:
            r = requests.get('http://' + server + '/multicastAck/%d/%d' % (logical_id, pid))
