import sys
import discord

import logfile_rw
import cfg_rw

class MyBot:
    pass

def main():
    mybot = MyBot()
    mybot.intents = discord.Intents.all() #全ての権限を許可
    #mybot.intents.message_content = True #メッセージコンテンツの読み取りを許可
    
    mybot.cfg = cfg_rw.main()
    mybot.chs = []
    mybot.hook_list = []
    mybot.guilds = []

    logfile_rw.create_log_dir()
    logfile_rw.make_logfile()
    
    print('Starting...')

    return mybot

if __name__ == '__main__':
    main()