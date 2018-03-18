#!/usr/bin/python
# -*- coding: utf-8 -*-

# Standard Library Imports
import datetime
import glob
import os
import stat
import subprocess

# Global Variables
DIR_PERMS = stat.S_ISGID | stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH

def get_log_ts():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[0:23]

def get_log_datetime():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def get_log_date():
    return datetime.datetime.today().strftime('%Y%m%d')

def print_write(f, text = ''):
    print text
    f.write(text + '\n')

class Screen:
    """Screen class"""
    
    def __init__(self, user, session):
        self.session    = session
        self.session_id = Screen.get_session_id(user, session)
        self.term       = os.getenv('TERM')
        self.sty        = os.getenv('STY')
    
    def start(self, cmd_args):
        screen_args = ['screen', '-d', '-m', '-S', self.session] + cmd_args
        return subprocess.call(screen_args)
    
    def stop(self):
        return subprocess.call(['screen', '-X', '-S', self.session_id, 'quit'])
    
    def attach(self):
        return subprocess.call(['screen', '-rd', self.session_id])
    
    def list(self, stdout_arg = None, stderr_arg = None):
        stdout = stdout_arg if stdout_arg != None else open(os.devnull, 'rw')
        stderr = stderr_arg if stderr_arg != None else open(os.devnull, 'rw')
        
        return subprocess.call(['screen', '-ls', self.session_id], stdout = stdout, stderr = stderr)
    
    def is_running(self):
        if (self.session_id is None):
            return False
        
        rc = self.list()
        return True if rc == 0 else False
    
    def is_running_inside_screen(self):
        return (self.term != None) and (self.term == 'screen')
    
    def is_running_inside_screen_session(self):
        if not self.is_running_inside_screen() or (self.sty == None) or ('.' not in self.sty):
            return False
        
        return self.sty.split('.')[1] == self.session
    
    @classmethod
    def get_session_id(cls, user, session):
        glob_results = glob.glob('/var/run/screen/S-' + user + '/*.' + session)
        
        if len(glob_results) == 1:
              return os.path.basename(glob_results[0])
        else: return None

