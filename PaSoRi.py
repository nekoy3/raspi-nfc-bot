from functools import partial
import asyncio
import time

'''
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
'''

#検証用
class MyCardReader():
    async def read_id(self):
        self.idm = "00000000000A"
        await asyncio.sleep(10)
    
    def get_idm(self):
        return self.idm
#https://www.kosh.dev/article/3/
'''
def main():
    #MyCardReaderクラスをインスタンス化
    cardReader = MyCardReader() 

    while True:
        #最初に表示
        print("Please Touch")

        #タッチ待ち
        cardReader.read_id()

        #リリース時の処理
        print("【 Released 】")
'''