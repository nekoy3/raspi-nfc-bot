from functools import partial
import asyncio
import time

import binascii
import nfc

class MyCardReader(object):
    def __init__(self):
        #カードがタッチしているか
        self.on_card = False
        self.idm = 0

    #カードタッチされたときの処理
    def on_connect(self, tag):
        self.on_card = False
        #IDmのみ取得
        self.idm = binascii.hexlify(tag._nfcid) #取得したIDm
        return True
    
    #カードが離されたときの処理
    def on_release(self, tag):
        self.on_card = False
        return True

    #経過時間(n秒経過後Trueを返す)
    def afrer(self, started, n):
        return time.time() - started > n and not self.on_card

    #idmを読み取るためのメソッド(タイムアウトまで1秒)
    async def read_id(self, started, n):
        clf = nfc.ContactlessFrontend('usb') #USB機器との接続するためのオブジェクト
        try:
            rdwr_options = {
                'on-connect': self.on_connect,
                'on-release': self.on_release
            }
            #ここでカードがタッチ→離されるまでずっと待機し続けている
            clf.connect(
                rdwr=rdwr_options,
                terminate=partial(self.afrer, started, n)
            ) 
        finally:
            clf.close()
    
    def get_idm(self):
        tmp = self.idm
        self.idm = 0
        return tmp
    
    #カードがタッチされているかの状態を取得する（タッチされていたらTrue)
    def get_on_card(self):
        return self.on_card
#read_id(time.time(), 1)