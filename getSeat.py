import requests
import datetime
import json
import re
#import sys
import time
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from apscheduler.schedulers.blocking import BlockingScheduler
 
 
global headers
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0',
    'Host': 'seat.gsupl.edu.cn'
}
 
#登录函数
def login():
 
    l_params = {
        'url': 'index',
        'user': '学号',
        'passwd':'经base64加密后的密码'
    }
    #自己分析得到的接口，下同
    login_url = '自己分析登录url'
    s = requests.session()
    re = s.post(url=login_url, headers=headers, params=l_params)
    #返回登录成功的实例
    return s

#预约函数
def yd(sessio,isAfternoon):
    y_params = {
	# 这里抢座座位号需要抓取参数，beskid和beskCanId早上和下午都不同
        #预定座位
        "roomno":"自行抓取",
        "tableid": "自行抓取",
        "tableno": "座位号",
        "begintime":"13:50:02",
        "endtime":"22:30:00",
        "beskid":"103",
        "beskCanId":"69"
    }
    y_url = 'https://seat.gsupl.edu.cn/readingroom/postbeskdata'
    if(isAfternoon):
        y_params["begintime"] = "07:00:00"
        y_params["endtime"] = "13:50:00"
        y_params["beskid"] = "122"
        y_params["beskCanId"] = "70"
    re = sessio.post(url=y_url, headers=headers, params=y_params)
    if re.status_code == 200:
        text = json.loads(re.text)
        if text['ReturnValue']==0:
            print ('---------',text['Msg'],'---------')
            return 1
        else:
            print ('---------',text['Msg'],'---------')
            return text['Msg']
    else:
        print ('---------请检查网络问题或者服务器回应问题！---------')
        return 2

# 发送结果邮件函数
def sender(isSelected):
    # 邮件内容
    subject = '预约失败，请检查重试！'
    body = '预约失败了，快检查检查哪里出问题。'
    if (isSelected):
        subject = '预约位置成功！'
        body = '位置预约成功！快去看看吧。'
    # 构建邮件
    msg = MIMEText(body, 'plain', 'utf-8')
    msg['Subject'] = Header(subject, 'utf-8')
    msg['From'] = '邮箱'
    msg['To'] = '邮箱'
    
    # 发送邮件
    smtp_server = 'smtp.qq.com'
    smtp_port = 465
    sender_email = '邮箱地址'
    password = '授权码' #在QQ邮箱设置里拿到的授权码

    try:
        server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        server.login(sender_email, password)
        server.sendmail(sender_email, [msg['To']], msg.as_string())
        print('---------通知邮件发送成功---------')
    except smtplib.SMTPException as e:
        print('---------通知邮件发送失败:', str(e),'---------')
    finally:
        server.quit()


# 使用正则表达式提取日期
def extract_date(text):
    pattern = r'\d{2}:\d{2}:\d{2}'
    match = re.search(pattern, text)
    if match:
        return match.group()
    else:
        return None
    

# 主函数，循环30次预约，如果成功提前退出
def job_func():
    now = datetime.datetime.now()
    nowHour = now.hour
    print('*********现在时间',now.strftime("%Y-%m-%d %H:%M:%S"),'*********')
    count = 30
    isAfternoon = False
    # 判断是早上还是下午
    if nowHour>8:
        isAfternoon = True
    # 执行登录操作
    loginRS = login()
    if(loginRS):
        #执行getSeat
        print ('---------登录成功！开始预约---------')
        while(count>0):
            rs = yd(loginRS,isAfternoon)
            if(rs==1):
                # 预约成功！
                sender(True)
                break
            # 将返回结果匹配时间规则，如果是时间类型，则延迟60-秒数后再次预约
            rsSlic = extract_date(rs)
            if(rsSlic!=None):
                count = count-1
                temptime = (60-int(rsSlic[3:5]))%60*60-int(rsSlic[6:8])+1
                if(temptime>0):
                    print ('---------将在延迟',temptime,'秒后运行---------')
                    time.sleep(temptime)
                if(count>0):
                    continue
                sender(False)
            else:
                count=count-1
                time.sleep(1)
                if(count>0):
                    continue
                sender(False)
        if isAfternoon:
            print ("*********将在明天八点再次预约*********")
        else:
            print ("*********将在下午五点再次预约*********")


