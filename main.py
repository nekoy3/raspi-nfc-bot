from code import interact
import discord
from discord import app_commands
from discord import Webhook
from datetime import datetime
import asyncio
import aiohttp
import random
import datetime
import time

from db_rw import DatabaseClass
import start
from PaSoRi import MyCardReader
import logfile_rw
import f_global as fg
import regist as r
import unregist as ur

client = None #bot本体のためのインスタンス（になるもの）
chs = [] #コマンド実行用チャンネルを取得して格納するリスト
guilds = [] #コマンド実装するdiscordサーバーのIDを格納するリスト
db = DatabaseClass() #データベース操作関連クラスのインスタンス化

stop_warn_infomation_flag = False #人数オーバー時の警告を周期的に行うまでの待機時間Trueになるフラグ
stop_warn_count = 0 #configを読み込んで人数オーバー警告をする人数の閾値を格納する変数

#Discordの処理関連をするためのクラス
#ここでコマンドを実装するdiscordサーバーを指定したり権限の設定項目を引き渡したり(初期設定）してbotのオブジェクトを生成
class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self) #全てのコマンドを管理するCommandTree型オブジェクトを生成

    async def setup_hook(self):
        for id in mybot.cfg.guild_id_list:
            guild=discord.Object(id=id)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)

#起動時設定（config読み取りやデータベースオープンなど）
mybot = start.main()

#botを動かすためのインスタンスを生成
client = MyClient(intents=mybot.intents)

#詳細メッセージ付きのembed(埋め込みメッセージ)を返す
def get_descript_embed(title, descrip, name, icon, timestamp, footer):
    embed = discord.Embed(title=title)
    embed.description = descrip
    embed.set_author(name=name, icon_url=icon.url)
    embed.timestamp = timestamp
    embed.set_footer(text=footer)
    return embed

#簡略化したembedを返す
def add_embed(title, descrip, type):
    embed = discord.Embed(title=title, description=descrip, color=int(mybot.cfg.type_dict[type], 16))
    return embed

#渡したメッセージを渡した秒数後に返す
def delete_message(msg, seconds):
    msg.delete(delay=seconds)

@client.event #client(botのインスタンス)が何かを検知した時に実行(メソッド名に依存)
async def on_ready(): #on_readyはbotが起動しログイン完了時に一度のみ実行する（詳細は省く）
    global chs, my_guilds
    logfile_rw.write_logfile('info', 'bot', 'Bot ready.')
    print('Logged in as\n' + client.user.name + "\n" + str(client.user.id) + "\n------")

    #botの状態を変更
    await client.change_presence(status=discord.Status.online, activity=discord.Game('/help'))
    await client.user.edit(username='RMBくん')

    #configで設定したチャンネルが同一の物であれば、1つで統一
    if mybot.cfg.channel_id_list[0] == mybot.cfg.channel_id_list[1]:
        chs = [client.get_channel(mybot.cfg.channel_id_list[0])]
    else:
        chs = [client.get_channel(mybot.cfg.channel_id_list[0]), client.get_channel(mybot.cfg.channel_id_list[1])]

    #discordサーバーidも同様に
    if mybot.cfg.guild_id_list[0] == mybot.cfg.guild_id_list[1]:
        my_guilds = [client.get_guild(mybot.cfg.guild_id_list[0])]
    else:
        my_guilds = [client.get_guild(mybot.cfg.guild_id_list[0]), client.get_guild(mybot.cfg.guild_id_list[1])]
    
    #カードタッチ待機メソッドを別スレッドに投げる
    #非同期処理についてはこのファイルの最下行に説明がある
    fg.tasks.append(asyncio.get_event_loop().create_task(card_touch_waiting_loop()))

