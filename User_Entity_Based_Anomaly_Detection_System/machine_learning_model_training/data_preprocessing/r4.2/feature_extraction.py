
import os, re
import sys 
import time 
from util import combine_by_timerange_pandas, get_mal_userdata, process_week_num, get_u_features_dicts, to_csv
import pandas as pd
from joblib import Parallel, delayed
import pickle

dname = os.getcwd().split('/')[-1]
print (f"Current directory name: {dname}")
if dname not in ['r4.1','r4.2','r6.2','r6.1','r5.1','r5.2']:
        raise Exception('Please put this script in and run it from a CERT data folder (e.g. r4.2)')

try: 
    [os.mkdir(x) for x in ["tmp", "ExtractedData", "DataByWeek", "NumDataByWeek"]]
except FileExistsError:
    pass

subsession_mode = {'nact':[25, 50], 'time':[120, 240]}

# 전처리 시 사용할 CPU 코어 수 설정 
numCores = 12
arguments = len(sys.argv) - 1
if arguments > 0:
        numCores = int(sys.argv[1])
print(f"사용할 코어 수: {numCores}")

# 주차 수 설정
numWeek = 73 if dname in ['r4.1','r4.2'] else 75
st = time.time()
print(f"시작 시간: {st}")

# Step 1: 데이터를 주차 단위로 분할 해, DataByWeek 폴더에 저장
try:
        existing_files = [
                f for f in os.listdir("DataByWeek") if f.endswith(".pickle")
        ]
        if len(existing_files) >= numWeek:
                print(f"Step 1 - 이미 완료됨 (주차 파일 {len(existing_files)}개 존재). 건너뜀.")
        else:
                combine_by_timerange_pandas(dname)
                print(f"Step 1 - Separate data by week - done. Time (mins): {(time.time()-st)/60:.2f}")
                st = time.time()
except Exception as e:
        print(f"Error occurred in Step 1: {e}")

# Step 2: 악성 사용자 목록을 가져와, 각 사용자별로 악성 시나리오 참여 여부/기간/관련 행위 ID/PC/ 공유 PC 정보 등을 수집
# 'users' 라는 단일 데이터 프레임 변수에 저장 
try:
    users = get_mal_userdata(dname)
    print(f"Step 2 - Get user list - done. Time (mins): {(time.time()-st)/60:.2f}")
    st = time.time()
except Exception as e:
       print(f"Error occurred in Step 2: {e}")

print("악성 사용자 및 정보")
# 악성 사용자만 필터링
malicious_users = users[users['malscene'] > 0]

# 원하는 컬럼만 선택
result = malicious_users[['mstart', 'mend', 'malacts', 'malscene']]

print(result)

# Step 3: 주차별 행동 데이터들을 숫자 데이터로 변환해, NumDataByWeek 폴더에 저장
print("Step 3 - Convert each action to numerical data - start")

# NumDataByWeek 폴더 내 이미 생성된 주차 파일 식별
out_dir = "NumDataByWeek"
os.makedirs(out_dir, exist_ok=True)

done = set()
pat = re.compile(r"^(\d+)_num\.pickle$")
for fn in os.listdir(out_dir):
    m = pat.match(fn)
    if m:
        done.add(int(m.group(1)))

# 이번에 처리할 주차만 선택
all_weeks = list(range(numWeek))
pending_weeks = [w for w in all_weeks if w not in done]

print(f"- total weeks: {len(all_weeks)} "
      f"| already done: {len(done)} "
      f"| to run: {len(pending_weeks)}")

st = time.time()

if pending_weeks:
    Parallel(n_jobs=numCores, verbose=10)(
        delayed(process_week_num)(w, users, data=dname) for w in pending_weeks
    )
else:
    print("모든 주차 파일이 이미 존재합니다. (생성 건너뜀)")

print(f"Step 3 - Convert each action to numerical data - done. "
      f"Time (mins): {(time.time()-st)/60:.2f}")

st = time.time()

#Step 4: csv 추출 
#원본: for mode in ['week','day','session'], weak 데이터 추출이 끝나서 day 만 남음
for mode in ['day']:
        weekRange = list(range(0, numWeek)) if mode in ['day', 'session'] else list(range(1, numWeek))
        # ul: user list, uf: 조직 속성 값, list_uf: 사용자 조직 속성 리스트 
        (ul, uf_dict, list_uf) = get_u_features_dicts(users, data= dname)

        Parallel(n_jobs=numCores, verbose = 10)(delayed(to_csv)(i, mode, dname, ul, uf_dict, list_uf, subsession_mode)
                                   for i in weekRange)

        all_csv = open('ExtractedData/'+mode+dname+'.csv','a')
        
        towrite = pd.read_pickle("tmp/"+str(weekRange[0]) + mode+".pickle")
        towrite.to_csv(all_csv,header=True, index = False)
        for w in weekRange[1:]:
            towrite = pd.read_pickle("tmp/"+str(w) + mode+".pickle")        
            towrite.to_csv(all_csv,header=False, index = False)
        
        if mode == 'session' and len(subsession_mode) > 0:
            for k1 in subsession_mode:
                for k2 in subsession_mode[k1]:
                    all_csv = open('ExtractedData/'+mode+ k1 + str(k2) + dname+'.csv','a')
                    towrite = pd.read_pickle('tmp/'+str(weekRange[0]) + mode + k1 + str(k2)+".pickle")
                    towrite.to_csv(all_csv,header=True, index = False)
                    for w in weekRange[1:]:
                        towrite = pd.read_pickle('tmp/'+str(w) + mode+ k1 + str(k2)+".pickle")        
                        towrite.to_csv(all_csv,header=False, index = False)
                    
        print(f'Extracted {mode} data. Time (mins): {(time.time()-st)/60:.2f}')
        st = time.time()

# 전처리를 처음부터 수행하려면 다음 명령어 실행해서 초기화
# [os.system(f"rm -r {x}") for x in ["tmp", "DataByWeek", "NumDataByWeek"]]   