# 꼬맨틀용 적응형 의미 탐색 솔버

## 개요

본 프로젝트는 실시간 유사도 학습을 기반으로 한 다단계 지능형 탐색 전략을 사용하는 꼬맨틀 적응형 의미 탐색 솔버를 제시한다. 기존의 사전 훈련된 언어 모델에 의존하는 접근법과 달리, 우리 시스템은 실제 게임 상호작용을 통해 단어 관계를 동적으로 학습하여 시간이 지남에 따라 성능이 향상되는 의미 연관 지식 베이스를 구축한다.

## 1. 서론

한국어 꼬맨틀은 플레이어가 추측한 단어에 대해 유사도 점수를 받아 목표 단어를 찾는 단어 추측 게임이다. 이 게임의 핵심 과제는 최소한의 시도로 정답에 수렴하기 위해 의미 공간을 효율적으로 탐색하는 것이다.

### 1.1 문제 정의

목표 단어 `w_target`과 어휘 `V = {w_1, w_2, ..., w_n}`가 주어졌을 때, 각 추측 `g_i`가 유사도 점수 `s_i = sim(g_i, w_target)`을 반환하는 추측 집합 `G = {g_1, g_2, ..., g_k}`의 크기를 최소화하여 `w_target`을 찾는 것이 목표이다.

### 1.2 주요 과제

1. **의미 공간 탐색**: 고차원 의미 공간의 효율적 탐색
2. **실시간 적응**: 사전 훈련 없이 즉각적인 피드백으로부터 학습
3. **다중 전략**: 현재 진행 상황에 따른 탐색 전략 적응
4. **지식 지속성**: 여러 게임 세션에 걸친 통찰력 축적

## 2. 시스템 아키텍처

### 2.1 핵심 구성요소

```
┌─────────────────────────────────────────────────────────────┐
│                    SemanticSolver                           │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   전략 엔진      │  │   학습 엔진      │  │   지식 베이스   │ │
│  │                 │  │                 │  │                 │ │
│  │ • 넓은 탐색     │  │ • 관계 학습     │  │ • 단어 쌍       │ │
│  │ • 경사 탐색     │  │ • 패턴 인식     │  │ • 성공 패턴     │ │
│  │ • 집중 탐색     │  │ • 효과성 평가   │  │ • 효과성 점수   │ │
│  │ • 정밀 탐색     │  │ • 정체 감지     │  │ • 빈도 데이터   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 데이터 구조

#### 2.2.1 추측 결과 클래스
```python
@dataclass
class GuessResult:
    word: str           # 추측한 단어
    similarity: float   # 유사도 점수 [0.0, 1.0]
    rank: str          # 순위 정보
    attempt: int       # 시도 번호
```

#### 2.2.2 학습 데이터 구조
```json
{
  "games_played": int,
  "successful_patterns": [
    {
      "answer": str,
      "attempts": int,
      "key_words": [str],
      "timestamp": str
    }
  ],
  "word_frequency": {
    "word": {
      "count": int,
      "avg_similarity": float,
      "best_similarity": float
    }
  }
}
```

#### 2.2.3 단어 쌍 구조
```json
{
  "word1|word2": {
    "similarity_diffs": [float],
    "co_occurrence_count": int
  }
}
```

## 3. 다단계 적응형 탐색 알고리즘

### 3.1 전략 선택 함수

핵심 알고리즘은 현재 성능 지표를 기반으로 한 4단계 적응형 탐색 전략을 사용한다:

```python
def select_strategy(best_similarity: float, is_stuck: bool) -> Strategy:
    if best_similarity < 0.1:
        return WideSemanticExploration()    # 넓은 의미 탐색
    elif best_similarity < 0.25 or is_stuck:
        return SemanticGradientSearch()     # 의미적 경사 탐색
    elif best_similarity < 0.5:
        return FocusedSemanticSearch()      # 집중 의미 탐색
    else:
        return PrecisionSemanticSearch()    # 정밀 의미 탐색