#webhookを送信するメソッド
async def webhook_sent(channel_id, user_name, user_icon, **kwargs):
    #kwargsは可変長引数で、「key=value」といった記述をすることで、dict型でセットで渡すことが出来る。
    #この場合kwargs['key']でvalueを得る事が出来る。
    
    #contentは送信するメッセージ内容、空のまま送信するとエラーになるので空白を送信する
    content = kwargs.setdefault('content', '.') 

    #filesが存在するならそれを代入、なければNoneにしておく
    files = kwargs['files'] if 'files' in kwargs else None 

    #何も存在しない場合は何もせず返す
    if files is None and content == ".":
        return

    #webhook送信先のチャンネルを引数で与えられたidから取得する
    ch = client.get_channel(channel_id) 


    #webhook通信をするためにsessionを開く
    async with aiohttp.ClientSession() as session:
        #チャンネルからwebhookを取得してくる、無ければ新たにwebhookを作る
        webhook_urls = await client.get_channel(channel_id).webhooks()
        if len(webhook_urls) == 0:
            await ch.create_webhook(name="bot")
            webhook_urls = await client.get_channel(channel_id).webhooks()
            logfile_rw.write_logfile('info', 'gc', 'Created webhook. ' + webhook_urls[0].url)

        webhook = Webhook.from_url(webhook_urls[0].url, session=session)

        #ファイル(画像含む）があれば送るし、なければテキストのみ
        if files is None:
            await webhook.send(content, username=user_name, avatar_url=user_icon.url)
        else:
            await webhook.send(content, username=user_name, avatar_url=user_icon.url, files=files)
        logfile_rw.write_logfile('info', 'gc', 'Webhook send. ' + content)

@client.event #何かを検知
async def on_message(message): #on_messageはメッセージが送信された時に実行する
    global guilds
    #送信者がbotかwebhookであるならば返す
    if message.author == client.user or message.webhook_id is not None: 
        return
    
    #参考 https://github.com/tsuyopon123/discord-channel-sync/blob/master/app.py
    if message.channel.id in mybot.cfg.webhook_channel_id_list:
        channel_ids = mybot.cfg.webhook_channel_id_list
        #indexメソッドでその要素のインデックスを取得する
        msg_guild_index = channel_ids.index(message.channel.id)
        #pop()と同意義
        del channel_ids[msg_guild_index]
        #ファイル類を取得
        files = [await a.to_file() for a in message.attachments]

        #filesが空
        if not files:
            for channel_id in channel_ids:
                await webhook_sent(channel_id, message.author.display_name, message.author.display_avatar, content=message.content)
        else:
            for channel_id in channel_ids:
                await webhook_sent(channel_id, message.author.display_name, message.author.display_avatar, content=message.content, files=files)

        await message.reply(content='送信しました。', delete_after=3.0)
    
fg.on_regist_mode = False #registモードであるかを確認するフラグ
fg.on_regist_reset = False #registモードを解除するためのフラグ

'''
embedのボタンについての処理
ボタンは毎回embedを生成するとともにボタンのインスタンスとして生成し、ボタンごとに処理を持つ。
ボタンのインスタンスはクラスフィールドにそのボタンのセッションIDを生成し、インスタンス生成とともにsession_idリストに投げる。
session_idリストに投げると同時にsession_button_timelimitメソッドにもidを投げて実行される。
このメソッドは時間制限に到達すると自動でセッションIDをsession_idリストから削除する。
ボタンの処理が実行される前にsession_idリストに自身のセッションIDが存在するかを確認して、存在しなければ時間切れとする。

要約：
コマンド実行->ボタン表示->制限時間がくると実行できなくなる　という仕組み

また、コマンド実行時に自己のセッションIDをsession_idリストから消すので2回目の実行も出来ないようにしている。
'''

#removeされる前にbuttonを押されてセッションが消滅している場合もあるため、投げっぱなしになる
#ボタンの制限時間を設ける。
async def session_button_timelimit(session_id, time): 
    logfile_rw.write_logfile('info', 'session', f'Session {session_id} button enabled.')
    for i in range(time):
        await asyncio.sleep(1)
    fg.sessions.remove(session_id) if session_id in fg.sessions else None
    logfile_rw.write_logfile('info', 'session', f'Session {session_id} button disabled.')

#セッションIDのための乱数を生成する
def make_session_id():
    r = random.randint(0, 2147483647)
    while r in fg.sessions: #重複するセッションIDがある
        r = random.randint(0, 2147483647)
    return r

@client.tree.command() #コマンドを登録するDiscordサーバ（tree)でスラッシュコマンドを追加するデコレータ
@app_commands.describe(
    st_num='学籍番号を7ケタ、k無し、アルファベット大文字、半角英数で入力してください。',
    st_name='フルネームを入力、姓と名の間に空白を入れてください。',
    st_belong='所属を入力'
) #各引数に対して表示する説明文を設定するためのデコレータ
@app_commands.choices(st_belong=[
        app_commands.Choice(name=mybot.cfg.first_server_name, value=mybot.cfg.first_server_name),
        app_commands.Choice(name=mybot.cfg.second_server_name, value=mybot.cfg.second_server_name)
        ]) #st_belong引数で選択肢を表示するためのデコレータ
