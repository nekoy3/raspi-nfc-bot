#!/bin/bash
#自身のファイルパスへ移動
cd /home/pi/raspi-nfc-bot

#botをscreenで起動
for i in 13
do
  #botをscreen（仮想端末）で起動する
  screen -S raspi_bot -dm python main.py
  sleep 5
  #起動に成功していたら$?に0を返す
  screen -ls | grep raspi_bot
  
  #起動に成功(0)していたらスクリプトを終了し、失敗(1)したら繰り返す
  if [ $? == 0 ]; then
    break
  elif [ $i == 12 ]; then #タイムアウト
    date=`date` #日付文字列取得
    msg="[${date}] 起動に失敗しました。"
    echo $msg >> run.log
    exit
  fi
done

date=`date`
msg="[${date}] 起動しました。"
echo $msg >> run.log
exit
#botが停止した場合にはscreenも勝手に消滅する

#crontabの設定
#sudo crontab -eに定期リブートの設定
#crontab -eにbot自動起動の設定

#tail -f /var/log/syslog でcronの実行状況を確認可能
