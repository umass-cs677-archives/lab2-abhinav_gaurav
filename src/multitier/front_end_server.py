import sys
sys.path.insert (0, "../")

import utils
import json
import requests
import multi_thread_server


class FrontEndHTTPServer(multi_thread_server.MultiThreadedHTTPServer):
    '''Multi-Threaded Database HTTP Server to handle several client requests
       concurrently.
    '''
    def __init__(self, server_address, handler_class, database_ip, database_port):
        multi_thread_server.MultiThreadedHTTPServer.__init__(self, server_address, handler_class)
        self.database_server_address = utils.create_address (database_ip, database_port)
        self.number_of_clients = 0
    
    def registerClient(self):
        self.number_of_clients += 1
        return json.dumps({"response":"failure"})
    
    def unregisterClient(self):
        self.number_of_clients -= 1
        return json.dumps({"response":"success"})
        
    def getMedalTally(self, teamName):
        r = requests.get(self.database_server_address + \
                         '/query_medal_tally_by_team/' + teamName)
        return r.text
    
    def incrementMedalTally(self, teamName, medalType, authID):
        self.check_authentication (authID)
        r = requests.get(self.database_server_address + \
                         '/increment_medal_tally/%s/%s/%s'%(teamName, 
                                                          medalType, 
                                                          authID))
        return r.text
        
    def getScore(self, eventType):
        r = requests.get(self.database_server_address + \
                         '/query_score_by_game/' + eventType)
        return r.text
        
    def setScore(self, eventType, romeScore, gaulScore, authID):
        self.check_authentication (authID)
        r = requests.get(self.database_server_address + \
                         '/update_score_by_game/%s/%s/%s/%s'%(eventType, romeScore, 
                                                  gaulScore, authID))
        return r.text
