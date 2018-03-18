#!/usr/bin/python
# -*- coding: utf-8 -*-

class Rocketmap:
    """Rocketmap class"""
    
    # Central rocketmap paths and variables
    cfg_dir   = '/home/teamunity/config/RocketMap'
    exec_dir  = '/home/teamunity/current/RocketMap'
    exec_file = 'runserver.py'
    hooks_cfg = cfg_dir + '/webhooks.sh'
    
    @classmethod
    def to_string(cls):
        return 'Config Dir   = ' + cls.cfg_dir   + '\n' \
             + 'Exec Dir     = ' + cls.exec_dir  + '\n' \
             + 'Exec File    = ' + cls.exec_file + '\n' \
             + 'Args File    = ' + cls.args_file + '\n' \
             + 'Hooks Config = ' + cls.hooks_cfg
    
    @classmethod
    def get_exec(cls):
        return cls.exec_dir + '/' + cls.exec_file
    
    @classmethod
    def get_hook_endpoints(cls):
        endpoints = {}
        
        with open(cls.hooks_cfg, 'r') as file_handle :
            for endpoint_config in file_handle.read().split() :
                # Split up the endpoint config
                endpoint_config_parts = endpoint_config.split('=')
                endpoint_name_parts = endpoint_config_parts[0].split('_')[1:]
                
                # Grab the name and address
                endpoint_name = '-'.join(endpoint_name_parts).lower()
                endpoint_addr = endpoint_config_parts[1]
                
                # And add it to our dictionary
                endpoints[endpoint_name] = endpoint_addr
        
        return endpoints

class Levelup:
    """Levelup class"""
    
    # Levelup paths and variables
    exec_cmd = [ [ 'python', 'tools/levelup.py' ] ]

