import pytest
import os
import datetime as dt
import app.application as application

def test_full_list():
    '''Check that the full list of image filenames is loaded from the target 
    directory and that they're in the expected order. 

    Expected is 10 png images from 00:01 through 00:10, named and ordered by
    their ISO YYYYMMDD_HHMM timestamp (e.g. 20210101_0001.png)
    '''
    
    start = dt.datetime(year = 2021,
                        month = 1,
                        day = 1,
                        hour = 0,
                        minute = 0,
                        second = 0,
                        microsecond = 0)
    
    end = dt.datetime(year = 2021,
                        month = 1,
                        day = 1,
                        hour = 0,
                        minute = 11,
                        second = 0,
                        microsecond = 0)

    img_fns = application.full_snapshot_list(start, end) 
    n = len(img_fns)
    
    delt = dt.timedelta(days = 1)
    date_expect = start
    fmt = '%Y%m%d_%H%M'

    date_err = "Date list mismatch.\nExpected:\n{}\nFound:\n{}"
    fn_err = "Filename mismatch. Expected: {}, Found: {}"

    #check files found are in correct new->old order
    tstamps_found = [f['timestamp'] for f in img_fns]
    tstamps_expect = [start + dt.timedelta(minutes=n) for n in range(10,0,-1)]

    assert tstamps_found == tstamps_expect, date_err.format(
                            '\n'.join(map(str,tstamps_expect)),
                            '\n'.join(map(str,tstamps_found)))
   
    #check filenames correctly match the timestamps
    fns_expect = [ts.strftime(fmt)+'.png' for ts in tstamps_expect]
    fns_found = [f['filename'] for f in img_fns]

    assert fns_found == fns_expect, fn_err.format(
                            '\n'.join(map(str,fns_expect)),
                            '\n'.join(map(str,fns_found)))