```

### 3.2 1단계: 넓은 의미 탐색

**목표**: 초기 앵커 포인트 설정을 위한 다양한 의미 영역 탐색

**알고리즘**:
```
입력: 이전 추측 G, 의미 씨앗 S
출력: 다음 단어 w_next

1. 시도한 의미 범주 식별 C_tried = {c | ∃g ∈ G, g ∈ c}
2. 미시도 범주 선택 C_untried = S \ C_tried
3. C_untried ≠ ∅ 이면:
   - 범주 c ∈ C_untried를 임의로 선택
   - c에서 임의의 단어 반환
4. 그렇지 않으면:
   - 파생어 탐색 수행
```

**의미 범주**:
- **추상 개념**: {생각, 마음, 정신, 의식, 감정, 느낌}
- **물리적 객체**: {사물, 물건, 물체, 존재, 실체, 형태}
- **관계**: {관계, 연결, 결합, 만남, 소통, 교류}
- **과정**: {변화, 과정, 발전, 성장, 진행, 흐름}
- **공간**: {공간, 장소, 위치, 지역, 영역, 범위}
- **시간**: {시간, 순간, 시기, 때, 기간, 순서}
- **행동**: {행동, 활동, 움직임, 작업, 노력, 실행}
- **상태**: {상태, 조건, 상황, 환경, 분위기, 기분}

### 3.3 2단계: 의미적 경사 탐색

**목표**: 고성능 앵커 단어를 기반으로 한 의미적 경사 추적

**알고리즘**:
```
입력: 상위 추측 G_top, 유사도 점수 S
출력: 다음 단어 w_next

1. 각 g ∈ G_top에 대해:
   - 의미적 확장 E_g = expand(g) 생성
   - 의미적 연관 A_g = associate(g) 생성
   - 문맥적 관계 R_g = relate(g) 생성
   
2. 후보 결합 C = ∪(E_g ∪ A_g ∪ R_g)
3. 미시도 단어 필터링 C' = C \ tried_words
4. 학습된 효과성 점수로 정렬
5. 최고 점수 후보 반환
```

**의미적 확장 함수**:

1. **어근 기반 확장**: `expand_root(word) = {w ∈ V | w가 word와 어근 공유}`
2. **범주적 확장**: `expand_category(word) = {w ∈ V | w ∈ same_category(word)}`
3. **형태론적 확장**: `expand_morph(word) = {w ∈ V | morphologically_related(w, word)}`

### 3.4 3단계: 집중 의미 탐색

**목표**: 다층 연관을 사용한 고유사도 영역 집중 탐색

**알고리즘**:
```
입력: 최고 추측 g_best, 유사도 임계값 θ
출력: 다음 단어 w_next

1. 공통 의미 영역 식별:
   - 상위 추측들의 의미적 교집합 찾기
   - 영역별 후보 생성
   
2. 다층 연관:
   - 1층: g_best의 직접 연관어
   - 2층: 1층 단어들의 연관어
   - 후보 결합 및 필터링
   
3. 학습된 효과성 점수 적용
4. 최적 후보 반환
```

**공통 의미 영역 감지**:
```python
def find_common_field(words: List[str]) -> List[str]:
    semantic_fields = {
        "정치사회": ["정치", "사회", "국가", "정부", "국민", "시민"],
        "교육학습": ["교육", "학습", "공부", "지식", "학문", "연구"],
        "감정심리": ["감정", "마음", "기분", "느낌", "정서", "심리"],
        "시공간": ["시간", "공간", "장소", "위치", "때", "순간"],
        "행동활동": ["행동", "활동", "움직임", "작업", "실행", "진행"]
    }
    
    for field, field_words in semantic_fields.items():
        if all(word_belongs_to_field(w, field_words) for w in words):
            return [w for w in field_words if w not in words]
    return []
```

### 3.5 4단계: 정밀 의미 탐색

**목표**: 형태론적 분석을 사용한 고유사도 시나리오 세부 조정

**알고리즘**:
```
입력: 최고 추측 g_best, 학습된 단어 쌍 P
출력: 다음 단어 w_next

