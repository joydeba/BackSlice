import csv
from github import Github
import time
from datetime import datetime
import pytz
import sys
csv.field_size_limit(sys.maxsize)

def wait(seconds):
    print("Waiting for {} seconds ...".format(seconds))
    time.sleep(seconds)
    print("Done waiting - resume!")

def changeG(g, accesskey, backup_keys, no_bused_key, load_object):
    print("Inside change G - remaining", str(g.get_rate_limit().core.remaining), "Used key -", str(no_bused_key))
    if g.get_rate_limit().core.remaining < 1000 and no_bused_key == (len(backup_keys) -1):
        reset_time = g.get_rate_limit().core.reset.replace(tzinfo=pytz.utc)
        diff_time = (reset_time - datetime.now(pytz.utc)).total_seconds()
        print("Waiting...")
        wait(diff_time + 300)
        g = Github(accesskey)
        no_bused_key = 0
        load_object = 1
        return g, no_bused_key, load_object
    elif g.get_rate_limit().core.remaining < 1000 and no_bused_key < (len(backup_keys) -1):
        g = Github(backup_keys[no_bused_key])
        no_bused_key = no_bused_key + 1
        load_object = 1
        print("Key Changed...")
        if g.get_rate_limit().core.remaining > 1000:
            return g, no_bused_key, load_object
        else:
            changeG(g, accesskey, backup_keys, no_bused_key, load_object)

    else:
        return g, no_bused_key, load_object

def changeSearchG(g, accesskey, backup_keys, no_bused_key, load_object):
    print("Inside changeSearch G - remaining", str(g.get_rate_limit().search.remaining), "Used key -", str(no_bused_key))
    if g.get_rate_limit().search.remaining < 5 and no_bused_key == (len(backup_keys) -1):
        reset_time = g.get_rate_limit().search.reset.replace(tzinfo=pytz.utc)
        diff_time = (reset_time - datetime.now(pytz.utc)).total_seconds()
        print("Waiting Search...")
        wait(diff_time + 30)
        g = Github(accesskey)
        no_bused_key = 0
        load_object = 1
        return g, no_bused_key, load_object
    elif g.get_rate_limit().search.remaining < 5 and no_bused_key < (len(backup_keys) -1):
        g = Github(backup_keys[no_bused_key])
        no_bused_key = no_bused_key + 1
        load_object = 1
        print("Key Changed Search...")
        if g.get_rate_limit().search.remaining > 5:
            return g, no_bused_key, load_object
        else:
            changeG(g, accesskey, backup_keys, no_bused_key, load_object)

    else:
        return g, no_bused_key, load_object        

def initialize_G():
    with open('keys.gconfig', 'r') as file:
        accesskey = file.read().replace('\n', '')
    g = Github(accesskey)

    with open('keys_multiple.gconfig') as f:
        backup_keys = f.readlines()
    backup_keys = [x.strip() for x in backup_keys] 
    no_bused_key = 0
    return g, backup_keys, no_bused_key, accesskey      