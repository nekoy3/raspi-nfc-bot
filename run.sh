#!/bin/bash
#自身のファイルパスへ移動
cd /home/pi/raspi-nfc-bot

log() {
  date=`date`
  msg="[${date}] $1"
  echo $msg >> run.log
}

log "起動スクリプト開始"
    
#pingでネットにつながるまで待機
for i in 181
do
  ping discord.com -c 1 >> /dev/null
  sleep 1
  
  #成功(0)していたらスクリプトを終了し、失敗(1)したら繰り返す
  if [ $? == 0 ]; then
    #botを起動する
    log "起動します"
    python main.py >> run.log
    log "botが停止"
    exit
    
  elif [ $i == 180 ]; then #タイムアウト
    log "起動に失敗しました。"
    exit
  fi
done
#botが停止した場合にはscreenも勝手に消滅する

#systemdを使って起動するように構成を変更
# systemctl --user start discordBot.service
# nano ~/.config/systemd/user/discordBot.service
#
#書き換えたら以下でリロードして再度自動起動をenableにする必要がある
# systemctl --user daemon-reload
# systemctl --user enable discordBot.service
#
#状態を確認する
# systemctl --user status discordBot.service
