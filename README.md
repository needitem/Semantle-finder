# 의미 기반 지능형 꼬맨틀 솔버 (Semantic Korean Wordle Solver)

한국어 워들 게임인 꼬맨틀(Semantle)을 자동으로 해결하는 지능형 솔버입니다. 의미 기반 탐색 전략과 실시간 학습을 통해 정답을 찾아냅니다.

## 주요 특징

- **4단계 적응형 탐색 전략**: 게임 진행 상황에 따라 자동으로 전략 전환
- **실시간 학습**: 단어 간 관계를 학습하여 점진적으로 성능 향상
- **웹 자동화**: Selenium을 사용한 완전 자동 플레이
- **상세한 로깅**: 모든 게임 과정을 기록하고 분석 가능

## 설치 방법

### 1. 필수 요구사항
- Python 3.7 이상
- Google Chrome 브라우저
- ChromeDriver (Chrome 버전과 일치해야 함)

### 2. 라이브러리 설치
```bash
pip install -r requirements.txt
```

### 3. ChromeDriver 설치
- [ChromeDriver 다운로드](https://chromedriver.chromium.org/)
- Chrome 버전 확인: Chrome 설정 → Chrome 정보
- 해당 버전의 ChromeDriver 다운로드 후 PATH에 추가

## 사용 방법

### 기본 실행
```bash
python semantic_solver.py
```

### 실시간 모니터링
두 개의 터미널을 열어서 실행:

**터미널 1 (게임 실행):**
```bash
python semantic_solver.py
```

**터미널 2 (실시간 모니터링):**
```bash
python monitor_game.py
```

### 로그 분석
게임 종료 후 분석:
```bash
# 기본 통계 분석
python analyze_logs.py

# 상세 분석 및 시각화
python view_detailed_log.py
```

## 전략 시스템

### 1. 넓은 의미 탐색 (Wide Semantic Exploration)
- **사용 시점**: 초기 단계 (유사도 < 10%)
- **목적**: 다양한 의미 영역 탐색
- **특징**: 8개 의미 범주에서 균형있게 선택

### 2. 의미적 경사 탐색 (Semantic Gradient Search)
- **사용 시점**: 초기-중간 단계 (유사도 10-30%)
- **목적**: 고성능 단어 주변 탐색
- **특징**: 언어학적 연관어 및 문맥적 관련어 활용

### 3. 집중 의미 탐색 (Focused Semantic Search)
- **사용 시점**: 중간-후반 단계 (유사도 30-60%)
- **목적**: 고유사도 영역 집중 탐색
- **특징**: 다층 연관 관계 분석

### 4. 정밀 의미 탐색 (Precision Semantic Search)
- **사용 시점**: 후반 단계 (유사도 60% 이상)
- **목적**: 정답 근처에서 정밀 탐색
- **특징**: 형태론적 변형 및 초근접 단어 활용

## 프로젝트 구조

```
autosemantle/
├── semantic_solver.py      # 메인 실행 파일
├── requirements.txt        # 필수 패키지 목록
├── README.md              # 프로젝트 문서
├── words.xls              # 한국어 어휘 목록
├── analyze_logs.py        # 로그 분석 도구
├── view_detailed_log.py   # 상세 분석 도구
├── monitor_game.py        # 실시간 모니터링
├── test_improved_algorithm.py  # 알고리즘 테스트
└── modules/               # 핵심 모듈
    ├── models.py          # 데이터 구조 정의
    ├── strategy_engine.py # 4단계 적응형 탐색 전략
    ├── learning_engine.py # 실시간 학습 엔진
    ├── web_automation.py  # 웹 자동화
    └── strategy_logger.py # 전략 로깅 시스템
```

## 핵심 모듈 설명

### models.py - 데이터 구조 모듈
- `GuessResult`: 추측 결과 (단어, 유사도, 순위)
- `GameSession`: 게임 세션 상태 관리
- `WordPairData`: 단어 쌍 관계 데이터
- `WordFrequencyData`: 단어 효과성 통계

### strategy_engine.py - 전략 엔진
- 4가지 탐색 전략 구현
- 상황별 자동 전략 전환
- 학습 데이터 기반 단어 선택

### learning_engine.py - 학습 엔진
- 실시간 단어 관계 학습
- 성공 패턴 저장 및 분석
- 효과성 점수 계산

### web_automation.py - 웹 자동화
- Selenium 기반 자동 플레이
- 최적화된 결과 파싱
- 견고한 오류 처리

### strategy_logger.py - 로깅 시스템
- 모든 게임 과정 기록
- 전략 변경 추적
- 성능 분석 데이터 생성

## 학습 시스템

### 단어 관계 학습
- 모든 단어 쌍의 유사도 차이를 기록
- 성공한 게임의 패턴 분석
- 효과적인 단어 식별 및 우선순위 부여

### 학습 데이터 파일
- `kkomantle_learning.json`: 게임 통계 및 성공 패턴
- `word_pairs.json`: 단어 쌍 관계 데이터
- `strategy_logs.json`: 상세 게임 로그

## 분석 도구

### 1. analyze_logs.py
- 전략별 효과성 분석
- 성공적인 단어 패턴 식별
- 개선 추천사항 생성

### 2. view_detailed_log.py
- 게임 진행 과정 시각화
- 단어별 효과성 점수
- 고득점 시퀀스 분석
- CSV 파일 내보내기

### 3. monitor_game.py
- 실시간 게임 진행 모니터링
- 유사도 변화 시각화
- 전략 변경 알림

## 개선된 기능 (최신 업데이트)

### 1. 고영향 단어 우선 선택
- 로그 분석을 통해 발견된 효과적인 단어들을 우선 시도
- "사례", "실패", "기원" 등 높은 유사도 증가를 보인 단어

### 2. 동적 전략 전환
- 20회 이상 같은 전략으로 정체 시 강제 전환
- 유사도 증가 속도에 따른 적응적 전환
- 순환 전략 패턴으로 다양성 확보

### 3. 학습 데이터 활용 강화
- 평균 유사도 30% 이상인 검증된 단어 우선 선택
- 단어 쌍 관계를 활용한 지능적 추천

## 성능 최적화

### 웹 자동화 최적화
- 단어당 총 처리 시간: ~0.01초
- 최적화된 JavaScript 파싱
- 비동기 처리로 빠른 응답

### 메모리 관리
- 슬라이딩 윈도우로 데이터 크기 제한
- 효율적인 데이터 구조 사용

## 문제 해결

### Chrome Driver 오류
```
selenium.common.exceptions.WebDriverException: Message: 'chromedriver' executable needs to be in PATH
```
**해결책**: ChromeDriver를 다운로드하고 시스템 PATH에 추가

### 페이지 로딩 실패
```
❌ 게임 사이트 접속 실패
```
**해결책**: 
1. 인터넷 연결 확인
2. 게임 사이트 URL 확인 (https://semantle-ko.newsjel.ly/)
3. 방화벽/프록시 설정 확인

### 단어 결과 파싱 실패
```
⚠️ 단어 '...' 결과를 찾을 수 없음
```
**해결책**: 게임 사이트의 HTML 구조가 변경되었을 수 있음. 이슈 제보 필요

## 기여 방법

1. Fork 후 개선사항 구현
2. 테스트 실행 및 로그 확인
3. Pull Request 제출

## 라이선스

MIT License

## 주의사항

- 이 프로그램은 교육 및 연구 목적으로 제작되었습니다
- 게임 서버에 부담을 주지 않도록 적절한 딜레이가 설정되어 있습니다
- 과도한 사용은 자제해 주세요

## 작성자

- 개발 및 문서화 지원: Claude (Anthropic)
- 프로젝트 관리: 사용자

---

더 자세한 기술적 내용은 프로젝트 소스 코드의 주석을 참고하세요.