from functools import partial
import asyncio
import time

import binascii
import nfc

class MyCardReader(object):
    def on_connect(self, tag):
        #IDmのみ取得
        self.idm = binascii.hexlify(tag._nfcid) #取得したIDm
        return True

    def read_id(self):
        clf = nfc.ContactlessFrontend('usb') #USB機器との接続するためのオブジェクト
        try:
            clf.connect(rdwr={'on-connect': self.on_connect}) #ここでカードがタッチ→離されるまでずっと待機し続けている
        finally:
            clf.close()
    
    def get_idm(self):
        return self.idm

def main():
    #MyCardReaderクラスをインスタンス化
    cardReader = MyCardReader() 

    while True:
        #タッチ待ち
        cardReader.read_id()