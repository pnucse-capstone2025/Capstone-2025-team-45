
import os 
import pandas as pd
import pickle
from pathlib import Path
from typing import Annotated
from sqlalchemy.orm import Session
from sqlalchemy.inspection import inspect as sqla_inspect
from fastapi import Depends
from datetime import datetime   
from model.database import engine, get_db, Base, SessionLocal

from .log_loader import LogLoader
from .log_merger import LogMerger
from .numeric_encoder import NumericEncoder
from .feature_aggregator import FeatureAggregator
class Preprocessor:
    """
    주 단위 로그 데이터 전처리 오케스트레이션 클래스
    """
    def __init__(self, engine: engine, db: Session, start_date: datetime, end_date: datetime):
        self.engine = engine
        self.db = db
        self.start_date = start_date
        self.end_date = end_date

    def run(self):
        # 1. 데이터 베이스로부터 특정 기간에 해당하는 로그 데이터 로드 
        print("# 1. 데이터 로드 중...")
        log_loader = LogLoader(self.engine, self.db, self.start_date, self.end_date)
        df = log_loader.run()
        print(df.head(3))
        if  df.empty:
            print("로그 데이터가 비어 있습니다.")
            return None

        # 2. 서로 다른 타입의 행동 로그 데이터를 병합하여 표준 포맷으로 변환
        print('# 2. 행동 데이터 병합 중...')
        log_merger = LogMerger(self.engine, self.db, df)
        merged_df = log_merger.run()
        print("병합된 표준 포맷 로그 데이터:")
        print(merged_df.head(10))

        # 3. 기본적인 사용자 정보가 저장된 파일 로드 (주사용 PC 등)
        print("# 3. 사용자 정보 로드 중...")
        user_df = pd.read_pickle( Path(__file__).resolve().parent /"user_df.pkl" )
        print("기본 사용자 정보:")
        print(user_df.head(10))

        # 4. 모델 학습에 적합한 숫자 데이터로 변환
        print("# 4. 숫자 데이터 변환 중...")
        numeric_encoder = NumericEncoder(user_df, merged_df)
        numeric_data = numeric_encoder.run()
        print("변환된 숫자 데이터:")
        print(numeric_data.head(10))    

        # 5. 특정 기간 동안의 변환한 숫자 데이터를 ./cache 폴더에 저장 
        print("# 5. 숫자 데이터 저장 중...")
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        cache_dir = os.path.join(BASE_DIR, "cache")
        os.makedirs(cache_dir, exist_ok=True)
        save_path = os.path.join(cache_dir, "numeric_data.pkl")
        numeric_data.to_pickle(save_path)

        print("전처리된 act 타입 별 숫자 데이터:")
        for a in range(1, 8):
            row = numeric_data[numeric_data["act"] == a].head(1)
            print(f"act={a}\n", row, "\n")

        # 6. 사용자 단위로 집계한 피처 테이블 생성
        print("# 6. 피처 테이블 생성 중...")
        feature_aggregator = FeatureAggregator(user_df, numeric_data)
        user_dict, feature_data = feature_aggregator.run()
        print("# 6. 피처 테이블 생성 완료")
        print(feature_data.head(10))

        # 7. 피처 테이블 및 사용자 사전 파일로 저장 
        pd.to_pickle(feature_data,  Path(__file__).resolve().parent/"result" / "start_date_{}_end_date_{}.pkl".format(self.start_date, self.end_date))
        pd.to_pickle(user_dict,  Path(__file__).resolve().parent/"result" / "user_dict_{}_{}.pkl".format(self.start_date, self.end_date))
        
        return user_dict, feature_data
    
# preprocessor = Preprocessor(engine, SessionLocal(), datetime(2010,10,11), datetime(2010,10,18))
# pd.set_option('display.max_columns', None)  
# user_dict, result = preprocessor.run()
# print(len(user_dict), len(result))