1. 형태론적 변형:
   - 접두사/접미사 변형 생성
   - 일반적인 한국어 형태론 규칙 적용
   
2. 초근접 단어 감지:
   - similarity_diff < 0.03인 학습 쌍 쿼리
   - 역사적 효과성으로 순위 매기기
   
3. 정밀 후보 선택:
   - 형태론적 및 학습된 후보 결합
   - 세밀한 유사도 추정 적용
   
4. 최고 순위 후보 반환
```

**형태론적 규칙**:
```python
def generate_morphological_variants(word: str) -> List[str]:
    variants = []
    if len(word) > 2:
        root = word[:-1]
        suffixes = ['다', '하다', '되다', '이다', '적', '의', '로', '을', '를']
        variants = [root + suffix for suffix in suffixes]
    return variants
```

## 4. 학습 및 적응 메커니즘

### 4.1 실시간 관계 학습

**목표**: 실제 유사도 차이를 기반으로 한 동적 단어 관계 맵 구축

**알고리즘**:
```python
def learn_word_relationships(word: str, similarity: float):
    for previous_guess in guesses:
        sim_diff = abs(similarity - previous_guess.similarity)
        pair_key = f"{min(word, previous_guess.word)}|{max(word, previous_guess.word)}"
        
        if pair_key not in word_pairs:
            word_pairs[pair_key] = {
                'similarity_diffs': [],
                'co_occurrence_count': 0
            }
        
        word_pairs[pair_key]['similarity_diffs'].append(sim_diff)
        word_pairs[pair_key]['co_occurrence_count'] += 1
        
        # 최근 관찰의 슬라이딩 윈도우 유지
        if len(word_pairs[pair_key]['similarity_diffs']) > 100:
            word_pairs[pair_key]['similarity_diffs'] = 
                word_pairs[pair_key]['similarity_diffs'][-50:]
```

### 4.2 효과성 점수 계산

**목표**: 역사적 성능을 기반으로 한 후보 단어 순위 매기기

**점수 함수**:
```python
def calculate_effectiveness_score(word: str) -> float:
    if word in word_frequency:
        freq_data = word_frequency[word]
        base_score = freq_data['avg_similarity'] * freq_data['count']
        best_bonus = freq_data['best_similarity'] * 0.5
        return base_score + best_bonus
    return 0.0
```

### 4.3 정체 감지

**목표**: 현재 전략이 비효율적임을 식별하고 전략 전환 유발

**알고리즘**:
```python
def detect_stagnation(recent_guesses: List[GuessResult], 
                     best_similarity: float, 
                     window_size: int = 3) -> bool:
    if len(recent_guesses) < window_size:
        return False
    
    recent_max = max(g.similarity for g in recent_guesses[-window_size:])
    improvement_threshold = 0.01
    
    return recent_max <= best_similarity + improvement_threshold
