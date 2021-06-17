import pytest
import os
import datetime as dt
import app.application as application

test_fns = [
    '20210101_0010.png',
    '20210101_0009.png',
    '20210101_0008.png',
    '20210101_0007.png',
    '20210101_0006.png',
    '20210101_0005.png',
    '20210101_0004.png',
    '20210101_0003.png',
    '20210101_0002.png',
    '20210101_0001.png'
]

test_fn_strs = [s.split('.')[0] for s in test_fns]
test_ts = [dt.datetime.strptime(f,'%Y%m%d_%H%M') for f in test_fn_strs]
test_output = [{'filename' : test_fns[i], 'timestamp' : test_ts[i]} 
                for i in range(len(test_fns))]

full_list_testdata = [
    ([], test_output),
    ([dt.datetime(2021, 1, 1, 0, 2), dt.datetime(2021, 1, 1, 0, 9)], test_output[1:9])
]

@pytest.mark.parametrize("args, expected", full_list_testdata)
def test_full_list(args, expected):
    '''Check that the full list of image filenames is loaded from the target 
    directory and that they're in the expected order. 

    Expected is 10 png images from 00:01 through 00:10, named and ordered by
    their ISO YYYYMMDD_HHMM timestamp (e.g. 20210101_0001.png)
    '''
   
    #used *args to test empty call; can't doc on this in pytest parametrize
    img_fns = application.full_snapshot_list(*args) 
    
    date_err = "Date list mismatch.\nExpected:\n{}\nFound:\n{}"
    fn_err = "Filename mismatch. Expected: {}, Found: {}"

    #check files found are in correct new->old order
    tstamps_found = [f['timestamp'] for f in img_fns]
    tstamps_expect = [t['timestamp'] for t in expected]

    assert tstamps_found == tstamps_expect, date_err.format(
                            '\n'.join(map(str,tstamps_expect)),
                            '\n'.join(map(str,tstamps_found)))
   
    #check filenames correctly match the timestamps
    fns_expect = [t['filename'] for t in expected]
    fns_found = [f['filename'] for f in img_fns]

    assert fns_found == fns_expect, fn_err.format(
                            '\n'.join(map(str,fns_expect)),
                            '\n'.join(map(str,fns_found)))
