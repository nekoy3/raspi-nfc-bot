tasks = [] #別スレッドに投げたコルーチンオブジェクト用のリスト
sessions = [] #registコマンド等のやりとりをID別に管理するために保管するためのリスト
regist_session = None #registコマンド実行中に他でregistを実行しないようにロックするための変数
unregist_session = None #unregistコマンドで上記同様