# coding: UTF-8

import ssl
import time
import urllib
import urllib2
import httplib
import json
import logging
import random
import threading
import urlparse
import socket

import select

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
        self.PIN_O_ONLINE=2
        self.PIN_O_RUNNING=3
        self.PIN_O_FINISHED=4

########################################################################################################
#### Own written code can be placed after this commentblock . Do not change or delete commentblock! ####
###################################################################################################!!!##

        self.logger = logging.getLogger("{}".format(random.randint(0, 9999999)))
        self.time_out = 5
        self.url = "https://api.home-connect.com"
        self.server = html_server.HtmlServer(self.logger)
        self.server_port = 8087
        self.auth_data = self.AuthData()
        self.appliances = []
        self.event_thread = None
        self.keep_event_thread_running = True
        self.msg_last = ""

    class AuthData:
        def __init__(self):
            self.client_id = ""
            self.device_code = ""
            self.user_code = ""
            self.access_token = ""
            self.expires_in = ""
            self.refresh_token = ""

        def get_json(self):
            ret = {"client_id": self.client_id,
                   "device_code": self.device_code,
                   "user_code": self.user_code,
                   "access_toke": self.access_token,
                   "expires_in": self.expires_in,
                   "refresh_token": self.refresh_token}

            return str(json.dumps(ret))

        def load_json(self, data_s):
            data = json.loads(data_s)
            self.client_id = data["client_id"]
            self.device_code = data["device_code"]
            self.user_code = data["user_code"]
            self.access_token = data["access_token"]
            self.expires_in = data["expires_in"]
            self.refresh_token = data["refresh_token"]

    class ApplianceDevice:
        def __init__(self):
            self.name = ""
            self.ha_id = ""
            self.connected = False
            self.type = ""

        def __init__(self, data):
            self.name = data["name"]
            self.ha_id = data["haId"]
            self.connected = bool(data["connected"])
            self.type = data["type"]

        def __str__(self):
            return "{}: {}".format(self.name, self.ha_id)

        def load_json(self, data_s):
            data = json.loads(str(data_s))
            self.name = data["name"]
            self.ha_id = data["haId"]
            self.connected = bool(data["connected"])
            self.type = data["type"]

    def set_output_value_sbc(self, pin, val):
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
        """
        Creates a URI for user verification. User verification is required prior to get an access token.

        If an access token exists already, the process will not be startet and the method simply returns.

        If no access token but a refresh token exsits, the token refresh process is started.

        :return: Nothing
        """
        if self.auth_data.access_token:
            self.logger.debug("get_auth_data | access_token existing. No need for action.")
            return

        if self.auth_data.refresh_token:
            self.logger.debug("get_auth_data | refresh_token existing. Trying to refresh access_token.")
            self._get_access_token(True)
            return

        path = "/security/oauth/device_authorization"
        scope = "IdentifyAppliance Monitor"

        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        body = {"client_id": self.auth_data.client_id, "scope": scope}
        data_s = self.get_data(self.url + path, body, headers, "POST")
        try:
            data = json.loads(data_s)

            if "verification_uri_complete" in data:
                verification_uri_complete = str(data["verification_uri_complete"])
            self.auth_data.device_code = str(data["device_code"])
            self.auth_data.user_code = str(data["user_code"])
            self.set_output_value_sbc(self.PIN_O_VERIFICATION_URI, verification_uri_complete)
            self.log_data("Verification URI", verification_uri_complete)

        except Exception as e:
            self.log_msg("Error in get_auth_data: '{}' with message'{}'".format(e, data_s))

    def _get_access_token(self, refresh=False):
        """
        After successful user verification, this method gets the access token. In addition. if a token is outdated but
        a refresh token exists. this method gets a new access token using the refresh token.

        :param refresh: Uses the refresh token to refresh an access token if True.
        :type refresh: bool
        :return : Nothing
        """
        self.logger.debug("_get_access_token | Entering")
        path = "/security/oauth/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        if refresh:
            # self.logger.debug("_get_access_token | Creating refresh_token body")
            body = {"grant_type": "refresh_token",
                    "refresh_token": self.auth_data.refresh_token,
                    "client_secret": self.auth_data.client_id[1:] + "."}
        else:
            # self.logger.debug("_get_access_token | Creating device_code body")
            body = {"grant_type": "device_code",
                    "device_code": self.auth_data.device_code,
                    "client_id": self.auth_data.client_id,
                    "client_secret": self.auth_data.client_id[1:] + "."}

        # self.logger.debug("_get_access_token | calling get_data from _get_access_token")
        ret = self.get_data(self.url + path, body, headers, method="POST")
        # self.logger.debug("_get_access_token | Received '{}'  from _get_access_token".format(ret))
        ret = json.loads(ret)

        self.auth_data.access_token = ret["access_token"]
        self.auth_data.expires_in = ret["expires_in"]
        self.auth_data.refresh_token = ret["refresh_token"]

    def get_appliances(self):
        """

        :return:
        """
        path = "/api/homeappliances"
        headers = {"Accept": "application/vnd.bsh.sdk.v1+json",
                   "Authorization": "Bearer {access_token}".format(access_token=self.auth_data.access_token)}

        ret = self.get_data(url=self.url + path, headers=headers)
        ret = json.loads(str(ret))

        if "data" not in ret:
            print("get_appliance | if 'data' not in ret: {}".format(ret))
            return

        appliances = ret["data"]["homeappliances"]

        html = '<html><title>Home Appliances</title><body><table>'
        html += '<table border="1"><tr><th>Name</th><th>haId</th></tr>'

        for appliance_device_json in appliances:
            appliance_device = self.ApplianceDevice(appliance_device_json)
            self.appliances.append(appliance_device)  # @todo add only of not yet existing
            html += '<tr><td>{}</td><td>{}</td></tr>'.format(appliance_device.name, appliance_device.ha_id)
        html += '<table></body></html>'
        self.server.set_html_content(html)

    def get_device_status(self, ha_id):
        path = "/api/homeappliances/{}/status".format(ha_id)
        headers = {"accept": "application/vnd.bsh.sdk.v1+json",
                   "Authorization": "Bearer {access_token}".format(access_token=self.auth_data.access_token)}
        ret = self.get_data(url=self.url + path, headers=headers)
        self.process_device_status(ret)

    def process_device_status(self, msg):
        try:
            msg = json.loads(msg)
        except Exception as e:
            self.logger.warning("process_device_status | No json formatted message received. "
                                "Message was '{}'. Error was '{}'".format(msg, e))
            return

        if "error" in msg:
            if msg["error"]["key"] == "SDK.Error.HomeAppliance.Connection.Initialization.Failed":
                # HomeAppliance is offline
                self.set_output_value_sbc(self.PIN_O_FINISHED, False)
                self.set_output_value_sbc(self.PIN_O_RUNNING, False)
                self.set_output_value_sbc(self.PIN_O_ONLINE, False)
                return
        elif "data" not in msg:
            self.log_msg("process_device_status | Invalid message received. Message was '{}'".format(msg))
            return

        data = msg["data"]
        for status in data["status"]:
            if status["key"] == "BSH.Common.Status.OperationState":
                if status["value"] == "BSH.Common.EnumType.OperationState.Finished":
                    self.set_output_value_sbc(self.PIN_O_FINISHED, True)
                    self.set_output_value_sbc(self.PIN_O_RUNNING, False)
                elif status["value"] == "BSH.Common.EnumType.OperationState.Run":
                    self.set_output_value_sbc(self.PIN_O_FINISHED, False)
                    self.set_output_value_sbc(self.PIN_O_RUNNING, True)
                else:
                    self.set_output_value_sbc(self.PIN_O_FINISHED, False)
                    self.set_output_value_sbc(self.PIN_O_RUNNING, False)

    def register_device_events(self, ha_id):
        self.event_thread = threading.Thread(target=self.run_event_thread, args=(ha_id,))
        self.event_thread.start()

    def run_event_thread(self, ha_id):
        self.log_msg("run_event_thread | Starting event loop.")

        while self.keep_event_thread_running:
            path = "/api/homeappliances/{}/events".format(ha_id)
            server_name = urlparse.urlparse(self.url).netloc
            host_ip = self.FRAMEWORK.get_homeserver_private_ip()
            sock_unsecured = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock = ssl.wrap_socket(sock_unsecured, cert_reqs=ssl.CERT_NONE)
            try:
                sock.connect((server_name, 443))
            except socket.error as e:
                raise

            # connect to server
            while self.keep_event_thread_running:
                ready = select.select([], [sock], [], 5)
                if ready[1]:
                    error = sock.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
                    if error == 0:
                        break
                    else:
                        raise socket.error(error, 'Connect error')
                else:
                    raise socket.error('Timeout while connecting')
            self.logger.info("run_event_thread | Connected to server.")

            # send register event stream
            try:
                sock.send("GET {} HTTP/1.1\r\n".format(path))
                sock.send("Host: " + server_name + "\r\n")
                sock.send("Accept-Language: de-DE\r\n")
                sock.send("Accept: text/event-stream\r\n")
                sock.send("Authorization: Bearer {access_token}\r\n\r\n".format(access_token=self.auth_data.access_token))
            except socket.socket as e:
                sock.close()
                self.logger.error("run_event_thread | Error connecting  to eventstream.")
                raise
            self.logger.info("run_event_thread | Connected to eventstream")

            # run eventstream
            data = self.msg_last
            while self.keep_event_thread_running:
                try:
                    ready = select.select([sock], [], [], 5)
                    if ready[0]:
                        new_data = sock.recv(4096)  # read data

                        if not new_data:  # Connection closed
                            self.logger.warning("run_event_thread | Eventstream closed.")
                            return []

                        self.logger.debug("run_event_thread | Received {} bytes via eventstream.".format(len(new_data)))
                        self.process_event_msg(new_data)
                        data += new_data
                        msgs = data.split("\n")  # is ending with seperator, an empty element will be attached
                        self.msg_last = msgs[-1]  # store last( incomplete or empty) msg for later usage

                        # valid_msgs = [msg[6:] for msg in msgs[:-1] if len(msg) > 6 and msg[:6] == "data: "]
                        # return valid_msgs  # return all complete messages
                    else:
                        pass
                        # self.logger.debug("No data available on socket.")

                except socket.error as e:
                    self.logger.error("run_event_thread | Eventstream disconnected due to socket error {} '{}'.".format(e.errno, e))
                    break  # go to outer loop

            # gently disconnect and wait for re-connection
            sock.close()

        self.log_msg("run_event_thread | Exiting event loop!")

    def process_event_msg(self, data):
        self.logger.debug("process_event_msg | Entering")
        data = data.replace("\r", "")
        msgs = data.split("\n")  # is ending with seperator, an empty element will be attached
        ha_data = {}
        for msg in msgs:
            key_val = msg.split(":")
            if len(key_val) is 2:
                ha_data[str(key_val[0])] = str(key_val[1])

        self.logger.debug("process_event_msg | ha_data: {}".format(ha_data))
        if "event" not in ha_data and "Connection" not in ha_data:
            self.logger.warning("process_event_msg | Unknown message: {}".format(ha_data))
            return

        if "event" in ha_data:
            if ha_data["event"] == "KEEP-ALIVE":
                self.logger.debug("process_event_msg | Msg: KEEP-ALIVE")
            else:
                if len(ha_data["data"]) > 0:
                    self.logger.info("process_event_msg | {}".format(ha_data["data"]))
                    self.process_device_status(ha_data["data"])

    def get_data(self, url, body=None, headers=None, method="GET", loop_count=0):
        # Build a SSL Context to disable certificate verification.
        if loop_count > 1:
            self.logger.error("get_data | loop count > 1 -> aborting.")
            return "{}"

        ctx = ssl._create_unverified_context()
        response_data = ""

        try:
            # Build a http request and overwrite host header with the original hostname.
            if not headers and not body:
                request = urllib2.Request(url)
            elif headers and not body:
                request = urllib2.Request(url, headers=headers)
            else:
                request = urllib2.Request(url, headers=headers, data=urllib.urlencode(body))

            if method is "POST":
                request.get_method = lambda: 'POST'

            response = urllib2.urlopen(request, timeout=self.time_out, context=ctx)
            response_data = response.read()

        except urllib2.HTTPError as e:
            error_s = e.read()
            if error_s.find("error") > 0:
                msg = json.loads(error_s)
                error_msg = str(msg["error"]["description"])
                self.logger.error("get_data | Home Connect error {} with msg: '{}'".format(e.code, error_msg))
            if int(e.code) == 409:
                # device is offline
                return error_s
            elif int(e.code) == 401:
                self.logger.debug("get_data | Received '{}' ins {}.-loop. "
                                  "Try to refresh access token".format(e, loop_count))
                self.logger.debug("get_data | access_token was '{}'.".format(self.auth_data.access_token))
                self.auth_data.access_token = ""
                self.get_auth_data()
                if self.auth_data.access_token:
                    # retry with new access data
                    self.logger.debug("get_data | Retry request with new access token: '{}'.".format(
                        self.auth_data.access_token))
                    return self.get_data(url, body, headers, method, loop_count=loop_count + 1)
                else:
                    self.auth_data.refresh_token = ""
                    self.logger.debug("get_data | Try to get new authentication data (user verification required!)")
                    self.get_auth_data()
                    return error_s
            else:
                return error_s

        return response_data

    def on_init(self):
        self.DEBUG = self.FRAMEWORK.create_debug_section()
        self.g_out_sbc = {}
        self.server.run_server(self.FRAMEWORK.get_homeserver_private_ip(), self.server_port)
        self.get_appliances()

    def on_input_value(self, index, value):
        if index is self.PIN_I_IS_VERIFIED and bool(value):
            # continue authentication
            self._get_access_token()
