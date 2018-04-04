import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(sys.modules[__name__].__file__)))

import utils
import json
import requests
import time




class FrontEndHTTPServer():
    '''Multi-Threaded Database HTTP Server to handle several client requests
       concurrently.
    '''

    def __init__(self, database_ip, database_port, disp_addr):
        self.database_server_address = utils.create_address(database_ip, database_port)
        self.number_of_clients = 0
        self.disp_addr = disp_addr

    def registerClient(self):
        '''
        A new client has come.
        '''
        self.number_of_clients += 1
        return json.dumps({"response": "success"})

    def unregisterClient(self):
        '''
        Remove client.
        '''
        self.number_of_clients -= 1
        return json.dumps({"response": "success"})

    def get_load(self):
        '''
        Load on this server.
        '''
        return self.number_of_clients

    def getMedalTally(self, teamName):
        r = requests.get(self.database_server_address + \
                         '/query_medal_tally_by_team/' + teamName)
        return r.text

    def incrementMedalTally(self, teamName, medalType, authID):
        self.check_authentication(authID)
        r = requests.get(self.database_server_address + \
                         '/increment_medal_tally/%s/%s/%s/%f' % (teamName,
                                                                 medalType,
                                                                 authID,
                                                                 time.time() + float(self.get_current_time_offset())))
        return r.text

    def getScore(self, eventType):
        r = requests.get(self.database_server_address + \
                         '/query_score_by_game/' + eventType)
        return r.text

    def setScore(self, eventType, romeScore, gaulScore, authID):
        self.check_authentication(authID)
        r = requests.get(self.database_server_address + \
                         '/update_score_by_game/%s/%s/%s/%s/%f' % (eventType, romeScore,
                                                                   gaulScore, authID,
                                                                   time.time() + float(self.get_current_time_offset())))
        return r.text

        # def get_current_time_offset(self):
        #    raise NotImplemented ("FrontEndServer.get_current_time_offset Not Implemented")
