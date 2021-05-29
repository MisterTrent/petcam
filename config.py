import datetime as dt
import os

class Config(object):
    PAGINATION_SIZE = 20
    IMGS_PER_ROW = 2
    TIME_RESOLUTIONS = [1,2,5,10,15]
    DEFAULT_SNAPSHOT_INTERVAL = 1

    SNAPSHOT_CAPTURE_START = dt.time(hour= 22,
                                    minute = 0,
                                    second = 0,
                                    microsecond = 0)
    
    SNAPSHOT_CAPTURE_END = dt.time(hour= 7,
                                    minute = 0,
                                    second = 0,
                                    microsecond = 0)
    
    SNAPSHOT_DIR = './static/snapshots' 

class DevelopmentConfig(Config):
    SECRET_KEY = 'DEVELOPMENT_KEY'