# 创建定时任务
print ("*********程序开始运行，将在每天8、17点开始预约*********")
scheduler = BlockingScheduler()
scheduler.add_job(job_func,'cron',hour='7,16',minute='59',second='0')

scheduler.start()



'''
# 判断中午还是下午函数
def job_func():
    now = datetime.datetime.now()
    nowHour = now.hour
    nowMinute = now.minute
    # 判断现在时间是否为8点
    if nowHour == 8 and nowMinute == 0:
        # 调用循环预约函数
        circuSelectSeat(nowHour)
        print ("---------将在下午五点再次预约：---------")
    elif nowHour == 17 and nowMinute == 0:
        # 调用循环预约函数
        circuSelectSeat(nowHour)
        print ("---------将在明天八点再次预约：---------")
elif(isFirst):
    nextyd = 0
    if(nowHour<8):
        nextyd = (7-nowHour)*3600+(59-nowMinute)*60
    elif(7<nowHour<17):
        nextyd = (16-nowHour)*3600+(59-nowMinute)*60
    elif(16<nowHour<24):
        nextyd = (24-nowHour+7)*3600+(59-nowMinute)*60
    print ("----不在预设时间段内，将在"+str(nextyd//3600)+"小时"+str(nextyd%3600//60)+"分钟后检查重试----")
    isFirst = False
    time.sleep(nextyd)
    continue
# 每1s检查一次时间
time.sleep(1)

'''
'''
ps -ef | grep getSeat.py
kill -9 pid
// 一个/是覆盖原文件，两个/是追加文件，在后台运行抢座且记录日志
nohup python3 -u getSeat.py >> getSeatOutput.log 2>&1 &
tail -f getSeatOutput.log # 实时查看输出的命令


    print(re.text)
    res = json.loads(re.text)
    msg = res['Msg']
    if msg == '操作成功！':
        print('success')
        return 1
    elif msg == '2020-09-11只能提前[1]天预约':
        return 0
    else:
        print('fail')
        return 2


#脚本输入提示信息
def useage():
    print(
	'
	Usage:
	    -i    学号（必填）
	    -p    密码
	    -s    座位id
	    -b    开始时间，格式13:00，下同
	    -e    结束时间
	')

if __name__ == '__main__':
    id = pwd = None
    #不填默认抢这个这个时间段的这个座位
    s_id = '100458282'
    begin = '8:00'
    end = '22:00'
 
    #处理输入
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'i:p:s:b:e:')
        for name, value in opts:
            if name == '-i':
                id = value
            if name == '-p':
                pwd = value
            if name == '-s':
                s_id = value
            if name == '-b':
                begin = value
            if name == '-e':
                end = value
    except getopt.GetoptError:
        useage()
    if not id:
        useage()
        sys.exit(3)
    if not pwd:
        pwd = id

    #先获取后天时间
    aftertomorrow = date.isoformat(date.today() + timedelta(days=2))
    while True:
        hour = int(time.strftime('%H',time.localtime(time.time())))
        m = int(time.strftime('%M', time.localtime(time.time())))
        #如果现在的明天等与之前的后天，即到了12点，开始抢座
        if date.isoformat(date.today() + timedelta(days=1)) == aftertomorrow:
 
            s = login(id, pwd)
 
            start = aftertomorrow + ' ' + begin
            endtime = aftertomorrow + ' ' + end
            result = yd(s, start, endtime, s_id)
 
            if result == 1:
                #预约成功
                aftertomorrow = date.isoformat(date.today() + timedelta(days=2))
                sleep_time = (23 - hour) * 3600 + (59 - m) * 60 + 35
                print('程序休眠{}s'.format(sleep_time))
                print(aftertomorrow)
                time.sleep(sleep_time)
 
            elif result == 2:
                #被预约，抢下一个id的座位
                s_id = str(int(s_id) - 1)
                continue
            else:
                continue
        else:
            sleep_time = (23 - hour) * 3600 + (59 - m) * 60
            time.sleep(sleep_time)
'''
