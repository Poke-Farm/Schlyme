#!/usr/bin/python
# -*- coding: utf-8 -*-

# Standard Library Imports
import datetime
import glob
import os
import re
import subprocess
import time
import pymysql

# Schlyme Imports
from schlyme.display import *
from schlyme.rocketmap import *
from schlyme.utils import *

class Rockethive:
    """Rockethive class"""

    # Define some paths
    home_dir  = '/home/teamunity'
    exec_dir  = home_dir + '/software/MonsterSociety'
    exec_file = exec_dir + '/rockethive.py'

class Region:
    """Region class"""
    
    # Get the user and region
    user = os.getlogin()
    if user.split('-')[0] == 'hives':
	      name = user.split('-')[1]
    else: name = user
    
    # Define region specific paths
    home_dir = '/home/' + user
    cfg_dir  = home_dir + '/config/RocketMap'
    log_dir  = '/home/log/' + user + '/RocketMap'
    run_dir  = home_dir + '/run'
    tmp_dir  = run_dir  + '/tmp'
    
    # Some account directories
    acct_dir     = '/home/teamunity/accounts/current/'    + name
    l30_acct_dir = '/home/teamunity/config/Accounts-L30/' + name
    
    # And a few files
    cfg_file            = Rocketmap.cfg_dir + '/config.'         + name + '.ini'
    levelup_coords_file = Rocketmap.cfg_dir + '/levelup-coords.' + name + '.txt'
    
    # Make sure the directories exist
    if (not os.path.isdir(cfg_dir)) : os.makedirs(cfg_dir) ; os.chmod(cfg_dir, DIR_PERMS)
    if (not os.path.isdir(log_dir)) : os.makedirs(log_dir) ; os.chmod(log_dir, DIR_PERMS)
    if (not os.path.isdir(run_dir)) : os.makedirs(run_dir) ; os.chmod(run_dir, DIR_PERMS)
    if (not os.path.isdir(tmp_dir)) : os.makedirs(tmp_dir) ; os.chmod(tmp_dir, DIR_PERMS)
    
    # Grab the level up coordiantes
    with open(levelup_coords_file, mode = 'r') as f:
        levelup_coords = f.read().strip()
    
    # Define an empty database connection
    db_connection = None
    
    @classmethod
    def to_string(cls):
        return 'Name = ' + cls.name + ' [' + cls.user + ']' + '\n' \
             + 'Home Dir         = ' + cls.home_dir         + '\n' \
             + 'Config Dir       = ' + cls.cfg_dir          + '\n' \
             + 'Log Dir          = ' + cls.log_dir          + '\n' \
             + 'Run Dir          = ' + cls.run_dir          + '\n' \
             + 'Temp Dir         = ' + cls.tmp_dir          + '\n' \
             + 'Accounts Dir     = ' + cls.acct_dir         + '\n' \
             + 'L30 Accounts Dir = ' + cls.l30_acct_dir     + '\n' \
             + 'Region Config    = ' + cls.cfg_file         + '\n' \
             + 'Level Up Coords  = ' + cls.levelup_coords
    
    @classmethod
    def get_zones(cls):
        pattern = re.compile('^.*\.config\.ini$')
        zones = {}
        
        for root, zone_dirs, cfg_files in os.walk(cls.cfg_dir):
            for cfg_file in sorted(cfg_files):
                if (pattern.search(cfg_file) and (cls.cfg_dir == root or cls.cfg_dir == os.path.dirname(root))):
                    if (root == cls.cfg_dir):
                        zone = 'none'
                    else:
                        zone = os.path.basename(root)
                    
                    if (zone not in ['archive', 'backup', 'old', 'original', 'pending', 'template']):
                        hive_name = cfg_file.split('.')[0]
                        
                        if (zone not in zones):
                            zones[zone] = Zone(zone)
                        
                        zones[zone].hive_names.append(hive_name)
        
        zone_names = []
        for zone in zones:
            zone_names.append(zone)
            zones[zone].hive_names = sorted(zones[zone].hive_names)
        
        zones_sorted = []
        for zone in sorted(zone_names):
            zones_sorted.append(zones[zone])
        
        return zones_sorted
    
    @classmethod
    def get_zone(cls, hive_name):
        zones = cls.get_zones()

        for zone in zones:
            if hive_name in zone.hive_names:
                break
            else:
                zone = None
        
        return zone.name if zone != None else None
    
    @classmethod
    def get_db_connection_details(cls):
        # Build the regexs
        db_host_regex = re.compile('^db-host:')
        db_name_regex = re.compile('^db-name:')
        db_user_regex = re.compile('^db-user:')
        db_pass_regex = re.compile('^db-pass:')
        
        # Initialize db variables
        db_host = None
        db_name = None
        db_user = None
        db_pass = None
        
        with open(cls.cfg_file, mode = 'r') as f:
             lines = f.read().split('\n')
            
             for line in lines:
                 if   db_host_regex.search(line): db_host = line.split(':')[1].strip()
                 elif db_name_regex.search(line): db_name = line.split(':')[1].strip()
                 elif db_user_regex.search(line): db_user = line.split(':')[1].strip()
                 elif db_pass_regex.search(line): db_pass = line.split(':')[1].strip()
        
        return ( db_host, db_name, db_user, db_pass )
    
    @classmethod
    def get_db_connection(cls):
        if cls.db_connection == None:
            # Get the database connection details
            ( db_host, db_name, db_user, db_pass ) = cls.get_db_connection_details()
            
            # Make the database connection
            cls.db_connection = pymysql.connect( host = db_host, user = db_user, passwd = db_pass, db = db_name )
        
        # And return it
        return cls.db_connection

class Zone:
    """Zone Class"""
    def __init__(self, name):
        self.name       = name
        self.hive_names = []
    
    def __str__(self):
        return self.name + '\n' + '  ' + '\n  '.join(self.hive_names)

