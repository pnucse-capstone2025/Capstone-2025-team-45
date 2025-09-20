import os
import sys
import time
import re
import pandas as pd
from tqdm import tqdm
from joblib import Parallel, delayed

from util import combine_by_timerange_pandas, get_mal_userdata, process_week_num



def main():
    """
    feature_extraction.py와 util.py의 전처리 로직을 사용하여,
    통계 집계 직전 단계의 숫자 피처 데이터를 생성하고,
    이를 'data/merge4.csv' 파일로 통합하여 저장합니다.
    """
    # --- 1. feature_extraction.py의 초기 설정 가져오기 ---
    dname = os.getcwd().split('/')[-1]
    if dname not in ['r4.1', 'r4.2', 'r6.2', 'r6.1', 'r5.1', 'r5.2']:
        raise Exception('이 스크립트는 r4.2와 같은 CERT 데이터 폴더 내에서 실행되어야 합니다.')
    
    numCores = 12
    if len(sys.argv) > 1:
        numCores = int(sys.argv[1])
    
    numWeek = 73 if dname in ['r4.1', 'r4.2'] else 75
    weekRange = range(numWeek)
    
    print(f"데이터셋 '{dname}'에 대한 merge4.csv 생성을 시작합니다.")
    print(f"사용할 코어 수: {numCores}")
    st = time.time()

    # --- 2. feature_extraction.py의 Step 1, 2, 3 실행 ---
    
    # Step 1: 원본 로그를 주(week) 단위로 통합하여 DataByWeek 폴더에 저장
    print("\n[Step 1] 주 단위 로그 통합 시작...")
    if len(os.listdir("DataByWeek")) >= numWeek:
        print("... DataByWeek 파일이 이미 존재하여 건너뜁니다.")
    else:
        combine_by_timerange_pandas(dname)
    print(f"...완료. 소요 시간: {(time.time()-st)/60:.2f} 분")
    st = time.time()

    # Step 2: LDAP 및 정답 데이터를 읽어 사용자 정보(users) 데이터프레임 생성
    print("\n[Step 2] 사용자 정보(LDAP) 및 정답 데이터 로딩...")
    users = get_mal_userdata(dname)
    print("...완료.")

    # Step 3: 주 단위 로그를 숫자 피처로 변환하여 NumDataByWeek 폴더에 저장
    # (이 단계가 바로 통계 집계 직전의 데이터를 만드는 과정입니다)
    print("\n[Step 3] 로그를 숫자 피처로 변환 시작 (병렬 처리)...")
    
    # 3-1. NumDataByWeek 폴더 내에 이미 생성된 주차 파일을 먼저 확인합니다.
    out_dir = "NumDataByWeek"
    os.makedirs(out_dir, exist_ok=True)
    done_weeks = set()
    # 파일 이름 패턴 (예: "25_num.pickle")을 찾기 위한 정규표현식
    pat = re.compile(r"^(\d+)_num\.pickle$")
    for filename in os.listdir(out_dir):
        match = pat.match(filename)
        if match:
            # 파일 이름에서 주차(week) 번호를 추출하여 'done_weeks' 집합에 추가
            done_weeks.add(int(match.group(1)))

    # 3-2. 전체 주차 범위에서, 아직 처리되지 않은 주차만 'pending_weeks' 리스트로 만듭니다.
    all_weeks = range(numWeek)
    pending_weeks = [w for w in all_weeks if w not in done_weeks]

    print(f"  - 전체 주차: {len(all_weeks)}개 | 이미 처리된 주차: {len(done_weeks)}개 | 이번에 처리할 주차: {len(pending_weeks)}개")
    
    st = time.time()

    # 3-3. 처리할 주차('pending_weeks')가 있는 경우에만 Parallel 작업을 실행합니다.
    if pending_weeks:
        Parallel(n_jobs=numCores, verbose=10)(
            delayed(process_week_num)(w, users, data=dname) for w in pending_weeks
        )
    else:
        print("  - 모든 주차 파일이 이미 존재하므로 생성을 건너뜁니다.")

    print(f"...완료. 소요 시간: {(time.time()-st)/60:.2f} 분")
    st = time.time()
    
    
    # --- 4. merge4.csv 생성을 위한 새로운 Step 4 ---
    

    print("\n[Step 4] 변환된 모든 숫자 피처를 merge4.csv로 통합 시작 (메모리 최적화 모드)...")
    
    num_data_folder = "NumDataByWeek/"
    output_folder = 'data'
    output_path = os.path.join(output_folder, 'merge4.csv')
    os.makedirs(output_folder, exist_ok=True)

    # 4-1. 첫 번째 파일(0_num.pickle)을 찾아 먼저 저장합니다. (헤더 포함)
    first_file_path = os.path.join(num_data_folder, "0_num.pickle")
    if not os.path.exists(first_file_path):
        print(f"!!! 에러: 시작 파일({first_file_path})을 찾을 수 없습니다.")
        return

    print(f" - 첫 번째 파일 '{first_file_path}' 처리 중...")
    df_first = pd.read_pickle(first_file_path)
    # mode='w'는 새로 쓰기(write)를 의미합니다.
    df_first.to_csv(output_path, index=False, mode='w', header=True)
    
    # 4-2. 나머지 파일들을 순서대로 읽어서 기존 CSV에 이어붙입니다.
    for w in tqdm(range(1, numWeek), desc="이어붙이기 작업 중"):
        pickle_path = os.path.join(num_data_folder, f"{w}_num.pickle")
        if os.path.exists(pickle_path):
            week_df = pd.read_pickle(pickle_path)
            # mode='a'는 이어붙이기(append)를, header=False는 헤더 제외를 의미합니다.
            week_df.to_csv(output_path, index=False, mode='a', header=False)

    print(f"...완료. 소요 시간: {(time.time()-st)/60:.2f} 분")
    print(f"\n✅ 최종 파일 '{output_path}' 생성이 완료되었습니다!")


if __name__ == '__main__':
    main()