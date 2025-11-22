import json
import time
import uuid
import zlib
import random
import hashlib
import binascii
import pyscrypt
import itertools
import tls_client

from .crypto import Crypto
from typing import Union, Callable, Any

class Fingerprint:
    @staticmethod
    def encode(obj):
        payload = json.dumps(obj, separators=(",", ":")).encode()
        
        crc = zlib.crc32(payload) & 0xFFFFFFFF
        crc_hex = f"{crc:08x}"

        checksum = crc_hex.encode("ascii").upper()

        return checksum, checksum + b"#" + payload
    
    @staticmethod
    def fingerprint():
        start = int(time.time() * 1000)

        webgl_data = {
            "webgl_unmasked_renderer": "ANGLE (Apple, ANGLE Metal Renderer: Apple M2 Pro, Unspecified Version)",
            "webgl": [
                {
                    "webgl_extensions": "ANGLE_instanced_arrays;EXT_blend_minmax;EXT_clip_control;EXT_color_buffer_half_float;EXT_depth_clamp;EXT_disjoint_timer_query;EXT_float_blend;EXT_frag_depth;EXT_polygon_offset_clamp;EXT_shader_texture_lod;EXT_texture_compression_bptc;EXT_texture_compression_rgtc;EXT_texture_filter_anisotropic;EXT_texture_mirror_clamp_to_edge;EXT_sRGB;KHR_parallel_shader_compile;OES_element_index_uint;OES_fbo_render_mipmap;OES_standard_derivatives;OES_texture_float;OES_texture_float_linear;OES_texture_half_float;OES_texture_half_float_linear;OES_vertex_array_object;WEBGL_blend_func_extended;WEBGL_color_buffer_float;WEBGL_compressed_texture_astc;WEBGL_compressed_texture_etc;WEBGL_compressed_texture_etc1;WEBGL_compressed_texture_pvrtc;WEBGL_compressed_texture_s3tc;WEBGL_compressed_texture_s3tc_srgb;WEBGL_debug_renderer_info;WEBGL_debug_shaders;WEBGL_depth_texture;WEBGL_draw_buffers;WEBGL_lose_context;WEBGL_multi_draw;WEBGL_polygon_mode",
                    "webgl_extensions_hash": "9cbeeda2b4ce5415b07e1d1e43783a58",
                    "webgl_renderer": "WebKit WebGL",
                    "webgl_vendor": "WebKit",
                    "webgl_version": "WebGL 1.0 (OpenGL ES 2.0 Chromium)",
                    "webgl_shading_language_version": "WebGL GLSL ES 1.0 (OpenGL ES GLSL ES 1.0 Chromium)",
                    "webgl_aliased_line_width_range": "[1, 1]",
                    "webgl_aliased_point_size_range": "[1, 511]",
                    "webgl_antialiasing": True,
                    "webgl_bits": "8,8,24,8,8,0",
                    "webgl_max_params": "16,32,16384,1024,16384,16,16,30,16,16,1024",
                    "webgl_max_viewport_dims": "[16384, 16384]",
                    "webgl_unmasked_vendor": "Google Inc. (Apple)",
                    "webgl_unmasked_renderer": "ANGLE (Apple, ANGLE Metal Renderer: Apple M2 Pro, Unspecified Version)",
                    "webgl_vsf_params": "23,127,127,23,127,127,23,127,127",
                    "webgl_vsi_params": "0,31,30,0,31,30,0,31,30",
                    "webgl_fsf_params": "23,127,127,23,127,127,23,127,127",
                    "webgl_fsi_params": "0,31,30,0,31,30,0,31,30",
                    "webgl_hash_webgl": "a5c294663e62715a685b8a5f7d436da2"
                }
            ]
        }

        bins = [random.randrange(0,40) for _ in range(256)]
        bins[0] = random.randrange(14473, 16573)
        bins[-1] = random.randrange(14473, 16573)

        fp = {
            "metrics": {
                "fp2": 1,
                "browser": 0,
                "capabilities": 1,
                "gpu": 7,
                "dnt": 0,
                "math": 0, 
                "screen": 0,
                "navigator": 0,
                "auto": 1,
                "stealth": 0,
                "subtle": 0,
                "canvas": 5,
                "formdetector": 1,
                "be": 0
            },
            "start": start,
            "flashVersion": None,
            "plugins": [
                {"name": "PDF Viewer", "str": "PDF Viewer "},
                {"name": "Chrome PDF Viewer", "str": "Chrome PDF Viewer "},
                {"name": "Chromium PDF Viewer", "str": "Chromium PDF Viewer "},
                {"name": "Microsoft Edge PDF Viewer", "str": "Microsoft Edge PDF Viewer "},
                {"name": "WebKit built-in PDF", "str": "WebKit built-in PDF "}
            ],
            "dupedPlugins": "PDF Viewer Chrome PDF Viewer Chromium PDF Viewer Microsoft Edge PDF Viewer WebKit built-in PDF ||1920-1080-1032-24-*-*-*",
            "screenInfo": "1920-1080-1032-24-*-*-*",
            "referrer": "",
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
            "location": "",
            "webDriver": False,
            "capabilities": {
                "css": {
                    "textShadow": 1,
                    "WebkitTextStroke": 1,
                    "boxShadow": 1,
                    "borderRadius": 1,
                    "borderImage": 1,
                    "opacity": 1,
                    "transform": 1,
                    "transition": 1
                },
                "js": {
                    "audio": True,
                    "geolocation": random.choice([True, False]),
                    "localStorage": "supported",
                    "touch": False,
                    "video": True,
                    "webWorker": random.choice([True, False]),
                },
                "elapsed": 1
            },
            "gpu": {
                "vendor": webgl_data["webgl"][0]["webgl_unmasked_vendor"],
                "model": webgl_data["webgl_unmasked_renderer"],
                "extensions": webgl_data["webgl"][0]["webgl_extensions"].split(";")
            },
            "dnt": None,
            "math": {
                "tan": "-1.4214488238747245",
                "sin": "0.8178819121159085",
                "cos": "-0.5753861119575491"
            },
            "automation": {
                "wd": {
                    "properties": {
                        "document": [],
                        "window": [],
                        "navigator": []
                    }
                },
                "phantom": {
                    "properties": {
                        "window": []
                    }
                }
            },
            "stealth": {
                "t1": 0,
                "t2": 0,
                "i": 1,
                "mte": 0,
                "mtd": False
            },
            "crypto": {
                "crypto": 1,
                "subtle": 1,
                "encrypt": True,
                "decrypt": True,
                "wrapKey": True,
                "unwrapKey": True,
                "sign": True,
                "verify": True,
                "digest": True,
                "deriveBits": True,
                "deriveKey": True,
                "getRandomValues": True,
                "randomUUID": True
            },
            "canvas": {
                "hash": random.randrange(645172295, 735192295),
                "emailHash": None,
                "histogramBins": bins
            },
            "formDetected": False,
            "numForms": 0,
            "numFormElements": 0,
            "be": {
                "si": False
            },
            "end": start + 1,
            "errors": [],
            "version": "2.4.0",
            "id": str(uuid.uuid4()),
        }

        checksum, data = Fingerprint.encode(fp)
        return checksum.decode(), Crypto.encrypt(data)
    
