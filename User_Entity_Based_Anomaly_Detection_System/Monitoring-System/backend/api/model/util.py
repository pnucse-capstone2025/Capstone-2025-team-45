"""
데이터 베이스 초기화에 사용되는 여러 함수 모음 
"""
import os
from pathlib import Path
import numpy as np
import pandas as pd
from datetime import datetime, date


def getuserlist(dname='r4.2'):
    """
    데이터 세트로부터 사용자 목록을 가져와 데이터 프레임으로 반환 
    """
    base_dir = Path(__file__).resolve().parent / "dataset" / "LDAP"
    if not base_dir.exists():
        raise FileNotFoundError(f"LDAP directory not found: {base_dir}")

    allfiles = [
        str(f) for f in base_dir.glob("*.csv") if f.is_file()
    ]
    
    alluser = {}
    alreadyFired = []

    for file in allfiles:
        af = (pd.read_csv(file, delimiter=',')).values
        employeesThisMonth = []
        for i in range(len(af)):
            employeesThisMonth.append(af[i][1])
            if af[i][1] not in alluser:
                month_str = os.path.basename(file).replace('.csv', '')
                alluser[af[i][1]] = af[i][0:1].tolist() + af[i][2:].tolist() + [month_str, np.nan]

        firedEmployees = list(set(alluser.keys()) - set(alreadyFired) - set(employeesThisMonth))
        alreadyFired = alreadyFired + firedEmployees
        for e in firedEmployees:
            month_str = os.path.basename(file).replace('.csv', '')
            alluser[e][-1] = month_str

    df = pd.DataFrame.from_dict(alluser, orient='index')
    df.columns = ['employee_name', 'email', 'role', 'b_unit', 'functional_unit', 'department', 'team', 'supervisor', 'wstart', 'wend']

    df = df.reset_index().rename(columns={'index': 'user_id'})
    print(df.head())
    return df

def ym_to_date(s: str) -> date | None:
    """
    wstart, wend YM TO YYYY-MM-DD  
    """
    if not isinstance(s, str) or not s.strip():
        return None
    try:
        # 'YYYY-MM-01'로 정규화
        return datetime.strptime(s + "-01", "%Y-%m-%d").date()
    except ValueError:
        return None