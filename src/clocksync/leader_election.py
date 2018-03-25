import requests
import time

import config
import utils

class LeaderElection():
    def __init__(self, id, servers):
        '''
        :param id: Server Address
        '''
        self.id = id
        self.load = 0               # TODO: check initialization and Lock needed. Never Decreases!!!
        self.servers = servers      # TODO: need to be initialized
        self.idx = servers.index(id)

    def perpetual_election(self):
        '''
        Runs on a thread perpetually. Purpose: Start Election.
        :return:
        '''
        while True:
            time.sleep(config.ELECTION_SNOOZE)
            self.newElection()

    def coordinatorMessage(self, leader_addr):
        print "I am the leader", leader_addr
        # r = requests.get(self.servers[(self.idx + 1) % len(self.servers)] + '/incrementMedalTally/%s' % (leader_addr))
        # obj = utils.check_response_for_failure(r.text)

    def newElection(self):
        r = requests.get( + '/passElection/%s/%s' % (self.id, self.load))
        obj = utils.check_response_for_failure(r.text)

    def passElection(self, *args):
        '''
        An API for the first pass in the ring. Every server pushes it's load.
        :param args:
        :return:
        '''
        sz = len(*args)
        ids = [x for x in range(sz/2)]
        loads = [x for x in range(sz/2, l)]

        if self.id in ids:              # Time to elect leader
            leader_idx = loads.index(min(loads))
            self.coordinatorMessage(leader_addr=self.servers[leader_idx])
        else:                           # Pass on the message
            ids.append(self.id)
            loads.append(self.load)

            arg = '/'.join(ids) + '/'.join(loads)
            r = requests.get(self.servers[(self.idx + 1)%len(self.servers)] + '/incrementMedalTally/%s' % (arg))
            obj = utils.check_response_for_failure(r.text)

    def incrementLoad(self):
        '''
        Dispatcher will update load on this server.
        :return: Success
        '''
        self.load += 1