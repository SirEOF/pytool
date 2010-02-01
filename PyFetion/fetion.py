#! /usr/bin/env python
# -*- coding: utf-8 -*-
#MIT License
#By : cocobear.cn@Gmail.com
#Ver:0.2

from PyFetion import *
from threading import Thread
from time import sleep
from copy import copy
import time
import sys
import exceptions
import cmd,wave
#from PIL import ImageGrab

ISOTIMEFORMAT='%Y-%m-%d %H:%M:%S'

status = {FetionHidden:"短信在线",FetionOnline:"在线",FetionBusy:"忙碌",FetionAway:"离开",FetionOffline:"离线"}

class fetion_recv(Thread):
    '''receive message'''
    def __init__(self,phone):
        self.phone = phone
        Thread.__init__(self)

    def run(self):
        #self.phone.get_offline_msg()
        global status
        start_time = time.time()

        #状态改变等消息在这里处理 收到的短信或者消息在recv中处理
        for e in self.phone.receive():
            #print e
            if e[0] == "PresenceChanged":
                #在登录时BN消息(e)有可能含有多个uri 
                for i in e[1]:
                    if time.time() - start_time > 5:
                        self.show_status(i[0],status[i[1]])
            elif e[0] == "Message":
                #获得消息
                #系统广告 忽略之
                if e[1] not in self.phone.contactlist:
                    continue
                if e[2].startswith("\\"):
                    self.parse_cmd(e[1],e[2])
                    return
                self.show_message(e)
                self.save_chat(e[1],e[2])


            elif e[0] == "deregistered":
                self.phone.receving = False
                printl('')
                printl("您从其它终端登录")

            elif e[0] == "NetworkError":
                printl("网络通讯出错:%s"%e[1])
                self.phone.receving = False

        printl("停止接收消息")

    def show_status(self,sip,status):
        try:
            import pynotify
            outstr = self.phone.contactlist[sip][0]+'['+ self.phone.get_order(sip) + ']'
            pynotify.init("Some Application or Title")
            self.notification = pynotify.Notification(outstr, status, "dialog-warning")
            self.notification.set_urgency(pynotify.URGENCY_NORMAL)
            self.notification.set_timeout(1)
            self.notification.show()
        except :
            #os.popen('play message.ogg')
            print u"\n",self.phone.contactlist[sip][0],"[",self.phone.get_order(sip),"]现在的状态：",status

    def show_message(self,e):
        s = {"PC":"电脑","PHONE":"手机"}
        try:
            import pynotify
            outstr = self.phone.contactlist[e[1]][0] + '[' + self.phone.get_order(e[1]) + ']'
            pynotify.init("Some Application or Title")
            self.notification = pynotify.Notification(outstr, e[2], "dialog-warning")
            self.notification.set_urgency(pynotify.URGENCY_NORMAL)
            self.notification.set_timeout(1)
            self.notification.show()
        except:
            os.system('play message.ogg')
            print self.phone.contactlist[e[1]][0],'[',self.phone.get_order(e[1]),']@',s[e[3]],"说：",e[2]
        
    def parse_cmd(self,to,line):
        flag = "以上信息由pyfetoin自动回复。更多指令请发送'\\help'。更多关于pyfetion的信息请访问http://code.google.com/p/pytool/"
        cmd = line[1:]
        file = open("command.log","a")
        record = to.split("@")[0].split(":")[1] + " " + time.strftime(ISOTIMEFORMAT) + " " + cmd + "\n"
        file.write(record)
        file.close()
        if cmd == 'weather':
            file = open("/home/laputa/data/WeatherForecast")
            lines = file.readlines()
            message = "Weather in Bejing:\n"
            i = 0
            for line in lines:
                if i==9:
                    break
                message = message + line
                i = i + 1
            message = message + flag
            if self.phone.send_msg(toUTF8(message),to):
                print "success"
        elif cmd == 'wish':
            wish = "Happy New Year!"
            wish = wish + flag
            if self.phone.send_msg(toUTF8(wish),to):
                print "success"
        elif cmd == 'help':
            message = "目前已实现的指令有：weather,wish,help这三个。发送'\\'+指令即可。weather获取天气预报，wish获取祝福，help获取帮助。"
            message = message + flag
            if self.phone.send_msg(toUTF8(message),to):
                print "success"
        else:
            message = "还没有这个指令呢。"
            message = message + flag
            if self.phone.send_msg(toUTF8(message),to):
                print "success"

    def save_chat(self,sip,text):
        file = open("chat_history.dat","a")
        record = sip.split("@")[0].split(":")[1] + " " + time.strftime(ISOTIMEFORMAT) + " " + text + "\n"
        file.write(record)
        file.close()

