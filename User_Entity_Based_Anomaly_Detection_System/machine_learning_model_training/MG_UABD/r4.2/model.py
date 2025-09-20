import os
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix, accuracy_score, recall_score, f1_score, classification_report, precision_score

from sklearn.model_selection import KFold
from sklearn.model_selection import StratifiedKFold
from collections import Counter
import sys
import numpy as np
from tqdm import tqdm

from imblearn.under_sampling import RandomUnderSampler
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline
from imblearn.over_sampling import RandomOverSampler

DATA_FOLDER = 'data/'
MERGE4_FILE = os.path.join(DATA_FOLDER, 'merge4.csv')
USERID_FOLDER = os.path.join(DATA_FOLDER, 'userID')
WEEKDATA_ID_FOLDER = os.path.join(DATA_FOLDER, 'weekData_ID')
OUTPUT_FOLDER = 'partRedo/'
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


# 이어붙이기 방식을 위한 임시 파일
TEMP_TRAIN_FILE = 'temp_train_data.csv'
# --- 2. 초기 훈련 데이터 생성 ---
print("초기 훈련 데이터 생성을 시작합니다...")

# 이전에 생성된 임시 파일이 있다면, 그 파일이 온전하다는 가정 하에, 그대로 사용
if not os.path.exists(TEMP_TRAIN_FILE):
    chunk_size = 500_000  # 한 번에 50만 줄씩 읽기
    is_first_chunk = True # 헤더를 한 번만 쓰기 위한 플래그

    # tqdm을 사용하여 진행 상황을 표시
    with tqdm(desc="merge4.csv에서 훈련 데이터 추출 중") as pbar:
        for chunk in pd.read_csv(MERGE4_FILE, chunksize=chunk_size):
            chunk['week'] = chunk['day'] // 7
            
            filtered_chunk = chunk[chunk['week'] < 26]
            
            if not filtered_chunk.empty:
                if is_first_chunk:
                    # 첫 번째 조각은 헤더를 포함하여 새로 씁니다.
                    filtered_chunk.to_csv(TEMP_TRAIN_FILE, index=False, mode='w', header=True)
                    is_first_chunk = False
                else:
                    # 두 번째 조각부터는 헤더 없이 아래에 이어붙입니다.
                    filtered_chunk.to_csv(TEMP_TRAIN_FILE, index=False, mode='a', header=False)
            pbar.update(len(chunk))
            
    # 생성된 임시 훈련 데이터 파일을 최종적으로 train_data로 불러옵니다.
    if not os.path.exists(TEMP_TRAIN_FILE):
        raise ValueError("초기 훈련 데이터(26주차 미만)가 없어 임시 파일을 생성하지 못했습니다.")

    print("...임시 훈련 파일 생성 완료. 최종 데이터 로딩 중...")
else:
    print("...임시 훈련 파일이 이미 생성되어 있습니다.")


train_data_full = pd.read_csv(TEMP_TRAIN_FILE)
#os.remove(TEMP_TRAIN_FILE) # 임시 파일 삭제
print("...초기 훈련 데이터 로딩 완료.")


# 25주차까지의 훈련 데이터 train_data_full이 너무 커서, 전체의 30%만 무작위로 샘플링함
# 이 비율은 메모리 상황에 따라 0.2, 0.1 등으로 조절할 수 있다.
sample_fraction = 0.3
train_data = train_data_full.sample(frac=sample_fraction, random_state=42)
print(f"...초기 훈련 데이터 로딩 완료 (전체 {len(train_data_full)}개 중 {len(train_data)}개 샘플링).")



# merge4.csv 컬럼 구조에 맞게 제외할 컬럼 목록을 수정합니다.
# 'userID', 'mal'은 없으므로 제거하고, 'day', 'week'를 추가합니다.
removed_cols = ['actid', 'pcid', 'time_stamp', 'user', 'day', 'week', 'insider', 'mal_act']

# train_data의 실제 컬럼 목록을 기준으로 x_cols를 정의합니다.
x_cols = [i for i in train_data.columns if i not in removed_cols]


TARGET_COL = 'insider' # 우리가 예측할 목표(정답) 컬럼을 명확히 정의합니다.

xTrain = train_data[x_cols].values
# 'insider' 컬럼의 값이 0보다 크면 모두 1(악성)로 변환하여 이진(0, 1) 형태로 만듭니다.
yTrainBin = (train_data[TARGET_COL].values > 0).astype(int)


MODEL_PATH = 'random_forest_model3.pkl'
if os.path.exists(MODEL_PATH):
    # 파일이 있다면, 훈련 과정을 건너뛰고 바로 불러옵니다.
    print("이미 생성된 초기 모델 파일을 불러옵니다...")
    rf = joblib.load(MODEL_PATH)
else:
    print("초기 모델 파일을 새로 생성합니다....")
    rf = RandomForestClassifier(n_jobs=-1, random_state=42)
    rf.fit(xTrain, yTrainBin)
    joblib.dump(rf, MODEL_PATH)


trained_users = []
output_file = open('outputNew3.txt', mode = 'a',encoding='utf-8')