class HiveStatus:
    """Hive Status class"""
    
    def __init__(self, hive):
        
        #
        # Get the current task
        #

        self.task = hive.get_task()
        
        #
        # Get the spawn details
        #

        ( self.spawns_total
        , self.spawns_active
        , self.spawns_active_pct
        , self.spawns_inactive
        , self.spawns_inactive_pct ) = hive.get_last_spawn_log()
        
        #
        # Get the account file timestamp
        #
        
        if hive.acct_csv_target == None:
            self.acct_csv_ts = None
        else:
            acct_csv_target_file = os.path.basename(hive.acct_csv_target)
            acct_csv_ts_string   = acct_csv_target_file.split('.')[1]
            self.acct_csv_ts     = datetime.datetime.strptime(acct_csv_ts_string, '%Y%m%d-%H%M%S')
        
        #
        # Get the database status
        #

        db_connection = Region.get_db_connection()
        db_cursor     = db_connection.cursor()
        db_query      = "SELECT worker_name, method, message, last_modified, accounts_working, accounts_captcha, accounts_failed, success, fail, empty, skip, captcha, start, elapsed FROM mainworker WHERE worker_name = '" + hive.status_name + "'"
        
        # Execute the query
        db_cursor.execute(db_query)
        
        if db_cursor.rowcount > 0:
            # Fetch the results
            ( worker_name
            , method
            , message
            , last_modified
            , acct_working
            , acct_captcha
            , acct_failed
            , scan_success
            , scan_fail
            , scan_empty
            , scan_skip
            , captcha
            , start
            , elapsed ) = db_cursor.fetchone()
            
            # Close the query
            db_cursor.close()
            
            # Assign the results
            self.method        = method
            self.message       = message
            self.last_modified = last_modified
            self.acct_working  = int(acct_working)
            self.acct_captcha  = int(acct_captcha)
            self.acct_failed   = int(acct_failed)
            self.scan_success  = int(scan_success)
            self.scan_fail     = int(scan_fail)
            self.scan_empty    = int(scan_empty)
            self.scan_skip     = int(scan_skip)
            self.captcha       = int(captcha)
            self.start         = int(start)
            self.elapsed       = int(elapsed)

        else:
            # Assign the results
            self.method        = ''
            self.message       = 'Initializing'
            self.last_modified = ''
            self.acct_working  = int(0)
            self.acct_captcha  = int(0)
            self.acct_failed   = int(0)
            self.scan_success  = int(0)
            self.scan_fail     = int(0)
            self.scan_empty    = int(0)
            self.scan_skip     = int(0)
            self.captcha       = int(0)
            self.start         = int(0)
        
        # Calculate the total number of accounts
        self.acct_total = self.acct_working + self.acct_captcha + self.acct_failed
        
        # Calculate account percentages
        if self.acct_total > 0:
            self.acct_working_pct = ( float(self.acct_working) / float(self.acct_total) ) * 100.0
            self.acct_captcha_pct = ( float(self.acct_captcha) / float(self.acct_total) ) * 100.0
            self.acct_failed_pct  = ( float(self.acct_failed)  / float(self.acct_total) ) * 100.0
        
        else:
            self.acct_working_pct = 0.0
            self.acct_captcha_pct = 0.0
            self.acct_failed_pct  = 0.0
        
        #
        # Parse the database status message
        #
        
        ( self.scan_waiting
        , self.scan_init_bands
        , self.scan_tth_searches
        , self.scan_new_spawns

        , self.init_scan_pct
        , self.tth_found_pct
        , self.tth_missing
        , self.spawns_reached_pct
        , self.spawns_found_pct
        , self.good_scans_pct

        , self.queue_search_items
        , self.queue_db_updates
        , self.queue_webhook
        , self.acct_spare
        , self.acct_on_hold
        , self.acct_captcha ) = self.parse_db_status_message(self.message);
    
    def parse_db_status_message(self, message):
        lines = message.split('\n')
        
        scan_waiting      = 0
        scan_init_bands   = 0
        scan_tth_searches = 0
        scan_new_spawns   = 0
        
        init_scan_pct      = None
        tth_found_pct      = None
        tth_missing        = None
        spawns_reached_pct = None
        spawns_found_pct   = None
        good_scans_pct     = None
        
        queue_search_items = None
        queue_db_updates   = None
        queue_webhook      = None
        acct_spare         = None
        acct_on_hold       = None
        acct_captcha       = None
        
        # Uncomment when we need to debug
        #print
        #print message
        #print
        
        # Check if we have no status
        if lines[0].strip() not in ['Initializing', 'Search queue 0 empty, scheduling more items to scan.']:
            # Parse the first line
            # Scanning status: 1200 total waiting, 12 initial bands, 417 TTH searches, and 771 new spawns
            line_parts = lines[0].split(':')[1].strip().split(',')
            
            scan_waiting      = int( line_parts[0].strip().split(' ')[0] )
            scan_init_bands   = int( line_parts[1].strip().split(' ')[0] )
            scan_tth_searches = int( line_parts[2].strip().split(' ')[0] )
            scan_new_spawns   = int( line_parts[3].strip().split(' ')[1] )
            
            # Parse the second line
            # Initial scan: 97.90%, TTH found: 13.94% [2827 missing], Spawns reached: 10.05%, Spawns found: 100.00%, Good scans 83.45%
            if (len(lines) > 1) and ('Initial scan' in lines[1]):
                line_parts = lines[1].strip().split(',')
            
                init_scan_pct      = float( line_parts[0].split(':')[1].strip().split('%')[0] )
                tth_found_pct      = float( line_parts[1].split(':')[1].strip().split('%')[0] )
                tth_missing        = int  ( line_parts[1].split(':')[1].strip().split('[')[1].split(' ')[0] )
                spawns_reached_pct = float( line_parts[2].split(':')[1].strip().split('%')[0] )
                spawns_found_pct   = float( line_parts[3].split(':')[1].strip().split('%')[0] )
                good_scans_pct     = float( line_parts[4].split(' ')[3].strip().split('%')[0] )
            
            # Parse the third line
            # Queues: 0 search items, 9 db updates, 0 webhook.  Spare accounts available: 0. Accounts on hold: 0. Accounts with captcha: 0
            if   len(lines) > 1 and 'Queues' in lines[1] :
                                  line_parts = lines[1].strip().split('.')
            elif len(lines) > 2 : line_parts = lines[2].strip().split('.')
            else                : line_parts = []
            
            if len(line_parts) != 0:
                queue_search_items = int( line_parts[0].split(':')[1].strip().split(',')[0].strip().split(' ')[0] )
                queue_db_updates   = int( line_parts[0].split(':')[1].strip().split(',')[1].strip().split(' ')[0] )
                queue_webhook      = int( line_parts[0].split(':')[1].strip().split(',')[2].strip().split(' ')[0] )
                acct_spare         = int( line_parts[1].split(':')[1].strip() )
                acct_on_hold       = int( line_parts[2].split(':')[1].strip() )
                acct_captcha       = int( line_parts[3].split(':')[1].strip() )
            
            # Parse the fourth line
            # Total active: 30  |  Success: 7732 (2612.2/hr) | Fails: 0 (0.0/hr) | Empties: 2250 (760.1/hr) | Skips 0 (0.0/hr) | Captchas: 0 (0.0/hr) ($0.0/hr, $0.0/mo) | Elapsed: 3.0h
            
            #
            # Maybe add this later if we need it
            #

        return ( scan_waiting, scan_init_bands, scan_tth_searches, scan_new_spawns
               , init_scan_pct, tth_found_pct, tth_missing, spawns_reached_pct, spawns_found_pct, good_scans_pct
               , queue_search_items, queue_db_updates, queue_webhook, acct_spare, acct_on_hold, acct_captcha )

