import sys
from os.path import dirname, join, abspath
sys.path.insert(0, abspath(join(dirname(__file__), '..', 'src', 'panopto_api')))

from SFTPClient import SFTPClient
import unittest


class TestsFTPClient(unittest.TestCase):
    """
    Tests the SoapApi
    """
    @classmethod
    def setup_class(self):
        """
        Initialize the test via pytest
        """

    def test_create_sftp_client(self):
        """
        Tests creating an sftp client
        """
        sftp = SFTPClient(
            server = 'localhost',
            port = 22,
            username = 'admin',
            password = 'password',
            folder = 'root') 
        self.assertIsNotNone(sftp)

