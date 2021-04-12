import re
import time
import requests
import json
import os
import sys
import urllib
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr
from encrypto import encrypt_passwd


def get_user():
    account = []
    passwd = []
    state = 0
    name_file = 'data/username.txt';
    pass_file = 'data/password.txt';

    try:
        f = open(name_file, mode='r');
        lines = f.readlines();
        for line in lines:
            conn = line.strip('\n');
            account.append(conn);
        f.close();
        print('账号文件打开成功');
    except:
        state = 1;
        print('账号文件打开有误');

    try:
        f = open(pass_file, mode='r');
        lines = f.readlines();
        for line in lines:
            conn = line.strip('\n');
            passwd.append(encrypt_passwd(conn));
        f.close();
        print('密码文件打开成功');
    except:
        state = 1;
        print('密码文件打开有误');
    return account, passwd, state;


def get_time_stamp():
    now_time = time.localtime(time.time());

    if now_time[3] >= 3 and now_time[3] <= 5:
        start_time = '11:00:00';
    else:
        return 1;

    now_year = str(now_time[0]);
    now_mouth = str(now_time[1]);
    now_day = str(now_time[2]);
    fixed_time = (str(now_year + '-' + now_mouth + '-' + now_day + ' ' + start_time));
    fixed_time = time.strptime(fixed_time, "%Y-%m-%d  %H:%M:%S");
    timestamp = int(time.mktime(fixed_time));

    return timestamp;


def login(account, passwd, csrf, csrf_cookies, header):
    params = {
        "account": account,
        "ct": 1,
        "identify": 1,
        "v": "4.7.12",
        "passwd": passwd
    }
    login_url = 'https://mobile.yiban.cn/api/v2/passport/login';
    login_r = requests.get(login_url, params=params);
    login_json = login_r.json();
    user_name = login_json['data']['user']['name'];
    access_token = login_json['data']['access_token'];

    return user_name, access_token;


def auth(access_token, csrf, csrf_cookies, header):
    auth_first_url = 'http://f.yiban.cn/iapp/index?act=iapp7463&v=' + access_token + '';
    auth_first_r = requests.get(auth_first_url, timeout=10, headers=header, allow_redirects=False).headers['Location'];
    verify_request = re.findall(r"verify_request=(.*?)&", auth_first_r)[0];

    auth_second_url = 'https://api.uyiban.com/base/c/auth/yiban?verifyRequest=' + verify_request + '&CSRF=' + csrf;
    auth_result = requests.get(auth_second_url, timeout=10, headers=header, cookies=csrf_cookies);
    auth_cookie = auth_result.cookies;
    auth_json = auth_result.json();

    return auth_cookie;


def get_uncomplete_list(csrf, csrf_cookies, auth_cookie, header):
    uncomplete_url = 'https://api.uyiban.com/officeTask/client/index/uncompletedList?CSRF={}'.format(csrf);

    result_cookie = {
        'csrf_token': csrf,
        'PHPSESSID': auth_cookie['PHPSESSID'],
        'cpi': auth_cookie['cpi']
    }
    uncomplete_r = requests.get(uncomplete_url, timeout=10, headers=header, cookies=result_cookie);
    task_num = len(uncomplete_r.json()['data']);
    for i in range(0, task_num):
        task_time = uncomplete_r.json()['data'][i]['StartTime'];
        time = get_time_stamp();
        if time == task_time:
            task_id = uncomplete_r.json()['data'][i]['TaskId'];
            user_state = 0;
            return task_id, result_cookie, user_state;
            break;


def get_task_detail(task_id, csrf, result_cookie, header):
    task_detail_url = 'https://api.uyiban.com/officeTask/client/index/detail?TaskId={0}&CSRF={1}'.format(task_id, csrf);
    task_detail_r = requests.get(task_detail_url, timeout=10, headers=header, cookies=result_cookie);
    task_result = task_detail_r.json();
    task_wfid = task_result['data']['WFId'];
    return task_result, task_wfid;


def task_submit(task_wfid, csrf, result_cookie, header, task_result, temperature):
    extend = {"TaskId": task_result['data']['Id'],
              "title": "任务信息",
              "content": [{"label": "任务名称", "value": task_result['data']['Title']},
                          {"label": "发布机构", "value": task_result['data']['PubOrgName']},
                          {"label": "发布人", "value": task_result['data']['PubPersonName']}]}
    data = {"0caddc48d709afde9cc4986b3a85155e": temperature,
            "a4f42d8428d2d4ca3f4562ff86305eb0": {"name": "菜鸟驿站",
                                                 "location": "113.109408,22.629419",
                                                 "address": "潮连街道潮连大道6号江门职业技术学院"}}

    params = {
        'data': json.dumps(data),
        'extend': json.dumps(extend)
    }

    task_submit_url = 'https://api.uyiban.com/workFlow/c/my/apply/{0}?CSRF={1}'.format(task_wfid, csrf);
    task_submit_r = requests.post(task_submit_url, timeout=10, headers=header, cookies=result_cookie, data=params);


