import pytest
import os
import datetime as dt
import app.application as application
import pdb

#all one day, no gaps
#cross midnight, no gaps
date_sets = [
    {'t2' : dt.datetime(2021,1,1,0,9), 't1' : dt.datetime(2021,1,1)},
    {'t2' : dt.datetime(2021,1,2,0,9), 't1' : dt.datetime(2021,1,1,23,50)},
]

date_params = [(ds, ds) for ds in date_sets]

@pytest.fixture
def date_lists(request):
    '''Fixture that does the actual work of creating lists as specified by
    the requesting test or fixture. A factory pattern is used b/c we may not 
    always want the full set of possible inputs for every test. This approach 
    (over the fixed parameter list in a fixture signature) allows for that
    flexibility.

    '''

    fmt = '%Y%m%d_%H%M'
    delt = (request.param['t2'] - request.param['t1']).seconds
    start = request.param['t2']

    rng = range(delt//60) #timestamps don't use seconds, so always round 
    
    ts_list = [(start-dt.timedelta(minutes = x)) for x in rng]
    str_list = [ts.strftime(fmt)+'.png' for ts in ts_list]
    
    return ts_list, str_list

@pytest.fixture
def basic_info(date_list):
    '''Fixture to create lists of input data for tests.  Assumes that the 
    requester will indirectly parametrize with the necessary args to pass
    to the make_list fixture.
    '''
    
    ts, strs = date_list
    out = [{'timestamp' : ts[i], 'filename' : strs[i]} for i in range(len(ts))]

    return out

@pytest.mark.parametrize("date_lists, time_ranges", date_params, indirect=['date_lists'])
def test_full_list(date_lists, time_ranges):
    '''Check that the full list of image filenames is correctly truncated and
    converted into a file information object. 
    '''
   
    #used *args to test empty call; can't doc on this in pytest parametrize
    #img_fns = application.full_snapshot_list(*args) 
    tstamps_expect, fns = date_lists
    
    t2 = time_ranges['t2']
    t1 = time_ranges['t1']

    output = application.full_snapshot_list(fns, t1, t2) 
    
    date_err = "Date list mismatch.\nExpected:\n{}\nFound:\n{}"

    tstamps_found = [f['timestamp'] for f in output]
    
    assert tstamps_found == tstamps_expect, date_err.format(
                            '\n'.join(map(str,tstamps_expect)),
                            '\n'.join(map(str,tstamps_found)))
