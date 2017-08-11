#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# (c) 2017, Jose Riguera

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from datetime import datetime

from ansible.plugins.callback.default import CallbackModule as CallbackModuleDefault
from ansible.utils.display import Display

class StderrDisplay(Display):

    def display(self, msg, *args, **kwargs):
        # Everything is displayed on stderr
        return super(StderrDisplay, self).display(msg, stderr=True, *args, **kwargs)



class CallbackModule(CallbackModuleDefault):
    '''
    This is the concourse callback plugin, which reuses the default
    callback plugin but sends output to stderr.
    '''
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'concourse'

    def __init__(self):
        super(CallbackModule, self).__init__()
        self._display = StderrDisplay()
        self.start_time = datetime.now()

    def _human_runtime(self, runtime):
        minutes = (runtime.seconds // 60) % 60
        r_seconds = runtime.seconds - (minutes * 60)
        return runtime.days, runtime.seconds // 3600, minutes, r_seconds

    def v2_playbook_on_stats(self, stats):
        super(CallbackModule, self).v2_playbook_on_stats(stats)
        end_time = datetime.now()
        runtime = end_time - self.start_time
        self._display.display("Runtime: %s days, %s hours, %s minutes, %s seconds" % (self._human_runtime(runtime)))
 
