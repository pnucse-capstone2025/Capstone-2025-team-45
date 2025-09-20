#### 1. 프로젝트 배경
#### 1.1. 국내외 시장 현황 및 문제점
> 팬데믹 이후 기업의 디지털 전환 및 원격 근무 확산, 클라우드 환경 도입이 가속화되면서 기업 네트워크의 규모와 복잡도는 급격히 증가하고 있다. 이로 인해 네트워크에 연결되는 엔드포인트(Endpoint)의 수도 늘어나고 있으며, 이는 곧 내부자 위협(Insider Threat)의 증가로 이어진다.
>
> 내부자 위협은 기업 내부 시스템에 합법적 접근 권한을 가진 사용자가 부주의하거나 악의적 목적으로 발생시키는 보안 위협을 의미한다. 외부 공격보다 탐지가 어렵고 피해 복구 비용이 더 크다는 특징을 가지며, 이에 대응하기 위한 제로 트러스트 모델(Zero Trust Model)의 필요성이 대두되고 있다.
> 
> 제로 트러스트는 “절대 신뢰하지 말고, 항상 검증하라 (Never Trust, Always Verify)”라는 원칙에 기반하며, 한국인터넷진흥원(KISA)에서 발표한 가이드라인에서는 다음과 같은 원칙을 강조한다:
> - 모든 접근에 대해 신뢰하지 않을 것
>
> - 일관되고 중앙 집중적인 정책 관리 및 접근제어 필요
>
> - 모든 상태를 모니터링하고 로그 기반으로 지속 검증 수행
> 
> 그러나 기존 NAC(Network Access Control), 특히 IEEE 802.1x 프로토콜은 접속 시점의 인증은 보장하지만, 인증 이후 발생하는 내부자의 악의적 행위는 탐지하지 못한다. 예를 들어, 합법적으로 인증받은 사용자가 민감 데이터를 무단 반출하거나, 계정 탈취자가 정상 사용자를 위장해 내부 네트워크에 접근하는 상황은 기존 NAC로는 방어할 수 없다. 
> 
> 따라서 단순한 인증 절차를 넘어, 사용자의 행동 로그를 수집하고 패턴을 분석하여 이상 행위를 탐지 및 네트워크에서 격리하는 새로운 접근 방식이 필요하다.


#### 1.2. 필요성과 기대효과

> - 필요성
>   - 기존 NAC는 접속 시점의 인증만 수행 → 내부자 위협 탐지 불가
>   - 기업 환경에서 실시간 이상 탐지 및 차단 시스템 요구
>   - 제로 트러스트 보안 모델을 충족할 수 있는 동적 접근 제어 필요
> - 기대효과 
>   - 사용자 행동 기반 탐지를 통해 내부자 위협 조기 발견
>   - 이상 사용자의 PC를 즉시 네트워크에서 격리하여 피해 확산 방지
>   - 관리자 대시보드를 통한 보안 가시성 및 운영 효율성 향상
>   - 학술적·산업적 활용 가치: NAC 고도화 및 보안 정책 자동화에 기여

### 2. 개발 목표
#### 2.1. 목표 및 세부 내용
> 본 프로젝트의 목표는 조직 내 네트워크에서 사용자의 행동 로그를 실시간 수집·분석하여 이상 사용자를 탐지하고, 해당 사용자가 사용하는 PC를 자동으로 네트워크에서 격리하는 시스템을 구축하는 것이다.