data=[]
columns = ['user', 'cm00', 'cm01', 'cm10', 'cm11', 'mal_user']
df2 = pd.DataFrame(columns=columns)
df0 = pd.DataFrame(columns=columns)
df1 = pd.DataFrame(columns=columns)
# Training by week
data_folder = "data/weekData_ID"
for week in range(26, 73):  # 26주차부터 72주차까지
    week_files = os.path.join(data_folder, str(week)) # 각 주차 폴더에 접근합니다.
    # 특정 주차 폴더의 모든 csv 파일 이름(사용자 이름) 리스트 
    files = [file for file in os.listdir(week_files) if file.endswith(".csv")]  
    for file in files:
        
        # coarse-grained anomaly detection
        file_path = os.path.join(week_files, file) 
        print("-------------------------------------------------------------------------",file=output_file)
        print("At",week,"week,user",file,"situation",file=output_file)
        test_data = pd.read_csv(file_path)
        xTest = test_data[x_cols].values
        yTestBin = (test_data[TARGET_COL].values > 0).astype(int) # 타겟을 insider로 변경 및 이진화

        cm=confusion_matrix(yTestBin,rf.predict(xTest))
        # print(cm, file=output_file)

        
        # fine-grained anomaly detection
        if((len(cm)>1 and cm[0][1]>0) or (len(cm)>1 and cm[1][1]>0) or (len(cm)>1 and cm[1][0]>0)) :
            print(cm[0][1],"--------------",cm[1][1],file=output_file)
            print("!!!!!!!!!!!!!!!!!!!!",file=output_file)
            print("at",week,"week, user",file,"abnormal",file=output_file)

            if(file not in trained_users):
                print("at",week,"week, user",file,"abnormal, and this user haven't been used",file=output_file)
                trained_users.append(file)

                fold="data/userID"
                data=pd.read_csv(os.path.join(fold, file))

                data_shuffled = data.sample(frac=1, random_state=42).reset_index(drop=True)
                train_ratio = 0.8
                train_size = int(train_ratio * len(data_shuffled))
                trainData = data_shuffled.iloc[:train_size]
                testData = data_shuffled.iloc[train_size:int(len(data_shuffled))]
                # print(len(trainData))
                # print(len(testData))

                
                
                # 복잡한 removed, removedX 대신 이미 정의된 x_cols와 TARGET_COL을 일관되게 사용합니다.
                X = trainData[x_cols]
                y = (trainData[TARGET_COL].values > 0).astype(int) # 타겟을 insider로 변경 및 이진화
                

                if(len(np.unique(y)) < 2): # y에 클래스가 1개(0 또는 1)만 있는지 확인
                    print('without oversampling',file=output_file)
                    overData_X = X
                    overData_y = y
                else:
                    # y에서 악성(1) 샘플의 개수를 셉니다.
                    if(np.sum(y == 1) < 5):
                        over = RandomOverSampler(random_state=0, sampling_strategy=0.5)
                    else:
                        k = min(4, np.sum(y == 1) - 1)
                        over = SMOTE(sampling_strategy=0.5, k_neighbors=k, random_state=42)
                        
                    overData_X, overData_y = over.fit_resample(X, y)
                    print('oversampling:{}'.format(Counter(overData_y)), file=output_file)
                


                run = 1
                np.random.seed(run)
                x_Train = overData_X
                y_TrainBin = overData_y # 이미 0과 1로 되어 있으므로 추가 변환 불필요

                rf = RandomForestClassifier(n_jobs=-1)
                rf.fit(x_Train, y_TrainBin)

                x_Test = testData[x_cols].values
                y_TestBin = (testData[TARGET_COL].values > 0).astype(int)
                    
                # results
                confusion = confusion_matrix(y_TestBin, rf.predict(x_Test))
                accuracy = accuracy_score(y_TestBin, rf.predict(x_Test))
                recall = recall_score(y_TestBin, rf.predict(x_Test))
                f1 = f1_score(y_TestBin, rf.predict(x_Test))
                if len(confusion)==1:
                    mal_user=0
                    # print(confusion)
                elif confusion[1][0]==0 and confusion[1][1] == 0:
                    mal_user=0
                    # print(confusion)
                else:
                    mal_user=1
                    # print(confusion)

                if len(confusion) == 1:
                    row = {'user': file, 'cm00': confusion[0][0], 'cm01': 0, 'cm10': 0, 'cm11': 0, 'mal_user': mal_user}
                    df2.loc[file] = row
                    df0.loc[file] = row
                else:
                    row = {'user': file, 'cm00': confusion[0][0], 'cm01': confusion[0][1], 'cm10': confusion[1][0], 'cm11': confusion[1][1], 'mal_user': mal_user}
                    df2.loc[file] = row
                    if mal_user == 0:
                        df0.loc[file] = row
                    else:
                        df1.loc[file] = row
                # print(df2)
                output_file.write(f"Confusion Matrix:\n{confusion}\n")
                output_file.write(f"Accuracy: {accuracy}\n")
                output_file.write(f"Recall: {recall}\n")
                output_file.write(f"F1 Score: {f1}\n")
                output_file.write(f"over!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

df2.to_csv('partRedo/data_0.8.csv',index=False)
df0.to_csv('partRedo/data_0.8_0.csv',index=False)
df1.to_csv('partRedo/data_0.8_1.csv',index=False)

output_file.close()
