# flake8: noqa
import sys
from os.path import dirname, join, abspath
import pycron
import time
from datetime import datetime

sys.path.insert(0, abspath(join(dirname(__file__), '.', 'panopto_api')))
from Watershed import Watershed

sys.path.insert(0, abspath(join(dirname(__file__), '.', 'config')))
from readCfg import read_config

now = datetime.now().strftime('%m/%d/%Y %I:%M %p')
print('-------')
print(now + ': startup execution...')
print('-------')
#upon restart, pull the data:
Watershed()

# parse config file for cron job
config = read_config(['cron.properties'])
# catch parsing failures
if (config.has_option('Cron Schedule', 'cron_enabled') == False and config.has_option('Cron Schedule', 'cron_scheduler') == False):
    exit()
else:
    # get the cron config settings (from cron.properties)
    cron_setting = config.get('Cron Schedule','cron_scheduler')
    cron_enabled = config.getboolean('Cron Schedule','cron_enabled')

    if (cron_enabled) :

        while True:
            # https://crontab.guru/ to create cron expression
            #if pycron.is_now('0/2 * * *'):   # True every 2nd minute
            now = datetime.now().strftime('%m/%d/%Y %I:%M %p')
            if pycron.is_now( cron_setting ):   # True every day at 3 am
                
                print('-------')
                print(now + ': cron job triggered...')
                print('-------')

                # Execute the Panopto to Watershed data migration
                Watershed()
                
                time.sleep(300)               # The process should take 5 minutes
                                              # to avoid running twice in one minute
            else:

                #print(now + ': sleeping..')
                time.sleep(60)               # Check again in 1 minute