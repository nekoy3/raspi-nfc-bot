import sys 
import sqlite3

def main(args):
    conn = sqlite3.connect("student_list.db")
    cur = conn.cursor()
    if args[1] == "get":
        cur.execute("SELECT * FROM students")
        exist = cur.fetchall()
        print("students\n" + str(exist))
        cur.execute("SELECT * FROM cards")
        exist = cur.fetchall()
        print("cards\n" + str(exist))
    cur.close()
    conn.close()


if __name__ == '__main__':
    args = sys.argv
    main(args)
    