```

## 5. 지식 지속성 및 전이

### 5.1 세션 간 학습

시스템은 두 가지 주요 메커니즘을 통해 게임 세션 간 지속적 지식을 유지한다:

1. **단어 쌍 지식**: 단어 쌍 간 유사도 차이 누적
2. **성공 패턴 인식**: 성공적인 결과로 이어진 전략 및 단어 순서

### 5.2 데이터 지속성 형식

**학습 데이터 구조**:
```json
{
  "games_played": 42,
  "successful_patterns": [
    {
      "answer": "사랑",
      "attempts": 15,
      "key_words": ["감정", "마음", "인간", "관계", "사랑"],
      "timestamp": "2024-01-15T10:30:00"
    }
  ],
  "word_frequency": {
    "사랑": {
      "count": 8,
      "avg_similarity": 0.342,
      "best_similarity": 0.891
    }
  }
}
```

### 5.3 지식 전이 메커니즘

1. **의미적 프라이밍**: 성공적인 단어 순서를 사용하여 향후 탐색 준비
2. **부정적 학습**: 역사적으로 성능이 낮은 단어 조합 회피
3. **적응적 임계값**: 역사적 성공률을 기반으로 한 전략 전환 임계값 조정

## 6. 성능 최적화

### 6.1 웹 자동화 효율성

**파싱 최적화**:
```javascript
// last-input 클래스를 대상으로 한 최적화된 파싱 스크립트
var lastInputRow = table.querySelector('tbody tr.last-input');
if (lastInputRow) {
    var cells = lastInputRow.querySelectorAll('td');
    return {
        word: cells[1].textContent.trim(),
        similarity: cells[2].textContent.trim(),
        rank: cells[3].textContent.trim()
    };
}
```

**타이밍 최적화**:
- 제출 지연: 0.005초
- 파싱 지연: 0.005초
- 단어당 총 오버헤드: ~0.01초

### 6.2 메모리 관리

**슬라이딩 윈도우 접근법**:
```python
def maintain_data_size():
    # 메모리 팽창 방지를 위한 유사도 차이 제한
    if len(similarity_diffs) > 100:
        similarity_diffs = similarity_diffs[-50:]
    
    # 성공 패턴 제한
    if len(successful_patterns) > 100:
        successful_patterns = successful_patterns[-50:]
```

## 7. 실험 분석

### 7.1 성능 지표

1. **수렴률**: 해답 도달까지의 평균 시도 횟수
2. **학습 효율성**: 게임 세션 간 개선율
3. **전략 효과성**: 전략 유형별 성공률
4. **지식 보존**: 학습된 관계의 지속성

### 7.2 이론적 복잡도

**시간 복잡도**: 단어 선택당 O(n log n), 여기서 n은 어휘 크기
**공간 복잡도**: 단어 쌍 저장에 O(k²), 여기서 k는 만난 고유 단어 수

### 7.3 예상 성능 특성

1. **콜드 스타트**: 초기 게임은 30-50회 시도 필요
2. **워밍업 기간**: 10-20게임 후 평균 시도 횟수가 20-30회로 감소
3. **성숙 상태**: 광범위한 학습 후 평균 10-20회 시도 예상

## 8. 모듈 구조

본 프로젝트는 확장성과 유지보수성을 위해 기능별로 모듈화되어 있습니다.

### 8.1 핵심 모듈

#### 📊 models.py - 데이터 구조 모듈
```python
from models import GuessResult, GameSession, WordPairData
```
- **GuessResult**: 추측 결과 데이터 클래스 (단어, 유사도, 순위, 시도번호)
- **WordPairData**: 단어 쌍 간 유사도 차이 데이터 저장
- **SuccessPattern**: 성공한 게임의 패턴 정보 저장
- **WordFrequencyData**: 단어 사용 빈도 및 효과성 통계
- **GameSession**: 현재 게임 세션 상태 관리 (추측 목록, 전략 이력 등)

#### 🧠 strategy_engine.py - 전략 엔진 모듈
```python
from strategy_engine import StrategyEngine, SearchStrategy
```
- **SearchStrategy**: 모든 탐색 전략의 추상 기본 클래스
- **WideSemanticExploration**: 1단계 넓은 의미 탐색 (유사도 < 0.1)
- **SemanticGradientSearch**: 2단계 의미적 경사 탐색 (유사도 < 0.25)
- **FocusedSemanticSearch**: 3단계 집중 의미 탐색 (유사도 < 0.5)
- **PrecisionSemanticSearch**: 4단계 정밀 의미 탐색 (유사도 ≥ 0.5)
- **StrategyEngine**: 상황에 따른 전략 선택 및 실행

#### 📚 learning_engine.py - 학습 엔진 모듈
```python
from learning_engine import LearningEngine
```
- **실시간 관계 학습**: 단어 간 유사도 차이 패턴 학습
- **성공 패턴 인식**: 성공한 게임의 전략 순서 및 핵심 단어 저장
- **효과성 점수 계산**: 단어별 역사적 성능 기반 점수 산출
- **지속적 데이터 저장**: JSON 형식으로 학습 결과 영구 보존
- **전략 분석**: 전략별 효과성 통계 및 최적 패턴 식별

#### 🌐 web_automation.py - 웹 자동화 모듈
```python
from web_automation import WebAutomation, WebAutomationConfig
```
- **WebAutomationConfig**: 브라우저 설정 및 타이밍 구성
- **WebAutomation**: 셀레니움 기반 게임 자동화
- **최적화된 파싱**: `last-input` 클래스 활용한 빠른 결과 추출
- **초고속 처리**: 총 0.01초 대기시간으로 실시간 플레이
- **견고한 오류 처리**: 파싱 실패시 자동 복구 및 단어 제거

#### 🚀 semantic_solver.py - 메인 솔버 모듈
```python
from semantic_solver import SemanticSolver
```
- **SemanticSolver**: 모든 구성요소를 통합한 완전한 솔버
- **게임 실행 로직**: 초기화부터 완료까지 전체 프로세스 관리
- **학습 통계 제공**: 현재 학습 상태 및 성과 분석
- **수동 입력 지원**: 디버깅 및 테스트용 수동 단어 입력
- **추천 시스템**: 현재 상황에 최적화된 후보 단어 제안

### 8.2 사용법

#### 기본 실행
```bash
python semantic_solver.py
```

#### 기존 호환성 (래퍼)
```bash
python simple_solver.py
```

#### 모듈별 사용 예시
```python
# 솔버 초기화 및 실행
from semantic_solver import SemanticSolver
from web_automation import WebAutomationConfig

