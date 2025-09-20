import pandas as pd
import sys

def inspect_csv(file_path, target_col=None, max_rows=5):
    """
    CSV 파일 기본 특성 확인
    :param file_path: CSV 파일 경로
    :param target_col: (선택) 타겟 변수 이름 → 클래스 분포 출력
    :param max_rows: 출력할 샘플 행 수
    """
    print(f"📂 Loading: {file_path}")
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        print(f"❌ CSV 로드 실패: {e}")
        sys.exit(1)
    
    print("\n=== 데이터셋 기본 정보 ===")
    print(f"행 수 (rows): {df.shape[0]}")
    print(f"열 수 (cols): {df.shape[1]}")

    print("\n=== 데이터 타입 & 결측치 ===")
    info_df = pd.DataFrame({
        "dtype": df.dtypes,
        "null_count": df.isnull().sum(),
        "null_ratio": df.isnull().mean()
    })
    print(info_df)

    print("\n=== 샘플 데이터 ===")
    print(df.head(max_rows))

    print("\n=== 기초 통계 (수치형) ===")
    print(df.describe())

    if target_col and target_col in df.columns:
        print(f"\n=== 타겟 변수 '{target_col}' 클래스 분포 ===")
        print(df[target_col].value_counts())
        print("\n(비율)")
        print(df[target_col].value_counts(normalize=True))


if len(sys.argv) < 2:
    print("사용법: python inspect_csv.py <csv 파일 경로> [타겟 컬럼명]")
    sys.exit(1)

file_path = sys.argv[1]
target_col = sys.argv[2] if len(sys.argv) > 2 else None

inspect_csv(file_path, target_col)