class fetion_alive(Thread):
    '''keep alive'''
    def __init__(self,phone):
        self.phone = phone
        Thread.__init__(self)

    def run(self):
        last_time = time.time()
        while self.phone.receving:
            sleep(3)
            if time.time() - last_time  > 300:
                last_time = time.time()
                self.phone.alive()

        printl("停止发送心跳")

class CLI(cmd.Cmd):
    '''解析命令行参数'''
    def __init__(self,phone):
        global status
        cmd.Cmd.__init__(self)
        self.phone=phone
        self.to=""
        self.type="msg"
        self.nickname = self.phone.get_personal_info()[0]
        self.sta=self.color(self.nickname,self.phone.presence)
        self.prompt = self.sta + ">"

    def  preloop(self):
        print u"欢迎使用PyFetion!\n要获得帮助请输入help或help help.\n更多信息请访问http://code.google.com/p/pytool/\n"
        print u"当前\033[32m在线\033[0m或\033[36m离开\033[0m或\033[31m忙碌\033[0m的好友为(ls命令可以得到下面结果)："
        self.do_ls("")

    def default(self, line):
        '''会话中：快速发送消息'''
        c = copy(self.phone.contactlist)
        if self.to:
            if self.phone.send_msg(toUTF8(line),self.to):
                print u'send to ',c[self.to][0]
                self.save_chat(self.to,line)
            else:
                printl("发送消息失败")
        else:
            print line, u' 不支持的命令!'

    def do_test(self,line):
        pass

    def do_info(self,line):
        '''用法：info
            查看个人信息'''
        if line:
            to = self.get_sip(line)
            if to == None:
                return
            info = self.get_info(to)
            print u"序号：",self.phone.get_order(to)
            print u"昵称：",info[0]
            print u"飞信号：",self.get_fetion_number(to)
            print u"手机号：",info[1]
            print u"状态：",status[info[2]]
            return
        info = self.phone.get_personal_info()
        print u"昵称：",info[0]
        print u"状态：",info[1]

    def get_info(self,uri):
        c = copy(self.phone.contactlist)
        response=[]
        response.append(c[uri][0])
        response.append(c[uri][1])
        response.append(c[uri][2])
        return response

    def do_la(self,line):
        '''用法:ls\n显示所有好友列表.
            \033[34m短信在线\t\033[35m离线
            \033[36m离开\t\033[31m忙碌\t\033[32m在线\033[0m'''
        if not self.phone.contactlist:
            printl("没有好友")
            return
        if self.phone.contactlist.values()[0] != 0:
            pass
        #当好友列表中昵称为空重新获取
        else:
            self.phone.get_contactlist()

        #print self.phone.contactlist
        c = copy(self.phone.contactlist)
        num = len(c.items())
        for i in c:
            if c[i][0] == '':
                c[i][0] = i[4:4+9]
        printl(status[FetionOnline])
        for i in range(num):
            if c[c.keys()[i]][2] != FetionHidden and c[c.keys()[i]][2] != FetionOffline:
                print self.color(str(i)+c[c.keys()[i]][0],status[c[c.keys()[i]][2]]),"\t",

        printl("\n"+status[FetionHidden])
        for i in range(num):
            if c[c.keys()[i]][2] == FetionHidden:
                print self.color(str(i)+c[c.keys()[i]][0],status[c[c.keys()[i]][2]]),"\t",

        printl("\n"+ status[FetionOffline])
        for i in range(num):
            if c[c.keys()[i]][2] == FetionOffline:
                print self.color(str(i)+c[c.keys()[i]][0],status[c[c.keys()[i]][2]]),"\t",
        print ""

    def do_ls(self,line):
        '''用法: ls\n 显示在线好友列表
            \033[36m离开\t\033[31m忙碌\t\033[32m在线\033[0m'''
        if line:
                to=self.get_sip(line)
                if to == None:
                    return
                print self.phone.get_order(to),self.get_nickname(to)
        if not self.phone.contactlist:
            printl("没有好友")
            return
        if self.phone.contactlist.values()[0] != 0:
            pass
        #当好友列表中昵称为空重新获取
        else:
            self.phone.get_contactlist()

        #print self.phone.contactlist
        c = copy(self.phone.contactlist)
        num = len(c.items())
        for i in c:
            if c[i][0] == '':
                c[i][0] = i[4:4+9]
        for i in range(num):
            if c[c.keys()[i]][2] != FetionHidden and c[c.keys()[i]][2] != FetionOffline:
                print self.color(str(i)+c[c.keys()[i]][0],status[c[c.keys()[i]][2]]),"\t",
        print ""

    def do_ll(self,line):
        '''用法: ll\n列出好友详细信息:序号，昵称，手机号，状态.
            \033[34m短信在线\t\033[35m离线
            \033[36m离开\t\033[31m忙碌\t\033[32m在线\033[0m'''
        if not self.phone.contactlist:
            printl("没有好友")
            return
        if self.phone.contactlist.values()[0] != 0:
            pass
        #当好友列表中昵称为空重新获取
        else:
            self.phone.get_contactlist()

        #print self.phone.contactlist
        c = copy(self.phone.contactlist)
        num = len(c.items())
        for i in c:
            if c[i][0] == '':
                c[i][0] = i[4:4+9]
        for i in range(num):
            uri = c.keys()[i]
            outstr = str(i)+"\t" + c[uri][0]+"\t" + c[uri][1]+"\t" + status[c[uri][2]]
            print self.color(outstr,status[c[uri][2]])

    def do_status(self,i):
        '''用法: status [i]\n改变状态:0 隐身 1 离开 2 离线 3 忙碌 4 在线.'''
        if i:
            i = int(i)
            self.phone.set_presence(status.keys()[i])
            color=""
            self.sta= color(self.nickname,i)
            self.prompt = self.sta + ">"
        else:
            print status[self.phone.presence],u"\n用法: status [i]\n改变状态:0 隐身 1 离开 2 离线 3 忙碌 4 在线."

    def do_msg(self,line):
        """msg [num] [text]
        send text to num and save the session"""
        if not line:
            print u'用法：msg [num] [text]'
            return
        cmd = line.split()
        num = cmd[0]

        to = self.get_sip(num)
        if to == None:
            return
        self.to = to
        nickname = self.get_nickname(self.to)
        self.prompt = self.sta +" [to] "+nickname+">"
        if len(cmd)>1:
            if self.phone.send_msg(toUTF8(cmd[1]),self.to):
                self.save_chat(self.to,cmd[1])
                print u'send message to ', nickname
            else:
                printl("发送消息失败")

    def save_chat(self,sip,text):
        file = open("chat_history.dat","a")
        record ="out!" + self.get_fetion_number(sip) + " " + time.strftime(ISOTIMEFORMAT) + " " + text + "\n"
        file.write(record)
        file.close()

    def do_sms(self,line):
        '''用法：sms [num] [text]
            send sms to num'''
        if not line:
            print u'用法：sms [num] [text]'
            return
        cmd = line.split()
        if len(cmd) ==1:
            num = cmd[0]
        num = cmd[0]
        to=self.get_sip(num)
        if to == None:
            return
        if not self.phone.send_sms(toUTF8(cmd[1]),to):
            printl("发送短信失败")
        else:
            print u'已发送 ',self.get_nickname(to)

    def do_find(self,line):
        '''用法：find [序号|手机号]|all
            隐身查询'''
        if not line:
            print u'用法：find [num]'
            return
        if line=='all':
            c = copy(self.phone.contactlist)
            num = len(c.items())
            for i in c:
                if c[i][0] == '':
                    c[i][0] = i[4:4+9]
            for i in range(num):
                uri = c.keys()[i]
                if c[uri][2] == FetionHidden:
                    ret = self.phone.start_chat(uri)
                    if ret:
                        if ret == c[uri][2]:
                            print self.color(str(i)+c[uri][0],status[c[uri][2]]),"\t",
                        #elif ret == FetionOnline:
                            #print c[c.keys()[i]][0],u"不在线"
            return
        cmd = line.split()
        to = self.get_sip(cmd[0])
        if to == None:
            return
        nickname = self.get_nickname(to)
        if self.phone.contactlist[to][2] != FetionHidden:
            printl("拜托人家写着在线你还要查!")
        else:
            ret = self.phone.start_chat(to)
            if ret:
                if ret == self.phone.contactlist[to][2]:
                    print nickname, u"果然隐身"
                elif ret == FetionOnline:
                    print nickname, u"的确不在线哦"
            else:
                printl("获取隐身信息出错")

    def do_add(self,line):
        '''用法：add 手机号或飞信号'''
        if not line:
            printl("命令格式:add[a] 手机号或飞信号")
            return

        if line.isdigit() and len(line) == 9 or len(line) == 11:
            code = self.phone.add(line)
            if code:
                printl("添加%s成功"%line)
            else:
                printl("添加%s失败"%line)
        else:
            printl("命令格式:add[a] 手机号或飞信号")

    def do_del(self,line):
        '''delete buddy'''
        if not line:
            printl("命令格式:del[d] 手机号或飞信号")
            return
        if line.isdigit() and len(line) == 9 or len(line) == 11:
            code = self.phone.delete(line)
            if code:
                printl("删除%s成功"%line)
            else:
                printl("删除%s失败"%line)
        else:
            sip = self.get_sip(line)
            if sip == None:
                return
            num = self.get_fetion_number(sip)
            code = self.phone.delete(num)
            if code:
                printl("删除%s成功"%num)
            else:
                printl("删除%s失败"%num)

    def get_fetion_number(self,uri):
        '''get fetion number from uri'''
        return uri.split("@")[0].split(":")[1]

    def do_get(self,line):
        self.phone.get_offline_msg()

    def do_update(self,line):
        '''用法：update [状态]
            更新飞信状态'''
        pass

    def do_scrot(self,line):
        if line:
            print "用法:scrot"
            return
        #im = ImageGrab.grab()
        #name = time.strftime("%Y%m%d%H%M%S") + ".png"
        #im.save(name)

    def do_cls(self,line):
        pass

    def get_sip(self,num):
        '''get sip and nickname from phone number or order or fetion number'''
        c = copy(self.phone.contactlist)
        if not num.isdigit():
            '''昵称形式'''
            for uri in c.keys():
                if num == c[uri][0]:
                    return uri
            return
        if len(num)==11:
            '''cellphone number'''
            sip = ""
            for c in c.items():
                if c[1][1] == num:
                    sip=c[0]
                    return sip
            if not sip:
                printl("手机号不是您的好友")
        elif len(num) == 9:
            '''fetion number'''
            for uri in c.keys():
                if num == self.get_fetion_number(uri):
                    return uri
        elif len(num) < 4:
            '''order number'''
            n = int(num)
            if n >= 0 and n < len(c):
                return c.keys()[n]
            else:
                printl("编号超出好友范围")

    def get_nickname(self,sip):
        return self.phone.contactlist[sip][0]

    def color(self,message,status):
        if status=='0' or status == '短信在线':
            '''FetionHidden'''
            return "\033[35m" + message  + "\033[0m"
        elif status == '1' or status =='离开':
            '''FetionAway'''
            return "\033[34m" + message + "\033[0m"
        elif status == '2' or status == '离线':
            '''FetionOffline'''
            return "\033[36m" + message + "\033[0m"
        elif status == '3' or status == '忙碌':
            '''FetionBusy'''
            return "\033[31m" + message + "\033[0m"
        elif status == '4' or status == '在线':
            '''FetionOnline'''
            return "\033[32m" + message + "\033[0m"

    def do_history(self,line):
        '''usage:history
        show the chat history information'''
        file = open("chat_history.dat","r")
        records = file.readlines()
        for record in records:
            temp = record.split()
            time = temp[2].split(":")[0]+":"+temp[2].split(":")[1]
            text = temp[3]

            fetions = temp[0].split("!")
            if len(fetions)==2:
                fetion= fetions[1]
                if not line:
                    nickname = self.get_nickname(fetion)
                    print self.nickname," to ",nickname," ",time,text
                else:
                    sip = self.get_sip(line)
                    num = self.get_fetion_number(sip)
                    if num == fetion:
                        print self.nickname," to ",nickname," ",time,text
            else:
                fetion=fetions[0]
                if not line:
                    nickname = self.get_nickname(fetion)
                    print nickname," to ",self.nickname," ",time,text
                else:
                    sip = self.get_sip(line)
                    num = self.get_fetion_number(sip)
                    if num == fetion:
                        print nickname," to ",self.nickname," ",time,text

    def do_quit(self,line):
        '''quit\nquit the current session'''
        self.to=""
        self.prompt=self.sta+">"
        pass

    def do_exit(self,line):
        '''exit\nexit the program'''
        self.phone.logout()
        sys.exit(0)

    def do_help(self,line):
        self.clear()
        printl("""
------------------------基于PyFetion的一个CLI飞信客户端-------------------------

        命令不区分大小写中括号里为命令的缩写

        help[?]           显示本帮助信息
        ls                列出在线好友列表
        la                列出所有好友列表
        ll                列出序号，备注，昵称，所在组，状态
        status[st]        改变飞信状态 参数[0隐身 1离开 2忙碌 3在线]
                          参数为空显示自己的状态
        msg[m]            发送消息 参数为序号或手机号 使用quit退出
        sms[s]            发送短信 参数为序号或手机号 使用quit退出
                          参数为空给自己发短信
        find[f]           查看好友是否隐身 参数为序号或手机号
        info[i]           查看好友详细信息,无参数则显示个人信息
        update[u]         更新状态
        add[a]            添加好友 参数为手机号或飞信号
        del[d]            删除好友 参数为手机号或飞信号
        cls[c]            清屏
        quit[q]           退出对话状态
        exit[x]           退出飞信

        """)

    def clear(self):
        if os.name == "posix":
            os.system("clear")
        else:
            os.system("cls")

    def do_EOF(self, line):
        return True
    
    def postloop(self):
        print

    #shortcut
    do_q = do_quit
    do_h = do_history
    do_x = do_exit
    do_m = do_msg
    do_s = do_sms
    do_st = do_status
    do_f = do_find
    do_a = do_add
    do_d = do_del
    do_i = do_info
    do_u = do_update

