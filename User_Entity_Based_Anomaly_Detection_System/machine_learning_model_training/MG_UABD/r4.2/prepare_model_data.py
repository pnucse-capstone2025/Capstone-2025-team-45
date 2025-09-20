import pandas as pd
import os
from tqdm import tqdm

# --- 설정 ---
# 원본 파일
SOURCE_MERGE4_FILE = 'data/merge4.csv'

# 생성될 폴더 경로
USERID_FOLDER = 'data/userID'
WEEKDATA_ID_FOLDER = 'data/weekData_ID'

# 메모리 관리를 위한 청크 사이즈 (한 번에 읽을 행의 수)
CHUNK_SIZE = 1_000_000

# 사용자 ID(숫자)를 원래의 문자열 ID로 변환하기 위해 util 함수 import
from util import get_mal_userdata


def main():
    """
    merge4.csv 파일을 읽어, model.py 훈련에 필요한 
    'data/userID/'와 'data/weekData_ID/' 폴더 및 파일들을 생성합니다.
    """
    # 1. 결과를 저장할 폴더들을 미리 생성합니다.
    print("결과를 저장할 폴더를 생성합니다...")
    os.makedirs(USERID_FOLDER, exist_ok=True)
    os.makedirs(WEEKDATA_ID_FOLDER, exist_ok=True)
    print("...완료.")

    # 2. 사용자 ID(숫자) -> 사용자 이름(문자열) 매핑을 생성합니다.
    print("사용자 ID-이름 매핑을 생성합니다...")
    dname = os.getcwd().split('/')[-1]
    users_df = get_mal_userdata(dname)
    # users_df의 인덱스가 사용자 이름(예: DTAA-USER-0001)입니다.
    # enumerate를 통해 생성된 숫자 ID(i)와 인덱스(idx)를 매핑합니다.
    user_id_map = {i: idx for i, idx in enumerate(users_df.index)}
    print("...완료.")
    
    # 3. 각 파일에 헤더를 한 번만 쓰기 위한 기록용 집합(set)을 초기화합니다.
    written_user_files = set()
    written_week_user_files = set()

    print(f"'{SOURCE_MERGE4_FILE}' 파일을 청크 단위로 처리하여 데이터 분할을 시작합니다...")
    
    # 4. merge4.csv 파일을 청크 단위로 순회합니다.
    # tqdm을 사용하여 전체 진행 상황을 시각적으로 보여줍니다.
    total_size = os.path.getsize(SOURCE_MERGE4_FILE)
    with tqdm(total=total_size, unit='B', unit_scale=True, desc="merge4.csv 처리 중") as pbar:
        for chunk in pd.read_csv(SOURCE_MERGE4_FILE, chunksize=CHUNK_SIZE):
            
            # --- 4-1. data/userID/ 폴더 데이터 생성 ---
            # 현재 청크에 있는 모든 고유한 사용자 ID에 대해 반복
            for user_id_numeric in chunk['user'].unique():
                user_name = user_id_map.get(user_id_numeric)
                if not user_name:
                    continue # 매핑에 없는 사용자는 건너뜀
                
                # 해당 사용자의 데이터만 필터링
                user_data = chunk[chunk['user'] == user_id_numeric]
                user_file_path = os.path.join(USERID_FOLDER, f"{user_name}.csv")
                
                # 이 파일에 헤더를 쓴 적이 있는지 확인
                write_header = user_name not in written_user_files
                # mode='a'(append)로 파일에 데이터를 추가합니다.
                user_data.to_csv(user_file_path, mode='a', header=write_header, index=False)
                # 헤더를 썼다고 기록합니다.
                written_user_files.add(user_name)

            # --- 4-2. data/weekData_ID/ 폴더 데이터 생성 ---
            # 'week' 컬럼이 없다면 'day' 컬럼으로 생성합니다.
            if 'week' not in chunk.columns:
                chunk['week'] = chunk['day'] // 7
            
            # 현재 청크에 있는 모든 고유한 주차(week)에 대해 반복
            for week in chunk['week'].unique():
                week_folder = os.path.join(WEEKDATA_ID_FOLDER, str(week))
                os.makedirs(week_folder, exist_ok=True) # 주차별 폴더 생성
                
                week_data = chunk[chunk['week'] == week]
                
                # 해당 주차에 활동한 모든 고유한 사용자에 대해 반복
                for user_id_numeric in week_data['user'].unique():
                    user_name = user_id_map.get(user_id_numeric)
                    if not user_name:
                        continue
                    
                    user_week_data = week_data[week_data['user'] == user_id_numeric]
                    user_week_file_path = os.path.join(week_folder, f"{user_name}.csv")
                    
                    # 이 주차-사용자 조합의 파일에 헤더를 쓴 적이 있는지 확인
                    week_user_key = (week, user_name)
                    write_header = week_user_key not in written_week_user_files
                    # mode='a'(append)로 데이터를 추가합니다.
                    user_week_data.to_csv(user_week_file_path, mode='a', header=write_header, index=False)
                    # 헤더를 썼다고 기록합니다.
                    written_week_user_files.add(week_user_key)
            
            # 진행 바 업데이트
            pbar.update(chunk.memory_usage(deep=True).sum())
            
    print("\n✅ 모든 데이터 분할이 완료되었습니다!")

if __name__ == '__main__':
    main()