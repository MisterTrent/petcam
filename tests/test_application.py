import pytest
import os
import datetime as dt
import app.application as application

@pytest.fixture
def make_list():
    '''Fixture that does the actual work of creating lists as specified by
    the requesting test or fixture. A factory pattern is used b/c we may not 
    always want the full set of possible inputs for every test. This approach 
    (over the fixed parameter list in a fixture signature) allows for that
    flexibility.
    '''

    def _make_list(_type, length):
        if _type == 'basic':
            start = dt.datetime(2021,1,1,0,length)
        elif _type == 'overnight':
            start = dt.datetime(2021,1,2,0,length)

        start = dt.datetime(2021, 1, 1, 0, 10)
        fmt = '%Y%m%d_%H%M'
        
        L = [(start - dt.timedelta(minutes = x)).strftime(fmt) + '.png'
            for x in range(length)]
        
        return L
    
    return _make_list

@pytest.fixture
def basic_info(request, make_list):
    '''Fixture to create lists of input data for tests.  Assumes that the 
    requester will indirectly parametrize with the necessary args to pass
    to the make_list fixture.
    '''

    _type = request.param['type']
    length = request.param['length']

    out = [{'timestamp' : dt.datetime.strptime(f.split('.')[0], '%Y%m%d_%H%M'),
            'filename' : f} for f in make_list(_type, length)]

    return out


list_data = [
    ([], {"type" : 'basic', "length" : 10})
]

@pytest.mark.parametrize("args, basic_info", list_data, indirect=['basic_info'])
def test_full_list(args, basic_info):
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
    tstamps_expect = [t['timestamp'] for t in basic_info]

    assert tstamps_found == tstamps_expect, date_err.format(
                            '\n'.join(map(str,tstamps_expect)),
                            '\n'.join(map(str,tstamps_found)))
   
    #check filenames correctly match the timestamps
    fns_expect = [t['filename'] for t in basic_info]
    fns_found = [f['filename'] for f in img_fns]

    assert fns_found == fns_expect, fn_err.format(
                            '\n'.join(map(str,fns_expect)),
                            '\n'.join(map(str,fns_found)))

