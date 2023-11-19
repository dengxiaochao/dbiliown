import time
import requests
from config import Config
from dataclasses import dataclass
import wbi

g_ua = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:32.0) Gecko/20100101 Firefox/32.0'


class Bili(object):
    def __init__(self, c: Config) -> None:
        self.config = c
        self.wbi = wbi.WBIKey()
        self.inited = False
        self.sessdata = None
        self.refresh_token = None
        pass

    def init(self):
        if self.inited:
            return
        ok = self.qrcode_login()
        if not ok:
            raise Exception('Failed to login')
        self.inited = True

    def qrcode_login(self):
        qr_key, qr_img = self.gen_qr_login()
        print(f'scan QR code to login: {qr_img}')
        while True:
            data, sessdata = self.query_qr_status(qr_key)
            if data['code'] == 86101 or data['code'] == 86090:
                time.sleep(1)
                continue
            if data['code'] == 86038:
                print('QR code login timeout')
                return False
            if data['code'] == 0:
                print('QR code login success')
                self.refresh_token = data['refresh_token']
                self.sessdata = sessdata
                return True
            raise Exception(
                f'Unknown QR code login status: {data["code"]}, {data["message"]}')

    def gen_qr_login(self):
        qr_url = 'https://passport.bilibili.com/x/passport-login/web/qrcode/generate'
        qr_resp = self.get(qr_url)
        qr_key = qr_resp['data']['qrcode_key']
        qr_img = qr_resp['data']['url']
        return qr_key, qr_img

    def query_qr_status(self, qr_key):
        poll_url = 'https://passport.bilibili.com/x/passport-login/web/qrcode/poll'
        resp = requests.get(poll_url, params={'qrcode_key': qr_key})
        if resp.status_code != 200:
            raise Exception(
                f'Failed to poll QR code: {resp.status_code}, {resp.text}')
        body = resp.json()
        if body['code'] != 0:
            raise Exception(
                f'Failed to poll QR code: {body["code"]}, {body["message"]}')
        return body['data'], resp.cookies.get('SESSDATA')

    def get(self, url, params=None):
        resp = requests.get(url, params=params)
        if resp.status_code != 200:
            raise Exception(
                f'Failed to get {url}: {resp.status_code}, {resp.text}')
        body = resp.json()
        if body['code'] != 0:
            raise Exception(
                f'Failed to get {url}: {body["code"]}, {body["message"]}')
        return body['data']

    def sess_get(self, url, params=None):
        headers = {'User-Agent': g_ua,
                   'Cookie': f'SESSDATA={self.sessdata}'}
        resp = requests.get(url, params=params, headers=headers)
        if resp.status_code != 200:
            raise Exception(
                f'Failed to get {url}: {resp.status_code}, {resp.text}')
        body = resp.json()
        if body['code'] != 0:
            raise Exception(
                f'Failed to get {url}: {body["code"]}, {body["message"]}')
        return body['data']

    def user_videos(self, uid, from_ts=0):
        pn = 1
        vlist = []
        while True:
            params = {
                'mid': uid,
                'pn': pn,
                'ps': 30,
                'order': 'pubdate',
                'platform': 'web',
                'web_location': 1550101,
                'order_avoided': 'true'
            }
            query = self.wbi.sign(params)
            url = f'https://api.bilibili.com/x/space/wbi/arc/search?{query}'
            headers = {'User-Agent': g_ua,
                       'Cookie': f'SESSDATA={self.sessdata}'}
            resp = requests.get(url, headers=headers)
            if resp.status_code != 200:
                raise Exception(
                    f'Failed to get user videos: {resp.status_code}, {resp.text}')
            body = resp.json()
            if body['code'] != 0:
                raise Exception(
                    f'Failed to get user videos: {body["code"]}, {body["message"]}')
            oldest_ts = body['data']['list']['vlist'][-1]['created']
            if oldest_ts < from_ts:
                vlist += list_to_video_info([v for v in body['data']
                                            ['list']['vlist'] if v['created'] >= from_ts])
                break
            vlist += list_to_video_info(body['data']['list']['vlist'])
            pn += 1
            if body['data']['page']['count'] <= 30:
                break
        return vlist

@dataclass()
class VideoInfo:
    bvid: str
    title: str
    description: str
    created: int
    duration: int


def list_to_video_info(vlist):
    return [VideoInfo(v['bvid'], v['title'], v['description'], v['created'], duration_from_length(v['length'])) for v in vlist]


def duration_from_length(length: str) -> int:
    parts = length.split(':')
    if len(parts) > 2:
        raise Exception(f'Invalid length: {length}')
    ret = int(parts[0]) * 60
    if len(parts) == 2:
        ret += int(parts[1])
    return ret
