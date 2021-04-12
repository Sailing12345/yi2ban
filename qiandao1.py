import re
import time
import requests
import json
import os
import urllib
import sys
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
   except:
       state = 1;

   try:
       f = open(pass_file, mode='r');
       lines = f.readlines();
       for line in lines:
           conn = line.strip('\n');
           passwd.append(encrypt_passwd(conn));
       f.close();
   except:
       state = 1;

   return account, passwd, state;


def get_time_stamp():
   now_time = time.localtime(time.time());

   if now_time[3] == 0 or now_time[3] == 1 or now_time[3] == 2:
       start_time = '7:00:00';
   elif now_time[3] == 3 or now_time[3] == 4 or now_time[3] == 5:
       start_time = '11:00:00';
   elif now_time[3] >= 10 and now_time[3] <= 12:
       start_time = '17:30:00';
   else:
       return 1;

   now_year = str(now_time[0]);
   now_mouth = str(now_time[1]);
   now_day = str(now_time[2]);
   fixed_time = (str(now_year + '-' + now_mouth + '-' + now_day + ' ' + start_time));
   fixed_time = time.strptime(fixed_time, "%Y-%m-%d  %H:%M:%S");
   timestamp = int(time.mktime(fixed_time));

   return timestamp;

#登录页面
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

#二次认证
def auth(access_token, csrf, csrf_cookies, header):
   auth_first_url = 'http://f.yiban.cn/iapp/index?act=iapp7463&v=' + access_token + '';
   auth_first_r = requests.get(auth_first_url, timeout=10, headers=header, allow_redirects=False).headers['Location'];
   verify_request = re.findall(r"verify_request=(.*?)&", auth_first_r)[0];

   auth_second_url = 'https://api.uyiban.com/base/c/auth/yiban?verifyRequest=' + verify_request + '&CSRF=' + csrf;
   auth_result = requests.get(auth_second_url, timeout=10, headers=header, cookies=csrf_cookies);
   auth_cookie = auth_result.cookies;
   auth_json = auth_result.json();

   return auth_cookie;


'''
def get_complete_list(csrf,csrf_cookies,auth_cookie,header):
   complete_url = 'https://api.uyiban.com/officeTask/client/index/completedList?CSRF={}'.format(csrf);

   result_cookie = {
       'csrf_token': csrf,
       'PHPSESSID': auth_cookie['PHPSESSID'],
       'cpi': auth_cookie['cpi']
   }
   complete_r = requests.get(complete_url, timeout = 10, headers = header, cookies = result_cookie);
   task_num = len(complete_r.json()['data']);
   time = get_time_stamp();

   for i in range(0, task_num):
       task_time = complete_r.json()['data'][i]['StartTime'];
       if time == task_time:
           task_id = complete_r.json()['data'][i]['TaskId'];
           get_task_detail(task_id, csrf, result_cookie, header);
           break;
'''

#未完成的任务
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

#获取表单信息
def get_task_detail(task_id, csrf, result_cookie, header):
   task_detail_url = 'https://api.uyiban.com/officeTask/client/index/detail?TaskId={0}&CSRF={1}'.format(task_id, csrf);
   task_detail_r = requests.get(task_detail_url, timeout=10, headers=header, cookies=result_cookie);
   task_result = task_detail_r.json();
   task_wfid = task_result['data']['WFId'];
   return task_result, task_wfid;

#提交表单
def task_submit(task_wfid, csrf, result_cookie, header, task_result):
   extend = {"TaskId": task_result['data']['Id'],
             "title": "任务信息",
             "content": [{"label": "任务名称", "value": task_result['data']['Title']},
                         {"label": "发布机构", "value": task_result['data']['PubOrgName']},
                         {"label": "发布人", "value": task_result['data']['PubPersonName']}]}
   data = {"0caddc48d709afde9cc4986b3a85155e": "36.5",
           "a4f42d8428d2d4ca3f4562ff86305eb0": {"name": "菜鸟驿站",
                                                "location": "113.109408,22.629419",
                                                "address": "潮连街道潮连大道6号江门职业技术学院"}}

   params = {
       'data': json.dumps(data),
       'extend': json.dumps(extend)
   }

   task_submit_url = 'https://api.uyiban.com/workFlow/c/my/apply/{0}?CSRF={1}'.format(task_wfid, csrf);
   task_submit_r = requests.post(task_submit_url, timeout=10, headers=header, cookies=result_cookie, data=params);

#运行程序
def start():
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

   for i in range(0, len(account)):
       print(account[i]);
       try:
           user_name, access_token = login(account[i], passwd[i], csrf, csrf_cookies, header);
           try:
               auth_cookie = auth(access_token, csrf, csrf_cookies, header);
               try:
                   task_id, result_cookie, user_state = get_uncomplete_list(csrf, csrf_cookies, auth_cookie, header);

                   try:
                       task_result, task_wfid = get_task_detail(task_id, csrf, result_cookie, header);
                       conncet = task_submit(task_wfid, csrf, result_cookie, header, task_result);
                       print(user_name + '完成签到');
                   except:
                       print('');
               except:
                   print(user_name + '没有获取到未完成的任务');
                   continue;
           except:
               print(user_name + '没有获取到cookie');
               continue;
       except:
           print(user_name + '账号或者密码错误');
           continue;

#脚本自动跑
if __name__ == '__main__':
   def time_sleep(n):
       while True:
           a = get_time_stamp();
           now_time = time.localtime(time.time());
           print(
               str(now_time[1]) + '-' + str(now_time[2]) + ' ' + str(now_time[3]) + ':' + str(now_time[4]) + ':' + str(
                   now_time[5]));
           start();
           if (now_time[3] >= 0 and now_time[3] <= 12):
               time.sleep(18);
               sys.exit(0)
           else:
               time.sleep(36);
               sys.exit(0)
   time_sleep(5);

