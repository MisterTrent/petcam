from flask import (Flask, Response, render_template, request,
                    session, url_for, get_template_attribute,
                    render_template_string)
import datetime as dt
import os
from dotenv import load_dotenv

load_dotenv('.env')
app = Flask(__name__)

if app.config['ENV'] == 'test':
    app.config.from_object('config.TestConfig')
else:
    app.config.from_object('config.DevelopmentConfig')

def full_snapshot_list(since, to):
    '''Returns list of filenames between "since" and "to" times, where "since"
    is the beginning of the desired time window (older times) and "to" is the 
    end (newer times).

    Parameters
    ----------
    since : datetime.datetime
        Start of time for which captured images will be displayed
    to : datetime.datetime
        End of time for which captured images will be displayed

    Returns
    -------
    list
        List returned will contain dicts as elements that in turn each have 
        two key-value pairs: {'filename' : <filename string value>, 
        'timestamp' : <datetime.datetime object>}
    '''
    
    snap_dir = app.config['SNAPSHOT_DIR'] 
    files = [f for f in os.listdir(snap_dir) if f.endswith('.png')]
    files.sort(reverse = True) #filenames are ISO datetime; alphabetical sort OK

    output = []

    for f in files:
        try:
            timestamp_str = f.split('.')[0]
            timestamp = dt.datetime.strptime(timestamp_str, '%Y%m%d_%H%M')
        except:
            #skip 'errors' caused by unexpected files, wrong format, etc
            #TODO log errors? 
            continue
    
        #b/c list sorted new to old; stop once we hit end of target window
        if timestamp > to:
            continue 
        if timestamp < since:
            break
        
        output.append({'filename' : f, 'timestamp' : timestamp})
     
    return output

def resolution_filter(srclist, resolution = 1):
    '''Extracts a subset of the srclist of timestamps at a chosen resolution
    of time intervals.  Source expected to have a max frequency of 1 per 
    minute, so a resolution of 1 is the trivial case returning an unchanged
    srclist.  A resolution greater than 1 will start with the most recent 
    timestamp and return subsequent selections from the srclist at every
    'resolution' timestamp. This will be approximate, as timestamps are
    not guaranteed to be exactly every 1 minute in the source.

    Parameters
    ---------
    srclist : list of datetime.datetime 
        This is the list of timestamps to be filtered at the chosen
        resolution of intervals.  Must be ordered newest to oldest.
    resolution : int
        Frequency of timestamps to be extracted from the source timestamps.

    Return
    ------
    list
        Output will be same format as input, simply reduced in size depending
        on what sampling resolution from the source is used.
    '''
    
    if resolution not in app.config['TIME_RESOLUTIONS']:
        resstr = ", ".join(str(x) for x in app.config['TIME_RESOLUTIONS'])
        raise ValueError("Resolution must be one of: {}". format(resstr))
    
    delta = dt.timedelta(minutes = resolution)
    last_time = srclist[0]['timestamp'] + delta 
    
    dstlist = []
    for d in srclist:
        if (last_time - d['timestamp']) < delta:
            continue

        dstlist.append(d)
        last_time = d['timestamp']

    return dstlist

def snapshot_labels(src_imgs):
    '''Create label strings for snapshot objects to use in templating.

    Parameters
    ----------
    src_dicts : list (of image objects)

    Return
    ------
    list
        Output is same as input, with new element or attribute added to
        hold the image object's label.
    '''

    for src in src_imgs:
        src['label'] = src['timestamp'].strftime('%I:%M %p')

    return src_imgs

def capture_window_dt(start, end, now):
    '''Convert datetime.time endpoints into datetime.datetime for the 
    current day. This is trivial for capture windows that do not cross
    midnight, but requires more steps if they do. If 'now' is outside the
    capture time window, then this will use the most recent one to determine
    the day instead of the future one.

    Parameters
    ----------
    start : datetime.time
        Start time of the window in a given day
    end : datetime.time
        End time of the window in a given day
    now : datetime.datetime
        Current time and current day, but not necessarily currently within
        the capture window between 'start' and 'end'

    Return
    ------
    tuple (datetime.datetime, datetime.datetime)
        'start' and 'end' converted into datetimes.
    '''       
    start_dt = dt.datetime(year = now.year,
                         month = now.month,
                         day = now.day,
                         hour = start.hour, 
                         minute = start.minute, 
                         second = start.second,
                         microsecond = start.microsecond)

    end_dt = dt.datetime(year = now.year,
                         month = now.month,
                         day = now.day,
                         hour = end.hour, 
                         minute = end.minute, 
                         second = end.second,
                         microsecond = end.microsecond)

    in_window = check_time(now.time(), start, end)

    if in_window:
        #window crosses 00:00, adjust end on other side of it from 'now'
        if start > end and now.hour >= 0:
            start_dt -= dt.timedelta(days = 1) 
        elif start > end and now.hour < 0:
            end_dt += dt.timedelta(days = 1)
        elif start == end:
            msg = 'Unexpected behavior: Observation window covers entire day'
            raise Exception(msg)

    else:
        if start > end:
            #b/c window crosses 00:00 and we only use past windows, start
            #always 'yesterday' and end always 'today'
            start_dt -= dt.timedelta(days = 1)

        elif start < end:
            #window all one day, so adjust stamps to yesterday only 
            #if 'now' before today's window
            if now.time() < start:
                start_dt -= dt.timedelta(days = 1)
                end_dt -= dt.timedelta(days = 1)

        elif start == end:
            msg = 'Unexpected behavior: Observation window covers entire day'
            raise Exception(msg)

    return start_dt, end_dt