async def regist(interaction: discord.Interaction, st_num: str, st_name: str, st_belong: app_commands.Choice[str]):
    #registセッション保持中の場合弾く
    if fg.on_regist_mode:
        await interaction.response.send_message(content='現在別のregistコマンドが実行中です。お手数ですが、時間を空けてから再度お試しください。', ephemeral=True)
        logfile_rw.write_logfile('info', 'session', f'Regist cancelled by duplicate. {interaction.user.name}')
        return
    
    #そのユーザのレコードが存在すれば弾く（複数カード機能実装時には削除すること）
    if db.getRecordIdByUser(interaction.user.id) != None:
        await interaction.response.send_message(content='既に登録されたカードが存在します。何らかの手違いか再登録したい場合は/unregist コマンドを使用して登録を削除してから再度登録してください。', ephemeral=True)
    
    #registコマンド実行中のフラグはregist_timelimitメソッドで動作

    #registコマンド実行時embedを生成
    embed = get_descript_embed('部屋認証システムへの登録', f'{st_belong.value}\n学籍番号：{st_num}　名前：{st_name}様\n学生証の登録を開始します。よろしいですか？', interaction.user.display_name, interaction.user.display_avatar, interaction.created_at, "ボタンは一度のみ、この表示のあと1分有効です。")

    session_id = make_session_id() #セッションIDを生成 

    #egistOkとNoボタンとembedを送信する
    await interaction.response.send_message(embed=embed, view=r.RegistButton(session_id, client), ephemeral=True)

    #ボタンのセッションIDをsession_idリストに投下
    fg.sessions.append(session_id)

    #registセッション(登録作業の流れ）を開始 グローバルで所持するため１つのみ同時実行できる。
    fg.regist_session = r.RegistSession(session_id, interaction, st_name, st_num, st_belong.value) #インスタンス生成 グローバルで所有する
    logfile_rw.write_logfile('info', 'session', 'Regist session created. ' + str(session_id))

    #ボタンの有効期限を1分で設ける（時間制限を別スレッドに投げる）
    fg.tasks.append(asyncio.get_event_loop().create_task(session_button_timelimit(session_id, 60))) 

#入退室認証処理
async def entering_and_exiting_room(IDm):
    #changed_statusはFalseになったら退室した、Trueになったら入室した、という判定
    #このIDmの生徒が部屋に入室->退室 もしくは退室->入室の処理をして、その生徒の状態偏移語の状態と所属サーバーを取得
    #db.printFetchStudent(IDm) #検証用
    changed_status, belong = db.changeStudentRoomStatus(IDm) 
    
    #部屋人数の取得
    count, _ = db.getRoom()

    #所属AかBでembedカラーを変更
    if mybot.cfg.first_server_name == belong:
        color_type = 'one'
    else:
        color_type = 'two'
    
    #ユーザを取得
    user_id = db.getUserIdByIDm(IDm)
    user = await client.fetch_user(user_id)

    #時間文字列取得
    date_str = datetime.datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')
    
    #生徒が入室した場合の処理
    if changed_status:
        embed = add_embed("利用通知", f'{belong}のメンバーが入室しました。現在の利用人数は{count}人です。', color_type)
        for ch in chs:
            await ch.send(embed=embed)
        st_num = db.getStudentNumberByCard(IDm)
        logfile_rw.write_logfile('info', 'room', f'Changed room_status and Entering room. idm={IDm}, now_room_count={count} st_num={st_num} belong={belong}')
        #ユーザに入退室認証の情報をdmで送信する
        await user.send(content=f"（入退室認証通知）[{date_str}]部屋を入室しました。")
    
    #生徒が退室した場合の処理
    else:
        embed = add_embed("利用通知", f'{belong}のメンバーが退室しました。現在の利用人数は{count}人です。', color_type)
        for ch in chs:
            await ch.send(embed=embed)
        st_num = db.getStudentNumberByCard(IDm)
        logfile_rw.write_logfile('info', 'room', f'Changed room_status and Exiting room. idm={IDm}, now_room_count={count} st_num={st_num} belong={belong}')
        await user.send(content=f"（入退室認証通知）[{date_str}]部屋を退室しました。")