class Hive:
    """Hive class"""
    # Define spawn filtering regexs
    spawns_total_regex    = re.compile('[0-9]+$')
    spawns_active_regex   = re.compile('[0-9]+ or [0-9.]+%$')
    spawns_inactive_regex = re.compile('[0-9]+ or [0-9.]+%$')
    
    def __init__(self, name, zone = None):
        self.name = name
        
        # Validate the zone name
        derived_zone = Region.get_zone(self.name)
        
        if (derived_zone == None):
            print 'TODO: Deal with this error - Could not identify zone for hive name'
            self.zone = None
        
        elif (zone != None and zone != derived_zone):
            print 'TODO: Deal with this error - Given zone does not match identified zone for hive name'
            self.zone = None
        
        elif (zone == None or zone == derived_zone):
            self.zone = derived_zone
        
        # Set the status name
        self.status_name = self.zone + '.' + self.name
        
        # Define hive specific paths
        self.cfg_dir = Region.cfg_dir + ( '' if self.zone == 'none' else '/' + self.zone )
        self.log_dir = Region.log_dir + '/' + self.name
        self.tmp_dir = Region.tmp_dir + '/' + self.name
        
        # Define hive screen attributes
        self.session = 'hive-' + self.name
        self.screen  = Screen(Region.user, self.session)
        
        # Define hive attributes
        self.acct_csv         = Region.acct_dir + '/' + self.name + '.csv'
        self.acct_csv_target  = None if not os.path.exists(self.acct_csv) else os.readlink(self.acct_csv)
        self.l30_acct_csv     = Region.l30_acct_dir + '/accounts.L30.' + self.name + '.csv'
        self.cfg_file         = self.cfg_dir + '/' + self.name + '.config.ini'

        self.task_file        = self.get_task_file()
        self.scanner_pid_file = self.get_scanner_pid_file()
        self.levelup_pid_file = self.get_levelup_pid_file()
        self.rotate_pid_file  = self.get_rotate_pid_file()
        
        # Define webhook attributes
        self.hooks_cfg_file = self.cfg_dir + '/' + self.name + '.hooks.ini'
        
        all_hook_endpoints = Rocketmap.get_hook_endpoints()
        self.hook_endpoints = []
         
        with open(self.hooks_cfg_file, mode = 'r') as f:
            hooks = f.read().replace('\n', ' ').split()
        
        for hook in hooks :
            self.hook_endpoints.append(all_hook_endpoints[hook])

        # Get initscan details
        ( self.initscan_coords, self.initscan_count, self.initscan_ts ) = self.get_initscan_details()
        
        # Make sure directories exist
        if (not os.path.isdir(self.cfg_dir)) : os.mkdir(self.cfg_dir) ; os.chmod(self.cfg_dir, DIR_PERMS)
        if (not os.path.isdir(self.log_dir)) : os.mkdir(self.log_dir) ; os.chmod(self.log_dir, DIR_PERMS)
        if (not os.path.isdir(self.tmp_dir)) : os.mkdir(self.tmp_dir) ; os.chmod(self.tmp_dir, DIR_PERMS)
    
    def __str__(self):
        return 'Name                = ' +       str(self.name)              + '\n' \
             + 'Zone                = ' +       str(self.zone)              + '\n' \
             + 'Session             = ' +       str(self.session)           + '\n' \
             + 'Session ID          = ' +       str(self.screen.session_id) + '\n' \
             + 'Accounts            = ' +       str(self.acct_csv)          + '\n' \
             + 'L30 Accounts        = ' +       str(self.l30_acct_csv)      + '\n' \
             + 'Config Dir          = ' +       str(self.cfg_dir)           + '\n' \
             + 'Log Dir             = ' +       str(self.log_dir)           + '\n' \
             + 'Tmp Dir             = ' +       str(self.tmp_dir)           + '\n' \
             + 'Task File           = ' +       str(self.task_file)         + '\n' \
             + 'PID File (scanner)  = ' +       str(self.scanner_pid_file)  + '\n' \
             + 'PID File (level up) = ' +       str(self.levelup_pid_file)  + '\n' \
             + 'PID File (rotate)   = ' +       str(self.rotate_pid_file)   + '\n' \
             + 'Config File         = ' +       str(self.cfg_file)          + '\n' \
             + 'Hooks File          = ' +       str(self.hooks_cfg_file)    + '\n' \
             + 'Hook Endpoints      = ' + ', '.join(self.hook_endpoints)    + '\n' \
             + 'Init Scan Coords    = ' +       str(self.initscan_coords)   + '\n' \
             + 'Init Scan TS        = ' +       str(self.initscan_ts)       + '\n' \
             + 'Spawn Log File      = ' +       str(self.get_spawn_log_file())
    
    #@classmethod
    #def get_session_id(cls, session):
    #    return Screen.get_session_id(Region.user, session)
    
    @classmethod
    def get_log_filter_regexs(cls):
        log_filter_regexs = []
        log_filter_regexs.append('Proxy check completed')
        log_filter_regexs.append('[Ss]pawn points within hex')
        log_filter_regexs.append('Spawn Points found in hex')
        
        regexs_compiled = []
        for regex in log_filter_regexs:
            regexs_compiled.append( re.compile(regex) )
        
        return regexs_compiled
    
    @classmethod
    def parse_spawns_total(cls, line):
        result = cls.spawns_total_regex.search(line)
        
        if (not result):
            return None
        else:
            spawns_total = result.group(0)
            return int(spawns_total)
    
    @classmethod
    def parse_spawns_active(cls, line):
        result = cls.spawns_active_regex.search(line)
        
        if (not result):
            return None
        else:
            result_parts      = result.group(0).split(' ')
            spawns_active     = int(result_parts[0])
            spawns_active_pct = float(result_parts[2].split('%')[0])
            
            return ( spawns_active, spawns_active_pct )
    
    @classmethod
    def parse_spawns_inactive(cls, line):
        result = cls.spawns_inactive_regex.search(line)
        
        if (not result):
            return None
        else:
            result_parts        = result.group(0).split(' ')
            spawns_inactive     = int(result_parts[0])
            spawns_inactive_pct = float(result_parts[2].split('%')[0])
            
            return ( spawns_inactive, spawns_inactive_pct )
    
    @classmethod
    def create_spawn_log( cls
                        , spawns_total
                        , spawns_active,   spawns_active_pct
                        , spawns_inactive, spawns_inactive_pct ):
        return get_log_ts() \
             + ' - ' + str(spawns_total)                                      +   ' total'  \
             + ', '  + str(spawns_active)   + ' (' + str(spawns_active_pct)   + '%) active' \
             + ', '  + str(spawns_inactive) + ' (' + str(spawns_inactive_pct) + '%) inactive'
    
    def get_detailed_log_file  (self, ts) : return self.log_dir + '/' + ts + '.' + self.name + '.detailed.log'
    def get_filtered_log_file  (self, ts) : return self.log_dir + '/' + ts + '.' + self.name + '.filtered.log'
    def get_resetscan_log_file (self, ts) : return self.log_dir + '/' + ts + '.' + self.name + '.resetscan.log'
    def get_initscan_log_file  (self, ts) : return self.log_dir + '/' + ts + '.' + self.name + '.initscan.log'
    def get_levelup_log_file   (self, ts) : return self.log_dir + '/' + ts + '.' + self.name + '.levelup.log'
    def get_rotate_log_file    (self, ts) : return self.log_dir + '/' + ts + '.' + self.name + '.rotate.log'
    def get_spawn_log_file     (self)     : return self.log_dir + '/' + self.name + '.spawns.' + get_log_date() + '.log'
        
    def get_task_file          (self)     : return Region.run_dir + '/' + self.name + '.task'
    def get_scanner_pid_file   (self)     : return Region.run_dir + '/' + self.name + '.scanner.pid'
    def get_rotate_pid_file    (self)     : return Region.run_dir + '/' + self.name + '.rotate.pid'
    def get_levelup_pid_file   (self)     : return Region.run_dir + '/' + self.name + '.levelup.pid'
    
    def get_task(self):
        task = None
        
        if (os.path.exists(self.task_file)):
            with open(self.task_file, mode = 'r') as f:
                task = f.read().strip()
        
        return task
    
    def set_task(self, task):
        with open(self.task_file, mode = 'w') as f:
            f.write(task + '\n')
    
    def get_initscan_details(self):
        regex = re.compile('^location:')
        location_line = None
        
        with open(self.cfg_file, mode = 'r') as f:
             lines = f.read().split('\n')
             for line in lines:
                 if (regex.search(line)):
                     location_line = line
        
        if (location_line != None):
            coords = location_line.split(' ')[1]
            if ('#' in location_line):
                ts_text = location_line.split('#')[1].strip()
                
                if ',' in ts_text:
                    ts_text_parts = ts_text.split(',')
                    count = ts_text_parts[0].strip()
                    ts    = ts_text_parts[1].strip()
                
                else:
                    count = '?'
                    ts    = ts_text
            
            else:
                count = '?'
                ts    = None

            return ( coords, count, ts )
        
        else:
            return ( None, '?', None )
    
    def get_last_spawn_log(self):
        last_spawn_log_line = None
        
        try:
            with open(self.get_spawn_log_file(), mode = 'rb') as f:
                f.seek(0, os.SEEK_END)
                last_spawn_log_line_reversed = ''
                x = -2
                
                while True:
                    f.seek(x, os.SEEK_END)
                    c = f.read(1)
                    
                    if (c == '\n'):
                        break
                    else:
                        last_spawn_log_line_reversed += c
                        x -= 1
                
                last_spawn_log_line = last_spawn_log_line_reversed[::-1]
        
        except:
            last_spawn_log_line = None
        
        if ( last_spawn_log_line != None ):
            spawn_detail       = last_spawn_log_line.split(' - ')[1]
            spawn_detail       = spawn_detail.replace(',', '')
            spawn_detail       = spawn_detail.replace('(', '')
            spawn_detail       = spawn_detail.replace(')', '')
            spawn_detail       = spawn_detail.replace('%', '')
            spawn_detail_parts = spawn_detail.split(' ')
            
            total        =   int( spawn_detail_parts[0] )
            active       =   int( spawn_detail_parts[2] )
            active_pct   = float( spawn_detail_parts[3] )
            inactive     =   int( spawn_detail_parts[5] )
            inactive_pct = float( spawn_detail_parts[6] )
        
        else:
            total        = 0
            active       = 0
            active_pct   = 0.0
            inactive     = 0
            inactive_pct = 0.0
        
        return ( total, active, active_pct, inactive, inactive_pct )
    
    def run_command(self, command):
        if   (command == 'attach')     : self.run_command_attach()
        elif (command == 'start')      : self.run_command_start()
        elif (command == 'restart')    : self.run_command_restart()
        elif (command == 'stop')       : self.run_command_stop()
        elif (command == 'reset-scan') : self.run_command_resetscan()
        elif (command == 'init-scan')  : self.run_command_initscan()
        elif (command == 'level-up')   : self.run_command_levelup()
        elif (command == 'rotate')     : self.run_command_rotate()
    
    def run_command_attach(self):
        if self.screen.is_running_inside_screen_session():
            print "ERROR: Cannot attach to hive from within screen session"
            return 1
        
        if not self.screen.is_running():
            print "ERROR: Hive is not running, cannot attach!"
            return 1
        
        return self.screen.attach()
    
    def run_command_resetscan(self):
        # Check if we are NOT running inside of the screen session
        # Because if we are, we should just move along and do what we have come here to do
        if not self.screen.is_running_inside_screen_session():
            
            # We are not inside of the screen session, stop it if the hive is running
            if self.screen.is_running():
                self.run_command_stop()
            
            # The hive is not running (or has been stopped) and we are not inside of the screen session
            # Rerun the initscan command inside of screen
            return self.screen.start([Rockethive.exec_file, 'reset-scan', self.name])
        
        # For the log, print self
        print self
        
        # Capture a run timestamp and open the log file
        ts = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        log = open(self.get_resetscan_log_file(ts), mode = 'w', buffering = 0)
        
        # Create the regex 
        regex = re.compile('^#?location:')
        
        # Read the current config
        with open(self.cfg_file, mode = 'r') as f:
            cfg_lines = f.read().split('\n')
        
        # Log the original config
        print_write( log, 'Original Config File' )
        print_write( log, '--------------------' )
        print_write( log )
        
        for cfg_line in cfg_lines:
            print_write( log, cfg_line )
        
        print_write( log )
        
        # And the new config
        print_write( log, 'Reset Config File' )
        print_write( log, '-----------------' )
        print_write( log )

        # Sort the lines into the location and non-location lines
        location_lines = []
        other_lines    = []

        for cfg_line in cfg_lines:
            if regex.search(cfg_line):
                location_lines.append(cfg_line)
            else:
                other_lines.append(cfg_line)
        
        # Get the initial coords from the first location line
        reset_initscan_coords = location_lines[0].split(' ')[1]
        
        # Build the reset config
        with open(self.cfg_file, mode = 'w') as f:
            coords_line = 'location: ' + reset_initscan_coords + ' # 0, ' + get_log_datetime()
            
            f.write( coords_line + '\n' )
            print_write( log, coords_line )
            
            for cfg_line in other_lines:
                if len(cfg_line) > 0:
                    f.write( cfg_line.strip() + '\n' )
                    print_write( log, cfg_line )
        
        print_write( log )
        
        # Close the log file
        log.close()
        
        # Create a zero spawn log line
        spawn_log_line = Hive.create_spawn_log(0, 0, 0, 0, 0)
        
        # Write it to stdout
        print
        print spawn_log_line
        print
        
        # Most importantly to the spawn log which we will open only as required
        with open(self.get_spawn_log_file(), mode = 'a') as f:
            f.write(spawn_log_line + '\n')
        
        #
        # Finally, with a reset-scan do NOT start the hive back up
        # This command is often going to be run with  --all on a clear-db
        # Restarting all of the hives at once is bad
        #
    
    def run_command_initscan(self):
        # Check if we are NOT running inside of the screen session
        # Because if we are, we should just move along and do what we have come here to do
        if not self.screen.is_running_inside_screen_session():
            
            # We are not inside of the screen session, stop it if the hive is running
            if self.screen.is_running():
                self.run_command_stop()
            
            # The hive is not running (or has been stopped) and we are not inside of the screen session
            # Rerun the initscan command inside of screen
            return self.screen.start([Rockethive.exec_file, 'init-scan', self.name])
        
        # Capture a run timestamp and open the log file
        ts = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        log = open(self.get_initscan_log_file(ts), mode = 'w', buffering = 0)
        
        # Get the current initscan latitude and longitude
        initscan_coords_split = self.initscan_coords.split(',')
        lat = float( initscan_coords_split[0] )
        lon = float( initscan_coords_split[1] )
        
        new_lat = lat + 0.0000001
        new_lon = lon + 0.0000001
        
        new_initscan_coords = '{0:.7f},{1:.7f}'.format( new_lat, new_lon )
        
        # Magic up the count
        new_initscan_count = ( 0 if self.initscan_count == '?' else int(self.initscan_count) ) + 1
        
        print_write( log )
        print_write( log, Color.UNDERLINE + Color.GREEN + 'Current Init Scan:' + Color.PLAIN )
        print_write( log, 'count  = ' + str(self.initscan_count) )
        print_write( log, 'coords = ' +     self.initscan_coords )
        print_write( log, 'lat    = ' + str(lat) )
        print_write( log, 'lon    = ' + str(lon) )
        print_write( log )
        print_write( log, Color.UNDERLINE + Color.GREEN + 'New Init Scan:' + Color.PLAIN )
        print_write( log, 'count  = ' + str(new_initscan_count) )
        print_write( log, 'coords = ' +     new_initscan_coords )
        print_write( log, 'lat    = ' + str(new_lat) )
        print_write( log, 'lon    = ' + str(new_lon) )
        print_write( log ) 

        # Create the regex 
        regex = re.compile('^location:')
        
        # Read the current config
        with open(self.cfg_file, mode = 'r') as f:
            cfg_lines = f.read().split('\n')
        
        # Log the original config
        print_write( log, 'Original Config File' )
        print_write( log, '--------------------' )
        print_write( log )
        
        for cfg_line in cfg_lines:
            print_write( log, cfg_line )
        
        print_write( log )
        
        # And the new config
        print_write( log, 'New Config File' )
        print_write( log, '---------------' )
        print_write( log )

        # Build the new config
        with open(self.cfg_file, mode = 'w') as f:
            for cfg_line in cfg_lines:
                if not regex.search(cfg_line):
                    f.write( cfg_line + '\n' ) ; print_write( log, cfg_line )
                
                else:
                    old_line = '#' + cfg_line
                    new_line = 'location: ' + new_initscan_coords + ' # ' + str(new_initscan_count) + ', ' + get_log_datetime()
                    
                    f.write( old_line + '\n' ) ; print_write( log, old_line )
                    f.write( new_line + '\n' ) ; print_write( log, new_line )
        
        print_write( log )
        
        # Close the log file
        log.close()
        
        # Create a zero spawn log line
        spawn_log_line = Hive.create_spawn_log(0, 0, 0, 0, 0)
        
        # Write it to stdout
        print
        print spawn_log_line
        print
        
        # Most importantly to the spawn log which we will open only as required
        with open(self.get_spawn_log_file(), mode = 'a') as f:
            f.write(spawn_log_line + '\n')
        
        # And finally, start the hive again
        self.run_command_start()
    
    def run_command_levelup(self):
        # Check if we are NOT running inside of the screen session
        # Because if we are, we should just move along and do what we have come here to do
        if not self.screen.is_running_inside_screen_session():
            
            # We are not inside of the screen session, abort if the hive is running
            # We are not inside of the screen session, stop it if the hive is running
            if self.screen.is_running():
                self.run_command_stop()
            
            # The hive is not running and we are not inside of the screen session
            # Rerun the levelup command inside of screen
            # For the levelup command, this should only happen if levelup was called independently
            return self.screen.start([Rockethive.exec_file, 'level-up', self.name])
        
        # For the log, print self
        print self
        
        # Capture a run timestamp
        ts = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        
        # Build the command argument array starting with the basic rocketmap command
        levelup_cmd_tree = Levelup.exec_cmd
        levelup_cmd_tree.append( [ '--status-name'       , self.status_name      ] )
        levelup_cmd_tree.append( [ '--config'            , Region.cfg_file       ] )
        levelup_cmd_tree.append( [ '--location'          , Region.levelup_coords ] )
        levelup_cmd_tree.append( [ '--accountcsv'        , self.acct_csv         ] )
        levelup_cmd_tree.append( [ '--workers'           , '100'                 ] )
        levelup_cmd_tree.append( [ '--account-max-spins' , '50'                  ] )
        levelup_cmd_tree.append( [ '--no-file-logs' ]                              )
        
        print
        print ' '.join( levelup_cmd_tree[0] )
        levelup_cmd = levelup_cmd_tree[0]
        for arg in levelup_cmd_tree[1:] :
            if isinstance(arg, (list, tuple)):
                  levelup_cmd.extend(arg) ; print '    ' + ' '.join(arg)
            else: levelup_cmd.append(arg) ; print '    ' + arg
        print
        
        print levelup_cmd
        print
        
        # Set the task and pen the level up log file
        self.set_task('levelup')
        log = open(self.get_levelup_log_file(ts), mode = 'w', buffering = 0)
        
        # Open the subprocess
        levelup = subprocess.Popen( levelup_cmd
                                  , stdout = subprocess.PIPE
                                  , stderr = subprocess.STDOUT
                                  , cwd    = Rocketmap.exec_dir )
        
        # Save the PID
        with open(self.levelup_pid_file, mode = 'w') as f:
            f.write(str(levelup.pid) + '\n')
        
        # Poll the output of the rocketmap process
        while levelup.poll() is None:
            line = levelup.stdout.readline()
            
            if line:
                print line.strip()
                log.write(line)
        
        # Delete the pid file
        os.remove(self.levelup_pid_file)
        
        # Log the return code
        line = "Level Up process exited - rc = " + str(levelup.returncode)
        log.write(line + '\n')
        
        print
        print line
        print
        
        # Close the log files
        log.close()
        
        # Now start the hive
        self.run_command_start()
    
    def run_command_rotate(self):
        # Check if we are NOT running inside of the screen session
        # Because if we are, we should just move along and do what we have come here to do
        if not self.screen.is_running_inside_screen_session():
            
            # We are not inside of the screen session, stop it if the hive is running
            if self.screen.is_running():
                self.run_command_stop()
            
            # The hive is not running (or has been stopped) and we are not inside of the screen session
            # Rerun the rotate command inside of screen
            return self.screen.start([Rockethive.exec_file, 'rotate', self.name])
        
        # For the log, print self
        print self
        
        # Capture a run timestamp
        ts = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        
        # Build the command argument array starting with the basic rocketmap command
        rotate_cmd = [ 'sudo', '-u', 'teamunity', '/home/teamunity/scripts/lib/get-new-accounts.sh' ]
        rotate_cmd.append( Region.name )
        rotate_cmd.append( 'none' if self.zone == None else self.zone )
        rotate_cmd.append( self.name )
        
        print
        print ' '.join( rotate_cmd )
        print
        print rotate_cmd
        print
        
        # Set the task and open the rotate log file
        self.set_task('rotate')
        log = open(self.get_rotate_log_file(ts), mode = 'w', buffering = 0)
        
        # Open the subprocess
        rotate = subprocess.Popen( rotate_cmd
                                 , stdout = subprocess.PIPE
                                 , stderr = subprocess.STDOUT
                                 , cwd    = self.tmp_dir )
        
        # Save the PID
        with open(self.rotate_pid_file, mode = 'w') as f:
            f.write(str(rotate.pid) + '\n')
        
        # Poll the output of the rocketmap process
        while rotate.poll() is None:
            line = rotate.stdout.readline()
            
            if line:
                print line.strip()
                log.write(line)
        
        # Delete the pid file
        os.remove(self.rotate_pid_file)
        
        # Log the return code
        line = "Rotate process exited - rc = " + str(rotate.returncode)
        log.write(line + '\n')
        
        print
        print line
        print
        
        # Close the log files
        log.close()

        # Now level up the hive (level up will start it)
        self.run_command_levelup()

    def run_command_start(self):
        # Check if we are NOT running inside of the screen session
        # Because if we are, we should just move along and do what we have come here to do
        if not self.screen.is_running_inside_screen_session():
            
            # We are not inside of the screen session, abort if the hive is running
            if self.screen.is_running():
                print "ERROR: Hive is already running"
                return 1
            
            # The hive is not running and we are not inside of the screen session
            # Rerun the start command inside of screen
            return self.screen.start([Rockethive.exec_file, 'start', self.name])
        
        # For the log, print self
        print self
        
        # Capture a run timestamp
        ts = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        
        # Build the command argument array starting with the basic rocketmap command
        rm_cmd_tree = [ [ Rocketmap.get_exec(), '--no-server' ] ]
        
        # Setup the hive other arguments
       #rm_cmd_tree.append( [ '-v' ] )
        rm_cmd_tree.append( [ '--status-name'   , self.status_name ] )
        rm_cmd_tree.append( [ '--shared-config' , Region.cfg_file  ] )
        rm_cmd_tree.append( [ '--config'        , self.cfg_file    ] )
       #rm_cmd_tree.append( [ '--log-path'      , self.log_dir     ] )
        rm_cmd_tree.append( [ '--no-file-logs' ] )
         
        # Setup the accounts csv argument
        rm_cmd_tree.append( [ '--accounts-refresh', '5' ] )
        rm_cmd_tree.append( [ '--accountcsv', self.acct_csv ] )
        
        # Setup the encounter arguments (if the level 30 accounts csv file is found)
        if (os.path.exists(self.l30_acct_csv)) :
            rm_cmd_tree.extend( [ [ '--high-lvl-accounts', self.l30_acct_csv ], '--encounter' ] )
        
        for hook_endpoint in self.hook_endpoints:
            rm_cmd_tree.append( [ '--webhook', hook_endpoint ] )
        
        print
        print ' '.join( rm_cmd_tree[0] )
        rm_cmd = rm_cmd_tree[0]
        for arg in rm_cmd_tree[1:] :
            if isinstance(arg, (list, tuple)):
                  rm_cmd.extend(arg) ; print '    ' + ' '.join(arg)
            else: rm_cmd.append(arg) ; print '    ' + arg
        print
        
        print rm_cmd
        print
        
        # Set the task and open the detailed and filtered log files
        self.set_task('scanning')
        detailed_log = open(self.get_detailed_log_file(ts), mode = 'w', buffering = 0)
        filtered_log = open(self.get_filtered_log_file(ts), mode = 'w', buffering = 0)
        
        # Prepare the spawn log metrics
        spawns_total        = 0
        spawns_active       = 0
        spawns_active_pct   = 0.0
        spawns_inactive     = 0
        spawns_inactive_pct = 0.0
        
        # Prepare the spawn log regexs
        spawns_total_substr    = 'Total Spawn Points found in hex'
        spawns_active_substr   = 'Active Spawn Points found in hex'
        spawns_inactive_substr = 'Inactive Spawn Points found in hex'
        
        # Prepare the filter regexs
        filter_regexs = Hive.get_log_filter_regexs()
        
        # Open the subprocess
        rm = subprocess.Popen( rm_cmd
                             , stdout = subprocess.PIPE
                             , stderr = subprocess.STDOUT
                             , cwd    = self.tmp_dir )
        
        # Save the PID
        with open(self.scanner_pid_file, mode = 'w') as f:
            f.write(str(rm.pid) + '\n')
        
        # Poll the output of the rocketmap process
        while rm.poll() is None:
            line = rm.stdout.readline()
            
            if line:
                # Write all lines to stdout and the detailed log
                print line.strip()
                detailed_log.write(line)
                
                # Write lines to the filterd log if it matches one of the filters
                for regex in filter_regexs:
                    if (regex.search(line)):
                        filtered_log.write(line)
                        
                        # Check for spawn counts
                        if   (spawns_total_substr in line):
                            spawns_total = Hive.parse_spawns_total(line)
                        
                        elif (spawns_inactive_substr in line):
                            ( spawns_inactive, spawns_inactive_pct ) = Hive.parse_spawns_inactive(line)
                            
                        elif (spawns_active_substr in line):
                            ( spawns_active, spawns_active_pct ) = Hive.parse_spawns_active(line)
                        
                            spawn_log_line = Hive.create_spawn_log( spawns_total
                                                                  , spawns_active,   spawns_active_pct
                                                                  , spawns_inactive, spawns_inactive_pct )
                            
                            # Write it to stdout
                            print
                            print spawn_log_line
                            print
                            
                            # Most importantly to the spawn log which we will open only as required
                            with open(self.get_spawn_log_file(), mode = 'a') as f:
                                f.write(spawn_log_line + '\n')
                            
                            # And to the detailed log
                            detailed_log.write('\n')
                            detailed_log.write(spawn_log_line + '\n')
                            detailed_log.write('\n')
                            
                            # And to the filtered log
                            filtered_log.write('\n')
                            filtered_log.write(spawn_log_line + '\n')
                            filtered_log.write('\n')
                        
                        break
        
        # Delete the pid file
        os.remove(self.scanner_pid_file)
        
        # Log the return code
        line = "RocketMap process exited - rc = " + str(rm.returncode)
        detailed_log.write(line + '\n')
        filtered_log.write(line + '\n')
        
        print
        print line
        print
        
        # Close the log files
        detailed_log.close()
        filtered_log.close()
    
    def run_command_stop(self):
        if self.screen.is_running():
            return self.screen.stop()
    
    def run_command_restart(self):
        if self.screen.is_running():
            self.run_command_stop()
            time.sleep(1)
        
        self.run_command_start()
    
    def get_pretty_status(self):
        # Get the time
        now = datetime.datetime.now()
        
        # Get the hive status
        s = HiveStatus(self)
        
        #
        # Put together basic status
        #
        
        if not self.screen.is_running() :
                                   status = ( '{0:25} ' + Color.RED    + '{1:8}' + Color.PLAIN ).format( self.name, 'dead'     )
        elif s.task == 'levelup' : status = ( '{0:25} ' + Color.YELLOW + '{1:8}' + Color.PLAIN ).format( self.name, s.task     )
        elif s.task == 'rotate'  : status = ( '{0:25} ' + Color.YELLOW + '{1:8}' + Color.PLAIN ).format( self.name, s.task     )
        else                     : status = ( '{0:25} ' + Color.GREEN  + '{1:8}' + Color.PLAIN ).format( self.name, 'scanning' )
       #status += ( '{0:22} ' ).format( self.initscan_coords  )
        
        #
        # Put together the accounts status
        #
        
        if s.acct_csv_ts == None:
            acct_csv_ts_string = ''
            acct_csv_ts_color  = Color.BLUE
        else:
            delta = ( now - s.acct_csv_ts )
            
           #acct_csv_ts_string = s.acct_csv_ts.strftime('%Y-%m-%d %H:%M')
            acct_csv_ts_string = '{0:2}d {1:2}h {2:2}m'.format( delta.days, delta.seconds // 3600, (delta.seconds // 60) % 50 )
            
            if   delta.days == 0 : acct_csv_ts_color = Color.CYAN
            elif delta.days >= 3 : acct_csv_ts_color = Color.YELLOW
            else                 : acct_csv_ts_color = Color.BLUE
        
        acct_status  = ( acct_csv_ts_color + '{0:>11}'   + Color.PLAIN + ' : ' ).format( acct_csv_ts_string )
        acct_status += ( Color.CYAN        + '{0:3} wph' + Color.PLAIN + ' : ' ).format( s.acct_total )
        acct_status += ( Color.GREEN       + '{1:3.0f}%' + Color.PLAIN + ' : ' ).format( s.acct_working, s.acct_working_pct )
       #acct_status += ( Color.YELLOW      + '{1:3.0f}%' + Color.PLAIN + ' : ' ).format( s.acct_captcha, s.acct_captcha_pct )
        acct_status += ( Color.RED         + '{1:3.0f}%' + Color.PLAIN         ).format( s.acct_failed,  s.acct_failed_pct  )
        
        #
        # Put together the initial scan status
        #
        
	if self.initscan_ts == None:
            initscan_ts_string = ''
            initscan_ts_color  = Color.BLUE
	else:
            then  = datetime.datetime.strptime(self.initscan_ts, '%Y-%m-%d %H:%M:%S')
            delta = ( now - then )
            
           #initscan_ts_string = then.strftime('%Y-%m-%d %H:%M')
            initscan_ts_string = '{0:2}d {1:2}h {2:2}m'.format( delta.days, delta.seconds // 3600, (delta.seconds // 60) % 50 )
            
            if   delta.days == 0 : initscan_ts_color = Color.CYAN
            elif delta.days >= 3 : initscan_ts_color = Color.YELLOW
            else                 : initscan_ts_color = Color.BLUE
        
        init_scan_pct_display = '    ' if s.init_scan_pct == None else '{0:3.0f}%'.format( s.init_scan_pct )
        tth_found_pct_display = '    ' if s.tth_found_pct == None else '{0:3.0f}%'.format( s.tth_found_pct )
        
        initscan_status  = ( Color.YELLOW      + '[{0}]'        + Color.PLAIN + ' '   ).format( self.initscan_count )
        initscan_status += ( initscan_ts_color + '{0:>11}'      + Color.PLAIN + ' : ' ).format( initscan_ts_string )
        initscan_status += 'init ' + Color.GREEN  + init_scan_pct_display + Color.PLAIN + ' : '
        initscan_status += 'tth '  + Color.YELLOW + tth_found_pct_display + Color.PLAIN
        
        #
        # Put together the spawns status
        #
        
        spawns_status  = ( Color.CYAN        + '{0:5} spawns' + Color.PLAIN + ' : ' ).format( s.spawns_total )
        spawns_status += ( Color.GREEN       + '{1:3.0f}%'    + Color.PLAIN + ' : ' ).format( s.spawns_active,   s.spawns_active_pct   )
        spawns_status += ( Color.RED         + '{1:3.0f}%'    + Color.PLAIN         ).format( s.spawns_inactive, s.spawns_inactive_pct )
        
        # Put together the database status
        db_status = 'dbq ' + Color.RED + str( s.queue_db_updates ) + Color.PLAIN
        
        # Print them both out
        return status + ' | ' + acct_status + ' | ' + initscan_status + ' | ' + spawns_status + ' | ' + db_status