class fetion_input(Thread):
    def __init__(self,phone):
        self.phone = phone
        self.to    = ""
        self.type  = "SMS"
        self.hint  = "PyFetion:"
        Thread.__init__(self)

    def run(self):
        sleep(1)
        #self.help()
        #while self.phone.receving:
        #    try:
        #        self.hint = toEcho(self.hint)
        #    except :
        #        pass

        #    #self.cmd(raw_input(self.hint))
        CLI(self.phone).cmdloop()
        printl("退出输入状态")

    def cmd(self,arg):
        global status

        if not self.phone.receving:
            return
        cmd = arg.strip().lower().split(' ')
        if cmd[0] == "":
            return
        elif cmd[0] == "quit" or cmd[0] == "q":
            self.to = ""
            self.hint = "PyFetion:"


        elif self.to == "ME":
            self.phone.send_sms(toUTF8(arg))

        elif self.to:
            if self.type == "SMS":
                if not self.phone.send_sms(toUTF8(arg),self.to):
                    printl("发送短信失败")
            else:
                if self.to in self.phone.session:
                    self.phone.session[self.to]._send_msg(toUTF8(arg))
                    return
                if not self.phone.send_msg(toUTF8(arg),self.to):
                    printl("发送消息失败")
                
            return

        elif cmd[0] == "help" or cmd[0] == "h" or cmd[0] == '?':
            #显示帮助信息
            self.help()
        elif cmd[0] == "status" or cmd[0] == "st":
            #改变飞信的状态
            if len(cmd) != 2:
                printl("当前状态为[%s]" % status[self.phone.presence])
                return

            try:
                i = int(cmd[1])
            except exceptions.ValueError:
                printl("当前状态为[%s]" % status[self.phone.presence])
                return

            if i >3 or i < 0:
                printl("当前状态为[%s]" % status[self.phone.presence])
                return
                
            if self.phone.presence == status.keys()[i]:
                return
            else:
                self.phone.set_presence(status.keys()[i])
                
        elif cmd[0] == "sms" or cmd[0] == 'msg' or cmd[0] == 's' or cmd[0] == 'm' or cmd[0] == "find" or cmd[0] == 'f':
            #发送短信或者消息
            s = {"MSG":"消息","SMS":"短信","FIND":"查询"}
            if len(cmd) == 1 and cmd[0].startswith('s'):
                self.hint = "给自己发短信:"
                self.to = "ME"
                return
            if len(cmd) != 2:
                printl("命令格式:sms[msg] 编号[手机号]")
                return

            if cmd[0].startswith('s'):
                self.type = "SMS"
            elif cmd[0].startswith('m'):
                self.type = "MSG"
            else:
                self.type = "FIND"
            self.to   = ""
 
            try:
                int(cmd[1])
            except exceptions.ValueError:
                if cmd[1].startswith("sip"):
                    self.to = cmd[1]
                    self.hint = "给%s发%s:" % (cmd[1],s[self.type])
                else:
                    printl("命令格式:sms[msg] 编号[手机号]")
                    return
           
            c = copy(self.phone.contactlist)
            #使用编号作为参数
            if len(cmd[1]) < 4:
                n = int(cmd[1])
                if n >= 0 and n < len(self.phone.contactlist):
                    self.to = c.keys()[n]
                    self.hint = "给%s发%s:" % (c[self.to][0],s[self.type])
                else:
                    printl("编号超出好友范围")
                    return

            #使用手机号作为参数
            elif len(cmd[1]) == 11:
                for c in c.items():
                    if c[1][1] == cmd[1]:
                        self.to = c[0]
                        self.hint = "给%s发%s:" % (c[1][0],s[self.type])

                if not self.to:
                    printl("手机号不是您的好友")

            else:
                printl("不正确的好友")


            if self.type == "FIND":
                #如果好友显示为在线(包括忙碌等) 则不查询
                if self.phone.contactlist[self.to][2] != FetionHidden:
                    printl("拜托人家写着在线你还要查!")
                else:
                    ret = self.phone.start_chat(self.to)
                    if ret:
                        if ret == c[self.to][2]:
                            printl("该好友果然隐身")
                        elif ret == FetionOnline:
                            printl("该好友的确不在线哦")
                    else:
                        printl("获取隐身信息出错")

                self.to = ""
                self.type = "SMS"
                self.hint  = "PyFetion:"
                    
            
        elif cmd[0] == "ls" or cmd[0] == "l":
            #显示好友列表
            if not self.phone.contactlist:
                printl("没有好友")
                return
            if self.phone.contactlist.values()[0] != 0:
                pass
            #当好友列表中昵称为空重新获取
            else:
                self.phone.get_contactlist()

            #print self.phone.contactlist
            c = copy(self.phone.contactlist)
            num = len(c.items())
            for i in c:
                if c[i][0] == '':
                    c[i][0] = i[4:4+9]
            printl(status[FetionOnline])
            for i in range(num):
                if c[c.keys()[i]][2] != FetionHidden and c[c.keys()[i]][2] != FetionOffline:
                    printl("%-4d%-20s" % (i,c[c.keys()[i]][0]))

            printl(status[FetionHidden])
            for i in range(num):
                if c[c.keys()[i]][2] == FetionHidden:
                    printl("%-4d%-20s" % (i,c[c.keys()[i]][0]))

            printl(status[FetionOffline])
            for i in range(num):
                if c[c.keys()[i]][2] == FetionOffline:
                    printl("%-4d%-20s" % (i,c[c.keys()[i]][0]))


        elif cmd[0] == "add" or cmd[0] == 'a':
            if len(cmd) != 2:
                printl("命令格式:add[a] 手机号或飞信号")
                return

            if cmd[1].isdigit() and len(cmd[1]) == 9 or len(cmd[1]) == 11:
                
                code = self.phone.add(cmd[1])
                if code:
                    printl("添加%s成功"%cmd[1])
                else:
                    printl("添加%s失败"%cmd[1])
                    
            else:
                printl("命令格式:add[a] 手机号或飞信号")
                return
                
        elif cmd[0] == "del" or cmd[0] == 'd':
            if len(cmd) != 2:
                printl("命令格式:del[d] 手机号或飞信号")
                return
            if cmd[1].isdigit() and len(cmd[1]) == 9 or len(cmd[1]) == 11:
                code = self.phone.delete(cmd[1])
                if code:
                    printl("删除%s成功"%cmd[1])
                else:
                    printl("删除%s失败"%cmd[1])
            else:
                printl("命令格式:del[d] 手机号或飞信号")
                return

        elif cmd[0] == "get":
            self.phone.get_offline_msg()
        elif cmd[0] == "cls" or cmd[0] == 'c':
            #清屏
            self.clear()

        elif cmd[0] == "exit" or cmd[0] == 'x':
            self.phone.logout()

        else:
            printl("不能识别的命令 请使用help")