# 설정 커스터마이징
config = WebAutomationConfig(
    headless=False,  # 브라우저 창 표시
    submit_delay=0.01,  # 더 긴 대기 시간
    window_size=(1600, 900)
)

# 솔버 생성 및 실행
solver = SemanticSolver(web_config=config)
result = solver.solve_game(max_attempts=100)
```

#### 수동 테스트
```python
# 개별 단어 테스트
solver = SemanticSolver()
result = solver.manual_word_input("사랑")
print(f"결과: {result.similarity}")

# 추천 단어 확인
recommendations = solver.get_word_recommendations(5)
print(f"추천: {recommendations}")
```

### 8.3 시스템 요구사항

- **Python 3.8+**
- **Chrome/Chromium 브라우저**
- **ChromeDriver** (PATH에 등록 또는 프로젝트 폴더에 위치)

### 8.4 패키지 설치

```bash
pip install -r requirements.txt
```

필수 패키지:
- `selenium>=4.0.0`: 웹 브라우저 자동화
- `numpy>=1.21.0`: 수치 계산 (기존 호환성)

### 8.5 프로젝트 파일 구조

```
autosemantle/
├── 📊 models.py              # 데이터 구조 및 클래스 정의
├── 🧠 strategy_engine.py     # 4단계 적응형 탐색 전략
├── 📚 learning_engine.py     # 실시간 학습 및 패턴 인식
├── 🌐 web_automation.py      # 셀레니움 기반 웹 자동화
├── 🚀 semantic_solver.py     # 메인 솔버 (모든 모듈 통합)
├── 🔗 simple_solver.py       # 기존 호환성 래퍼
├── 📋 requirements.txt       # 필수 패키지 목록
├── 📖 README.md             # 프로젝트 문서
├── 📝 words.txt             # 한국어 어휘 목록 (170,000+ 단어)
├── 🧠 kkomantle_learning.json # 학습 데이터 (게임 통계, 성공 패턴)
└── 🔗 word_pairs.json       # 단어 쌍 유사도 관계 데이터
```

### 8.6 빠른 시작 가이드

1. **저장소 클론 및 이동**
```bash
git clone https://github.com/needitem/Semantle-finder.git
cd Semantle-finder
```

2. **필수 패키지 설치**
```bash
pip install -r requirements.txt
```

3. **ChromeDriver 설치**
   - [ChromeDriver 다운로드](https://chromedriver.chromium.org/)
   - PATH에 등록하거나 프로젝트 폴더에 위치

4. **솔버 실행**
```bash
python semantic_solver.py
```

### 8.7 설정 옵션

#### 웹 자동화 설정
```python
from web_automation import WebAutomationConfig

