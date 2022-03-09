# flake8: noqa
import sys
from os.path import dirname, join, abspath
from os import environ
sys.path.insert(0, abspath(join(dirname(__file__), '..', 'src', 'panopto_api')))

from datetime import datetime
from AuthenticatedClientFactory import AuthenticatedClientFactory
from SFTPClient import SFTPClient
from PanoptoFolders import parseFoldersReport, getFoldersFromPanopto
from PanoptoUserSessions import parseUserSessionsReport, getUserSessionsFromPanopto
from PanoptoSessions import parseSessionsReport, getSessionsFromPanopto
from PanoptoUsage import parseUsageReport, getUsageFromPanopto

from dotenv import load_dotenv
load_dotenv()

def Watershed():
    # Panopto usage reporting -> Watershed sFTP as CSV
    
    pan_host = environ.get('PAN_HOST')
    pan_user = environ.get('PAN_USER')
    pan_pw = environ.get('PAN_PW')

    ftp_server = environ.get('FTP_SERVER')
    ftp_port = environ.get('FTP_PORT')
    ftp_user = environ.get('FTP_USER')
    ftp_pw = environ.get('FTP_PW')
    ftp_loc = environ.get('FTP_LOC')

    if pan_host != None :

        # init authentication
        auth = AuthenticatedClientFactory(
            host = pan_host,
            username = pan_user,
            password = pan_pw)
        # auth should return:
        # print(auth)
        # ['AccessManagement', 'Auth', 'RemoteRecorderManagement', 'SessionManagement', 'UsageReporting', 'UserManagement']

        # init the sFTP config
        sftp = SFTPClient(
            server = ftp_server,
            port = ftp_port,
            username = ftp_user,
            password = ftp_pw,
            folder = ftp_loc) 
        
        # get Panopto folders data
        folders_rpt = getFoldersFromPanopto(auth) # get the folders reports service
        folders_service = folders_rpt[0]
        folders_reports = folders_rpt[1]
        folders_csv = parseFoldersReport(folders_service, folders_reports) # call the service and parse the results into csv
        sftp.submit('PANOPTO_TO_WATERSHED_HIERARCHY_', folders_csv) # send the csv to Watershed

        # get Panopto sessions metadata
        sessions_rpt = getSessionsFromPanopto(auth) 
        sessions_service = sessions_rpt[0]
        sessions_reports = sessions_rpt[1]
        sessions = parseSessionsReport(sessions_service, sessions_reports) # call the service and parse the results into the sessions array
        
        # get Panopto user sessions metadata for the progress percentages
        user_sessions_rpt = getUserSessionsFromPanopto(auth) 
        user_sessions_service = user_sessions_rpt[0]
        user_sessions_reports = user_sessions_rpt[1]
        user_sessions = parseUserSessionsReport(user_sessions_service, user_sessions_reports) # call the service and parse the results into the sessions array

        # get Panopto usage data
        usage_rpt = getUsageFromPanopto(auth) # get the usage reports service
        usage_service = usage_rpt[0]
        usage_reports = usage_rpt[1]
        usage_csv = parseUsageReport(usage_service, usage_reports, sessions, user_sessions) # call the service and parse the results into csv
        sftp.submit('PANOPTO_TO_WATERSHED_VIEWS_', usage_csv) # send the csv to Watershed

        now = datetime.now().strftime('%m/%d/%Y %I:%M %p')
        print('-------')
        print(now + ': Panopto -> Watershed sFTP operation finished.')
        print('-------')
    else :
        print('-------')
        print('ERROR: Environment vars not set!')
        print('-------')
        exit()