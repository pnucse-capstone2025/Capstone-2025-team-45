import os
import joblib
import numpy as np
import pandas as pd
from collections import Counter

from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.metrics import classification_report, confusion_matrix, balanced_accuracy_score
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier

from imblearn.pipeline import Pipeline
from imblearn.over_sampling import RandomOverSampler, SMOTE
from threadpoolctl import threadpool_limits


# step 1. 데이터 로드
print ("대상 데이터 셋을 선택해 주세요.")
print("day: 1")
print("week: 2")
selected_dataset = input("")
if selected_dataset == "2":
    CSV_PATH = "./dataset/weekr4.2.csv"
elif selected_dataset == "1":
    CSV_PATH = "./dataset/dayr4.2.csv"
else:
    print("잘못된 선택입니다. 'day' 또는 'week'를 입력해주세요.")
    os._exit(1)

TARGET = "insider"

df  = pd.read_csv(CSV_PATH)
if selected_dataset == "1":
    drop_cols = ['starttime', 'endtime', 'user', 'day', 'role', 'b_unit', 'f_unit', 'dept', 'team', TARGET]
else:
    drop_cols = ['starttime', 'endtime', 'user', 'week', 'role', 'b_unit', 'f_unit', 'dept', 'team', TARGET]
    
X = df.drop(columns=drop_cols)
y = df[TARGET].astype(int)

print("분포: ", y.value_counts().sort_index().to_dict())

# step 2. 데이터 분할
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print("Train 분포:", y_train.value_counts().sort_index().to_dict())
print("Test  분포:", y_test.value_counts().sort_index().to_dict())

# step 3. SMOTE 기반 오버샘플링을 위해 데이터 정규화 
num_cols = X_train.columns.tolist()
preprocess = ColumnTransformer(
    transformers=[("num", StandardScaler(with_mean=True, with_std=True), num_cols)],
    remainder="drop"
)

# step 4. SMOTE 오버샘플링

# === 오버샘플링 전략 설정 (예전 의도 반영) ===
# - "다수 클래스의 10%"까지 소수 클래스 늘리기
# - 소수 클래스가 너무 적으면 SMOTE 전에 RandomOverSampler로 씨앗 확보
cnt = Counter(y_train)
maj = max(cnt, key=cnt.get)
maj_n = cnt[maj]

# 1) 씨앗 확보(= SMOTE 전에 최소 개수까지 복제)
#    예전 코드의 “5개 미만이면 RandomOverSampler” 의도를 일반화
seed_min = 6  # k=5를 쓸 수 있게 최소 6개는 확보(필요시 조정)
seed_targets = {
    c: max(n, seed_min)
    for c, n in cnt.items() if c != maj and n < seed_min
}
# seed_targets가 비어있으면 RandomOverSampler는 건너뛰어도 됨

# 2) SMOTE 목표 개수: 다수의 10% 수준(예전 sampling_strategy=0.1 의도)
target_per_class = max(1, int(maj_n * 0.10))
# 이미 target 이상인 클래스는 생략(불필요한 증강 방지)
smote_targets = {
    c: target_per_class
    for c, n in cnt.items() if c != maj and n < target_per_class
}

# 3) k_neighbors 가드: 최소 클래스가 seed_min 이상이므로 3~5 권장
#   (혹시 전처리/필터로 더 작아질 위험까지 커버하려면 아래 계산으로 보수적 설정)
minor_counts_after_seed = {c: (seed_targets.get(c, cnt[c])) for c in cnt if c != maj}
min_minor = min(minor_counts_after_seed.values()) if minor_counts_after_seed else min(cnt[c] for c in cnt if c != maj)
k_neighbors = max(1, min(5, min_minor - 1))

# step 4. 오버샘플러 구성
# 순서: 스케일링 -> (필요시) RandomOverSampler -> SMOTE -> RF
samplers = []
if len(seed_targets) > 0:
    samplers.append(("over_seed", RandomOverSampler(sampling_strategy=seed_targets, random_state=42)))

# smote_targets가 비었으면 SMOTE는 스킵(증강 불필요)
if len(smote_targets) > 0:
    samplers.append(("smote", SMOTE(sampling_strategy=smote_targets, k_neighbors=k_neighbors,
                                    random_state=42, n_jobs=-1)))

# step 5. 랜덤 포레스트 모델 생성
rf = RandomForestClassifier(
    n_estimators=400,
    max_depth=16,
    min_samples_leaf=2,
    max_features="sqrt",
    n_jobs=-1,
    random_state=42,
    # class_weight="balanced"  # 필요하면 추가 (SMOTE와 병행 시 과보정될 수 있어 처음엔 off 권장)
)

steps = [("scaler", preprocess)] + samplers + [("rf", rf)]
pipe = Pipeline(steps=steps, verbose=False)

# step 6. 학습 
with threadpool_limits(limits=1):  # 중첩 스레드 폭주 방지(체감 속도↑)
    pipe.fit(X_train, y_train)

# step 7. 예측 및 평가
y_pred = pipe.predict(X_test)
print("\n== Confusion Matrix ==")
print(confusion_matrix(y_test, y_pred))
print("\n== Classification Report ==")
print(classification_report(y_test, y_pred, digits=4))
print("Balanced Accuracy:", f"{balanced_accuracy_score(y_test, y_pred):.4f}")

# step 8. 모델 저장
MODEL_PATH = "rf_insider_smote_pipeline.joblib"
joblib.dump(pipe, MODEL_PATH, compress=3)
print(f"\nSaved model -> {MODEL_PATH}")

# step 9. 모델 로드 및 예측
pipe2 = joblib.load(MODEL_PATH)
sample_pred = pipe2.predict(X_test.iloc[:5])
print("\n샘플 예측(상위 5개):", sample_pred.tolist())