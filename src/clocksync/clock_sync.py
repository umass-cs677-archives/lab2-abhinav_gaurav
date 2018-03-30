import requests
import utils
import time
import json
import threading

class Clock:
  def __init__ (self, time_offset):
    self.current_time_offset = time_offset
    self.delta = 10
    self.rho = 5
    self._is_leader = False
    self.clock_sync_thread = None
    self.servers = None
    self.clock_sync_lock = threading.RLock() #TODO: Use two different locks
    
  def get_current_time_offset (self):
    to_ret = None
    self.clock_sync_lock.acquire ()
    to_ret = self.current_time_offset
    self.clock_sync_lock.release ()
    return to_ret
    
  def get_clock_from_address (self, address):
    ''' Get signed clock offset from given address
    '''
    assert (self.is_leader())
    
    r = requests.get("http://" + address + "/getClock/%d"%(self.get_current_time_offset()))
    obj = utils.check_response_for_failure (r.text)
    return int (obj.clock)
  
  def getClock (self, leaderClock):
    '''Get clock REST endpoint
    '''
    return json.dumps({"response":"success", "clock":str(self.current_time_offset-int(leaderClock))})
  
  def setClock (self, clock):
    '''Set Clock REST endpoint
    '''
    self.clock_sync_lock.acquire ()
    self.current_time_offset -= int(clock)
    self.clock_sync_lock.release ()
    return json.dumps({"response":"success"})
    
  def get_slave_times (self):
    self.slave_times = []
    for addr in self._servers:
      if addr != self.id:
        slave_time = self.get_clock_from_address (addr)
        self.slave_times.append (slave_time)
      
    self.slave_times.append(0)
    average_time = sum(self.slave_times)/len(self.slave_times)
    
    return average_time
    
  def set_slave_times (self, average_time):
    for addr in self._servers:
      if addr != self.id:
        r = requests.get ("http://"+addr + "/setClock/"+str(average_time))
        utils.check_response_for_failure (r.text)
  
  def set_leader (self):
    self._is_leader = True
    self.clock_sync_lock.acquire ()
    if (self.clock_sync_thread == None):
      self.clock_sync_thread = utils.run_thread (self.perform_clock_sync)
    self.clock_sync_lock.release ()
    
  def perform_clock_sync (self):
    while self.is_leader():
      #if (self.servers == None):
      self._servers = ["127.0.0.1:7000","127.0.0.1:7001", "127.0.0.1:7002"]
      self.set_slave_times(self.get_slave_times ())
      time.sleep(self.delta/(2*self.rho))
      print "TODO: Do this periodically?"

  def is_leader (self):
    return self._is_leader
  
  def unset_leader (self):
    self._is_leader = False
    self.clock_sync_lock.acquire ()
    if (self.clock_sync_thread != None):
      self.clock_sync_thread.join ()
      self.clock_sync_thread = None
    self.clock_sync_lock.release ()
