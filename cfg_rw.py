import configparser
import os

config = configparser.ConfigParser()

class ConfigClass:
    pass

def create_config():
    config.read('config.ini', encoding="utf-8_sig")

    config['SERVER'] = {'first_server_name': '', 'second_server_name': '', 'first_server_color': '0x66A6FF', 'second_server_color': '0xCA80FF', 'first_server_id': '', 'second_server_id': ''}
    config['TOKEN'] = {'token': ''}
    config['CHANNEL'] = {'first_channel_id': '', 'second_channel_id': ''}
    config['OTHER'] = {'max_roomcount': '10', 'error_message_color': '0xFF0000', 'can_max_over': True, 'daily_reset_time': '04:00', 'stop_warn_delay_minutes': '150'}
    config['CHAT'] = {'first_channel_id': '', 'second_channel_id': ''}

    with open('config.ini', 'w') as configfile:
        config.write(configfile)

def main():
    global config
    try:
        config.read('config.ini', encoding="utf-8_sig")

        configClass = ConfigClass()
        configClass.first_server_name = str(config['SERVER']['first_server_name'])
        configClass.second_server_name = str(config['SERVER']['second_server_name'])

        configClass.TOKEN = str(config['TOKEN']['token'])

        configClass.type_dict = {'one': config['SERVER']['first_server_color'], 'two': config['SERVER']['second_server_color'], 'er': config['OTHER']['error_message_color']}
        configClass.channel_id_list = [int(config['CHANNEL']['first_channel_id']), int(config['CHANNEL']['second_channel_id'])]
        configClass.webhook_channel_id_list = [int(config['CHAT']['first_channel_id']), int(config['CHAT']['second_channel_id'])]
        
        configClass.guild_id_list = [int(config['SERVER']['first_server_id']), int(config['SERVER']['second_server_id'])]
        if configClass.guild_id_list[0] == configClass.guild_id_list[1]:
            configClass.guild_id_list = [configClass.guild_id_list[0]]

        configClass.max_count = int(config['OTHER']['max_roomcount'])
        configClass.can_max_over = config['OTHER']['can_max_over']
        configClass.daily_reset_time = config['OTHER']['daily_reset_time']
        configClass.stop_warn_delay_minutes = int(config['OTHER']['stop_warn_delay_minutes'])

    except Exception as e:
        print("config.iniが存在しないか、設定が間違っています。\n" + str(e))
        #ファイルの存在確認(カレントディレクトリにconfig.iniがあるか)
        if not os.path.isfile('config.ini'):
            create_config()
        exit()
    else:
        return configClass

if __name__ == '__main__':
    main()