class progressBar(Thread):
    def __init__(self):
        self.running = True
        Thread.__init__(self)

    def run(self):
        i = 1
        while self.running:
            sys.stderr.write('\r')
            sys.stderr.write('-'*i)
            sys.stderr.write('>')
            sleep(0.5)
            i += 1

    def stop(self):
        self.running = False


def toUTF8(str):
    return str.decode((os.name == 'posix' and 'utf-8' or 'cp936')).encode('utf-8')

def toEcho(str):
    return str.decode('utf-8').encode((os.name == 'posix' and 'utf-8' or 'cp936'))

def printl(msg):
    msg = str(msg)
    try:
        print(msg.decode('utf-8'))
    except exceptions.UnicodeEncodeError:
        print(msg)

def getch():
    
    if os.name == 'posix':
        import sys,tty,termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd,termios.TCSADRAIN,old_settings)

        return ch

    elif os.name == 'nt':
        import msvcrt
        return msvcrt.getch()
        
def getpass(msg):
    """实现一个命令行下的密码输入界面"""
    passwd = ""
    sys.stdout.write(msg)
    ch = getch()
    while (ch != '\r'):
        #Linux下得到的退格键值是\x7f 不理解
        if ch == '\b' or ch == '\x7f':
            passwd = passwd[:-1]
        else:
            passwd += ch
        sys.stdout.write('\r')
        sys.stdout.write(msg)
        sys.stdout.write('*'*len(passwd))
        sys.stdout.write(' '*(80-len(msg)-len(passwd)-1))
        sys.stdout.write('\b'*(80-len(msg)-len(passwd)-1))
        ch = getch()

    sys.stdout.write('\n')
    return passwd
    

