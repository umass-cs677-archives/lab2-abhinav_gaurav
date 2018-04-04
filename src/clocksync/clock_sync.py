import requests
import utils
import time
import json
import threading
import config

class Clock:
    def __init__(self, time_offset, server_id):
        self.current_time_offset = time_offset
        self.delta = config.DELTA
        self.rho = config.RHO
        self._is_leader = False
        self.clock_sync_thread = None
        self.server_addresses = None
        self.clock_sync_lock = threading.RLock()
        self.__thread_lock = threading.RLock()
        self.__server_id = server_id
        
    def set_current_time_offset(self, offset):
        self.clock_sync_lock.acquire()
        self.current_time_offset = offset
        self.clock_sync_lock.release()
        
    def get_current_time_offset(self):
        to_ret = None
        self.clock_sync_lock.acquire()
        to_ret = self.current_time_offset
        self.clock_sync_lock.release()
        return to_ret

    def get_clock_from_address(self, address):
        ''' Get signed clock offset from given address
        '''
        assert (self.is_leader())

        r = requests.get("http://" + address + "/getClock/%d" % (self.get_current_time_offset()))
        obj = utils.check_response_for_failure(r.text)
        return int(obj.clock)

    def getClock(self, leaderClock):
        '''Get clock REST endpoint
        '''
        return json.dumps({"response": "success", "clock": str(self.current_time_offset - int(leaderClock))})

    def setClock(self, clock):
        '''Set Clock REST endpoint
        '''
        self.clock_sync_lock.acquire()
        self.current_time_offset = int(clock) - self.current_time_offset
        print "Setting new time offset of", self.__server_id, " = ", self.current_time_offset, "changing offset with = ", clock
        self.clock_sync_lock.release()
        return json.dumps({"response": "success"})

    def get_slave_times(self):
        '''
        Return the average time of the slaves.
        :return:
        '''
        self.slave_times = []
        for addr in self.server_addresses:
            if addr != self.__server_id:
                slave_time = self.get_clock_from_address(addr)
                self.slave_times.append(slave_time)

        self.slave_times.append(0)
        average_time = sum(self.slave_times) / len(self.slave_times)

        return average_time

    def set_slave_times(self, average_time):
        '''
        Set the time of the slaves.
        :param average_time:
        :return:
        '''
        for addr in self.server_addresses:
                r = requests.get("http://" + addr + "/setClock/" + str(average_time))
                utils.check_response_for_failure(r.text)

        print "All slaves changed with offset", average_time

    def set_leader(self, start_clock_sync=True):
        '''
        Set the clock to be master clock.
        :return:
        '''
        self._is_leader = True
        if start_clock_sync:
            self.__thread_lock.acquire()
            if self.clock_sync_thread is None:
                self.clock_sync_thread = utils.run_thread(self.perform_clock_sync)
            self.__thread_lock.release()

    def perform_clock_sync_func (self):
        if self.server_addresses is None:
            self.server_addresses = self.get_all_servers()
        self.set_slave_times(self.get_slave_times())
        time.sleep(self.delta / (2 * self.rho))
        
    def perform_clock_sync(self):
        '''
        Perform Berkley clock synchronization.
        :return:
        '''
        while self.is_leader():
            self.perform_clock_sync_func ()
  
    def end_clock_sync(self):
        self._is_leader = False
        if (self.clock_sync_thread):
          self.clock_sync_thread.join()
        
    def is_leader(self):
        return self._is_leader

    def get_all_servers(self):
        raise NotImplemented("Clock.get_all_servers not implemented")

    def unset_leader(self):
        '''
        To give up leadership voluntarily
        :return:
        '''
        self._is_leader = False
        self.__thread_lock.acquire()
        if self.clock_sync_thread is not None:
            self.clock_sync_thread.join()
            self.clock_sync_thread = None
        self.__thread_lock.release()