def start(log):
    csrf = "365a9bc7c77897e40b0c7ecdb87806d9"
    csrf_cookies = {"csrf_token": csrf}
    header = {"Origin": "https://c.uyiban.com", "User-Agent": "yiban"}

    get_time_stamp();

    account, passwd, state = get_user();

    if state == 1:
        print('账号或者密码文件打开有误');
        exit();

    if len(account) != len(passwd):
        print('账号和密码数量不一致');
        exit();
    a = get_time_stamp();
    for i in range(0, len(account)):
        now_time = time.localtime(time.time());
        temperature = '36.' + str((now_time[5] % 10) // 2 + 4)
        print(account[i]);
        print(account[i], file=log);
        try:
            user_name, access_token = login(account[i], passwd[i], csrf, csrf_cookies, header);
            try:
                auth_cookie = auth(access_token, csrf, csrf_cookies, header);
                try:
                    task_id, result_cookie, user_state = get_uncomplete_list(csrf, csrf_cookies, auth_cookie, header);

                    try:
                        task_result, task_wfid = get_task_detail(task_id, csrf, result_cookie, header);
                        conncet = task_submit(task_wfid, csrf, result_cookie, header, task_result, temperature);
                        print(user_name + '完成签到，随机温度为：' + temperature + '。本程序于' + str(now_time[5] % 10) + '秒后继续运行！');
                        print(user_name + '完成签到，随机温度为：' + temperature + '。本程序于' + str(now_time[5] % 10) + '秒后继续运行！',
                              file=log);
                    except:
                        print('');
                except:
                    print(user_name + '没有获取到未完成的任务');
                    print(user_name + '没有获取到未完成的任务', file=log);
                    continue;
            except:
                print(user_name + '没有获取到cookie');
                print(user_name + '没有获取到cookie', file=log);
                continue;
        except:
            print(user_name + '账号或者密码错误');
            print(user_name + '账号或者密码错误', file=log);
            continue;
        time.sleep(now_time[5] % 10)


def email(now_time):
    log = open('log/' + str(now_time[0]) + '.' + str(now_time[1]) + '.' + str(now_time[2]) + '-' + str(
        now_time[3]) + '.' + str(now_time[4]) + '.txt', 'r')
    my_sender = '2041804945@qq.com'  # 发件人邮箱账号
    my_pass = 'xdvwecoafgsfbgfc'  # 发件人邮箱密码(当时申请smtp给的口令)
    my_user = '847442404@qq.com'  # 收件人邮箱账号，我这边发送给自己

    def mail():
        ret = True
        try:
            msg = MIMEText(log.read(), 'plain', 'utf-8')
            msg['From'] = formataddr(["Sailing", my_sender])  # 括号里的对应发件人邮箱昵称、发件人邮箱账号
            msg['To'] = formataddr(["易班自动签到提醒", my_user])  # 括号里的对应收件人邮箱昵称、收件人邮箱账号
            msg['Subject'] = "已经完成" + str(now_time[0]) + '-' + str(now_time[1]) + '-' + str(now_time[2]) + ' ' + str(
                now_time[3]) + "点的签到任务"  # 邮件的主题，也可以说是标题

            server = smtplib.SMTP_SSL("smtp.qq.com", 465)  # 发件人邮箱中的SMTP服务器，端口是465
            server.login(my_sender, my_pass)  # 括号中对应的是发件人邮箱账号、邮箱密码
            server.sendmail(my_sender, [my_user, ], msg.as_string())  # 括号中对应的是发件人邮箱账号、收件人邮箱账号、发送邮件
            server.quit()  # 关闭连接

            token = '643c8194bd58416d88717fabbe6f9bde'  # 在pushpush网站中可以找到
            title = '易班签到'  # 改成你要的标题内容
            content = '签到完毕'  # 改成你要的正文内容
            topic = '111'
            #url = 'http://pushplus.hxtrip.com/send?token=' + token + '&title=' + title + '&content=' + content + '&template=html&topic=' + topic
            #requests.get(url)

        except Exception:  # 如果 try 中的语句没有执行，则会执行下面的 ret=False
            ret = False
        return ret

    ret = mail()
    if ret:
        print("邮件发送成功")
    else:
        print("邮件发送失败")
    log.close()


if __name__ == '__main__':
    while True:
        now_time = time.localtime(time.time());
        if (now_time[3] >= 3 and now_time[3] <= 5):
            log = open('log/' + str(now_time[0]) + '.' + str(now_time[1]) + '.' + str(now_time[2]) + '-' + str(
                now_time[3]) + '.' + str(now_time[4]) + '.txt', 'w')
            print('---------------------------------------------------');
            print('目前时间：' + str(now_time[1]) + '-' + str(now_time[2]) + ' ' + str(now_time[3]) + ':' + str(
                now_time[4]) + '。签到开始！！！')
            print('目前时间：' + str(now_time[1]) + '-' + str(now_time[2]) + ' ' + str(now_time[3]) + ':' + str(
                now_time[4]) + '。签到开始！！！', file=log)
            start(log);
            log.close()
            print('---------------------------------------------------');
            email(now_time);
            print('---------------------------------------------------');
            print('已经完成' + str(now_time[3]) + '点的签到任务，本程序于1小时后重新检测。')
            print('---------------------------------------------------');
            time.sleep(36);
            sys.exit(0)

        else:
            print('目前时间：' + str(now_time[1]) + '-' + str(now_time[2]) + ' ' + str(now_time[3]) + ':' + str(
                now_time[4]) + '。不在签到时间！本程序于30分钟后重新检测。')
            time.sleep(18);
            sys.exit(0)