def login():
    '''登录设置'''
    if len(sys.argv) > 3:
        print u'参数错误'
    elif len(sys.argv) == 3:
        mobile_no = sys.argv[1]
        passwd = sys.argv[2]
    else:
        if len(sys.argv) == 2:
            mobile_no = sys.argv[1]
        elif len(sys.argv) == 1:
            mobile_no = raw_input(toEcho("手机号:"))
        passwd = getpass(toEcho("口  令:"))
    phone = PyFetion(mobile_no,passwd,"TCP",debug="FILE")
    return phone


def main(phone):
    '''main function'''
    try:
        t = progressBar()
        t.start()
        #可以在这里选择登录的方式[隐身 在线 忙碌 离开]
        ret = phone.login(FetionHidden)
    except PyFetionSupportError,e:
        printl("手机号未开通飞信")
        return 1
    except PyFetionAuthError,e:
        printl("手机号密码错误")
        return 1
    except PyFetionSocketError,e:
        print(e.msg)
        printl("网络通信出错 请检查网络连接")
        return 1
    finally:
        t.stop()

    if ret:
        printl("登录成功")
    else:
        printl("登录失败")
        return 1

    threads = []
    threads.append(fetion_recv(phone))
    threads.append(fetion_alive(phone))
    #threads.append(fetion_input(phone))
    t1 = fetion_input(phone)
    t1.setDaemon(True)
    t1.start()
    for t in threads:
        t.setDaemon(True)
        t.start()

    while len(threads):
        t = threads.pop()
        if t.isAlive():
            t.join()
    del t1
    printl("飞信退出")

    #phone.send_schedule_sms("请注意，这个是定时短信",time)
    #time_format = "%Y-%m-%d %H:%M:%S"
    #time.strftime(time_format,time.gmtime())
    
if __name__ == "__main__":
    phone = login()
    sys.exit(main(phone))
