'''
Created on 20 Nov 2015

@author: neilswainston
'''
from threading import Thread


class JobThread(Thread):
    '''Wraps a job into a thread, and fires events.'''

    def __init__(self, job_id):
        Thread.__init__(self)
        self.__job_id = job_id
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
            evt = Event(self.__job_id, progress)
            self._fire_event(evt)
            progress += 1

        return 'Done!!'

    def _fire_event(self, event):
        '''Fires an event to event listeners.'''
        for listener in self.__listeners:
            listener.event_fired(event)


class Event(object):
    '''Class to represent a simple event.'''

    def __init__(self, job_id, progress, value=None):
        self.__job_id = job_id
        self.__progress = progress
        self.__value = value

    def get_job_id(self):
        '''Gets job id.'''
        return self.__job_id

    def get_progress(self):
        '''Gets progress.'''
        return self.__progress

    def get_value(self):
        '''Gets value.'''
        return self.__value
