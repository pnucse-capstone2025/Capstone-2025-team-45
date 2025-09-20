
import re
import pandas as pd
import pickle
import numpy as np  
from pathlib import Path
from typing import Annotated
from sqlalchemy.orm import Session
from sqlalchemy.inspection import inspect as sqla_inspect
from fastapi import Depends
from datetime import datetime, timedelta  
from model.database import engine, get_db, Base, SessionLocal

class NumericEncoder:
    """
    일주일 치 행동 로그 데이터를 숫자 데이터로 변환하는 클래스 
    """
    def __init__ (self, users : pd.DataFrame, logs: pd.DataFrame):
        self.users = users
        self.logs = logs
    
    def run(self):
        user_dict = {idx: i for (i, idx) in enumerate(self.users.index)}
        user_list = self._get_user_list(self.logs)
        df_u_week = self._encode_log(user_list, user_dict)
        return df_u_week    

    def _get_user_list(self, logs: pd.DataFrame):
        """
        행동 로그에 포함된 사용자 목록 반환 
        """
        result = []
        for log in logs.itertuples():
            if log.user not in result:
                result.append(log.user)
        return result   

    def _encode_log(self, user_list, user_dict):
        """
        사용자 행동 로그를 숫자 데이터로 변환
        """
        acts_week = self.logs.copy()
        acts_week.sort_values('date', ascending = True, inplace = True)
        n_cols = 25
        u_week = np.zeros((len(acts_week), n_cols))
        pc_time = []

        current_ind = 0
        for user in user_list:
            df_acts_u = self.logs[self.logs.user == user]
            list_uacts = df_acts_u.type.tolist()
            list_activity = df_acts_u.activity.tolist()
            list_uacts = [list_activity[i].strip().lower() 
              if (type(list_activity[i])==str 
                  and list_activity[i].strip() in ['Logon','Logoff','Connect','Disconnect']) 
              else list_uacts[i] 
              for i in range(len(list_uacts))]
            uacts_mapping = {'logon':1, 'logoff':2, 'connect':3, 'disconnect':4, 'http':5,'email':6,'file':7}
            list_uacts_num = [uacts_mapping[x] for x in list_uacts]

            oneu_week = np.zeros((len(df_acts_u), n_cols))
            oneu_pc_time = []
            for i in range(len(df_acts_u)): 
                pc, _ = self._from_pc(df_acts_u.iloc[i], self.users)
                if self._is_weekend(df_acts_u.iloc[i]['date']):
                    if self._is_after_whour(df_acts_u.iloc[i]['date']):
                        act_time = 4
                    else:
                        act_time = 3
                elif self._is_after_whour(df_acts_u.iloc[i]['date']):
                    act_time = 2
                else:
                    act_time = 1
                device_f = [0]
                file_f = [0, 0, 0, 0, 0]
                http_f = [0,0,0,0,0]
                email_f = [0]*9
                if list_uacts[i] == 'file':
                    file_f = self._file_process(df_acts_u.iloc[i])
                elif list_uacts[i] == 'email':
                    email_f = self._email_process(df_acts_u.iloc[i])
                elif list_uacts[i] == 'http':
                    http_f = self._http_process(df_acts_u.iloc[i])
                elif list_uacts[i] == 'connect':
                    tmp = df_acts_u.iloc[i:]
                    disconnect_acts = tmp[(tmp['activity'] == 'Disconnect\n') & \
                    (tmp['user'] == df_acts_u.iloc[i]['user']) & \
                    (tmp['pc'] == df_acts_u.iloc[i]['pc'])]
                    
                    connect_acts = tmp[(tmp['activity'] == 'Connect\n') & \
                    (tmp['user'] == df_acts_u.iloc[i]['user']) & \
                    (tmp['pc'] == df_acts_u.iloc[i]['pc'])]

                    if len(disconnect_acts) > 0:
                        distime = disconnect_acts.iloc[0]['date']
                        if len(connect_acts) > 0 and connect_acts.iloc[0]['date'] < distime:
                            connect_dur = -1
                        else:
                            tmp_td = distime - df_acts_u.iloc[i]['date']
                            connect_dur = tmp_td.days*24*3600 + tmp_td.seconds
                    else:
                        connect_dur = -1 # disconnect action not found!
                    device_f = [connect_dur]
                    
                val = df_acts_u.iloc[i]['date']
                dt  = pd.to_datetime(val, utc=True).tz_localize(None).to_pydatetime()
                day =  self._time_convert(inp = dt, mode ='dt2dn')
                oneu_week[i,:] = [ user_dict[user], day, list_uacts_num[i], pc, act_time] \
                + device_f + file_f + http_f + email_f
                oneu_pc_time.append([df_acts_u.index[i], df_acts_u.iloc[i]['pc'],df_acts_u.iloc[i]['date']])

            u_week[current_ind:current_ind+len(oneu_week),:] = oneu_week
            pc_time += oneu_pc_time
            current_ind += len(oneu_week)
        
        u_week = u_week[0:current_ind, :]
        col_names = ['user','day','act','pc','time']
        device_feature_names = ['usb_dur']
        file_feature_names = ['file_type', 'file_len', 'file_nwords', 'disk', 'file_depth']
        http_feature_names = ['http_type', 'url_len','url_depth', 'http_c_len', 'http_c_nwords']
        email_feature_names = ['n_des', 'n_atts', 'Xemail', 'n_exdes', 'n_bccdes', 'exbccmail', 'email_size', 'email_text_slen', 'email_text_nwords']

        col_names = col_names + device_feature_names + file_feature_names+ http_feature_names + email_feature_names
        df_u_week = pd.DataFrame(columns=['actid','pcid','time_stamp'] + col_names, index = np.arange(0,len(pc_time)))
        df_u_week[['actid','pcid','time_stamp']] = np.array(pc_time)
        df_u_week[col_names] = u_week
        bad = ~np.isfinite(df_u_week[col_names].to_numpy(dtype=float))

        df_u_week[col_names] = df_u_week[col_names].astype(int)
        # df_u_week.to_pickle("Result/week_num.pickle")
        return df_u_week



    def _from_pc(self, act, ul):
        """
        사용한 PC 의 타입을 반환 
        0: 본인 pc
        1: 공유 pc
        2: 타인 pc
        3: 관리자 pc
        """
        user_pc = ul.loc[act.user, "pc"]
        act_pc = act["pc"]
        if act_pc == user_pc:
            return (0, act_pc) #using normal PC
        elif ul.loc[act['user']]['sharedpc'] is not None and act_pc in ul.loc[act['user']]['sharedpc']:
            return (1, act_pc)
        elif ul.loc[act['user']]['sup'] is not None and act_pc == ul.loc[ul.loc[act['user']]['sup']]['pc']:
            return (3, act_pc)
        else:
            return (2, act_pc)
        
    def _is_weekend(self, date):
        """
        주말 여부 확인
        """
        if date.strftime("%w") in ['0', '6']:
            return True
        return False

    def _is_after_whour(self, dt): 
        #작업 시간: 7:30 - 17:30
        wday_start = datetime.strptime("7:30", "%H:%M").time()
        wday_end = datetime.strptime("17:30", "%H:%M").time()
        dt = dt.time()
        if dt < wday_start or dt > wday_end:
            return True
        return False

    def _file_process(self, act):   
        ftype = act['url/fname'].split(".")[1]
        disk = 0
        file_depth = 0 
        fsize = 0
        f_nwords = 0

        if ftype in ['zip','rar','7z']:
            r = 2
        elif ftype in ['jpg', 'png', 'bmp']:
            r = 3
        elif ftype in ['doc','docx', 'pdf']:
            r = 4
        elif ftype in ['txt','cfg','rtf']:
            r = 5
        elif ftype in ['exe', 'sh']:
            r = 6
        else:
            r = 1
        return [r, fsize, disk, file_depth, f_nwords]
    
    def _email_process(self, act):  
        receivers = act['to'].split(';')
        if type(act['cc']) == str:
            receivers = receivers + act['cc'].split(";")
        if type(act['bcc']) == str:
            bccreceivers = act['bcc'].split(";")   
        else:
            bccreceivers = []
        
        exemail = False
        n_exdes = 0

        for i in receivers + bccreceivers:
            if 'dtaa.com' not in i:
                exemail = True
                n_exdes += 1

        n_des = len(receivers) + len(bccreceivers)
        Xemail = 1 if exemail else 0
        n_bccdes = len(bccreceivers)
        exbccmail = 0

        email_text_len = 0
        email_text_nwords = 0

        for i in bccreceivers:
            if 'dtaa.com' not in i:
                exbccmail = 1
                break

        return [n_des, int(act['#att']), Xemail, n_exdes, n_bccdes, exbccmail, int(act['size']), email_text_len, email_text_nwords]
    
    def _http_process(self, act):
        if pd.isna(act['url/fname']):
            return [1, 0, 0, 0, 0]
        url_len = len(act['url/fname'])
        url_depth = act['url/fname'].count('/')-2
        content_len = 0
        content_nwords = 0

        domainname = re.findall("//(.*?)/", act['url/fname'])[0]
        domainname.replace("www.","")
        dn = domainname.split(".")
        if len(dn) > 2 and not any([x in domainname for x in ["google.com", '.co.uk', '.co.nz', 'live.com']]):
            domainname = ".".join(dn[-2:])

        # other 1, socnet 2, cloud 3, job 4, leak 5, hack 6
        if domainname in ['dropbox.com', 'drive.google.com', 'mega.co.nz', 'account.live.com']:
            r = 3
        elif domainname in ['wikileaks.org','freedom.press','theintercept.com']:
            r = 5
        elif domainname in ['facebook.com','twitter.com','plus.google.com','instagr.am','instagram.com',
                            'flickr.com','linkedin.com','reddit.com','about.com','youtube.com','pinterest.com',
                            'tumblr.com','quora.com','vine.co','match.com','t.co']:
            r = 2
        elif domainname in ['indeed.com','monster.com', 'careerbuilder.com','simplyhired.com']:
            r = 4
        
        elif ('job' in domainname and ('hunt' in domainname or 'search' in domainname)) \
        or ('aol.com' in domainname and ("recruit" in act['url/fname'] or "job" in act['url/fname'])):
            r = 4
        elif (domainname in ['webwatchernow.com','actionalert.com', 'relytec.com','refog.com','wellresearchedreviews.com',
                            'softactivity.com', 'spectorsoft.com','best-spy-soft.com']):
            r = 6
        elif ('keylog' in domainname):
            r = 6
        else:
            r = 1
        
        return [r, url_len, url_depth, content_len, content_nwords]
        
    def _time_convert(self, inp, mode, real_sd = '2010-01-02', sd_monday= "2009-12-28"):
        if mode == 'e2t':
            return datetime.fromtimestamp(inp).strftime('%m/%d/%Y %H:%M:%S')
        elif mode == 't2e':
            return datetime.strptime(inp, '%m/%d/%Y %H:%M:%S').strftime('%s')
        elif mode == 't2dt':
            return datetime.strptime(inp, '%m/%d/%Y %H:%M:%S')
        elif mode == 't2date':
            return datetime.strptime(inp, '%m/%d/%Y %H:%M:%S').strftime("%Y-%m-%d")
        elif mode == 'dt2t':
            return inp.strftime('%m/%d/%Y %H:%M:%S')
        elif mode == 'dt2W':
            return int(inp.strftime('%W'))
        elif mode == 'dt2d':
            return inp.strftime('%m/%d/%Y %H:%M:%S')
        elif mode == 'dt2date':
            return inp.strftime("%Y-%m-%d")
        elif mode =='dt2dn': #datetime to day number
            startdate = datetime.strptime(sd_monday,'%Y-%m-%d')
            return (inp - startdate).days
        elif mode =='dn2epoch': #datenum to epoch
            dt = datetime.strptime(sd_monday,'%Y-%m-%d') + timedelta(days=inp)
            return int(dt.timestamp())
        elif mode =='dt2wn': #datetime to week number
            startdate = datetime.strptime(real_sd,'%Y-%m-%d')
            return (inp - startdate).days//7
        elif mode =='t2wn': #datetime to week number
            startdate = datetime.strptime(real_sd,'%Y-%m-%d')
            return (datetime.strptime(inp, '%m/%d/%Y %H:%M:%S') - startdate).days//7
        elif mode == 'dt2wd':
            return int(inp.strftime("%w"))
        elif mode == 'm2dt':
            return datetime.strptime(inp, "%Y-%m")
        elif mode == 'datetoweekday':
            return int(datetime.strptime(inp,"%Y-%m-%d").strftime('%w'))
        elif mode == 'datetoweeknum':
            w0 = datetime.strptime(sd_monday,"%Y-%m-%d")
            return int((datetime.strptime(inp,"%Y-%m-%d") - w0).days / 7)
        elif mode == 'weeknumtodate':
            startday = datetime.strptime(sd_monday,"%Y-%m-%d")
            return startday+timedelta(weeks = inp)