#### 2.2. 기존 서비스 대비 차별성 
> 일반적인 **인공지능 기반 보안 시스템**은 주로 외부 침입 탐지(IDS/IPS), 악성코드 탐지, 네트워크 트래픽 이상 탐지 등 **외부 공격 대응**에 초점을 맞추고 있다.  
> 이러한 시스템들은 **시그니처 기반** 또는 **네트워크 패킷 분석**을 통해 공격 패턴을 탐지하는 경우가 많다.  
> 그러나 내부자의 정상적인 네트워크 접근 이후 발생하는 **행동 기반 위협**에는 한계가 존재한다.  
>  
> **본 시스템의 차별성은 다음과 같다:**  
>  
> 1. **탐지 대상의 차별성**  
>    - 기존 AI 보안: 악성코드, 외부 트래픽, 이상 패킷 패턴에 집중  
>    - 본 시스템: **사용자 행동 로그(로그온/로그오프, 파일 접근, 웹 사용, 이메일 전송 등)** 기반 내부자 위협 탐지  
>  
> 2. **접근 제어 연계성**  
>    - 기존 AI 보안: 위협 탐지 후 관리자 경고(Alert)에 그치는 경우 다수  
>    - 본 시스템: 탐지 결과를 즉시 **NAC 제어 모듈과 연동**하여 해당 PC를 네트워크에서 격리 → **탐지와 대응(Detection & Response) 자동화**  
>  
> 3. **제로 트러스트 모델 구현 수준**  
>    - 기존 AI 보안: “위협을 발견하면 차단” 수준  
>    - 본 시스템: **“항상 검증”** 원칙에 기반하여 접속 이후에도 사용자의 행동을 지속 검증 → 제로 트러스트 아키텍처 실현에 근접  
>  
> 4. **실행 환경 차별성**  
>    - 기존 AI 보안: 대규모 보안 장비(방화벽, IDS 등) 중심  
>    - 본 시스템: **에이전트 + 가상 라우터(OpenWRT) + 머신러닝 모듈**로 경량화 → 중소 규모 조직에서도 적용 가능  

### 3. 시스템 구성도