class Verify:
    @staticmethod
    def _check(digest, difficulty):
        full, rem = divmod(difficulty, 8)
        if digest[:full] != b"\x00" * full:
            return False
        if rem and (digest[full] >> (8 - rem)):
            return False
        return True
    
    @staticmethod
    def _scrypt(input, salt, memory_cost):
        return binascii.hexlify(pyscrypt.hash(password=input.encode(), salt=salt.encode(), N=memory_cost, r=8, p=1, dkLen=16)).decode()
    
    @staticmethod
    def pow(input, checksum, difficulty):
        combined_bytes = (input + checksum).encode("utf-8")

        for nonce in itertools.count(0):
            data = combined_bytes + str(nonce).encode()
            digest = hashlib.sha256(data).digest()
            if Verify._check(digest, difficulty):
                return str(nonce)
            
        return None
    
    @staticmethod
    def compute_scrypt_nonce(input, checksum, difficulty):
        combined = input + checksum
        salt = checksum
        memory = 128

        for nonce in itertools.count(0):
            result = Verify._scrypt(f"{combined}{nonce}", salt, memory)
            if Verify._check(binascii.unhexlify(result), difficulty):
                return str(nonce)
    
        return None
    
    CHALLENGE_TYPES: dict[str, Union[Callable[[Any, Any, Any], str], str]] = {
        "h72f957df656e80ba55f5d8ce2e8c7ccb59687dba3bfb273d54b08a261b2f3002": compute_scrypt_nonce,
        "h7b0c470f0cfe3a80a9e26526ad185f484f6817d0832712a4a37a908786a6a67f": pow,
        "ha9faaffd31b4d5ede2a2e19d2d7fd525f66fee61911511960dcbb52d3c48ce25": "mp_verify"
    }

