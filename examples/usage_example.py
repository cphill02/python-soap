# flake8: noqa

import sys
import argparse
import urllib3
import requests
import time

from hashlib import sha256
from base64 import b64encode

from os.path import dirname, join, abspath
sys.path.insert(0, abspath(join(dirname(__file__), '..', 'src', 'panopto_api')))

from AuthenticatedClientFactory import AuthenticatedClientFactory
from ClientWrapper import ClientWrapper
from datetime import datetime, timedelta
from math import ceil

from os.path import dirname, join, abspath
sys.path.insert(0, abspath(join(dirname(__file__), '..', 'common')))
from panopto_oauth2 import PanoptoOAuth2

host = 'localhost'
# method 1: you already have a cookie; just specify it
cookie = None
# method 2: use an oauth token to get a cookie
# see here for instructions: https://support.panopto.com/s/article/oauth2-for-services
# see here for code examples: https://github.com/Panopto/panopto-api-python-examples

def parse_argument():
    parser = argparse.ArgumentParser(description='Sample of Authorization for ID provider integration')
    parser.add_argument('--server', dest='server', required=True, help='Server name as FQDN')
    parser.add_argument('--client-id', dest='client_id', required=True, help='Client ID of OAuth2 client')
    parser.add_argument('--client-secret', dest='client_secret', required=True, help='Client Secret of OAuth2 client')
    parser.add_argument('--application-key', dest='application_key', required=True, help='Application Key of ID provider')
    parser.add_argument('--username', dest='username', required=True, help='Username for OAuth2 Resource Owner Grant')
    parser.add_argument('--skip-verify', dest='skip_verify', action='store_true', required=False, help='Skip SSL certificate verification. (Never apply to the production code)')
    return parser.parse_args()

def main():
    username = ''
    password = ''
    args = parse_argument()

    if args.skip_verify:
        # This line is needed to suppress annoying warning message.
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # Use requests module's Session object in this example.
    # ref. https://2.python-requests.org/en/master/user/advanced/#session-objects
    requests_session = requests.Session()
    requests_session.verify = not args.skip_verify

    def inspect_response_is_unauthorized(response):
        '''
        Inspect the response of a requets' call, and return True if the response was Unauthorized.
        An exception is thrown at other error responses.
        Reference: https://stackoverflow.com/a/24519419
        '''
        if response.status_code // 100 == 2:
            # Success on 2xx response.
            return False
            
        if response.status_code == requests.codes.unauthorized:
            print('Unauthorized. Access token is invalid.')
            return True

        # Throw unhandled cases.
        response.raise_for_status()
    
    def authorization(requests_session, oauth2, application_key, username):
        # Generate authentication code
        authcode = b64encode(sha256((username.lower() + '|' + application_key.lower()).encode('utf-8')).digest())
        # Go through authorization
        access_token = oauth2.get_access_token_resource_owner_grant(username, authcode)
        # Set the token as the header of requests
        requests_session.headers.update({'Authorization': 'Bearer ' + access_token})
        return {'Authorization': 'Bearer ' + access_token}

    # Load OAuth2 logic
    oauth2 = PanoptoOAuth2(args.server, args.client_id, args.client_secret, not args.skip_verify)

    # Initial authorization
    access_token = authorization(requests_session, oauth2, args.application_key, args.username)

    oauth_token = access_token

    # create a client factory for making authenticated API requests
    auth = AuthenticatedClientFactory(
        host,
        cookie,
        oauth_token,
        username, password,
        verify_ssl=host != 'localhost')

    # let's get some admin user
    user = auth.get_client('UserManagement')
    lu_response = user.call_service(
        'ListUsers',
        searchQuery='admin',
        parameters={})
    admin = lu_response['PagedResults']['User'][0]

    # what has the admin user been watching?
    page_size = 10
    usage = auth.get_client('UsageReporting')
    gudu_response = usage.call_service(
        'GetUserDetailedUsage',
        userId=admin['UserId'],
        pagination={ 'MaxNumberResults': page_size }
    )
    if gudu_response['TotalNumberResponses'] > 0:
        # get the last page!
        gudu_response = usage.call_service(
            'GetUserDetailedUsage',
            userId=admin['UserId'],
            pagination={
                'MaxNumberResults': page_size,
                'PageNumber': int(ceil(gudu_response['TotalNumberResponses'] / float(page_size)) - 1)
            }
        )
        endRange = datetime.utcnow()
        beginRange = endRange - timedelta(days=7)
        week_views = [v for v in gudu_response['PagedResponses']['DetailedUsageResponseItem'] if v['Time'].replace(tzinfo=None) > beginRange]
        if week_views:
            # let's get the sessionId of the first view and see who else has been watching it in the past week
            sessionId = week_views[0]['SessionId']
            print('admin viewed session {} in the past week'.format(sessionId))

            ssu_response = usage.call_service(
                'GetSessionSummaryUsage',
                sessionId=sessionId,
                beginRange=beginRange,
                endRange=endRange,
                granularity='Daily' # zeep doesn't currently support parsing enumeration types, so this is a magic string
            )
            view_days = [r for r in ssu_response if r['Views'] > 0]
            for day in sorted(view_days, key=lambda d:d['Time']):
                day_offset = int(ceil((endRange - day['Time'].replace(tzinfo=None)).total_seconds() / (3600 * 24)))
                print('{} day{} ago: {} unique users viewed {} minutes in {} distinct views'.format(
                    day_offset,
                    's' if day_offset > 1 else ' ',
                    day['UniqueUsers'],
                    day['MinutesViewed'],
                    day['Views']))
        else:
            print('no admin views in the past week')

if __name__ == '__main__':
    main()