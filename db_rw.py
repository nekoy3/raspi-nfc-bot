import sqlite3

#https://resanaplaza.com/2021/06/22/%E3%80%90%E5%AE%9F%E7%94%A8%E3%80%91windows%E3%81%AEpython%E3%81%8B%E3%82%89sqlite%E3%82%92%E4%BD%BF%E3%81%86/

#connに対して直接executeすることも出来るが、カーソルを取得してから実行しないとメモリに残骸が残る。
class DatabaseClass():
    def __init__(self):
        # student_list.dbを作成する
        self.dbname = 'student_list.db'
        self.connectionDatabase()
        self.createTableStudents() #テーブルが存在しない場合に限り新しく作成する
    
    #データベースと接続を確立する
    def connectionDatabase(self):
        self.conn = sqlite3.connect(self.dbname) #自身の持つフィールドにアクセスするには引数でselfを与える必要がある

    #studentsテーブルを作成する
    def createTableStudents(self):
        cur = self.conn.cursor()
        # 大文字部はSQL文。小文字でも問題ない
        cur.execute(
            'CREATE TABLE IF NOT EXISTS students(id INTEGER PRIMARY KEY AUTOINCREMENT, sid STRING, sname STRING, cid STRING, user_id INT, date STRING, student_room_status boolean, belong STRING )'
            )
    
    #生徒のレコードを追加する
    def addRecord(self, sid, sname, cid, user_id, date, student_room_status, belong): #id, 学籍番号, 生徒名, カードID, 登録日, 入室フラグ
        # sqliteを操作するカーソルオブジェクトを作成
        cur = self.conn.cursor()
        cur.execute('INSERT INTO students(sid, sname, cid, user_id, date, student_room_status, belong) values(?, ?, ?, ?, ?, ?, ?) ', [sid, sname, cid, user_id, date, student_room_status, belong])
        self.conn.commit() # データベースへコミット これで変更が反映される
        cur.close()
    
    #生徒のレコードを削除する
    def removeRecord(self, id):
        cur = self.conn.cursor()
        cur.execute('DELETE FROM students where id=?', (id,))
        self.conn.commit() # データベースへコミット これで変更が反映される
        cur.close()

    #カードidで生徒を検索する、返り値は部屋状況(bool)
    def getRoomStateByCard(self, cid):
        cur = self.conn.cursor()
        cur.execute('SELECT student_room_status FROM students WHERE cid=?', (cid,) )
        exist = cur.fetchone()
        cur.close()
        if exist is None:
            return None
        else:
            return exist[0]
    
    #discordのユーザidで生徒を検索する、帰り値はレコードid
    def getRecordIdByUser(self, user_id):
        cur = self.conn.cursor()
        cur.execute('SELECT * FROM students WHERE user_id=?', (user_id,) )
        exist = cur.fetchone()
        cur.close()
        if exist is None:
            return None
        else:
            return exist
    
    #カードidで生徒を検索する、返り値は学籍番号
    def getStudentNumberByCard(self, IDm):
        cur = self.conn.cursor()
        cur.execute('SELECT sid FROM students WHERE cid=?', (IDm,) )
        exist = cur.fetchone()
        cur.close()
        if exist is None:
            return None
        else:
            return exist[0]
    
    #discordのユーザidで生徒を検索する、帰り値は所属
    def getBelongByUser(self, cid):
        cur = self.conn.cursor()
        cur.execute('SELECT belong FROM students WHERE cid=?', (cid,) )
        exist = cur.fetchone()
        cur.close()
        if exist is None:
            return None
        else:
            return exist[0]

    #適合するレコードを全部取得してprintするメソッド(検証用)
    def printFetchStudent(self, cid):
        cur = self.conn.cursor()
        cur.execute('SELECT student_room_status, belong, sid FROM students WHERE cid=?', (cid,) )
        fetch_tuple = cur.fetchall()
        print(str(fetch_tuple))
        print("<" + str(cid) + ">")
    
    #レコードをカードidで検索して、変更後ステータスと所属を返す
    def changeStudentRoomStatus(self, cid):
        cur = self.conn.cursor()
        cur.execute('SELECT student_room_status, belong FROM students WHERE cid=?', (cid,) )
        fetch_tuple = cur.fetchone()
        student_room_status = fetch_tuple[0]
        belong = fetch_tuple[1]
        changed_status = not student_room_status
        cur.execute('UPDATE students SET student_room_status=? WHERE cid=?', (changed_status, cid))
        cur.close()
        return changed_status, belong
    
    #現時点での入室人数と学籍番号を取得
    def getRoom(self):
        cur = self.conn.cursor()
        cur.execute('SELECT sid, student_room_status FROM students WHERE student_room_status=True')
        count = 0
        st_nums = []
        for record in cur.fetchall(): #レコード数ループ
            count+=1
            st_nums.append(record[0])
        cur.close()
        return count, st_nums
    
    #すべての入室中生徒のフラグを下ろすメソッド
    def roomFlagAllFalse(self):
        cur = self.conn.cursor()
        cur.execute('UPDATE students SET student_room_status=False')

    #特定のカードIDのレコードを削除
    def deleteRecord(self, cid):
        cur = self.conn.cursor()
        cur.execute('DELETE FROM students WHERE cid=?', (cid,) )
        self.conn.commit()
        cur.close()
    
    #接続を切断
    def disconnectionDatabase(self):
        self.conn.close()

    '''
    dataA = addRecord(0, 2, 4, 6, 8)
    dataB = addRecord(1, 3, 5, 7, 9)

    deleteDataA = deleteRecord(6)
    searchDataB = searchRecord(7)
    print(searchDataB)

    cur.execute('SELECT * FROM students')
    # 中身を全て取得するfetchall()を使って、printする
    print(cur.fetchall())

    dataC = addRecord(11, 22, 33, 44, 55)

    cur.execute('SELECT * FROM students')
    print(cur.fetchall())
    '''