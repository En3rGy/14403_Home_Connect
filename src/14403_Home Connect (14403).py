# coding: UTF-8

import ssl
import urllib
import urllib2
import json
import logging
import random
import html_server.html_server as html_server

##!!!!##################################################################################################
#### Own written code can be placed above this commentblock . Do not change or delete commentblock! ####
########################################################################################################
##** Code created by generator - DO NOT CHANGE! **##

class HomeConnect_14403_14403(hsl20_4.BaseModule):

    def __init__(self, homeserver_context):
        hsl20_4.BaseModule.__init__(self, homeserver_context, "14403_Home_Connect")
        self.FRAMEWORK = self._get_framework()
        self.LOGGER = self._get_logger(hsl20_4.LOGGING_NONE,())
        self.PIN_I_IS_VERIFIED=1
        self.PIN_O_VERIFICATION_URI=1

########################################################################################################
#### Own written code can be placed after this commentblock . Do not change or delete commentblock! ####
###################################################################################################!!!##

        self.logger = logging.getLogger("{}".format(random.randint(0, 9999999)))
        self.time_out = 5
        self.url = "https://api.home-connect.com"
        self.client_id = ""
        self.device_code = ""
        self.user_code = ""
        self.access_token = ""
        self.expires_in = ""
        self.refresh_token = ""
        self.server = html_server.HtmlServer(self.logger)
        self.server_port = 8095

    def set_output_value_sbc(self, pin, val):
        self.logger.debug("Entering set_output_value_sbc({}, {})".format(pin, val))
        if pin in self.g_out_sbc:
            if self.g_out_sbc[pin] == val:
                print ("# SBC: pin " + str(pin) + " <- data not send / " + str(val).decode("utf-8"))
                return

        self._set_output_value(pin, val)
        self.g_out_sbc[pin] = val

    def log_msg(self, text):
        self.DEBUG.add_message("14403: {}".format(text))

    def log_data(self, key, value):
        self.DEBUG.set_value("14403 {}".format(key), str(value))

    def get_auth_data(self):
        path = "/security/oauth/device_authorization"
        scope = "IdentifyAppliance"

        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        body = {"client_id": self.client_id, "scope": scope}
        ret = self.get_data(self.url + path, body, headers, "POST")
        ret = json.loads(ret)

        verification_uri_complete = str(ret["verification_uri_complete"])
        self.device_code = str(ret["device_code"])
        self.user_code = str(ret["user_code"])
        self.set_output_value_sbc(self.PIN_O_VERIFICATION_URI, verification_uri_complete)
        # Wait for verification

        self.server.set_html_content("<a href={}>Link zum Anmelden</a>".format(verification_uri_complete))

    def get_access_token(self):
        path = "/security/oauth/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        body = {"grant_type": "device_code",
                "device_code": self.device_code,
                "client_id": self.client_id,
                "client_secret": self.client_id[1:] + "."}
        ret = self.get_data(self.url + path, body, headers)
        ret = json.loads(ret)

        self.access_token = ret["access_token"]
        self.expires_in = ret["expires_in"]
        self.refresh_token = ret["refresh_token"]

        print(ret)

    def get_data(self, url, body=None, headers=None, method="GET"):
        # Build a SSL Context to disable certificate verification.
        ctx = ssl._create_unverified_context()
        response_data = ""

        try:
            # Build a http request and overwrite host header with the original hostname.
            if not headers and not body:
                request = urllib2.Request(url)
            else:
                request = urllib2.Request(url, headers=headers, data=urllib.urlencode(body))

            if method is "POST":
                request.get_method = lambda: 'POST'
            response = urllib2.urlopen(request, timeout=self.time_out, context=ctx)
            response_data = response.read()
        except urllib2.HTTPError as e:
            self.log_data("Error", "getData: " + str(e))
            print(e.geturl())
            print(e.read())
            print(e.getcode())

        return response_data

    def on_init(self):
        self.DEBUG = self.FRAMEWORK.create_debug_section()
        self.g_out_sbc = {}
        self.server.run_server(self.FRAMEWORK.get_homeserver_private_ip(), self.server_port)

    def on_input_value(self, index, value):
        if index is self.PIN_I_IS_VERIFIED and bool(value):
            # continue authentication
            self.get_access_token()
