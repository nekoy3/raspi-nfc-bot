#coding: utf-8
import discord

import logfile_rw
import f_global as fg

#登録解除ボタンセットのクラス
class UnregistButton(discord.ui.View):
    def __init__(self, session_id, db):
        super().__init__()
        self.add_item(UnregistOkButton(session_id, db))
        self.add_item(UnregistNoButton(session_id))

#登録解除OKボタン
class UnregistOkButton(discord.ui.Button):
    def __init__(self, session_id, db):
        super().__init__(label="削除する", style=discord.ButtonStyle.red)
        self.session_id = session_id
        self.db = db

    async def callback(self, interaction: discord.Interaction):
        #print(str(session_id) + " / " + str(sessions))
        record = self.db.getRecordIdByUser(interaction.user.id)
        record_id = record[0]

        if self.session_id in fg.sessions:
            self.db.removeRecord(record_id)
            await interaction.response.send_message('データを削除しました。', ephemeral=True)
            fg.sessions.remove(self.session_id) if self.session_id in fg.sessions else None
            logfile_rw.write_logfile('info', 'session', f'Session {self.session_id} unregisted record. {record[0]}')
        
        else:
            await interaction.response.send_message('このボタンは有効期限が切れています。', ephemeral=True)

#登録解除NOボタン
class UnregistNoButton(discord.ui.Button):
    def __init__(self, session_id):
        super().__init__(label="キャンセル", style=discord.ButtonStyle.secondary)
        self.session_id = session_id

    async def callback(self, interaction: discord.Interaction):
        if self.session_id in fg.sessions:
            await interaction.response.send_message('登録受付をキャンセルしました。', ephemeral=True)
            fg.sessions.remove(self.session_id) if self.session_id in fg.sessions else None
        
        else:
            await interaction.response.send_message('このボタンは有効期限が切れています。', ephemeral=True)