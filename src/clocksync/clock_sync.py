import requests
import utils

class Clock:
  def __init__ (self, time_offset, slave_addresses):
    self.current_time_offset = time_offset
    
  def get_current_time_offset (self):
    return self.current_time_offset
  
  def get_clock_from_address (self, address):
    ''' Get signed clock offset from given address
    '''
    r = requests.get(address +"/getClock")
    obj = utils.check_response_for_failure (r.text)
    return int (obj.clock)
  
  def getClock (self, leaderClock):
    '''Get clock REST endpoint
    '''
    return json.dump({"response":"success", "clock":str(self.current_time_offset-leaderClock)}
  
  def setClock (self, clock):
    '''Set Clock REST endpoint
    '''
    print "TODO: See if this should be + or -"
    self.current_time_offset -= int(clock)
    return json.dump({"response":"success"})
    
class LeaderClock (Clock):
  def __init__ (self, time_offset, slave_addresses):
    LeaderClock.__init__ (time_offset)
    self.slave_addresses = slave_addresses
  
  def get_slave_times (self):
    self.slave_times = []
    for addr in self.slave_addresses:
      slave_time = self.get_clock_from_address (addr)
      self.slave_times.append (slave_time)
    
    self.slave_times.append(0)
    average_time = (sum(self.slave_times)/len(self.slave_times)
    
    return average_time
    
  def set_slave_times (self, average_time):
    for addr in self.slave_addresses:
      r = requests.get (addr + "/setClock/"+str(average_time))
      utils.check_response_for_failure (r.text)
    
    print "All slaves changed with offset ", average_time

  def perform_clock_sync (self):
    self.set_slave_times (self.get_slave_times ())
    print "TODO: Do this periodically?"
    
class SlaveClock (Clock):
  def __init__ (self, time_offset, leader_address):
    LeaderClock.__init__ (time_offset)
