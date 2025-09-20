import json
import os 
import joblib
import pandas as pd
import pickle
from pathlib import Path
from typing import Annotated
from sqlalchemy.orm import Session
from sqlalchemy.inspection import inspect as sqla_inspect
from datetime import datetime   
from model.database import engine, SessionLocal
import numpy as np
from uuid import UUID

from services.feature_extraction.preprocessor import Preprocessor
from model.anomaly_detection_history.crud import create_anomaly_detection_history

MODEL_PATH = Path(__file__).resolve().parent /"models" / "rf_insider_smote_pipeline_week.joblib"

class AnomalyDetector: 
    """
    기간을 입력으로 받고, 해당 기간 동안의 악성 사용자를 탐지해 user_id : {예측 클래스, 악성 확률, 클래스별 확률} 딕셔너리로 반환
    """
    def __init__(self, engine: engine, db: Session, start_date: datetime, end_date: datetime, organization_id: UUID):
        self.engine = engine
        self.db = db
        self.start_date = start_date
        self.end_date = end_date
        self.organization_id = organization_id

    def run(self):
        # 전처리 시작
        user_dict, preprocessed_data = self._get_preprocessed_data()

        # DATA_PATH =Path(__file__).resolve().parent.parent / "feature_extraction" / "result" / "user_dict_{}_{}.pkl".format(self.start_date, self.end_date)
        # user_dict = pd.read_pickle(DATA_PATH)
        # DATA_PATH =Path(__file__).resolve().parent.parent / "feature_extraction" / "result" / "start_date_{}_end_date_{}.pkl".format(self.start_date, self.end_date)
        # preprocessed_data = pd.read_pickle(DATA_PATH)

        pipe = joblib.load(MODEL_PATH)

        user_idx = preprocessed_data["user"].tolist() 
        X_inf = preprocessed_data.drop(columns=["user"], errors="ignore")

        # 1) 예측/확률
        y_pred = pipe.predict(X_inf)
        proba = pipe.predict_proba(X_inf)              
        classes = pipe.named_steps["rf"].classes_      

        # 편의 인덱스들
        import numpy as np
        top_idx = proba.argmax(axis=1)
        top_prob = proba[np.arange(len(top_idx)), top_idx]

        # "정상(0)" 확률과 "이상 전체" 확률
        zero_pos = int(np.where(classes == 0)[0][0])  
        p_normal = proba[:, zero_pos]
        p_anomaly = 1.0 - p_normal

        # 2) 결과 구성 (라벨≠0 이고, 이상확률이 임계치 이상인 경우만 추림)
        anomaly_users = {}
        for i, u in enumerate(user_idx):
            uid = self._resolve_uid(user_dict, u)
            if y_pred[i] != 0 :
                anomaly_users[uid] = {
                    "pred_class": int(y_pred[i]),
                    "p_top": float(top_prob[i]),
                    "p_anomaly": float(p_anomaly[i]),
                    "proba": {int(c): float(proba[i, j]) for j, c in enumerate(classes)}
                }
            # 디버깅용 로그
            print(f"user id: {uid}, pred={y_pred[i]}, p_anom={p_anomaly[i]:.3f}, p_top={top_prob[i]:.3f}")

        # DB에 결과 저장
        try:
            resultjson = self._json_dumps(anomaly_users)
            create_anomaly_detection_history(self.db, self.organization_id, resultjson, self.start_date, self.end_date)
        except Exception as e:
            print(f"Error saving to DB: {e}")
        return anomaly_users
    
    def _resolve_uid(self,user_dict, idx):
        v = user_dict.get(idx)
        return v

    def _get_preprocessed_data(self):
        preprocessor = Preprocessor(self.engine, self.db, self.start_date, self.end_date)
        user_dict, preprocessed_data = preprocessor.run()
        return user_dict, preprocessed_data
    
    def _json_dumps(self, obj) -> str:
        def _default(o):
            if isinstance(o, (np.integer, np.int64)):
                return int(o)
            if isinstance(o, (np.floating, np.float32)):
                return float(o)
            if isinstance(o, (np.ndarray,)): return o.tolist()
        return json.dumps(obj, default=_default)

# anomalydetector = AnomalyDetector(engine, SessionLocal(), datetime(2010,10,11), datetime(2010,10,18))
# result = anomalydetector.run()
# print(result)