![설계도](https://private-user-images.githubusercontent.com/127084199/491908947-effb282c-e0ce-46be-8865-718885c72086.png?jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NTgzNjkzNjMsIm5iZiI6MTc1ODM2OTA2MywicGF0aCI6Ii8xMjcwODQxOTkvNDkxOTA4OTQ3LWVmZmIyODJjLWUwY2UtNDZiZS04ODY1LTcxODg4NWM3MjA4Ni5wbmc_WC1BbXotQWxnb3JpdGhtPUFXUzQtSE1BQy1TSEEyNTYmWC1BbXotQ3JlZGVudGlhbD1BS0lBVkNPRFlMU0E1M1BRSzRaQSUyRjIwMjUwOTIwJTJGdXMtZWFzdC0xJTJGczMlMkZhd3M0X3JlcXVlc3QmWC1BbXotRGF0ZT0yMDI1MDkyMFQxMTUxMDNaJlgtQW16LUV4cGlyZXM9MzAwJlgtQW16LVNpZ25hdHVyZT05NWU4ZWI3MzExNjRjOGFhOTUwZmM2YTQzNGE5OTQ4YmEzZWRjZDg2MGI5OTQ3YzBhOWE2MTFkNzk2ZTg2MjM1JlgtQW16LVNpZ25lZEhlYWRlcnM9aG9zdCJ9.zkZY4yK30IIuC65nkzAcxg35qYNtGUdo5w6AP6xfIwE)


> 전체 시스템은 서로 다른 역할과 책임을 수행하는 **4개의 모듈**로 구성된다.  
>  
> 1. **로그 수집 및 저장 모듈**  
>    - 조직 내 PC에서 발생하는 **사용자 행동 로그**를 수집한다.  
>    - 수집된 로그는 중앙 저장소(데이터베이스)에 안전하게 보관된다.  
>  
> 2. **이상 탐지 모듈**  
>    - 저장된 로그 데이터를 기반으로 **사용자 행위를 분석**한다.  
>    - 머신러닝 모델을 통해 **이상 여부를 판별**하고, 탐지된 결과를 바탕으로 **이상 사용자 목록**을 생성한다.  
>  
> 3. **네트워크 제어 모듈**  
>    - 탐지된 이상 사용자가 사용하는 **PC의 네트워크 연결을 허용하거나 차단**하는 역할을 수행한다.  
>    - 라우터와 연동하여 자동으로 정책을 적용함으로써, 보안 위협을 **실시간으로 제어**할 수 있다.  
>  
> 4. **모니터링 모듈**  
>    - 보안 관리자가 시스템 전체 현황을 직관적으로 확인할 수 있도록 **웹 기반 대시보드**를 제공한다.  
>    - 네트워크 상태, 이상 사용자 기록, 차단 내역 등을 시각화하여 관리 효율성을 높인다.  

#### 3.2. 사용 기술

| 번호 | 분야                     | 적용 기술 및 환경                                  |
|-----:|-------------------------|---------------------------------------------------|
| 1    | 프로그래밍 언어          | Python 3.10.14<br/>JavaScript (Node.js 18.19.1)   |
| 2    | 웹 프레임워크            | React 19.1.1<br/>FastAPI 0.103.1                  |
| 3    | 배포 환경                | Docker 28.3.0                                     |
| 4    | 데이터베이스             | PostgreSQL 15.4                                   |
| 5    | 머신 러닝 라이브러리     | Scikit-learn                                      |
| 6    | 가상 조직 네트워크 구축  | VirtualBox<br/>Ubuntu LTS 24.04<br/>OpenWRT       |
| 7    | 로그 수집 에이전트       | mitmproxy 12.1.2                                  |

### 4. 개발 결과

#### 4.1. 전체 시스템 흐름도
> 본 시스템은 조직 내 PC에서 발생하는 **사용자 행동 로그 수집 → 이상 탐지 → 네트워크 제어 → 모니터링**의 흐름으로 동작한다.  
> 로그 수집 모듈은 엔드포인트에서 데이터를 중앙 저장소로 전송하고, 이상 탐지 모듈은 이를 분석하여 이상 여부를 판별한다.  
> 네트워크 제어 모듈은 탐지 결과를 바탕으로 특정 PC를 격리하거나 허용하며, 모니터링 모듈은 관리자에게 보안 현황을 직관적으로 제공한다.

---

#### 4.2. 기능 설명 및 주요 기능 명세서

##### (1) 사용자 행동 로그 수집 범위 및 방법
- **로그온·로그오프**:  
  - `auditd`의 USER_START, USER_END 이벤트 기반 탐지  
  - 시스템 계정, 백그라운드 프로세스 등 불필요 레코드 제외  

- **웹 브라우징**:  
  - `mitmproxy` 기반 프록시를 통해 HTTP/HTTPS 요청 수집  
  - 요청 객체에서 URL 추출  

- **메일**:  
  - 서버 메일: Postfix `always_bcc` 기능으로 송·수신 메타데이터 확보  
  - 웹메일: `mitmproxy`에서 HTTP 요청 패턴 파싱  

- **디바이스 연결**:  
  - Linux 마운트/언마운트 이벤트 + `udisks2` 기반 자동 마운트 기록  
  - `auditd` 감사 규칙을 통해 이벤트 로깅  

- **파일 복사**:  
  - 외부 디바이스 마운트 지점으로의 복사 이벤트를 `auditd`로 수집  
  - PATH 항목을 파싱하여 파일명 추출  

- **표준 로그 스키마**:  
  - 공통 필드: `event_id`, `employee_id`, `pc_id`, `timestamp`, `event_type`  
  - 행동 유형별 확장 필드:  

    | 행동 유형 | 확장 필드 |
    |-----------|-----------|
    | logon     | activity (logon/logoff) |
    | http      | url |
    | file      | filename |
    | device    | activity (connect/disconnect) |
    | email     | from_addr, to, cc, bcc, size, attachment |

---

##### (2) 이상 탐지 모듈
- **이상 탐지 모델 학습**
  - 데이터셋: CMU CERT Insider Threat Dataset (R4.2) 사용  
  - 포함 로그 유형: logon, http, file, device, email  
  - 이상 행위 시나리오 4개 클래스  

    | 시나리오 (Class) | 상세 |
    |-----------------|------|
    | 0 | 정상 사용자 |
    | 1 | 근무 시간 외 로그인 → USB 연결 → 악성 사이트 업로드 후 퇴사 |
    | 2 | 구직 사이트 탐색 + USB 빈번 사용 |
    | 3 | 키로거 설치 후 상사 계정 탈취 → 대량 이메일 발송 후 퇴사 |

- **특징 추출 (주 단위 집계)**  
  - 사용자 ID, 행동 유형, 사용 시간대, PC 종류(자신/공유/상사)  
  - http: url 길이, 깊이, 도메인 유형  
  - file: 파일 크기, 단어 수, 경로 깊이  
  - device: USB 연결 지속 시간  
  - email: 수신자 수, 첨부파일 수, 외부 전송 여부 등  

- **학습 알고리즘**
  - Random Forest, XGBoost 비교  
  - 불균형 데이터 해결: SMOTE 적용  
  - 최종 모델: 정상/이상 여부 + 이상 시나리오 분류 가능  

- **이상 탐지 파이프라인**
  - 구성 요소: Preprocessor + Anomaly Detector  
  - Preprocessor 세부 클래스:  
    - Log Loader → DB에서 로그 조회  
    - Log Merger → 로그 병합  
    - Numeric Encoder → 문자열 속성 숫자 변환  
    - Feature Aggregator → 특징 추출  
  - Anomaly Detector: 학습 모델로 이상 확률 계산 후 DB에 저장  

---

##### (3) 네트워크 제어 모듈
- 가상 조직 네트워크: VirtualBox 기반 PC/라우터 환경 구축  
- 라우터 데몬:
  - ping sweep + ARP 테이블 업데이트  
  - MAC 주소 목록을 JSON 형태로 제어 모듈에 보고  
- 제어 흐름:
  1. 특정 PC 차단 요청 수신  
  2. DB에서 해당 PC MAC 주소 및 연결 라우터 조회  
  3. 라우터 SSH 접속 → iptables 방화벽 규칙 적용  
  4. DB 상태 업데이트 후 결과 반환  

---

##### (4) 모니터링 모듈
- **기능 개요**: 관리자 전용 웹페이지 제공, 시스템 보안 현황 실시간 관찰  
- **주요 페이지**:
  - **조직 인증 및 회원가입**: 조직 ID + 인증 코드 입력 후 계정 생성  
  - **로그인**: 관리자 계정 로그인 시 대시보드 진입  
  - **대시보드**:  
    - 로그온 PC 비율  
    - 주간 이상 사용자 탐지 현황  
    - 월/주 단위 로그 유형 집계  
    - 네트워크 차단 기록  
    - 이상 사용자 목록  
  - **이상 사용자 탐지 결과 조회**: 특정 기간 분석 → 시나리오 분류, 확률, 파이차트 제공  
  - **탐지 이력 조회**: 이전 탐지 작업 내역 및 상세 결과 확인  
  - **행동 로그 조회**: 부서, 팀, 사용자 ID, 이벤트 타입, 기간 조건 필터링  
    - http 로그: 접속 URL  
    - email 로그: 송신자/수신자/첨부파일 등 메타데이터  
  - **PC 상태 관리**: 각 PC의 현재 상태 및 접근 제어 수동 조작 가능  
  - **알림 기능**:  
    - 이상 사용자 로그온 시 네트워크 자동 차단  
    - WebSocket 실시간 알림 + 이메일 경고 전송  

---

#### 4.3. 디렉토리 구조
```
├── README.md
├── User_Entity_Based_Anomaly_Detection_System
│   ├── Log-Collection-System
│   │   ├── README.md
│   │   ├── docker-compose.yml
│   │   └── scripts
│   ├── Monitoring-System
│   │   ├── README.md
│   │   ├── backend
│   │   └── frontend
│   └── machine_learning_model_training
│       ├── MG_UABD
│       ├── data_preprocessing
│       └── model_training_randomforest
└── docs
    ├── 01.보고서
    │   ├── 01.착수보고서.pdf
    │   ├── 02.중간보고서.pdf
    │   └── 03.최종보고서.pdf
    ├── 02.포스터
    │   └── 포스터.pdf
    └── 03.발표자료
        └── 발표자료.pdf
```
### 5. 설치 및 실행 방법

#### 5.1. Git 환경 구성

1. 저장소 다운로드  
   프로젝트 소스를 내려받기 위해 다음 명령어를 실행합니다.
   ```bash
   git clone https://github.com/PNU-Capstone-CtrlAltDefend/Monitoring-System.git
   cd Monitoring-System
   ```

---

#### 5.2. 프론트엔드 환경 구성

1. Node.js 및 npm 설치  
   프론트엔드 실행을 위해 다음 버전 이상의 Node.js와 npm이 필요합니다.
   ```
   Node.js: 18.19.1
   npm: 9.2.0
   ```

2. 환경 변수 파일 생성  
   ```bash
   cp .env.example .env
   ```

3. 의존성 설치 및 서버 실행  
   ```bash
   cd frontend
   npm install
   npm start
   ```
   → 실행 후 [http://localhost:3000](http://localhost:3000) 접속 가능

---

#### 5.3. 백엔드 환경 구성

1. Python 및 Docker 설치  
   ```
   Python: 3.10.14
   Docker: 20.x 이상
   ```

2. 데이터베이스 및 pgAdmin 실행  
   ```bash
   cd backend
   sudo docker-compose up -d
   ```
   - pgAdmin 접속: [http://localhost:3030](http://localhost:3030)  
     - ID: `admin@sentra.co.kr`  
     - PW: `huni5504`  
   - 데이터베이스 접속:  
     - ID: `sentra_user`  
     - PW: `huni5504`

3. 백엔드 서버 실행  
   ```bash
   cd api
   python3 -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   gunicorn -c gunicorn.conf.py
   ```
   → 실행 후 [http://localhost:8001](http://localhost:8001) 접속 가능  
   → Swagger UI: [http://localhost:8001/docs](http://localhost:8001/docs)

---

#### 5.4. 접속 방법

- **프론트엔드 대시보드**: [http://localhost:3000](http://localhost:3000)  
- **백엔드 API**: [http://localhost:8001/docs](http://localhost:8001/docs)

---

#### 5.5. 자주 발생하는 오류 및 해결 방법

- **포트 충돌 발생 시**  
  ```bash
  lsof -i:3000   # 프론트엔드 포트
  lsof -i:8001   # 백엔드 포트
  kill -9 <PID>
  ```

- **DB 연결 오류 발생 시**  
  ```bash
  docker ps      # PostgreSQL 컨테이너 상태 확인
  docker logs <container_id>
  ```

- **npm 실행 오류 발생 시**  
  ```bash
  node -v        # Node.js 버전 확인 (18 이상 필요)
  npm install --force
  ```

### 6. 소개 자료 및 시연 영상

### 7. 팀 구성
#### 7.1. 팀원별 소개 및 역할 분담
이광훈, gbhuni@gmail.com, 개발총괄 및 제어 모듈 개발

조유진, yz0251@pusan.ac.kr, 로그 수집 에이전트 개발

신해진, grangbleu44@pusan.ac.kr, 이상탐지 모듈 개발

### 8. 참고 문헌 및 출처

[1] 보안뉴스. “내부자 보안사고 급증, 총계 6,803건에 연간 평균 총비용 1,540만 달러,” 보안뉴스, 14 June 2022. Available: [https://www.boannews.com/media/view.asp?idx=107451](https://www.boannews.com/media/view.asp?idx=107451). [Accessed: Aug. 26, 2025].

[2] 선애 김, “내부자 보안 사고 기업 29%, 피해 복구액 14억 이상,” DataNet, Nov. 27, 2024. [Online]. Available: [https://www.datanet.co.kr/news/articleView.html?idxno=198095](https://www.datanet.co.kr/news/articleView.html?idxno=198095). [Accessed: Aug. 26, 2025].

[3] 한국인터넷진흥원, “제로 트러스트 가이드라인 2.0,” 한국인터넷진흥원, 3 Dec 2024. [Online]. Available: [https://www.kisa.or.kr/2060204/form?postSeq=18&page=1#fnPostAttachDownload](https://www.kisa.or.kr/2060204/form?postSeq=18&page=1#fnPostAttachDownload). [Accessed: 26-Aug-2025].

[4] NIST, “Network Access Control (NAC),” Computer Security Resource Center Glossary, NIST SP 800-41 Rev. 1. [온라인]. Available: [https://csrc.nist.gov/glossary/term/network_access_control](https://csrc.nist.gov/glossary/term/network_access_control). [Accessed: 26-Aug-2025].

[5] Software Engineering Institute, “Insider Threat Test Dataset,” Carnegie Mellon University, Pittsburgh, PA, Nov. 28, 2016. DOI: [10.1184/R1/12841247.v1](https://doi.org/10.1184/R1/12841247.v1).
