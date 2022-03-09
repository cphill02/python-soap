# flake8: noqa
import sys
from os.path import dirname, join, abspath
sys.path.insert(0, abspath(join(dirname(__file__), '..', 'src', 'panopto_api')))

from datetime import datetime, timedelta
from io import BytesIO
import zipfile
import csv

def getSessionsFromPanopto(auth): #function for getting csv from Panopto on user views of videos
    sessions = auth.get_client('UsageReporting')
    reports = sessions.call_service('GetRecurringReports', reportType='SessionUsage')
    print('Getting SessionUsage report:')
    return [sessions, reports]

def parseSessionsReport(sessions_service, reports): #function for parsing Panopto report data
    # Create a new empty csv
    sessions = []

     #look for a report to call
    report_id = None
    #print(reports)
    for report in reports:
        if report['IsEnabled'] and report['Reports'] != None : #and report['Cadence'] == 'Daily' : #currently only reports are monthly
            #print(report)
            for r in report['Reports']['StatsReportStatus'] :
                if r['IsAvailable'] :
                    #if r['EndTime'].date() == datetime.today().date() : # - timedelta(days=1) : #just reports processed today
                    #print(r)
                    report_id = r['ReportId']

    if not report_id:
        print('no reports available!')
    else:
        print('Getting sessions report records:')
        # Let's get the report! this bit is a little tricky since we want to download raw bytes.
        raw_response = sessions_service.call_service_raw('GetReport', reportId=report_id)
        content_buffer = BytesIO(raw_response.content)
        zip_archive = zipfile.ZipFile(content_buffer)
        # There's just one report, the archive is for compression only
        report_file = zip_archive.namelist()[0]
        csv_data = zip_archive.open(report_file).readlines()
        print(str(len(csv_data)-1) + ' records returned from Panopto')
        report_csv = csv.reader([row.decode('utf-8-sig','replace') for row in csv_data])
        #print(report_csv)

        c = 0
        # Iterate over the report data and remove records that lack an email or the user name is set to Anonymous
        for row_no, row in enumerate(report_csv, 0):
            if row_no == 0: # CSV Headers
                #print(row)
                session_id_index = row.index('Session ID')
                session_length_index = row.index('Session Length')
            else: # CSV Records
                #print(row)
                sessions.append([row[session_id_index], row[session_length_index]])
                c += 1 #maintain recordcount
        print(str(c) + ' session metadata records parsed')
    return sessions

def getSessionLength(sessions, session_id):
    result = '0.00'
    for session in sessions:
        if session[0] == session_id:
            result = session[1]
    return result