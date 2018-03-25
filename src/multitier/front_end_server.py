import requests
import server

class FrontEndHTTPServer(server.MultiThreadedHTTPServer):
    '''Multi-Threaded Database HTTP Server to handle several client requests
       concurrently.
    '''
    def __init__(self, *args, **kwargs):
        MultiThreadedHTTPServer.__init__(self, *args, **kwargs)
        self.database_server_address = ""

    def getMedalTally(self, teamName):
        r = requests.get(self.database_server_address + \
                         '/getMedalTally/' + eventType)
        return r.text
    
    def incrementMedalTally(self, teamName, medalType, authID):
        self.check_authentication (authID)
        r = requests.get(self.database_server_address + \
                         '/incrementMedalTally/%s/%s/%s'%(teamName, 
                                                          medalType, 
                                                          authID))
        return r.text
        
    def getScore(self, eventType):
        r = requests.get(self.database_server_address + \
                         '/getScore/' + eventType)
        return r.text
        
    def setScore(self, eventType, romeScore, gaulScore, authID):
        self.check_authentication (authID)
        r = requests.get(self.database_server_address + \
                         '/setScore/%s/%s/%s/%s'%(eventType, romeScore, 
                                                  gaulScore, authID))
        return r.text
