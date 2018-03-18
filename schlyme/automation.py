#!/usr/bin/python
# -*- coding: utf-8 -*-

# Standard Library Imports

# Schlyme Imports
from schlyme.hive import *
from schlyme.utils import *

class HiveManager:
    """Hive Manager class"""

    def __init__(self):
        
        # Define screen attributes
        self.session = 'auto-hive'
        self.screen  = Screen(Region.user, self.session)

