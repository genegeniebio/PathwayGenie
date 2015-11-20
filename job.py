'''
Created on 20 Nov 2015

@author: neilswainston
'''
from threading import Thread


class JobThread(Thread):
    '''Wraps a job into a thread, and fires events.'''

    def __init__(self):
        Thread.__init__(self)
        self.__listeners = set()

    def add_listener(self, listener):
        '''Adds an event listener.'''
        self.__listeners.add(listener)

    def remove_listener(self, listener):
        '''Removes an event listener.'''
        self.__listeners.remove(listener)

    def run(self):
        self.__do_job()

    def __do_job(self):
        '''Performs the task. Should be overridden.'''
        import time

        progress = 0

        while progress < 100:
            time.sleep(1)
            self._fire_event(progress)
            progress += 1

        return 'Done!!'

    def _fire_event(self, event):
        '''Fires an event to event listeners.'''
        for listener in self.__listeners:
            listener.event_fired(event)
