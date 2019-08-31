from io import BytesIO
from typing import Iterator, Any
import base64
import hashlib
import urllib.request
import xml.etree.ElementTree as ET


class HLRequest(object):
    document = None

    def __init__(self):
        self.document = ET.Element('request')

    def __str__(self) -> str:
        return self.serialize().decode('utf-8')

    def __setitem__(self, name: str, value: str):
        self.set_param(name, value)

    def __iter__(self) -> Iterator[bytes]:
        return iter([self.serialize()])

    def add_param(self, name: str, value: str) -> 'HLRequest':
        node = ET.SubElement(self.document, name)
        node.text = value

        return self

    def set_param(self, name: str, value: str) -> 'HLRequest':
        node = self.document.find(name)
        if not node:
            node = ET.SubElement(self.document, name)
        node.text = value

        return self

    def serialize(self) -> bytes:
        et = ET.ElementTree(self.document)
        f = BytesIO()
        et.write(f, encoding='utf-8', xml_declaration=True, short_empty_elements=False)  # noqa

        return f.getvalue()


class HLResponse(object):
    def __init__(self, response: str):
        self.document = ET.fromstring(response)

    def __getitem__(self, key: str) -> str:
        try:
            return self.getvalue(key)
        except AttributeError:
            raise KeyError

    def __str__(self) -> str:
        return self.serialize().decode('utf-8')

    def __eq__(self, other: str) -> bool:
        return self.getvalue() == other

    def serialize(self) -> bytes:
        et = ET.ElementTree(self.document)
        f = BytesIO()
        et.write(f, encoding='utf-8', xml_declaration=True)

        return f.getvalue()

    def getvalue(self, name: str = '') -> str:
        if name:
            return self.document.find(name).text
        else:
            return self.document.text


class HLClient(object):
    ACCEPTED_TOKEN_HEADERS = ['__RequestVerificationTokenone',
                              '__RequestVerificationToken']
    TOKEN_HEADER = '__RequestVerificationToken'
    host = ''
    token = ''
    connected = False

    @property
    def url(self):
        return f'http://{self.host}/'

    @property
    def api_url(self):
        return f'http://{self.host}/api/'

    def __init__(self, host: str):
        cookieProcessor = urllib.request.HTTPCookieProcessor()
        self._client = urllib.request.build_opener(cookieProcessor)
        if host:
            self.host = host

    def connect(self):
        self._client.open(f'{self.url}html/home.html', timeout=15)
        self.connected = True

    def _compute_challenge(self, username: bytes, password: bytes) -> bytes:
        return base64.b64encode(
            hashlib.sha256(
                username +
                base64.b64encode(hashlib.sha256(password).hexdigest().encode('utf-8')) +  # noqa
                self.token.encode('utf-8')).hexdigest().encode('utf-8')
        )

    def _request(self, req: urllib.request.Request) -> bytes:
        if self.token:
            req.add_header(self.TOKEN_HEADER, self.token)

        resp = self._client.open(req, timeout=15)

        # find the first of any of the ACCEPTED_TOKEN_HEADERS and save it
        for th in self.ACCEPTED_TOKEN_HEADERS:
            if th in dict(resp.getheaders()):
                self.token = resp.getheader(th)
                break

        return resp.read()

    def get(self, endpoint: str) -> HLResponse:
        req = urllib.request.Request(f'{self.api_url}{endpoint}', method='GET')
        return HLResponse(self._request(req))

    def post(self, endpoint: str, data: Any) -> HLResponse:
        req = urllib.request.Request(
            f'{self.api_url}{endpoint}', data=data, method='POST')
        return HLResponse(self._request(req))

    def obtain_token(self):
        res = self.get('webserver/SesTokInfo')
        self.token = res['TokInfo']

    def login(self, username: str, password: str) -> HLResponse:
        if not self.connected:
            self.connect()
        if not self.token:
            self.obtain_token()

        challenge = self._compute_challenge(
            username.encode('utf-8'), password.encode('utf-8'))

        data = HLRequest()
        data['Username'] = username
        data['Password'] = challenge.decode('utf-8')
        data['password_type'] = '4'

        return self.post('user/login', data)

    def get_status(self) -> HLResponse:
        '''
        <?xml version="1.0" encoding="UTF-8"?>
        <response>
        <ConnectionStatus>902</ConnectionStatus>
        <WifiConnectionStatus></WifiConnectionStatus>
        <SignalStrength></SignalStrength>
        <SignalIcon>5</SignalIcon>
        <CurrentNetworkType>4</CurrentNetworkType>
        <CurrentServiceDomain>3</CurrentServiceDomain>
        <RoamingStatus>0</RoamingStatus>
        <BatteryStatus></BatteryStatus>
        <BatteryLevel></BatteryLevel>
        <BatteryPercent></BatteryPercent>
        <simlockStatus>0</simlockStatus>
        <PrimaryDns></PrimaryDns>
        <SecondaryDns></SecondaryDns>
        <PrimaryIPv6Dns></PrimaryIPv6Dns>
        <SecondaryIPv6Dns></SecondaryIPv6Dns>
        <CurrentWifiUser>0</CurrentWifiUser>
        <TotalWifiUser>32</TotalWifiUser>
        <currenttotalwifiuser>32</currenttotalwifiuser>
        <ServiceStatus>2</ServiceStatus>
        <SimStatus>1</SimStatus>
        <WifiStatus>0</WifiStatus>
        <CurrentNetworkTypeEx>41</CurrentNetworkTypeEx>
        <maxsignal>5</maxsignal>
        <wifiindooronly>0</wifiindooronly>
        <wififrequence>0</wififrequence>
        <classify>cpe</classify>
        <flymode>0</flymode>
        <cellroam>1</cellroam>
        <usbup>0</usbup>
        </response>
        '''
        return self.get('monitoring/status')

    def set_net_mode(self, network_mode: str, network_band: str, lte_band: str) -> HLResponse:  # noqa
        '''
        <?xml version="1.0" encoding="UTF-8"?>
        <response>OK</response>
        '''
        data = HLRequest()
        data['NetworkMode'] = network_mode
        data['NetworkBand'] = network_band
        data['LTEBand'] = lte_band

        return self.post('net/net-mode', data)

    def register(self) -> HLResponse:
        '''
        <?xml version="1.0" encoding="UTF-8"?>
        <response>OK</response>
        '''
        data = HLRequest()
        data['Mode'] = '0'
        data['Plmn'] = ''
        data['Rat'] = ''

        return self.post('net/register', data)

    def device_control(self, code: str) -> HLResponse:
        '''
        '''
        data = HLRequest()
        data['Control'] = code

        return self.post('device/control', data)

    def reboot(self) -> HLResponse:
        return self.device_control('1')
