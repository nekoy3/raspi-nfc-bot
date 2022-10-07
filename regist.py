#coding: utf-8
import discord
import asyncio
import datetime

import logfile_rw
import f_global as fg

#registerモードをonにし、新規registerコマンド受付を停止、登録済みカードはレコードを比較し通常通り認証する
async def regist_timelimit(client): 
    fg.regist_mode_flag = True
    await client.change_presence(status=discord.Status.online, activity=discord.Game('Registing mode'))
    #print("regist mode on") #デバッグ用
    sec = 15
    while sec > 0:
        await asyncio.sleep(1)
        if fg.regist_reset_flag:
            fg.regist_reset_flag = False
            print("regist mode broken")
            break
        sec-=1
        #print(sec)
    fg.regist_mode_flag = False
    await client.change_presence(status=discord.Status.online, activity=discord.Game('/register, /gc'))
    #print("regist mode off")

#registコマンドでボタンを表示するためにボタンのクラスを追加する
class RegistButton(discord.ui.View):
    def __init__(self, session_id, client):
        super().__init__()
        self.add_item(RegistOkButton(session_id, client))
        self.add_item(RegistNoButton(session_id))

#registコマンドでOKボタンを押したときの処理(登録処理を開始する)
class RegistOkButton(discord.ui.Button):
    def __init__(self, session_id, client):
        super().__init__(label="登録する", style=discord.ButtonStyle.green)
        self.session_id = session_id
        self.client = client

    async def callback(self, interaction: discord.Interaction):
        print(str(self.session_id) + " / " + str(fg.sessions))
        if self.session_id in fg.sessions:
            await interaction.response.send_message('登録を受け付けました。今から1分以内にカードリーダーに自身のカードをタッチして登録してください。\n1分を超えた場合は再度コマンドを入力してください。', ephemeral=True)
            asyncio.get_event_loop().create_task(regist_timelimit(self.client)) #registモード1分を測る
            fg.sessions.remove(self.session_id) if self.session_id in fg.sessions else None
        else:
            await interaction.response.send_message('このボタンは有効期限が切れています。', ephemeral=True)

#registコマンドでNOボタンを押したときの処理(登録処理をキャンセルする)
class RegistNoButton(discord.ui.Button):
    def __init__(self, session_id):
        super().__init__(label="キャンセル", style=discord.ButtonStyle.secondary)
        self.session_id = session_id

    async def callback(self, interaction: discord.Interaction):
        if self.session_id in fg.sessions:
            await interaction.response.send_message('登録受付をキャンセルしました。', ephemeral=True)
            fg.sessions.remove(self.session_id) if self.session_id in fg.sessions else None
        else:
            await interaction.response.send_message('このボタンは有効期限が切れています。', ephemeral=True)

#registコマンドが実行された時点でセッションをインスタンス化して保持し、時間切れで消滅する、セッションIDを保持し管理
class RegistSession(): 
    def __init__(self, session_id, interaction, st_name, st_num, st_belong):
        self.session_id = session_id
        self.interaction = interaction
        self.st_name = st_name
        self.st_num = st_num
        self.st_belong = st_belong
    
    async def regist_record(self, IDm, db): #学生証登録
        #「固有ID(int)」「学籍番号(string)」「名前(string)」「学生証ID(string)」「discordユーザid(int)」
        # 「登録日(string or datetime)」「最終認証日(string or datetime)」「room_status(boolean)」「所属(string)」
        now_datetime = datetime.datetime.now().strftime('%Y年%m月%d日 %H:%M')
        dm_channel = await self.interaction.user.create_dm()
        user_id = self.interaction.user.id

        try:
            db.addRecord(self.st_num, self.st_name, IDm, user_id, now_datetime, True, self.st_belong)
        except Exception as e:
            await dm_channel.send(content="エラーが発生しました。時間を空けてからお試しください。\n" + str(e))
            logfile_rw.write_logfile('error', 'session', f'Session {self.session_id} regist error. {self.st_name} {IDm} error->{str(e)}')
            fg.regist_reset_flag = True #regist_timelimitメソッドでregistモードをリセットするためのフラグ
        else:
            await dm_channel.send(content=f"学生証の登録が完了しました。登録したデータは/registを実行したチャンネルで/unregistを実行すると削除できます。\nカードID={IDm} 学籍番号={self.st_num} 名前={self.st_name} 様\n登録日時={now_datetime} 所属={self.st_belong}")
            logfile_rw.write_logfile('info', 'session', f'Session {self.session_id} registed record. {self.st_name} {IDm}')
            fg.regist_reset_flag = True
        finally:
            fg.sessions.remove(self.session_id) if self.session_id in fg.sessions else None
