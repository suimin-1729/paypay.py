import uuid
import pkce
import random
import requests
import tls_client

from typing import NamedTuple
from .solver.solver import Solver

class PayPayUtils:
    @staticmethod
    def generate_vector(r1, r2, r3, precision=8):
        v1 = f"{random.uniform(*r1):.{precision}f}"
        v2 = f"{random.uniform(*r2):.{precision}f}"
        v3 = f"{random.uniform(*r3):.{precision}f}"
        return f"{v1}_{v2}_{v3}"
    
    @staticmethod
    def generate_device_state():
        device_orientation = PayPayUtils.generate_vector(
            (2.2, 2.6),
            (-0.2, -0.05),
            (-0.05, 0.1)
        )
        device_orientation_2 = PayPayUtils.generate_vector(
            (2.0, 2.6),
            (-0.2, -0.05),
            (-0.05, 0.2)
        )

        device_rotation = PayPayUtils.generate_vector(
            (-0.8, -0.6),
            (0.65, 0.8),
            (-0.12, -0.04)
        )
        device_rotation_2 = PayPayUtils.generate_vector(
            (-0.85, -0.4),
            (0.53, 0.9),
            (-0.15, -0.03)
        )

        device_acceleration = PayPayUtils.generate_vector(
            (-0.35, 0.0),
            (-0.01, 0.3),
            (-0.1, 0.1)
        )
        device_acceleration_2 = PayPayUtils.generate_vector(
            (0.01, 0.04),
            (-0.04, 0.09),
            (-0.03, 0.1)
        )

        class DeviceHeaders(NamedTuple):
            device_orientation: str
            device_orientation_2: str
            device_rotation: str
            device_rotation_2: str
            device_acceleration: str
            device_acceleration_2: str

        return DeviceHeaders(
            device_orientation,
            device_orientation_2,
            device_rotation,
            device_rotation_2,
            device_acceleration,
            device_acceleration_2
        )
    
    @staticmethod
    def set_device_state_to_headers(headers):
        device_state = PayPayUtils.generate_device_state()

        headers["Device-Orientation"] = device_state.device_orientation
        headers["Device-Orientation-2"] = device_state.device_orientation_2
        headers["Device-Rotation"] = device_state.device_rotation
        headers["Device-Rotation-2"] = device_state.device_rotation_2
        headers["Device-Acceleration"] = device_state.device_acceleration
        headers["Device-Acceleration-2"] = device_state.device_acceleration_2

        return headers
    
class PayPayException(Exception):
    pass

class AwsWafException(Exception):
    pass
    