@client.tree.command()#コマンドを登録するDiscordサーバ（tree)でスラッシュコマンドを追加するデコレータ
async def unregist(interaction: discord.Interaction): #登録解除コマンド
    #必要情報の取得
    user_id = interaction.user.id
    record_id = db.getRecordIdByUser(user_id)

    #データベースからその生徒のレコードを取得できた場合、登録解除処理を続行
    if record_id:
        embed = get_descript_embed('部屋認証システム登録情報の削除', '学生証データの削除を開始します。よろしいですか？', interaction.user.display_name, interaction.user.display_avatar, interaction.created_at, "ボタンは一度のみ、この表示のあと1分有効です。")
        session_id = make_session_id() #セッションIDを生成 
        #登録解除embedとボタンを生成 RegistSessionと異なり、削除処理はOKボタンがすべてそろえている
        await interaction.response.send_message(embed=embed, view=ur.UnregistButton(session_id, db), ephemeral=True)
        fg.sessions.append(session_id) #セッション生成
        fg.tasks.append(asyncio.get_event_loop().create_task(session_button_timelimit(session_id, 60))) #ボタンの有効期限を1分で設ける

    #レコードが存在しない場合
    else:
        await interaction.response.send_message(content="登録されたデータを確認できませんでした。", ephemeral=True)

@client.tree.command()
@app_commands.choices(select=[
        app_commands.Choice(name="カードの追加登録", value="card_regist"),
        app_commands.Choice(name="カードの削除", value="card_unregist")
        ])
async def card(interaction: discord.Interaction, select: app_commands.Choice[str]):
    pass
    #select.valueにカード追加登録であればcard_regist、削除ならcard_unregistの文字列が格納される
    #(card_regist, card_unregist)ユーザがDBに登録されていない場合、registコマンドで最初に一枚登録してもらう趣旨の説明をして終わる

    #(card_unregist)カードが一枚の時、これ以上削除できない趣旨の通知をして終わる

    #(card_regist)カード追加処理
        #(上記処理中に）同一のカードがDBの自身のレコードにあれば使用済みと表示し終了

    #(card_unregist)カード削除処理
        #(上記処理中に）同一のカードが自分のユーザIDのレコードに存在しないとき未登録と表示し終了

#カード認証忘れ関連の修正を手動で行えるコマンド
@client.tree.command()
@app_commands.choices(
    select=[
        app_commands.Choice(name="前回の入退室時刻を修正したい", value="fix_time"),
        app_commands.Choice(name="退室認証を忘れたので認証する", value="add_roomout")
    ],
)
@app_commands.describe(
    select='修正する項目を選択してください。',
    hour='修正後の時間（時）を選択してください。(24時間表記：4~22)',
    minute='修正後の時間（分）を選択してください。(0~59)'
)
async def fix(interaction: discord.Interaction, select: app_commands.Choice[str], hour: app_commands.Range[int, 4, 22], minute: app_commands.Range[int, 0, 59]):
    #データベースにこのユーザーのidが存在するかを検索し、なければ弾く
    record_id = db.getRecordIdByUser(interaction.user.id)
    await interaction.response.send_message(content="登録されたデータを確認できませんでした。", ephemeral=True) if not record_id else None

    #select.value==fix_timeの時、認証履歴ログ蓄積テーブルから今日期間内で前回認証時のレコードを持ってきて、なければ弾く

    #そもそも蓄積テーブルがないので後回し

    
    fixed_time = datetime.datetime.now().strftime('%Y年%m月%d日 %H:%M')


#カードタッチを待機するためのメソッド(別スレッドで実行するメソッド)
async def card_touch_waiting_loop():
    global chs
    #カード読み取り関連の処理をインスタンス化
    cardReader = MyCardReader() 

    #同じカードがタッチされ続けている場合リリースされるまで保持する
    touching_idm = None
    while True:
        await asyncio.sleep(0.2)
        await cardReader.read_id(time.time(), 1) #タッチされて離されるまで待機し続ける
        
        #カードからIDmを取得する、取得できてなければ0が返る
        IDm = cardReader.get_idm() 
        
        #print("IDm = " + str(IDm) + " touching_idm = " + str(touching_idm))
        #カードを取得できていなければこれ以降の処理をpass
        if IDm == 0:
            touching_idm = None
            continue
        elif IDm == touching_idm: #今回取得したIDmとリリースされるまで保持するIDmが同じ場合、カードをタッチし続けていると判定しcontinuteする
            continue
        else:
            #初回処理の場合はtouching_idmに記録して後続の処理を続行
            touching_idm = IDm 

        #データベースを検索、存在すればroom_status(bool)も取得
        #room_statusはTrueで入室中、Falseで入室していないことを意味する
        student_room_status = db.getRoomStateByCard(IDm) #部屋状況(bool)を返す、存在しない場合None

        #データが取得できた場合
        if student_room_status is not None: #(TrueでもFalseでも実行する、Noneのみ実行しない)
           await entering_and_exiting_room(IDm) #入退室処理
        
        #新規登録モードの場合(登録されてないとデータが取得できない)
        elif fg.on_regist_mode: 
           await fg.regist_session.regist_record(IDm, db)
        
        #得たカードのレコードが存在しないならば却下処理
        else:
            for ch in chs:
                await ch.send(content='登録されていないカードが検出されました。\n初めて利用する場合は/registコマンドを使って登録処理を行ってからカードをタッチしてください。')
            logfile_rw.write_logfile('info', 'card', 'This card is not registed. IDm=' + str(IDm))

