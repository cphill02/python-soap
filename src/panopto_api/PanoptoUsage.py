# flake8: noqa
import sys
from os.path import dirname, join, abspath
sys.path.insert(0, abspath(join(dirname(__file__), '..', 'src', 'panopto_api')))

from PanoptoSessions import getSessionLength
from PanoptoUserSessions import getSessionProgress
from datetime import datetime, timedelta
from io import BytesIO
import zipfile
import csv
import io
from pytz import timezone, utc

def getUsageFromPanopto(auth): #function for getting csv from Panopto on video session metadata
    usage = auth.get_client('UsageReporting')
    reports = usage.call_service('GetRecurringReports', reportType='SystemViews')
    print('Getting SystemViews report:')
    return [usage, reports]

def parseUsageReport(usage_service, reports, sessions, user_sessions): #function for parsing Panopto report data
    # Create a new empty csv
    csv_file = io.StringIO()
    writer = csv.writer(csv_file)

    #add headers
    record = [
        'User - Email',
        'User - User ID',
        'User - User Name',
        'Session - Video Title',
        'Session - Video Object ID',
        'Folder - Parent Object Name',
        'Folder - Parent Object ID',
        'Session - Viewing Type',
        'Transcript - Transcript Status',
        'Transcript - Transcript Completed Date',
        'Training - Training Provider',
        'Transcript - Transcript Time in training (min)',
        'Transcript - Transcript Progress',
        'Training - Estimated Duration'
    ]
    writer.writerow(record) #add headers to the new csv

    #look for a report to call
    report_id = None
    #print(reports)
    for report in reports:
        if report['IsEnabled'] and report['Reports'] != None and report['Cadence'] == 'Daily' :
            #print(report)
            for r in report['Reports']['StatsReportStatus'] :
                if r['IsAvailable'] :
                    if r['EndTime'].date() == datetime.today().date() : # - timedelta(days=1) : #just reports processed today
                        #print(r)
                        report_id = r['ReportId']

    if not report_id:
        print('no reports available!')
    else:
        print('Getting usage report records:')
        # Let's get the report! this bit is a little tricky since we want to download raw bytes.
        raw_response = usage_service.call_service_raw('GetReport', reportId=report_id)
        content_buffer = BytesIO(raw_response.content)
        zip_archive = zipfile.ZipFile(content_buffer)
        # There's just one report, the archive is for compression only
        report_file = zip_archive.namelist()[0]
        csv_data = zip_archive.open(report_file).readlines()
        print(str(len(csv_data)-1) + ' records returned from Panopto')
        report_csv = csv.reader([row.decode('utf-8-sig','replace') for row in csv_data])
        #print(report_csv)

        c = 0
        local = timezone('US/Pacific') #Panopto date/times are always sent in Pacific Time.
        # Iterate over the report data and remove records that lack an email or the user name is set to Anonymous
        for row_no, row in enumerate(report_csv, 0):
            if row_no == 0: # CSV Headers
                #print(row)
                email_index = row.index('Email')
                user_id_index = row.index('User ID')
                user_name_index = row.index('User Name')
                session_name_index = row.index('Session Name')
                session_id_index = row.index('Session ID')
                folder_id_index = row.index('Folder ID')
                folder_name_index = row.index('Folder Name')
                type_index = row.index('Viewing Type')
                datetime_index = row.index('Timestamp')
                min_delivered_index = row.index('Minutes Delivered')
            else: # CSV Records
                if row[user_name_index] != 'Anonymous' and row[email_index] != '' : #filter out Cornerstone/LMS hosted videos
                    #convert Panopto dates to UTC in ISO8601
                    #catch malformed dates by replacing w/ the date/time of parsing (now)
                    try:
                        naive = datetime.strptime(row[datetime_index], "%m/%d/%Y %H:%M:%S %p")
                        local_dt = local.localize(naive, is_dst=None)
                        utc_dt = local_dt.astimezone(utc)
                    except:
                        utc_dt = datetime.utcnow()

                    session_datetm = utc_dt.strftime('%Y-%m-%dT%H:%M:%SZ')
                    #print(row)
                    record = [ 
                        row[email_index],
                        row[user_id_index],
                        row[user_name_index],
                        row[session_name_index],
                        row[session_id_index],
                        row[folder_name_index],
                        row[folder_id_index],
                        row[type_index],
                        'viewed',
                        session_datetm,
                        'Panopto',
                        row[min_delivered_index],
                        getSessionProgress(user_sessions, row[session_id_index]),
                        getSessionLength(sessions, row[session_id_index])
                    ]
                    writer.writerow(record) #add records to the new csv
                    c += 1 #maintain recordcount
        print(str(c) + ' records to transfer to Watershed:')
    return csv_file