class PayPay:
    def __init__(self, access_token=None, device_uuid=str(uuid.uuid4()), client_uuid=str(uuid.uuid4()), proxy=None):
        self.access_token = access_token
        self.device_uuid = device_uuid
        self.client_uuid = client_uuid
        self.proxy = proxy

        self.session = requests.Session()
        self.webview_session = tls_client.Session(
            client_identifier="chrome_132",
            random_tls_extension_order=True
        )

        if self.proxy != None:
            proxies = {
                "http": f"http://{proxy}",
                "https": f"http://{proxy}"
            }
            self.session.proxies.update(proxies)
            self.webview_session.proxies.update(proxies)

        solver = Solver()
        self.waf_token = solver.get_token()

        if self.waf_token == None:
            raise AwsWafException("Aws Waf Solve failed")
        else:
            self.webview_session.cookies.set(name="aws-waf-token", value=self.waf_token, domain="www.paypay.ne.jp")

        self.paypay_version = "5.11.1"

        device_state = PayPayUtils.generate_device_state()

        self.params = {
            "payPayLang": "ja"
        }

        self.headers = {
            "Accept": "*/*",
            "Accept-Charset": "UTF-8",
            "Accept-Encoding": "gzip",
            "Client-Mode": "NORMAL",
            "Client-OS-Release-Version": "10",
            "Client-OS-Type": "ANDROID",
            "Client-OS-Version": "29.0.0",
            "Client-Type": "PAYPAYAPP",
            "Client-UUID": self.client_uuid,
            "Client-Version": self.paypay_version,
            "Connection": "Keep-Alive",
            "Content-Type": "application/x-www-form-urlencoded",
            "Device-Acceleration": device_state.device_acceleration,
            "Device-Acceleration-2": device_state.device_acceleration_2,
            "Device-Brand-Name": "KDDI",
            "Device-Hardware-Name": "qcom",
            "Device-In-Call": "false",
            "Device-Lock-App-Setting": "false",
            "Device-Lock-Type": "NONE",
            "Device-Manufacturer-Name": "samsung",
            "Device-Name": "SCV38",
            "Device-Orientation": device_state.device_orientation,
            "Device-Orientation-2": device_state.device_orientation_2,
            "Device-Rotation": device_state.device_rotation,
            "Device-Rotation-2": device_state.device_rotation_2,
            "Device-UUID": self.device_uuid,
            "Host": "app4.paypay.ne.jp",
            "Is-Emulator": "false",
            "Network-Status": "WIFI",
            "System-Locale": "ja",
            "Timezone": "Asia/Tokyo",
            "User-Agent": f"PaypayApp/{self.paypay_version} Android10"
        }

        if self.access_token != None:
            self.headers["Authorization"] = f"Bearer {self.access_token}"
            self.headers["Content-Type"] = "application/json"

    def login_start(self, phone, password):
        if self.access_token != None:
            raise PayPayException("You are already logged in")
        
        self.verifier, self.challenge = pkce.generate_pkce_pair(43)

        _response = self.session.post(
            "https://app4.paypay.ne.jp/bff/v2/oauth2/par",
            params=self.params,
            headers=self.headers,
            data={
                "clientId": "pay2-mobile-app-client",
                "clientAppVersion": self.paypay_version,
                "clientOsVersion": "29.0.0",
                "clientOsType": "ANDROID",
                "redirectUri": "paypay://oauth2/callback",
                "responseType": "code",
                "state": pkce.generate_code_verifier(43),
                "codeChallenge": self.challenge,
                "codeChallengeMethod": "S256",
                "scope": "REGULAR",
                "tokenVersion": "v2",
                "prompt": "",
                "uiLocales": "ja"
            }
        )
        try:
            response = _response.json()
            if response["header"]["resultCode"] != "S0000":
                raise PayPayException(response)
        except:
            raise PayPayException("Connections from outside Japan are not possible.")

        self.webview_session.get(
            "https://www.paypay.ne.jp/portal/api/v2/oauth2/authorize",
            params={
                "client_id": "pay2-mobile-app-client",
                "request_uri": response["payload"]["requestUri"]
            },
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "ja-JP,ja;q=0.9",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Host": "www.paypay.ne.jp",
                "is-emulator": "false",
                "Pragma": "no-cache",
                "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132", "Android WebView";v="132"',
                "sec-ch-ua-mobile": "?1",
                "sec-ch-ua-platform": '"Android"',
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1",
                "User-Agent": f"Mozilla/5.0 (Linux; Android 10; SCV38 Build/QP1A.190711.020; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/132.0.6834.163 Mobile Safari/537.36 jp.pay2.app.android/{self.paypay_version}",
                "X-Requested-With": "jp.ne.paypay.android.app"
            }
        )
        
        self.webview_session.get(
            "https://www.paypay.ne.jp/portal/api/v2/oauth2/authorize",
            params={
                "client_id": "pay2-mobile-app-client",
                "request_uri": response["payload"]["requestUri"]
            },
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "ja-JP,ja;q=0.9",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Host": "www.paypay.ne.jp",
                "is-emulator": "false",
                "Pragma": "no-cache",
                "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132", "Android WebView";v="132"',
                "sec-ch-ua-mobile": "?1",
                "sec-ch-ua-platform": '"Android"',
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1",
                "User-Agent": f"Mozilla/5.0 (Linux; Android 10; SCV38 Build/QP1A.190711.020; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/132.0.6834.163 Mobile Safari/537.36 jp.pay2.app.android/{self.paypay_version}",
                "X-Requested-With": "jp.ne.paypay.android.app"
            }
        )

        self.webview_session.get(
            "https://www.paypay.ne.jp/portal/oauth2/sign-in",
            params={
                "client_id": "pay2-mobile-app-client",
                "mode": "landing"
            },
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "ja-JP,ja;q=0.9",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Host": "www.paypay.ne.jp",
                "is-emulator": "false",
                "Pragma": "no-cache",
                "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132", "Android WebView";v="132"',
                "sec-ch-ua-mobile": "?1",
                "sec-ch-ua-platform": '"Android"',
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1",
                "User-Agent": f"Mozilla/5.0 (Linux; Android 10; SCV38 Build/QP1A.190711.020; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/132.0.6834.163 Mobile Safari/537.36 jp.pay2.app.android/{self.paypay_version}",
                "X-Requested-With": "jp.ne.paypay.android.app"
            }
        )

        _response = self.webview_session.get(
            "https://www.paypay.ne.jp/portal/api/v2/oauth2/par/check",
            headers={
                "Accept": "application/json, text/plain, */*",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "ja-JP,ja;q=0.9",
                "Cache-Control": "no-cache",
                "Client-Id": "pay2-mobile-app-client",
                "Client-Type": "PAYPAYAPP",
                "Connection": "keep-alive",
                "Host": "www.paypay.ne.jp",
                "Pragma": "no-cache",
                "Referer": "https://www.paypay.ne.jp/portal/oauth2/sign-in?client_id=pay2-mobile-app-client&mode=landing",
                "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132", "Android WebView";v="132")',
                "sec-ch-ua-mobile": "?1",
                "sec-ch-ua-platform": '"Android"',
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
                "User-Agent": f"Mozilla/5.0 (Linux; Android 10; SCV38 Build/QP1A.190711.020; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/132.0.6834.163 Mobile Safari/537.36 jp.pay2.app.android/{self.paypay_version}",
                "X-Requested-With": "jp.ne.paypay.android.app"
            }
        )
        try:
            response = _response.json()
            if response["header"]["resultCode"] != "S0000":
                raise PayPayException(response)
        except:
            raise PayPayException("Connections from outside Japan are not possible.")

        _response = self.webview_session.post(
            "https://www.paypay.ne.jp/portal/api/v2/oauth2/sign-in/password",
            headers={
                "Accept": "application/json, text/plain, */*",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "ja-JP,ja;q=0.9",
                "Cache-Control": "no-cache",
                "Client-Id": "pay2-mobile-app-client",
                "Client-OS-Type": "ANDROID",
                "Client-OS-Version": "29.0.0",
                "Client-Type": "PAYPAYAPP",
                "Client-Version": self.paypay_version,
                "Connection": "keep-alive",
                "Content-Type": "application/json",
                "Host": "www.paypay.ne.jp",
                "Origin": "https://www.paypay.ne.jp",
                "Pragma": "no-cache",
                "Referer": "https://www.paypay.ne.jp/portal/oauth2/sign-in?client_id=pay2-mobile-app-client&mode=landing",
                "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132", "Android WebView";v="132")',
                "sec-ch-ua-mobile": "?1",
                "sec-ch-ua-platform": '"Android"',
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
                "User-Agent": f"Mozilla/5.0 (Linux; Android 10; SCV38 Build/QP1A.190711.020; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/132.0.6834.163 Mobile Safari/537.36 jp.pay2.app.android/{self.paypay_version}",
                "X-Requested-With": "jp.ne.paypay.android.app"
            },
            json={
                "username": phone,
                "password": password,
                "signInAttemptCount": 1
            }
        )
        try:
            response = _response.json()
            if response["header"]["resultCode"] != "S0000":
                raise PayPayException(response)
        except:
            raise PayPayException("Connections from outside Japan are not possible.")
        
        try:
            uri = response["payload"]["redirectUrl"].replace("paypay://oauth2/callback?","").split("&")
            
            headers = self.headers
            del headers["Device-Lock-Type"]
            del headers["Device-Lock-App-Setting"]

            _response = self.session.post(
                "https://app4.paypay.ne.jp/bff/v2/oauth2/token",
                params=self.params,
                headers=headers,
                data={
                    "clientId": "pay2-mobile-app-client",
                    "redirectUri": "paypay://oauth2/callback",
                    "code": uri[0].replace("code=",""),
                    "codeVerifier": self.verifier
                }
            )
            try:
                response = _response.json()
                if response["header"]["resultCode"] != "S0000":
                    raise PayPayException(response)
            except:
                raise PayPayException("Connections from outside Japan are not possible.")
            
            self.access_token= response["payload"]["accessToken"]
            self.headers["Authorization"] = f"Bearer {self.access_token}"
            self.headers["Content-Type"] = "application/json"

            self.headers = PayPayUtils.set_device_state_to_headers(self.headers)

            return True
        except:
            pass

        _response = self.webview_session.post(
            "https://www.paypay.ne.jp/portal/api/v2/oauth2/extension/code-grant/update",
            headers={
                "Accept": "application/json, text/plain, */*",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "ja-JP,ja;q=0.9",
                "Cache-Control": "no-cache",
                "Client-Id": "pay2-mobile-app-client",
                "Client-OS-Type": "ANDROID",
                "Client-OS-Version": "29.0.0",
                "Client-Type": "PAYPAYAPP",
                "Client-Version": self.paypay_version,
                "Connection": "keep-alive",
                "Content-Type": "application/json",
                "Host": "www.paypay.ne.jp",
                "Origin": "https://www.paypay.ne.jp",
                "Pragma": "no-cache",
                "Referer": "https://www.paypay.ne.jp/portal/oauth2/sign-in?client_id=pay2-mobile-app-client&mode=landing",
                "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132", "Android WebView";v="132")',
                "sec-ch-ua-mobile": "?1",
                "sec-ch-ua-platform": '"Android"',
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
                "User-Agent": f"Mozilla/5.0 (Linux; Android 10; SCV38 Build/QP1A.190711.020; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/132.0.6834.163 Mobile Safari/537.36 jp.pay2.app.android/{self.paypay_version}",
                "X-Requested-With": "jp.ne.paypay.android.app"
            },
            json={}
        )
        try:
            response = _response.json()
            if response["header"]["resultCode"] != "S0000":
                raise PayPayException(response)
        except:
            raise PayPayException("Connections from outside Japan are not possible.")
        
        _response = self.webview_session.post(
            "https://www.paypay.ne.jp/portal/api/v2/oauth2/extension/code-grant/update",
            headers={
                "Accept": "application/json, text/plain, */*",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "ja-JP,ja;q=0.9",
                "Cache-Control": "no-cache",
                "Client-Id": "pay2-mobile-app-client",
                "Client-OS-Type": "ANDROID",
                "Client-OS-Version": "29.0.0",
                "Client-Type": "PAYPAYAPP",
                "Client-Version": self.paypay_version,
                "Connection": "keep-alive",
                "Content-Type": "application/json",
                "Host": "www.paypay.ne.jp",
                "Origin": "https://www.paypay.ne.jp",
                "Pragma": "no-cache",
                "Referer": "https://www.paypay.ne.jp/portal/oauth2/verification-method?client_id=pay2-mobile-app-client&mode=navigation-2fa",
                "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132", "Android WebView";v="132")',
                "sec-ch-ua-mobile": "?1",
                "sec-ch-ua-platform": '"Android"',
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
                "User-Agent": f"Mozilla/5.0 (Linux; Android 10; SCV38 Build/QP1A.190711.020; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/132.0.6834.163 Mobile Safari/537.36 jp.pay2.app.android/{self.paypay_version}",
                "X-Requested-With": "jp.ne.paypay.android.app"
            },
            json={
                "params": {
                    "extension_id":"user-main-2fa-v1",
                    "data": {
                        "type": "SELECT_FLOW",
                        "payload": {
                            "flow": "OTL",
                            "sign_in_method": "MOBILE",
                            "base_url": "https://www.paypay.ne.jp/portal/oauth2/l"
                        }
                    }
                }
            }
        )
        try:
            response = _response.json()
            if response["header"]["resultCode"] != "S0000":
                raise PayPayException(response)
        except:
            raise PayPayException("Connections from outside Japan are not possible.")
        
        _response = self.webview_session.post(
            "https://www.paypay.ne.jp/portal/api/v2/oauth2/extension/code-grant/side-channel/next-action-polling",
            headers={
                "Accept": "application/json, text/plain, */*",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "ja-JP,ja;q=0.9",
                "Cache-Control": "no-cache",
                "Client-Id": "pay2-mobile-app-client",
                "Client-OS-Type": "ANDROID",
                "Client-OS-Version": "29.0.0",
                "Client-Type": "PAYPAYAPP",
                "Client-Version": self.paypay_version,
                "Connection": "keep-alive",
                "Content-Type": "application/json",
                "Host": "www.paypay.ne.jp",
                "Origin": "https://www.paypay.ne.jp",
                "Pragma": "no-cache",
                "Referer": "https://www.paypay.ne.jp/portal/oauth2/otl-request?client_id=pay2-mobile-app-client&mode=navigation-2fa",
                "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132", "Android WebView";v="132")',
                "sec-ch-ua-mobile": "?1",
                "sec-ch-ua-platform": '"Android"',
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
                "User-Agent": f"Mozilla/5.0 (Linux; Android 10; SCV38 Build/QP1A.190711.020; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/132.0.6834.163 Mobile Safari/537.36 jp.pay2.app.android/{self.paypay_version}",
                "X-Requested-With": "jp.ne.paypay.android.app"
            },
            json={
                "waitUntil": "PT5S"
            }
        )
        try:
            response = _response.json()
            if response["header"]["resultCode"] != "S0000":
                raise PayPayException(response)
        except:
            raise PayPayException("Connections from outside Japan are not possible.")
    
    def login_confirm(self, accept_url):
        if "https://" in accept_url:
            accept_url = accept_url.replace("https://www.paypay.ne.jp/portal/oauth2/l?id=", "")

        _response = self.webview_session.post(
            "https://www.paypay.ne.jp/portal/api/v2/oauth2/extension/sign-in/2fa/otl/verify",
            headers={
                "Accept": "application/json, text/plain, */*",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "ja-JP,ja;q=0.9",
                "Client-Id": "pay2-mobile-app-client",
                "Client-OS-Type": "ANDROID",
                "Client-OS-Version": "29.0.0",
                "Client-Type": "PAYPAYAPP",
                "Client-Version": self.paypay_version,
                "Connection": "keep-alive",
                "Content-Type": "application/json",
                "Host": "www.paypay.ne.jp",
                "Origin": "https://www.paypay.ne.jp",
                "Pragma": "no-cache",
                "Referer": f"https://www.paypay.ne.jp/portal/oauth2/l?id={accept_url}&client_id=pay2-mobile-app-client",
                "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132", "Android WebView";v="132")',
                "sec-ch-ua-mobile": "?1",
                "sec-ch-ua-platform": '"Android"',
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
                "User-Agent": f"Mozilla/5.0 (Linux; Android 10; SCV38 Build/QP1A.190711.020; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/132.0.6834.163 Mobile Safari/537.36 jp.pay2.app.android/{self.paypay_version}",
                "X-Requested-With": "jp.ne.paypay.android.app"
            },
            json={
                "code": accept_url
            }
        )
        try:
            response = _response.json()
            if response["header"]["resultCode"] != "S0000":
                raise PayPayException(response)
        except:
            raise PayPayException("Connections from outside Japan are not possible.")
        
        _response = self.webview_session.post(
            "https://www.paypay.ne.jp/portal/api/v2/oauth2/extension/code-grant/update",
            headers={
                "Accept": "application/json, text/plain, */*",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "ja-JP,ja;q=0.9",
                "Cache-Control": "no-cache",
                "Client-Id": "pay2-mobile-app-client",
                "Client-OS-Type": "ANDROID",
                "Client-OS-Version": "29.0.0",
                "Client-Type": "PAYPAYAPP",
                "Client-Version": self.paypay_version,
                "Connection": "keep-alive",
                "Content-Type": "application/json",
                "Host": "www.paypay.ne.jp",
                "Origin": "https://www.paypay.ne.jp",
                "Pragma": "no-cache",
                "Referer": f"https://www.paypay.ne.jp/portal/oauth2/l?id={accept_url}&client_id=pay2-mobile-app-client",
                "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132", "Android WebView";v="132")',
                "sec-ch-ua-mobile": "?1",
                "sec-ch-ua-platform": '"Android"',
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
                "User-Agent": f"Mozilla/5.0 (Linux; Android 10; SCV38 Build/QP1A.190711.020; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/132.0.6834.163 Mobile Safari/537.36 jp.pay2.app.android/{self.paypay_version}",
                "X-Requested-With": "jp.ne.paypay.android.app"
            },
            json={
                "params": {
                    "extension_id": "user-main-2fa-v1",
                    "data": {
                        "type": "COMPLETE_OTL",
                        "payload": None
                    }
                }
            }
        )
        try:
            response = _response.json()
            if response["header"]["resultCode"] != "S0000":
                raise PayPayException(response)
        except:
            raise PayPayException("Connections from outside Japan are not possible.")
        
        try:
            uri = response["payload"]["redirect_uri"].replace("paypay://oauth2/callback?","").split("&")

            headers = self.headers
            del headers["Device-Lock-Type"]
            del headers["Device-Lock-App-Setting"]

            _response = self.session.post(
                "https://app4.paypay.ne.jp/bff/v2/oauth2/token",
                params=self.params,
                headers=headers,
                data={
                    "clientId": "pay2-mobile-app-client",
                    "redirectUri": "paypay://oauth2/callback",
                    "code": uri[0].replace("code=",""),
                    "codeVerifier": self.verifier
                }
            )
            try:
                response = _response.json()
                if response["header"]["resultCode"] != "S0000":
                    raise PayPayException(response)
            except:
                raise PayPayException("Connections from outside Japan are not possible.")
            
            self.access_token= response["payload"]["accessToken"]
            self.headers["Authorization"] = f"Bearer {self.access_token}"
            self.headers["Content-Type"] = "application/json"

            self.headers = PayPayUtils.set_device_state_to_headers(self.headers)
        except:
            pass
    
    def get_profile(self):
        _response = self.session.get(
            "https://app4.paypay.ne.jp/bff/v2/getProfileDisplayInfo",
            headers=self.headers,
            params={
                "includeExternalProfileSync": "true",
                "completedOptionalTasks": "ENABLED_NEARBY_DEALS",
                "payPayLang": "ja"
            }
        )
        try:
            response = _response.json()
            if response["header"]["resultCode"] != "S0000":
                return None
        except:
            raise PayPayException("Connections from outside Japan are not possible.")
        
        display_name = response["payload"]["userProfile"]["nickName"]
        external_user_id = response["payload"]["userProfile"]["externalUserId"]
        icon_image_url = response["payload"]["userProfile"]["avatarImageUrl"]
        
        class GetProfileResponse(NamedTuple):
            display_name: str
            external_user_id: str
            icon_image_url: str
            raw: dict
        
        return GetProfileResponse(display_name, external_user_id, icon_image_url, response)
    
    def get_balance(self):
        _response = self.session.get(
            "https://app4.paypay.ne.jp/bff/v1/getBalanceInfo",
            params={
                "includePendingBonusLite": "false",
                "includePending": "true",
                "noCache": "true",
                "includeKycInfo": "true",
                "includePayPaySecuritiesInfo": "true",
                "includePointInvestmentInfo": "true",
                "includePayPayBankInfo": "true",
                "includeGiftVoucherInfo": "true",
                "payPayLang": "ja"
            },
            headers=self.headers
        )
        try:
            response = _response.json()
            if response["header"]["resultCode"] != "S0000":
                return None
        except:
            raise PayPayException("Connections from outside Japan are not possible.")
        
        try:
            money = response["payload"]["walletDetail"]["emoneyBalanceInfo"]["balance"]
        except:
            money = 0
        money_lite = response["payload"]["walletDetail"]["prepaidBalanceInfo"]["balance"]

        total_balance = response["payload"]["walletSummary"]["allTotalBalanceInfo"]["balance"]
        useable_balance = response["payload"]["walletSummary"]["usableBalanceInfoWithoutCashback"]["balance"]
        point_balance = response["payload"]["walletDetail"]["cashBackBalanceInfo"]["balance"]

        class GetBalanceResponse(NamedTuple):
            money: int
            money_lite: int
            total_balance: int
            useable_balance: int
            point_balance: int
            raw: dict

        return GetBalanceResponse(money, money_lite, total_balance, useable_balance, point_balance, response)
    
    def get_claim(self, amount: int = None):
        payload = {
            "amount": None,
            "sessionId": None
        }
        if amount != None:
            payload["amount"] = amount
            payload["sessionId"] = str(uuid.uuid4())

        _response = self.session.post(
            "https://app4.paypay.ne.jp/bff/v1/createP2PCode",
            params=self.params,
            headers=self.headers,
            json=payload
        )
        try:
            response = _response.json()
            if response["header"]["resultCode"] != "S0000":
                return None
        except:
            raise PayPayException("Connections from outside Japan are not possible.")
        
        claim_link = response["payload"]["p2pCode"]

        class GetClaimResponse(NamedTuple):
            claim_link: str
            raw: dict
        
        return GetClaimResponse(claim_link, response)
    
    def check_link(self, url):
        if "https://" in url:
            url = url.replace("https://pay.paypay.ne.jp/", "")

        _response = self.session.get(
            "https://app4.paypay.ne.jp/bff/v2/getP2PLinkInfo",
            params={
                "verificationCode": url,
                "payPayLang": "ja"
            },
            headers=self.headers
        )
        try:
            response = _response.json()
            if response["header"]["resultCode"] != "S0000":
                return None
        except:
            raise PayPayException("Connections from outside Japan are not possible.")
        
        sender_display_name = response["payload"]["sender"]["displayName"]
        sender_external_user_id = response["payload"]["sender"]["externalId"]
        sender_icon_url = response["payload"]["sender"]["photoUrl"]

        order_id = response["payload"]["pendingP2PInfo"]["orderId"]
        order_status = response["payload"]["orderStatus"]
        chat_room_id = response["payload"]["message"]["chatRoomId"]
        amount = response["payload"]["pendingP2PInfo"]["amount"]
        status = response["payload"]["message"]["data"]["status"]
        is_set_passcode = response["payload"]["pendingP2PInfo"]["isSetPasscode"]

        money_lite = response["payload"]["message"]["data"]["subWalletSplit"]["senderPrepaidAmount"]
        money = response["payload"]["message"]["data"]["subWalletSplit"]["senderEmoneyAmount"]

        class CheckLinkResponse(NamedTuple):
            sender_display_name: str
            sender_external_user_id: str
            sender_icon_url: str
            order_id: str
            order_status: str
            chat_room_id: str
            amount: int
            status: str
            is_set_passcode: bool
            money: int
            money_lite: int
            raw: dict
        
        return CheckLinkResponse(sender_display_name, sender_external_user_id, sender_icon_url, order_id, order_status, chat_room_id, amount, status, is_set_passcode, money, money_lite, response)
        
    def accept_link(self, url, passcode=None):
        if "https://" in url:
            url = url.replace("https://pay.paypay.ne.jp/", "")

        info = self.check_link(url)
        if info == None:
            return False
        elif info.order_status != "PENDING":
            return False
        
        payload = {
            "requestId": str(uuid.uuid4()),
            "orderId": info["payload"]["pendingP2PInfo"]["orderId"],
            "verificationCode": url,
            "passcode": None,
            "senderMessageId": info["payload"]["message"]["messageId"],
            "senderChannelUrl": info["payload"]["message"]["chatRoomId"]
        }

        if info.is_set_passcode:
            payload["passcode"] = passcode

        _response = self.session.post(
            "https://app4.paypay.ne.jp/bff/v2/acceptP2PSendMoneyLink",
            params=self.params,
            headers=self.headers,
            json=payload
        )
        try:
            response = _response.json()
            if response["header"]["resultCode"] != "S0000":
                return False
        except:
            raise PayPayException("Connections from outside Japan are not possible.")
        
        return True
    
    def reject_link(self, url: str):
        if "https://" in url:
            url = url.replace("https://pay.paypay.ne.jp/", "")

        info = self.check_link(url)
        if info == None:
            return False
        elif info.order_status != "PENDING":
            return False
        
        payload = {
            "requestId": str(uuid.uuid4()),
            "orderId": info["payload"]["pendingP2PInfo"]["orderId"],
            "verificationCode": url,
            "senderMessageId": info["payload"]["message"]["messageId"],
            "senderChannelUrl": info["payload"]["message"]["chatRoomId"]
        }

        _response = self.session.post(
            "https://app4.paypay.ne.jp/bff/v2/rejectP2PSendMoneyLink",
            params=self.params,
            headers=self.headers,
            json=payload
        )
        try:
            response = _response.json()
            if response["header"]["resultCode"] != "S0000":
                return False
        except:
            raise PayPayException("Connections from outside Japan are not possible.")
        
        return True
    
    def create_link(self, amount: int, passcode: str = None):
        payload = {
            "requestId": str(uuid.uuid4()),
            "amount": amount,
            "socketConnection": "P2P",
            "theme": "default-sendmoney",
            "source": "sendmoney_home_sns"
        }
        if passcode != None:
            payload["passcode"] = passcode

        _response = self.session.post(
            "https://app4.paypay.ne.jp/bff/v2/executeP2PSendMoneyLink",
            params=self.params,
            headers=self.headers,
            json=payload
        )
        try:
            response = _response.json()
            if response["header"]["resultCode"] != "S0000":
                return None
        except:
            raise PayPayException("Connections from outside Japan are not possible.")
        
        link = response["payload"]["link"]

        order_id = response["payload"]["orderId"]
        chat_room_id = response["payload"]["chatRoomId"]

        class CreateLinkResponse(NamedTuple):
            link: str
            order_id: str
            chat_room_id: str
            raw: dict
        
        return CreateLinkResponse(link, order_id, chat_room_id, response)
    
    def bypass(self):
        _response = self.session.get(
            "https://app4.paypay.ne.jp/bff/v1/getGlobalServiceStatus",
            params={
                "payPayLang": "en"
            },
            headers=self.headers
        )
        try:
            response = _response.json()
            if response["header"]["resultCode"] != "S0000":
                return False
        except:
            return False
        
        self.session.post(
            "https://app4.paypay.ne.jp/bff/v3/getHomeDisplayInfo",
            params={
                "payPayLang": "ja"
            },
            headers=self.headers,
            json={
                "excludeMissionBannerInfoFlag": False,
                "includeBeginnerFlag": False,
                "includeSkinInfoFlag": False,
                "networkStatus": "WIFI"
            }
        )

        self.session.get(
            "https://app4.paypay.ne.jp/bff/v1/getSearchBar?payPayLang=ja",
            params={
                "payPayLang": "ja"
            },
            headers=self.headers
        )

        return True