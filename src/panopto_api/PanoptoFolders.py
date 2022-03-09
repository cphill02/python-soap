# flake8: noqa
import sys
from os.path import dirname, join, abspath
sys.path.insert(0, abspath(join(dirname(__file__), '..', 'src', 'panopto_api')))

from datetime import datetime, timedelta
from io import BytesIO
import zipfile
import csv
import io
from pytz import timezone, utc

def getFoldersFromPanopto(auth): #function for getting csv from Panopto on video folder hierarchy
    folders = auth.get_client('UsageReporting')
    reports = folders.call_service('GetRecurringReports', reportType='FolderUsage')
    print('Getting FolderUsage report:')
    return [folders, reports]

def parseFoldersReport(folders_service, reports): #function for parsing Panopto report data
    # Create a new empty csv
    csv_file = io.StringIO()
    writer = csv.writer(csv_file)
    #add headers
    record = [
            'Folder - Parent Object ID',
            'Folder - Parent Object Name',
            'Views and Downloads', 
            'Unique Viewers', 
            'Minutes Delivered', 
            'Average Minutes Delivered', 
            'Most Recent View Date', 
            'Root Folder (Level 0)', 
            'Subfolder (Level 1)', 
            'Subfolder (Level 2)', 
            'Subfolder (Level 3)'
    ]
    writer.writerow(record) #add headers to the new csv

    #look for a report to call
    report_id = None
    #print(reports)
    for report in reports:
        if report['IsEnabled'] and report['Reports'] != None and report['Cadence'] == 'Monthly': #and report['Cadence'] == 'Daily' :
            #print(report)
            for r in report['Reports']['StatsReportStatus'] :
                #print(r)
                if r['IsAvailable'] : # grab the last month (they are ordered most in the past to most recent)
                    #print(r)
                    #if r['EndTime'].date() == datetime.today().date() : # - timedelta(days=1) : #just reports processed today
                        #print(r)
                        report_id = r['ReportId']

    if not report_id:
        print('no reports available!')
    else:
        print('Getting folder report records:')
        # Let's get the report! this bit is a little tricky since we want to download raw bytes.
        raw_response = folders_service.call_service_raw('GetReport', reportId=report_id)
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
        # Iterate over the report data
        for row_no, row in enumerate(report_csv, 0):
            if row_no == 0: # CSV Headers
                #print(row)
                folder_id_index = row.index('Folder ID')
                folder_name_index = row.index('Folder Name')
                views_downloads_index = row.index('Views and Downloads')
                unique_viewers_index = row.index('Unique Viewers')
                minutes_delivered_index = row.index('Minutes Delivered')
                avg_minutes_delivered_index = row.index('Average Minutes Delivered')
                view_date_index = row.index('Most Recent View Date')
                folder_level0_index = row.index('Root Folder (Level 0)')
                folder_level1_index = row.index('Subfolder (Level 1)')
                folder_level2_index = row.index('Subfolder (Level 2)')
                folder_level3_index = row.index('Subfolder (Level 3)')
            else: # CSV Records
                #print(row)
                #convert Panopto dates to UTC in ISO8601
                #catch malformed dates by replacing w/ the date/time of parsing (now)
                try:
                    naive = datetime.strptime(row[view_date_index], "%m/%d/%Y %H:%M:%S %p")
                    local_dt = local.localize(naive, is_dst=None)
                    utc_dt = local_dt.astimezone(utc)
                except:
                    utc_dt = datetime.utcnow()

                view_datetm = utc_dt.strftime('%Y-%m-%dT%H:%M:%SZ')

                record = [ 
                    row[folder_id_index],
                    row[folder_name_index],
                    row[views_downloads_index],
                    row[unique_viewers_index],
                    row[minutes_delivered_index],
                    row[avg_minutes_delivered_index],
                    view_datetm,
                    row[folder_level0_index],
                    row[folder_level1_index],
                    row[folder_level2_index],
                    row[folder_level3_index],
                ]
                writer.writerow(record) #add records to the new csv
                c += 1 #maintain recordcount
        print(str(c) + ' records to transfer to Watershed:')
    return csv_file