import os
import time

import f_global

#ログファイル生成
def create_log_dir():
    os.mkdir('logs') if not os.path.exists('logs') else None

def tail(fn):
    with open(fn, 'r') as latest_file:
        lines = latest_file.readlines()
    print(str(lines))
    if len(lines) == 1:
        return lines[0]
    else:
        return lines[-1]

#ログファイル作成
def make_logfile():
    filename = time.strftime("room-%Y-%m-%d-%H-%M-%S") + ".log"
    f_global.f = open("./logs/" + filename, "a")

#ログ書き込み
def write_logfile(state, place, str): #ログレベル、処理、本文
    f_global.f.write(f"{time.strftime('%Y/%m/%d %H:%M:%S')}<{state}>:[{place}] {str}\n")
'''
error 緊急性は無いが確認次第修正するべき
info 基本的な動き
logfile_rw.write_logfile('info', 'bot', 'Bot ready.')
'''

def main():
    pass

if __name__ == '__main__':
    main()