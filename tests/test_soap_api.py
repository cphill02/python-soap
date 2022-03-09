import sys
from os.path import dirname, join, abspath
sys.path.insert(0, abspath(join(dirname(__file__), '..', 'src', 'panopto_api')))

from panopto_api.AuthenticatedClientFactory import AuthenticatedClientFactory
import unittest


class TestSoapApi(unittest.TestCase):
    """
    Tests the SoapApi
    """
    @classmethod
    def setup_class(self):
        """
        Initialize the test via pytest
        """

    def test_create_auth_client_factory(self):
        """
        Tests creating an auth client
        """
        host = 'localhost'
        username = 'admin'
        password = 'password'
        auth = AuthenticatedClientFactory(
                host, username, password, verify_ssl=host != 'localhost')
        self.assertIsNotNone(auth)