config = WebAutomationConfig(
    game_url="https://semantle-ko.newsjel.ly/",
    headless=False,              # 브라우저 창 표시 여부
    window_size=(1200, 800),     # 브라우저 창 크기
    submit_delay=0.005,          # 단어 제출 후 대기 시간
    parse_delay=0.005,           # 결과 파싱 전 대기 시간
    page_load_timeout=30         # 페이지 로드 최대 대기 시간
)
```

#### 전략 임계값 설정
- **넓은 탐색**: 유사도 < 0.1 (다양한 의미 영역 탐색)
- **경사 탐색**: 유사도 < 0.25 (의미적 방향성 추적)
- **집중 탐색**: 유사도 < 0.5 (고유사도 영역 집중)
- **정밀 탐색**: 유사도 ≥ 0.5 (형태론적 미세 조정)

#### 학습 매개변수
- **정체 감지 윈도우**: 최근 3회 시도
- **정체 임계값**: 0.01 (유사도 개선 최소값)
- **단어 쌍 기록 한계**: 100개 (메모리 절약)
- **성공 패턴 보존**: 최대 100개

### 8.3 오류 처리 및 견고성

1. **우아한 성능 저하**: 부분 실패 시에도 시스템 작동 지속
2. **자동 복구**: 실패한 단어는 어휘에서 제거하여 반복 실패 방지
3. **데이터 무결성**: 지속적 저장을 위한 오류 처리가 포함된 JSON 직렬화

## 9. 향후 개선사항

### 9.1 고급 학습 메커니즘

1. **의미적 임베딩**: 사전 훈련된 한국어 언어 모델과의 통합
2. **강화학습**: 전략 선택 최적화를 위한 Q-learning
3. **전이 학습**: 다른 단어 게임 간 도메인 간 지식 전이

### 9.2 성능 개선

1. **병렬 처리**: 동시 후보 평가
2. **캐싱**: 비용이 많이 드는 의미적 연산의 메모화
3. **배치 학습**: 관계 학습을 위한 효율적인 배치 업데이트

### 9.3 분석 및 모니터링

1. **성능 대시보드**: 학습 진행 상황의 실시간 시각화
2. **전략 분석**: 전략 효과성의 상세 분석
3. **의미적 시각화**: 학습된 단어 관계의 그래프 기반 표현

## 10. 결론

적응형 의미 탐색 솔버는 동적 학습과 다단계 적응형 탐색을 통해 한국어 꼬맨틀을 해결하는 새로운 접근법을 제시한다. 실시간 관계 학습과 전략적 탐색 알고리즘을 결합함으로써, 시스템은 사전 훈련된 지식에만 의존하지 않고 경험을 통해 개선되는 지능형 게임 플레이 에이전트의 잠재력을 보여준다.

세션 간 지식을 지속하고 성능 피드백을 기반으로 전략을 적응시키는 시스템의 능력은 해답 공간이 크고 동적인 개방형 문제 영역에 특히 적합하다. 모듈식 아키텍처는 다양한 단어 추측 게임 변형에 대한 쉬운 확장 및 사용자 정의를 허용한다.

## 참고문헌

1. 자연어 처리에서의 의미적 유사성
2. 인공지능의 적응형 탐색 알고리즘
3. 게임 플레이를 위한 강화학습
4. 한국어 처리 및 형태론적 분석
5. 웹 자동화 및 실시간 데이터 처리

---

**키워드**: 의미적 탐색, 적응형 알고리즘, 한국어 자연어처리, 게임 AI, 기계학습, 웹 자동화

**소스 코드**: `/mnt/c/Users/th072/Desktop/autosemantle/simple_solver.py`에서 확인 가능

**데이터 파일**: 
- `kkomantle_learning.json` - 학습 데이터 및 성공 패턴
- `word_pairs.json` - 단어 관계 매핑
- `words.txt` - 한국어 어휘 말뭉치