class Solver:
    def __init__(self):
        self.session = tls_client.Session(
            client_identifier="chrome_132",
            random_tls_extension_order=True
        )

        self.session.headers = {
            "Connection": "keep-alive",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "https://www.paypay.ne.jp",
            "Sec-Ch-Ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
        }

    def get_goku_props(self):
        response = self.session.get(
            "https://www.paypay.ne.jp/portal/api/v2/oauth2/authorize",
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "ja-JP,ja;q=0.9",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Host": "www.paypay.ne.jp",
                "is-emulator": "false",
                "Pragma": "no-cache",
                "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
                "sec-ch-ua-mobile": "?1",
                "sec-ch-ua-platform": '"Android"',
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
                "X-Requested-With": "jp.ne.paypay.android.app"
            }
        ).text

        goku_props = json.loads(response.split("window.gokuProps = ")[1].split(";")[0])
        return goku_props
    
    def get_inputs(self):
        response = self.session.get(
            "https://02dad1968f9c.81b5a82a.ap-northeast-1.token.awswaf.com/02dad1968f9c/a61454b1ee5d/2748e176355d/inputs",
            params={
                "client": "browser"
            }
        ).json()

        return response
    
    def build_payload(self):
        inputs = self.get_inputs()
        goku_props = self.get_goku_props()
        checksum, fp = Fingerprint.fingerprint()

        verify_func = Verify.CHALLENGE_TYPES[inputs["challenge_type"]]
        solution = verify_func(inputs["challenge"]["input"], checksum, inputs["difficulty"])

        payload = {
            "challenge": inputs["challenge"],
            "checksum": checksum,
            "solution": solution,
            "signals": [
                {
                    "name": "Zoey",
                    "value": {
                        "Present": fp
                    }
                }
            ],
            "existing_token": None,
            "client": "Browser",
            "domain": "www.paypay.ne.jp",
            "metrics": [
                {
                    "name": "2",
                    "value": random.uniform(0, 1),
                    "unit": "2"
                },
                {
                    "name": "100",
                    "value": 0,
                    "unit": "2"
                },
                {
                    "name": "101",
                    "value": 0,
                    "unit": "2"
                },
                {
                    "name": "102",
                    "value": 0,
                    "unit": "2"
                },
                {
                    "name": "103",
                    "value": 8,
                    "unit": "2"
                },
                {
                    "name": "104",
                    "value": 0,
                    "unit": "2"
                },
                {
                    "name": "105",
                    "value": 0,
                    "unit": "2"
                },
                {
                    "name": "106",
                    "value": 0,
                    "unit": "2"
                },
                {
                    "name": "107",
                    "value": 0,
                    "unit": "2"
                },
                {
                    "name": "108",
                    "value": 1,
                    "unit": "2"
                },
                {
                    "name": "undefined",
                    "value": 0,
                    "unit": "2"
                },
                {
                    "name": "110",
                    "value": 0,
                    "unit": "2"
                },
                {
                    "name": "111",
                    "value": 2,
                    "unit": "2"
                },
                {
                    "name": "112",
                    "value": 0,
                    "unit": "2"
                },
                {
                    "name": "undefined",
                    "value": 0,
                    "unit": "2"
                },
                {
                    "name": "3",
                    "value": 4,
                    "unit": "2"
                },
                {
                    "name": "7",
                    "value": 0,
                    "unit": "4"
                },
                {
                    "name": "1",
                    "value": random.uniform(10, 20),
                    "unit": "2"
                },
                {
                    "name": "4",
                    "value": 36.5,
                    "unit": "2"
                },
                {
                    "name": "5",
                    "value": random.uniform(0, 1),
                    "unit": "2"
                },
                {
                    "name": "6",
                    "value": random.uniform(50, 60),
                    "unit": "2"
                },
                {
                    "name": "0",
                    "value": random.uniform(130, 140),
                    "unit": "2"
                },
                {
                    "name": "8",
                    "value": 1,
                    "unit": "4"
                }
            ],
            "goku_props": goku_props
        }

        return payload
    
    def get_token(self):
        payload = self.build_payload()

        response = self.session.post(
            "https://02dad1968f9c.81b5a82a.ap-northeast-1.token.awswaf.com/02dad1968f9c/a61454b1ee5d/2748e176355d/verify",
            json=payload
        )

        if response.status_code == 200:
            return response.json()["token"]
        else:
            return None