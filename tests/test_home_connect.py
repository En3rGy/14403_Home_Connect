# coding: UTF-8
import json
import time
import unittest
import logging

################################
# get the code
with open('framework_helper.py', 'r') as f1, open('../src/14403_Home Connect (14403).py', 'r') as f2:
    framework_code = f1.read()
    debug_code = f2.read()

exec (framework_code + debug_code)

################################################################################


class TestSequenceFunctions(unittest.TestCase):

    def setUp(self):
        print("\n###setUp")
        logging.basicConfig(level=logging.DEBUG)

        with open("credentials.txt") as f:
            self.cred = json.load(f)

        self.tst = HomeConnect_14403_14403(0)
        self.tst.client_id = self.cred["CLIENT_ID"]
        self.tst.user = self.cred["USER"]
        self.tst.pw = self.cred["PW"]
        self.tst.on_init()

    def test_get_auth_data(self):
        print("###tes_get_auth_data")
        # url = "https://simulator.home-connect.com"

        self.tst.get_auth_data()

        time.sleep(30)
        self.tst.on_input_value(self.tst.PIN_I_IS_VERIFIED, True)


if __name__ == '__main__':
    logging.basicConfig()
    unittest.main()
