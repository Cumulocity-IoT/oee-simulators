import logging

from random import randint
from datetime import datetime

log = logging.getLogger("task")

class Task:
    def __init__(self, start_in_seconds: int, run_block) -> None:
        self.extra = {}
        self.run_block = run_block
        self.next_run = datetime.timestamp(datetime.utcnow()) + start_in_seconds
    
    def tick(self):
        if (datetime.timestamp(datetime.utcnow()) - self.next_run) > 0:
            self.run_block(self)

class PeriodicTask:
    def __init__(self, minInterval: int, maxInterval: int, run_block) -> None:
        self.run_block = run_block
        self.min_interval_in_seconds = minInterval
        self.max_interval_in_seconds = maxInterval
        self.next_run = self.__calculate_next_run()
     
    def __calculate_next_run(self) -> int: 
        return datetime.timestamp(datetime.utcnow()) + randint(self.min_interval_in_seconds, self.max_interval_in_seconds)
    
    def __reschedule_and_run(self):
        duration = self.run_block(self)
        duration = duration.pop() or 0  # Why is duration a set?
        self.next_run = self.__calculate_next_run() + duration
        log.debug(f"Reschedule next run and wait for additional {duration} seconds. Next run is at {datetime.fromtimestamp(self.next_run).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")

    def tick(self):
        if (datetime.timestamp(datetime.utcnow()) - self.next_run) > 0:
            self.__reschedule_and_run()    
