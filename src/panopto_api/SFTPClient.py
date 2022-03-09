# flake8: noqa
import sys
from os.path import dirname, join, abspath
sys.path.insert(0, abspath(join(dirname(__file__), '..', 'src', 'panopto_api')))

from datetime import datetime
from io import BytesIO
import paramiko

#def SFTPClient(dest_filename, csv_file): #sFTP function for sending csv to Watershed
#server=sftp_server,port=sftp_port,username=sftp_username,password=sftp_password,filename='PANOPTO_TO_WATERSHED_VIEWS_', file=usage_csv
class SFTPClient(object):
    def __init__(self, server,
                port = None,
                username = None,
                password = None,
                folder = None
                ):
        self.server = server
        self.port = port
        self.username = username
        self.password = password
        self.folder = folder

    def submit(self, filename, file) :
        # convert from systemviews_2022-02-06--2022-02-12.csv -to- PANOPTO_TO_WATERSHED_YYYYMMDD_HH_MM_SS_AM/PM
        #print(csv_file.getvalue())
        #dest_filename = report_file.split('/')[1]
        format = '%Y%m%d_%H_%M_%S_%p'
        now = datetime.now() # current date and time
        date_time = now.strftime(format)
        filename += date_time + '.csv'
        print('Transfering ' + filename + ' to server:')
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(self.server, 
            port = self.port, 
            username = self.username, 
            password = self.password)
        sftp = ssh.open_sftp()
        sftp.chdir(self.folder) #set target folder
        sftp.putfo(BytesIO(file.getvalue().encode()), filename ) #write file
        print('sFTP transfer completed!')
        sftp.close()
        ssh.close()