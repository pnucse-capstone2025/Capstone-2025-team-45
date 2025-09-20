import pandas as pd
import numpy as np
from sklearn.metrics import confusion_matrix, classification_report

# --- 설정 ---
# 2차 정밀 분석 결과가 담긴 CSV 파일 경로
RESULTS_FILE = 'partRedo/data_0.8.csv'

# ✨ 최종 판결을 위한 임계값(Threshold) 설정 ✨
# "개인 맞춤형 모델이 예측한 전체 활동 로그 중, 악성으로 예측된 비율이 n%를 넘으면 최종 악성 사용자로 판정한다"
# THRESHOLD = n/100

def main(threshold):  # param 'threshold': 임계값
    """
    data_0.8.csv엥 기록된 로그 단위 결과를 바탕으로,
    '위험도 점수'를 계산하고 임계값을 적용하여 최종 사용자 단위 판결을 내립니다.
    """
    THRESHOLD = threshold
    try:
        # 1. 정밀 분석 결과가 담긴 CSV 파일을 불러옵니다.
        results_df = pd.read_csv(RESULTS_FILE)
    except FileNotFoundError:
        print(f"!!! 에러: '{RESULTS_FILE}' 파일을 찾을 수 없습니다.")
        print("model.py 스크립트를 먼저 실행하여 결과 파일을 생성했는지 확인하세요.")
        return

    # 2. 사용자별 '위험도 점수' 계산
    
    # FP(오탐)과 TP(정탐)는 모델이 '악성(1)'으로 예측한 경우입니다.
    predicted_positives = results_df['cm01'] + results_df['cm11']
    
    # TN, FP, FN, TP를 모두 더하면 해당 사용자의 전체 테스트 데이터 개수가 됩니다.
    total_samples = results_df['cm00'] + results_df['cm01'] + results_df['cm10'] + results_df['cm11']
    
    # 위험도 점수 = (악성 예측 수 / 전체 샘플 수)
    # 0으로 나누는 오류를 방지하기 위해 np.divide 사용
    results_df['risk_score'] = np.divide(predicted_positives, total_samples, 
                                         out=np.zeros_like(predicted_positives, dtype=float), 
                                         where=total_samples!=0)


    # 3. 임계값을 이용한 최종 판결
    # 위험도 점수가 임계값(THRESHOLD)보다 높거나 같으면 1(악성), 아니면 0(정상)으로 판결
    results_df['final_judgement'] = (results_df['risk_score'] >= THRESHOLD).astype(int)

    # 4. 결과 출력
    print("="*60)
    print(f"      '위험도 점수' 기반 최종 판결 (임계값: {THRESHOLD*100:.1f}%)")
    print("="*60)
    
    # 5. 최종 판결 요약
    final_counts = results_df['final_judgement'].value_counts().sort_index()
    print("\n[최종 판결 요약]")
    print(f"  - 최종 '정상' 판정 사용자 수: {final_counts.get(0, 0)} 명")
    print(f"  - 최종 '악성' 판정 사용자 수: {final_counts.get(1, 0)} 명")

   # 원본 mal_user와 비교하여 '사용자 단위' 성능 평가
    if 'mal_user' in results_df.columns:
        print("\n" + "-"*60)
        print("\n[최종 판결 성능 평가 (사용자 단위)]")

        y_true_user_level = results_df['mal_user']
        y_pred_user_level = results_df['final_judgement']

        user_level_cm = confusion_matrix(y_true_user_level, y_pred_user_level)
        
        print("\n[사용자 단위 Confusion Matrix]")
        if len(user_level_cm) == 2:
            print("                판결: 정상   판결: 악성")
            print(f"실제: 정상    [[{user_level_cm[0,0]:^10d}  {user_level_cm[0,1]:^10d}]")
            print(f"실제: 악성     [{user_level_cm[1,0]:^10d}  {user_level_cm[1,1]:^10d}]]")
        else:
            print(user_level_cm)
        
        print("\n[사용자 단위 Classification Report]")
        print(classification_report(y_true_user_level, y_pred_user_level, 
                                    target_names=['정상 사용자 (0)', '악성 사용자 (1)'], 
                                    digits=4, zero_division=0))

if __name__ == '__main__':
    main(0.05)  # 임계값 5%로 테스트
    main(0.02)  # 임계값 2%로 테스트