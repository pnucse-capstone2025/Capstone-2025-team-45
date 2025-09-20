import os 
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

class FeatureAggregator:
    """
    사용자 단위로 집계한 피처 테이블 생성
    week: 사용자 x 해당 주 1행
    """
    def __init__ (self, user_df: pd.DataFrame, week_data: pd.DataFrame):
        """
        user_df: 사용자 id, 이름, 이메일, 역할 소속, PC, 공유 PC 정보 
        """
        self.user_df = user_df
        self.week_data = week_data
    def run(self):
        # 사용자 목록 디셔너리화 - 0: "CEL0561"
        user_dict = {i : idx for (i, idx) in enumerate(self.user_df.index)}
        
        cols2a = ['starttime', 'endtime', 'user',] + ['ITAdmin']
        week_data = self.week_data.copy()

        # usnlist: 해당 주에 활동한 사용자 목록 (int)
        usnlist = list(map(int, set(week_data['user'].astype('int').values)))

        # ITAdmin 여부 col 추가
        cols = ['ITAdmin']
        uw = pd.DataFrame(columns = cols, index = user_dict.keys())
        uwdict = {}
        for v in user_dict:
            if v in usnlist:
                is_ITAdmin = 1 if self.user_df.loc[user_dict[v], 'role'] == 'ITAdmin' else 0
                row = [is_ITAdmin] 
                uwdict[v] = row
        
        #uw: 각 사용자들의 IT 관리자 여부 가 저장된 데이터 프레임 
        uw = pd.DataFrame.from_dict(uwdict, orient = 'index',columns = cols)  

        towrite = pd.DataFrame()
        towrite_list = []

        days = list(set(week_data['day']))
        uwdict = {}
        for v in user_dict:
            if v in usnlist:
                # 특정 사용자의 주간 행동 데이터 
                user_act_week = week_data[week_data['user'] == v]
                a = user_act_week.iloc[0]['time_stamp']
                a = a - timedelta(int(a.strftime("%w"))) # get the nearest Sunday
                starttime = datetime(a.year, a.month, a.day).timestamp()
                endtime = (datetime(a.year, a.month, a.day) + timedelta(days=7)).timestamp()
                if len(user_act_week) > 0:
                    tmp = self._feature_calculate(user_act_week)
                    i_fnames = tmp[3]
                    towrite_list.append([starttime, endtime, v,] + (uw.loc[v, ['ITAdmin']]).tolist() + tmp[2] )
        towrite = pd.DataFrame(columns = cols2a + i_fnames, data = towrite_list)
        return user_dict, towrite 
    
    def _feature_calculate(self, ud: pd.DataFrame, mode = 'week', data = 'r4.2'):
        """
        사용자 주간 행동 데이터로부터 피처를 계산
        """

        n_weekendact = (ud['time']==3).sum()
        if n_weekendact > 0: 
            is_weekend = 1
        else: 
            is_weekend = 0
        
        all_countonlyf = {'pc':[0,1,2,3]} if mode != 'session' else {}
        [all_f, all_f_names] = self._f_calc_subfeatures(ud, 'allact', None, [], [], [], all_countonlyf)
        if mode == 'day':
            [workhourf, workhourf_names] = self._f_calc_subfeatures(ud[(ud['time'] == 1) | (ud['time'] == 3)], 'workhourallact', None, [], [], [], all_countonlyf)
            [afterhourf, afterhourf_names] = self._f_calc_subfeatures(ud[(ud['time'] == 2) | (ud['time'] == 4) ], 'afterhourallact', None, [], [], [], all_countonlyf)
        elif mode == 'week':
            [workhourf, workhourf_names] = self._f_calc_subfeatures(ud[ud['time'] == 1], 'workhourallact', None, [], [], [], all_countonlyf)
            [afterhourf, afterhourf_names] = self._f_calc_subfeatures(ud[ud['time'] == 2 ], 'afterhourallact', None, [], [], [], all_countonlyf)
            [weekendf, weekendf_names] = self._f_calc_subfeatures(ud[ud['time'] >= 3 ], 'weekendallact', None, [], [], [], all_countonlyf)

        logon_countonlyf = {'pc':[0,1,2,3]} if mode != 'session' else {}
        logon_statf = []

        [all_logonf, all_logonf_names] = self._f_calc_subfeatures(ud[ud['act']==1], 'logon', None, [], [], logon_statf, logon_countonlyf)
        if mode == 'day':
            [workhourlogonf, workhourlogonf_names] = self._f_calc_subfeatures(ud[(ud['act']==1) & ((ud['time'] == 1) | (ud['time'] == 3) )], 'workhourlogon', None, [], [], logon_statf, logon_countonlyf)
            [afterhourlogonf, afterhourlogonf_names] = self._f_calc_subfeatures(ud[(ud['act']==1) & ((ud['time'] == 2) | (ud['time'] == 4) )], 'afterhourlogon', None, [], [], logon_statf, logon_countonlyf)
        elif mode == 'week':
            [workhourlogonf, workhourlogonf_names] = self._f_calc_subfeatures(ud[(ud['act']==1) & (ud['time'] == 1)], 'workhourlogon', None, [], [], logon_statf, logon_countonlyf)
            [afterhourlogonf, afterhourlogonf_names] = self._f_calc_subfeatures(ud[(ud['act']==1) & (ud['time'] == 2) ], 'afterhourlogon', None, [], [], logon_statf, logon_countonlyf)
            [weekendlogonf, weekendlogonf_names] = self._f_calc_subfeatures(ud[(ud['act']==1) & (ud['time'] >= 3) ], 'weekendlogon', None, [], [], logon_statf, logon_countonlyf)

        device_countonlyf = {'pc':[0,1,2,3]} if mode != 'session' else {}
        device_statf = ['usb_dur','file_tree_len'] if data not in ['r4.1','r4.2'] else ['usb_dur']

        [all_devicef, all_devicef_names] = self._f_calc_subfeatures(ud[ud['act']==3], 'usb', None, [], [], device_statf, device_countonlyf)
        if mode == 'day':
            [workhourdevicef, workhourdevicef_names] = self._f_calc_subfeatures(ud[(ud['act']==3) & ((ud['time'] == 1) | (ud['time'] == 3) )], 'workhourusb', None, [], [], device_statf, device_countonlyf)
            [afterhourdevicef, afterhourdevicef_names] = self._f_calc_subfeatures(ud[(ud['act']==3) & ((ud['time'] == 2) | (ud['time'] == 4) )], 'afterhourusb', None, [], [], device_statf, device_countonlyf)
        elif mode == 'week':
            [workhourdevicef, workhourdevicef_names] = self._f_calc_subfeatures(ud[(ud['act']==3) & (ud['time'] == 1)], 'workhourusb', None, [], [], device_statf, device_countonlyf)
            [afterhourdevicef, afterhourdevicef_names] = self._f_calc_subfeatures(ud[(ud['act']==3) & (ud['time'] == 2) ], 'afterhourusb', None, [], [], device_statf, device_countonlyf)
            [weekenddevicef, weekenddevicef_names] = self._f_calc_subfeatures(ud[(ud['act']==3) & (ud['time'] >= 3) ], 'weekendusb', None, [], [], device_statf, device_countonlyf)

        if mode != 'session': file_countonlyf = {'to_usb':[1],'from_usb':[1], 'file_act':[1,2,3,4], 'disk':[0,1], 'pc':[0,1,2,3]}
        else: file_countonlyf = {'to_usb':[1],'from_usb':[1], 'file_act':[1,2,3,4], 'disk':[0,1,2]}
        if data in ['r4.1','r4.2']: 
            [file_countonlyf.pop(k) for k in ['to_usb','from_usb', 'file_act']]

        (all_filef, all_filef_names) = self._f_calc_subfeatures(ud[ud['act']==7], 'file', 'file_type', [1,2,3,4,5,6], \
                ['otherf','compf','phof','docf','txtf','exef'], ['file_len', 'file_depth', 'file_nwords'], file_countonlyf)
        
        if mode == 'day':
            (workhourfilef, workhourfilef_names) = self._f_calc_subfeatures(ud[(ud['act']==7) & ((ud['time'] ==1) | (ud['time'] ==3))], 'workhourfile', 'file_type', [1,2,3,4,5,6], ['otherf','compf','phof','docf','txtf','exef'], ['file_len', 'file_depth', 'file_nwords'], file_countonlyf)
            (afterhourfilef, afterhourfilef_names) = self._f_calc_subfeatures(ud[(ud['act']==7) & ((ud['time'] ==2) | (ud['time'] ==4))], 'afterhourfile', 'file_type', [1,2,3,4,5,6], ['otherf','compf','phof','docf','txtf','exef'], ['file_len', 'file_depth', 'file_nwords'], file_countonlyf)
        elif mode == 'week':
            (workhourfilef, workhourfilef_names) = self._f_calc_subfeatures(ud[(ud['act']==7) & (ud['time'] ==1)], 'workhourfile', 'file_type', [1,2,3,4,5,6], ['otherf','compf','phof','docf','txtf','exef'], ['file_len', 'file_depth', 'file_nwords'], file_countonlyf)
            (afterhourfilef, afterhourfilef_names) = self._f_calc_subfeatures(ud[(ud['act']==7) & (ud['time'] ==2)], 'afterhourfile', 'file_type', [1,2,3,4,5,6], ['otherf','compf','phof','docf','txtf','exef'], ['file_len', 'file_depth', 'file_nwords'], file_countonlyf)
            (weekendfilef, weekendfilef_names) = self._f_calc_subfeatures(ud[(ud['act']==7) & (ud['time'] >= 3)], 'weekendfile', 'file_type', [1,2,3,4,5,6], ['otherf','compf','phof','docf','txtf','exef'], ['file_len', 'file_depth', 'file_nwords'], file_countonlyf)

        email_stats_f = ['n_des', 'n_atts', 'n_exdes', 'n_bccdes', 'email_size', 'email_text_slen', 'email_text_nwords']
        if data not in ['r4.1','r4.2']:
            email_stats_f += ['e_att_other', 'e_att_comp', 'e_att_pho', 'e_att_doc', 'e_att_txt', 'e_att_exe']
            email_stats_f += ['e_att_sother', 'e_att_scomp', 'e_att_spho', 'e_att_sdoc', 'e_att_stxt', 'e_att_sexe'] 
            mail_filter = 'send_mail'
            mail_filter_vals = [0,1]
            mail_filter_names = ['recvmail','send_mail']
        else:
            mail_filter, mail_filter_vals, mail_filter_names = None, [], []    
        
        if mode != 'session': mail_countonlyf = {'Xemail':[1],'exbccmail':[1], 'pc':[0,1,2,3]}
        else: mail_countonlyf = {'Xemail':[1],'exbccmail':[1]}

        (all_emailf, all_emailf_names) = self._f_calc_subfeatures(ud[ud['act']==6], 'email', mail_filter, mail_filter_vals, mail_filter_names , email_stats_f, mail_countonlyf)
        if mode == 'week':
            (workhouremailf, workhouremailf_names) = self._f_calc_subfeatures(ud[(ud['act']==6) & (ud['time'] == 1)], 'workhouremail', mail_filter, mail_filter_vals, mail_filter_names, email_stats_f, mail_countonlyf)
            (afterhouremailf, afterhouremailf_names) = self._f_calc_subfeatures(ud[(ud['act']==6) & (ud['time'] == 2)], 'afterhouremail', mail_filter, mail_filter_vals, mail_filter_names, email_stats_f, mail_countonlyf)
            (weekendemailf, weekendemailf_names) = self._f_calc_subfeatures(ud[(ud['act']==6) & (ud['time'] >= 3)], 'weekendemail', mail_filter, mail_filter_vals, mail_filter_names, email_stats_f, mail_countonlyf)
        elif mode == 'day':
            (workhouremailf, workhouremailf_names) = self._f_calc_subfeatures(ud[(ud['act']==6) & ((ud['time'] ==1) | (ud['time'] ==3))], 'workhouremail', mail_filter, mail_filter_vals, mail_filter_names, email_stats_f, mail_countonlyf)
            (afterhouremailf, afterhouremailf_names) = self._f_calc_subfeatures(ud[(ud['act']==6) & ((ud['time'] ==2) | (ud['time'] ==4))], 'afterhouremail', mail_filter, mail_filter_vals, mail_filter_names, email_stats_f, mail_countonlyf)

        if data in ['r5.2','r5.1'] or data in ['r4.1','r4.2']:
            http_count_subf =  {'pc':[0,1,2,3]}
        elif data in ['r6.2','r6.1']:
            http_count_subf = {'pc':[0,1,2,3], 'http_act':[1,2,3]}
        
        if mode == 'session': http_count_subf.pop('pc',None)

        (all_httpf, all_httpf_names) = self._f_calc_subfeatures(ud[ud['act']==5], 'http', 'http_type', [1,2,3,4,5,6], \
                ['otherf','socnetf','cloudf','jobf','leakf','hackf'], ['url_len', 'url_depth', 'http_c_len', 'http_c_nwords'], http_count_subf)
        
        if mode == 'week':
            (workhourhttpf, workhourhttpf_names) = self._f_calc_subfeatures(ud[(ud['act']==5) & (ud['time'] ==1)], 'workhourhttp', 'http_type', [1,2,3,4,5,6], \
                    ['otherf','socnetf','cloudf','jobf','leakf','hackf'], ['url_len', 'url_depth', 'http_c_len', 'http_c_nwords'], http_count_subf)
            (afterhourhttpf, afterhourhttpf_names) = self._f_calc_subfeatures(ud[(ud['act']==5) & (ud['time'] ==2)], 'afterhourhttp', 'http_type', [1,2,3,4,5,6], \
                    ['otherf','socnetf','cloudf','jobf','leakf','hackf'], ['url_len', 'url_depth', 'http_c_len', 'http_c_nwords'], http_count_subf)
            (weekendhttpf, weekendhttpf_names) = self._f_calc_subfeatures(ud[(ud['act']==5) & (ud['time'] >=3)], 'weekendhttp', 'http_type', [1,2,3,4,5,6], \
                    ['otherf','socnetf','cloudf','jobf','leakf','hackf'], ['url_len', 'url_depth', 'http_c_len', 'http_c_nwords'], http_count_subf)
        elif mode == 'day':
            (workhourhttpf, workhourhttpf_names) = self._f_calc_subfeatures(ud[(ud['act']==5) & ((ud['time'] ==1) | (ud['time'] ==3))], 'workhourhttp', 'http_type', [1,2,3,4,5,6], \
                    ['otherf','socnetf','cloudf','jobf','leakf','hackf'], ['url_len', 'url_depth', 'http_c_len', 'http_c_nwords'], http_count_subf)
            (afterhourhttpf, afterhourhttpf_names) = self._f_calc_subfeatures(ud[(ud['act']==5) & ((ud['time'] ==2) | (ud['time'] ==4))], 'afterhourhttp', 'http_type', [1,2,3,4,5,6], \
                    ['otherf','socnetf','cloudf','jobf','leakf','hackf'], ['url_len', 'url_depth', 'http_c_len', 'http_c_nwords'], http_count_subf)
    
        numActs = all_f[0]

        if mode == 'week':        
            features_tmp =  all_f + workhourf + afterhourf + weekendf +\
                            all_logonf + workhourlogonf + afterhourlogonf + weekendlogonf +\
                            all_devicef + workhourdevicef + afterhourdevicef + weekenddevicef +\
                            all_filef + workhourfilef + afterhourfilef + weekendfilef + \
                            all_emailf + workhouremailf + afterhouremailf + weekendemailf + all_httpf + workhourhttpf + afterhourhttpf + weekendhttpf
            fnames_tmp = all_f_names + workhourf_names + afterhourf_names + weekendf_names +\
                        all_logonf_names + workhourlogonf_names + afterhourlogonf_names + weekendlogonf_names +\
                        all_devicef_names + workhourdevicef_names + afterhourdevicef_names + weekenddevicef_names +\
                        all_filef_names + workhourfilef_names + afterhourfilef_names + weekendfilef_names + \
                        all_emailf_names + workhouremailf_names + afterhouremailf_names + weekendemailf_names + all_httpf_names + workhourhttpf_names + afterhourhttpf_names + weekendhttpf_names
        elif mode == 'day':
            features_tmp = all_f + workhourf + afterhourf +\
                            all_logonf + workhourlogonf + afterhourlogonf +\
                            all_devicef + workhourdevicef + afterhourdevicef + \
                            all_filef + workhourfilef + afterhourfilef + \
                            all_emailf + workhouremailf + afterhouremailf + all_httpf + workhourhttpf + afterhourhttpf
            fnames_tmp = all_f_names + workhourf_names + afterhourf_names +\
                        all_logonf_names + workhourlogonf_names + afterhourlogonf_names +\
                        all_devicef_names + workhourdevicef_names + afterhourdevicef_names +\
                        all_filef_names + workhourfilef_names + afterhourfilef_names + \
                        all_emailf_names + workhouremailf_names + afterhouremailf_names + all_httpf_names + workhourhttpf_names + afterhourhttpf_names
        elif mode == 'session':
            features_tmp = all_f + all_logonf + all_devicef + all_filef + all_emailf + all_httpf
            fnames_tmp = all_f_names + all_logonf_names + all_devicef_names + all_filef_names + all_emailf_names + all_httpf_names
        
        return [numActs, is_weekend, features_tmp, fnames_tmp]

    def _f_calc_subfeatures(self, ud, fname, filter_col, filter_vals, filter_names, sub_features, countonly_subfeatures):
        [n, stats, fnames] = self._f_stats_calc(ud, fname,sub_features, countonly_subfeatures)
        allf = [n] + stats
        allf_names = ['n_'+fname] + fnames
        for i in range(len(filter_vals)):
            [n_sf, sf_stats, sf_fnames] = self._f_stats_calc(ud[ud[filter_col]==filter_vals[i]], filter_names[i], sub_features, countonly_subfeatures)
            allf += [n_sf] + sf_stats
            allf_names += [fname+'_n_'+filter_names[i]] + [fname + '_' + x for x in sf_fnames]
        return (allf, allf_names)

    def _f_stats_calc(self, ud, fn, stats_f, countonly_f = {}, get_stats = False):
        f_count = len(ud)
        r = []
        f_names = []
        
        for f in stats_f:
            inp = ud[f].values
            if get_stats:
                if f_count > 0:
                    r += [np.min(inp), np.max(inp), np.median(inp), np.mean(inp), np.std(inp)]
                else: r += [0, 0, 0, 0, 0]
                f_names += [fn+'_min_'+f, fn+'_max_'+f, fn+'_med_'+f, fn+'_mean_'+f, fn+'_std_'+f]
            else:
                if f_count > 0: r += [np.mean(inp)]
                else: r += [0]
                f_names += [fn+'_mean_'+f]
            
        for f in countonly_f:
            for v in countonly_f[f]:
                r += [sum(ud[f].values == v)]
                f_names += [fn+'_n-'+f+str(v)]
        return (f_count, r, f_names)
    
