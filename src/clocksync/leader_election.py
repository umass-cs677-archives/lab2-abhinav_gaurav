import sys

sys.path.insert(0, "../")

import requests
import time
import config
import utils
import json


class LeaderElection:
    def __init__(self, server_id):
        '''
        :param id: Server Address
        '''
        self.id = server_id
        # TODO: check initialization and Lock needed. Never Decreases!!!
        self.servers = []  # TODO: need to be initialized
        utils.run_thread(self.perpetual_election)

    def get_info(self):
        '''
        To get the information needed to conduct the election.
        :return:
        '''
        self.servers = self.get_all_servers()
        self.idx = self.servers.index(self.id)
        self.next_server = self.servers[(self.idx + 1) % len(self.servers)]

    def perpetual_election(self):
        '''
        Runs on a thread perpetually. Purpose: Start Election.
        :return:
        '''
        while True:  # TODO
            time.sleep(config.ELECTION_SNOOZE)
            if not self.servers:
                self.get_info()
            r = requests.get('http://' + self.disp_addr + '/getLeaderElectionLock')
            obj = utils.check_response_for_failure(r.text)
            if obj.can_lock:
                self.newElection()

    def coordinatorMessage(self, leader_addr):
        '''
        Pass/coordinate the leader across all servers.
        :param leader_addr: The address of the leader.
        :return:
        '''
        if (leader_addr == self.id):
            print "I am the leader", leader_addr
            self.set_leader()
            r = requests.get('http://' + self.disp_addr + '/releaseLeaderElectionLock')
            utils.check_response_for_failure(r.text)
        else:
            self.unset_leader()
            # r = requests.get(self.servers[(self.idx + 1) % len(self.servers)] + '/incrementMedalTally/%s' % (leader_addr))
            # obj = utils.check_response_for_failure(r.text)

    def newElection(self):
        '''
        Start a new leader.
        :return:
        '''
        r = requests.get('http://' + self.next_server + '/passElection/%s/%d' % (self.id, self.get_load()))
        obj = utils.check_response_for_failure(r.text)

    def passElection(self, *args):
        '''
        An API for the first pass in the ring. Every server pushes it's load.
        :param args:
        :return:
        '''
        if not self.servers:
            self.get_info()
        sz = len(args)
        ids = [args[x] for x in range(sz / 2)]
        loads = [int(args[x]) for x in range(sz / 2, sz)]

        if self.id in ids:  # Time to find and elect leader
            minm = min(loads)
            indices = [i for i, x in enumerate(loads) if x == minm]
            subset_ids = [ids[i] for i in indices]
            leader_addr = min(subset_ids)
            self.coordinatorMessage(leader_addr)
        else:  # Pass on the message
            ids.append(self.id)
            loads.append(str(self.get_load()))

            arg = '/'.join(ids) + '/' + '/'.join([str(load) for load in loads])
            r = requests.get('http://' + self.next_server + '/passElection/%s' % (arg))
            obj = utils.check_response_for_failure(r.text)

        return json.dumps({"response": "success"})

    def get_all_servers(self):
        raise NotImplemented("LeaderElection.get_all_servers not implemented")

    def get_load(self):
        raise NotImplemented("LeaderElection.get_load not implemented")