def check_time(now, start, end):
    '''Checks whether the given time 'now' is within the capture window,
    including the start and end times themselves. Windows that cross midnight
    (where 23:59 turns over to 00:00) are handled so that the numerical 
    discontinuity doesn't affect user's provided range.

    Parameters
    ----------
    now : datetime.time
        Current time to assess
    start : datetime.time
        Start of the time window for snapshot captures. This is the
        'older' time of start and end
    end : datetime.time
        End of the time window for snapshot captures.

    Return
    ------
    bool
    '''

    if start > end:
        #midnight in window means two ranges: use OR
        if now >= start or now <= end:
            retval = True
    elif start < end:
        #midnight not in window, range 
        if now >= start and now <= end:
            retval = True
    else:
        #TODO window 24 hrs or 0, start == end
        retval = False
   
    return retval

def group_srcs(original, slice_size):
    '''Groups a single list into sub-lists of a given size.
    Eg: [1,2,3,4,5,6] with slice_size 2 becomes [[1,2],[3,4],[5,6]].
    If the final sub-list is shorter than the slice_size then it will 
    simply be truncated (rather than have blank elements inserted).
    
    Parameters
    ----------
    original : list
        Source list of image info objects to be partitioned into smaller lists.
    slice_size : int
        Length of sub-lists (rows) to use in the output.
    
    Return
    ------
    list
        List of lists, where the sub-lists are in the format of the original 
        input list 
    '''
    o_sz = len(original)
    if o_sz < slice_size:
        return original
   
    return [original[i:i+slice_size] if i < o_sz else original[i:] 
            for i in range(0, o_sz, slice_size)]

def snapshot_list(since, now, interval):
    '''Queries file directory for list of files within a set window of time, 
    and then reduces that list of files to those obtained at certain time 
    intervals.  E.g. If the complete list has files from each minute, then
    an interval of 2 will return a list of every other file (one every two
    minutes).
    
    Parameters
    ----------
    since : datetime.datetime
        The timestamp for the start (oldest times) of the time window.
    now : datetime.datetime
        Timestamp for the end (newest times) of the time window.
    interval : int
        Number of minutes between timestamps on the returned list of images. 
        This is approximate as capturing does not occur exactly on the minute.

    Return
    ------
    list
        Returns list of images' information with that format determined by the 
        full_snapshot_list for all images within the query window.
    '''
    
    #TODO doing this feels wrong; handle type conversion w/i list func? 
    start, end = capture_window_dt(app.config['SNAPSHOT_CAPTURE_START'],
                                  app.config['SNAPSHOT_CAPTURE_END'],
                                  now)
    #get full list first...
    src_list = full_snapshot_list(start, end)
    
    #truncate to requested times...
    sub_list = [t for t in src_list if 
                t['timestamp'] > since and t['timestamp'] < now]
    
    if len(sub_list) == 0:
        #return sub_list, is_last
        return sub_list
    
    #extract only the chosen samples
    filtered = resolution_filter(sub_list, interval)
    
    if len(filtered) > 0:
        last_all = src_list[-1]['timestamp']
        last_filt = filtered[-1]['timestamp']
        d = dt.timedelta(minutes = interval)

    sub_list = snapshot_labels(filtered)

    #return sub_list, is_last
    return sub_list

@app.route('/ajax/load_snapshots') 
def ajax_snapshots():
    '''XHR target to load additional images to be appended to the existing
    display on the page.
    '''
    
    #SS1 timing
    to = session['last_image']['timestamp']
    since, _ = capture_window_dt(app.config['SNAPSHOT_CAPTURE_START'],
                                  app.config['SNAPSHOT_CAPTURE_END'],
                                  session['now'])

    #SS2 get image list for time
    src_list = snapshot_list(since, to, session['interval'])
    n_imgs = len(src_list)
    page_sz = app.config['PAGINATION_SIZE']

    if n_imgs > page_sz:
        src_list = src_list[:page_sz]
        is_last_page = False
    elif n_imgs <= page_sz and n_imgs > 0:
        is_last_page = True
    else:
        #no images found TODO render message& return?
        pass

    row_lists = group_srcs(src_list, app.config['IMGS_PER_ROW']) 
    session['last_image'] = src_list[-1]
    
    #STEP 3: render and return
    render_pagination = get_template_attribute(
                        'macros.html', 'snapshot_pagination')
    response = render_pagination(row_lists, is_last_page)
    
    return render_template_string(response)

@app.route('/snapshots')
def snapshots():
    '''Main snapshot page using default display settings (number of images,
    interval at which they were obtained.)
    '''
    
    #SS1 timing
    #now = dt.datetime.now().replace(second=0)
    now = dt.datetime.now().replace(
                                year = 2021,
                                month = 4,
                                day = 7,
                                hour = 6, 
                                minute = 59, 
                                second = 0,
                                microsecond = 0)
    
    start = app.config['SNAPSHOT_CAPTURE_START']
    end = app.config['SNAPSHOT_CAPTURE_END']
    n_imgs = app.config['PAGINATION_SIZE'] 
    
    if not check_time(now.time(), start, end):
        pass
    
    session['interval'] = app.config['DEFAULT_SNAPSHOT_INTERVAL']
    session['now'] = now
    
    #SS2 load image list for time
    since, _ = capture_window_dt(start, end, now)
    src_list = snapshot_list(since, now, session['interval']) 
        
    if len(src_list) > n_imgs:
        src_list = src_list[:n_imgs]
        is_last_page = False
    else:
        is_last_page = True
    
    #TODO what if no images returned?
    row_lists = group_srcs(src_list, app.config['IMGS_PER_ROW'])
    
    #SS3 render and return
    session['last_image'] = src_list[-1]
    
    return render_template('snapshots.html', 
                            row_lists = row_lists,
                            is_last_page = is_last_page)
                            
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(port = 8000, use_reloader = False)