#コマンドを追加
@client.tree.command()
@app_commands.checks.has_permissions(administrator=True)
async def stop(interaction: discord.Interaction): #botを停止するコマンド(最低限)
    await interaction.response.send_message('Bot stopped', ephemeral=True)
    db.disconnectionDatabase()
    logfile_rw.write_logfile('info', 'bot', 'Bot stopped.')
    print("bye")
    await client.close()

#常時ループ処理(特定の時間にのみ処理する、定期的に実行する、とか)
async def loop():
    global stop_warn_infomation_flag
    global stop_warn_count
    
    while True:
        #部屋人数取得
        count, st_nums = db.getRoom()
        stNumString = ""
        for st_num in st_nums:
            stNumString += st_num + " "

        #現在時刻取得
        now = datetime.datetime.now().strftime('%H:%M')
        #人数カウントリセット時刻になったとき
        #if now == mybot.cfg.daily_reset_time:
        if now == '14:14':
            if count != 0:
                db.roomFlagAllFalse()
                logfile_rw.write_logfile("info", "bot", "Room status all reset.")

                embed = add_embed("現在の人数", f'人数が0で無かったため、リセットされました。\n入室していたメンバー -->\n{stNumString}', "one")
                for i in chs:
                    await i.send(embed=embed)
            
            #ログファイルを再生成する
            logfile_rw.make_logfile()
            logfile_rw.write_logfile("info", "bot", "Remake and closed logfile.")
        
        #警告を表示する->例えば150分間隔であれば、150分間フラグを立てる->制限時間後フラグが下りる
        if stop_warn_infomation_flag: #警告表示間隔
            stop_warn_count += 1
            if stop_warn_count > mybot.cfg.stop_warn_delay_minutes*2: #30秒に1カウントなので、間隔分*2以上で時間経過
                stop_warn_count = 0
                stop_warn_infomation_flag = False
        
        #上記処理でフラグが経ってる間警告を表示しないが、フラグが下がっており人数オーバーの時警告を表示する
        if count > mybot.cfg.max_count and stop_warn_infomation_flag == False: #人数が多く、停止フラグがFalse
            embed = add_embed("警告", f"定員{mybot.cfg.max_count}人に対して、現在大人数が入室しています。\n換気し、私語を控えるようにしてください。\n現在入室中のメンバー -->\n{stNumString}", "er")
            [await channel.send(embed=embed) for channel in chs] #各チャンネルに警告を表示
            stop_warn_infomation_flag = True #フラグを立てる

        await asyncio.sleep(30)

try:
    #botを起動
    client.run(mybot.cfg.TOKEN)
except RuntimeError:
    print("bot stopped")
    
#asyncio
#create_taskは見た目上並列に実行しているだけで、自身の処理をする番になったら落ちてる制御権を拾って処理する動きをする
#疑似的なマルチタスクで実際にはシングルスレッドでしか動作していない。asyncip.sleepは制御権をその時間手を放して別の処理をする事が出来るが、
# time.sleepは制御権を手放さないのでcreate_taskで投げても処理してくれない。
#どうしても実際にマルチスレッドで処理をさせたい場合はプロセスプールで調べる(run_in_executor())
#awaitは「時間のかかる処理を実行する」という意味で、そこでメインの処理を中断しasyncの処理を実行、
# そして処理が終わればまたawaitの行がエントリポイント（再開）として制御権が帰って処理を続行する
#Python3.5か7からジェネレータ以外の現在の方法が追加された（ジェネレータは3.10以降削除？）