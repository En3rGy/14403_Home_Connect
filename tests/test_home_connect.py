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
        self.tst.user = self.cred["USER"]
        self.tst.pw = self.cred["PW"]
        self.tst.auth_data.client_id = self.cred["CLIENT_ID"]
        self.tst.auth_data.device_code = self.cred["DEVICE_CODE"]
        self.tst.auth_data.access_token = self.cred["ACCESS_TOKEN"]

        self.tst.auth_data.expires_in = self.cred["EXPIRES_IN"]
        self.tst.auth_data.user_code = self.cred["USER_CODE"]
        self.tst.auth_data.refresh_token = self.cred["REFRESH_TOKEN"]

        # simulator
        # self.tst.auth_data.access_token = "eyJ4LWVudiI6IlBSRCIsImFsZyI6IlJTMjU2IiwieC1yZWciOiJFVSIsImtpZCI6InJldS1wcm9kdWN0aW9uIn0.eyJmZ3JwIjpbXSwiY2x0eSI6InByaXZhdGUiLCJzdWIiOiJkZTc2YTNjMi0yY2IzLTQ3MTAtODU0ZC04MmNkNjMwNzM5MTYiLCJhdWQiOiIwNjJEMzQ1NEFBRTM2RUZBMjUyMDYxMkQxMDc0NTNBNkFFNEQyNjgyNTY3MzlERkFCOTQ5MTcyMjRBQzZFNzg0IiwiYXpwIjoiMDYyRDM0NTRBQUUzNkVGQTI1MjA2MTJEMTA3NDUzQTZBRTREMjY4MjU2NzM5REZBQjk0OTE3MjI0QUM2RTc4NCIsInNjb3BlIjpbIklkZW50aWZ5QXBwbGlhbmNlIiwiTW9uaXRvciJdLCJpc3MiOiJFVTpQUkQ6MCIsImV4cCI6MTcwMTAwMTI4NiwiaWF0IjoxNzAwOTE0ODg2LCJqdGkiOiI2NTkxNzRjNy04NGVmLTRmZmMtODhlNy05MmQ5NjgyMzIzMTUifQ.V3nBFAWjhVEY09GuqxuBdD5CMHDFDvm0R08c_svqwSNxDrHki4GlerzMDTkJTxw751PjODaDblGR265PepOGaBJlTmontdgRivsKRTV6JHO22yJ7tJqmvFxghz5DJws6hT9LHI2xkB44TFjKs0wjBnBgoRaH-A4fwk03YxaqreCySkdg718nEIN6ti37odkaMOT-mxKoJFg9eIBDT69CISizSE5vqqYaXNwasAwqsPE2gQo1e3pPYG32CAvxXdxV7ihP8UnonMIABcjbEscMqwOviAeatwbtuQaExqdFvVAks2VZylczSLiMiyUX2JnlCUBU8JILYCozioKqn_XlYg"
        # self.tst.url = "https://simulator.home-connect.com"

        # self.tst.url = "https://api.home-connect.com"

        self.tst.on_init()

    def test_get_auth_data(self):
        print("test_get_auth_data | Entering")
        # url = "https://simulator.home-connect.com"

        self.tst.get_auth_data()
        print("test_get_auth_data | AUTH_DATA: {}".format(self.tst.auth_data.get_json()))

        time.sleep(30)
        self.tst.on_input_value(self.tst.PIN_I_IS_VERIFIED, True)
        print("test_get_auth_data | Result: {}".format(self.tst.auth_data.get_json()))

    def test_outdated_access_token(self):
        print("test_outdated_access_token | Entering")
        self.tst.auth_data.access_token = "___" + self.tst.auth_data.access_token[3:]
        self.tst.get_appliances()

    def test_refresh_auth_data(self):
        print("test_refresh_auth_data | Entering")
        # url = "https://simulator.home-connect.com"

        self.tst._get_access_token(True)
        print("test_refresh_auth_data | AUTH_DATA: {}".format(self.tst.auth_data.get_json()))

    def test_status(self):
        self.tst.get_appliances()
        for app in self.tst.appliances:
            print(app)
            self.tst.get_device_status(app.ha_id)

    def test_events(self):
        for app in self.tst.appliances:
            print(app)
            self.tst.register_device_events(app.ha_id)

        time.sleep(3000)
        self.tst.keep_event_thread_running = False
        time.sleep(2)

    def test_server(self):
        time.sleep(15)


if __name__ == '__main__':
    logging.basicConfig()
    unittest.main()
