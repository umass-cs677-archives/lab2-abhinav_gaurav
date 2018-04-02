import sys

sys.path.insert(0, "../")

import requests
import time
import config
import utils
import json


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
        
    def compute_info(self):
        if self.servers != []:
            return
        
        self.servers = self.get_all_front_end_servers()
        self.pids = [0]#TODO: self.get_all_pids()
        self.greater_pids = dict()
        for pid in self.pids:
            cnt = 0
            for gpid in self.pids:
                if gpid >= pid:
                    cnt += 1
            self.greater_pids[pid] = cnt

    def multicast_ordering(self):
        '''
        Every request to Front-end server is passed to this method.
        Implements the multicast total ordering.
        :return: ????
        '''
        print "multicase_ordering"
        self.compute_info ()
        #Step 1: set logical timestamp
        self.logical_id += 1
        
        print self.servers
        #Step 2: Multicast it to all front end
        for server in self.servers:
            #call API       # TODO the server itself receives so greater_pids should have count + 1
            r = requests.get('http://' + server + '/multicastMsg/%d/%d' % (self.logical_id, self.pid))
            print r.text
            utils.check_response_for_failure(r.text)


    def multicastMsg(self, logical_id, pid):
        '''
        API that receives the update message
        :return:
        '''
        #Step 3: Insert in local queue the message that is received
        self.queue.append((int(logical_id), int(pid), set()))
        sorted(self.queue)

        #Step 4: Message delivered
        # check if head is acknowledged by all
        head = self.queue[0]
        head_id, head_pid, head_set = head
        if self.greater_pids[self.pid] == 1:    ## I am the biggest server
            #self.queue.pop(0)   #TODO
            self.send_acknowledgement(logical_id, pid)
            
        return json.dumps({"response":"success"})
        
    def multicastAck(self, logical_id, pid, server_pid):
        '''

        :param logical_id:
        :param pid:
        :param server_pid:
        :return:
        '''

        idx = -1
        for i in range (len(self.queue)):
            if self.queue[i][0] == int(logical_id) and self.queue[i][1] == int(pid):
               idx = i
               break
        
        print "index", idx, logical_id, pid
        print self.queue
        elem = self.queue[idx]
        elem_id, elem_pid, elem_set = elem

        elem_set.add(server_pid)    # received acknowledgment from server
        print "Greater pids", self.greater_pids
        if len(elem_set) == self.greater_pids[int(pid)]:
            for pid in self.pids:
                if pid <= self.pid:
                    r = requests.get('http://' + self.pid2server(pid) + '/receiveMulticastAck/%d/%d' % (int(logical_id), int(pid)))     # TODO create dictionary pid2server
        
        return json.dumps({"response":"success"})
        
    def receiveMulticastAck(self, logical_id, pid):
        '''

        :param logical_id:
        :param pid:
        :return:
        '''
        self.queue.pop(0)
        self.send_acknowledgement(int(logical_id), int(pid))
        return json.dumps({"response":"success"})
        
    def pid2server(self, pid):
        return '127.0.0.1:%d'%(6000+pid)
        
    def send_acknowledgement(self, logical_id, pid):
        #Step 5: Send Acknowledgement
        for server in self.servers:
            r = requests.get('http://' + server + '/multicastAck/%d/%d/%s' % (int(logical_id), int(pid), "127.0.0.1:%d"%(6000+self.pid))) #TODO: Change this pid to server conversion
