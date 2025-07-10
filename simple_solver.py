#!/usr/bin/env python3
"""
의미 기반 지능형 꼬맨틀 솔버
실제 유사도를 학습하여 의미적 관계를 활용한 정답 탐색
"""

import time
import random
import numpy as np
import pickle
import os
import json
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass
from datetime import datetime

# --- User Configuration ---
# 필수 라이브러리: selenium, numpy
# pip install selenium numpy
# --------------------------

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
except ImportError as e:
    print(f"[오류] 필수 라이브러리가 설치되지 않았습니다: {e}")
    print("솔버를 실행하기 전에 `pip install selenium numpy` 명령어를 실행해주세요.")
    exit()

@dataclass
class GuessResult:
    word: str
    similarity: float
    rank: str = ""
    attempt: int = 0

class SemanticSolver:
    """의미 기반 지능형 꼬맨틀 솔버"""
    
    LEARNING_DATA_FILE = 'kkomantle_learning.json'
    WORD_PAIRS_FILE = 'word_pairs.json'

    def __init__(self):
        self.driver = None
        self.guesses: List[GuessResult] = []
        self.tried_words = set()
        
        self.vocab = self._load_korean_vocab_words()
        
        # 지속적 학습 데이터 로드
        self.learning_data = self._load_learning_data()
        self.word_pairs = self._load_word_pairs()
        
        # 현재 세션 데이터
        self.session_relationships = {}
        self.session_start = datetime.now()
        
        self.setup_driver()
        print(f"🧠 기존 학습 데이터: {len(self.word_pairs)}개 단어 쌍, {len(self.learning_data.get('successful_patterns', []))}개 성공 패턴")

    def _load_korean_vocab_words(self) -> List[str]:
        """words.txt에서 단어 목록을 로드합니다."""
        try:
            with open('words.txt', 'r', encoding='utf-8') as f:
                words = sorted(list(set(
                    line.strip()
                    for line in f
                    if line.strip() and not line.strip().startswith('[')
                )))
            print(f"✅ words.txt 기반 {len(words)}개 고유 단어 로드 완료")
            if not words:
                raise FileNotFoundError
            return words
        except FileNotFoundError:
            print("⚠️ words.txt를 찾을 수 없거나 비어있습니다. 기본 단어 목록을 사용합니다.")
            return ["사랑", "시간", "사람", "생각", "마음", "세상", "문제", "사회"]

    def _load_learning_data(self) -> Dict:
        """지속적 학습 데이터 로드"""
        if os.path.exists(self.LEARNING_DATA_FILE):
            try:
                with open(self.LEARNING_DATA_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ 학습 데이터 로드 실패: {e}")
        
        return {
            'games_played': 0,
            'successful_patterns': [],
            'category_effectiveness': {},
            'word_frequency': {},
            'best_strategies': []
        }
    
    def _load_word_pairs(self) -> Dict[str, Dict[str, float]]:
        """단어 쌍 유사도 데이터 로드"""
        if os.path.exists(self.WORD_PAIRS_FILE):
            try:
                with open(self.WORD_PAIRS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ 단어 쌍 데이터 로드 실패: {e}")
        return {}
    
    def _save_learning_data(self):
        """학습 데이터 저장"""
        try:
            with open(self.LEARNING_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.learning_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ 학습 데이터 저장 실패: {e}")
    
    def _save_word_pairs(self):
        """단어 쌍 데이터 저장"""
        try:
            with open(self.WORD_PAIRS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.word_pairs, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ 단어 쌍 데이터 저장 실패: {e}")

    def setup_driver(self):
        """브라우저 설정"""
        chrome_options = Options()
        # Headless 모드를 비활성화하려면 아래 줄을 주석 처리하세요. 
        # chrome_options.add_argument("--headless") 
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1200,800")
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            print("✅ 브라우저 설정 완료")
        except Exception as e:
            print(f"❌ 브라우저 설정 실패: {e}")
            raise

    def select_next_word(self) -> str:
        """의미 기반 지능형 단어 선택"""
        if not self.guesses:
            # 초기 의미적으로 다양한 단어들 (균형적 탐색)
            initial_words = ["사람", "시간", "사랑", "자연", "음식", "기술", "감정", "장소", "행동", "생각"]
            available_initial = [w for w in initial_words if w in self.vocab and w not in self.tried_words]
            return random.choice(available_initial) if available_initial else self.vocab[0]

        # 최고 유사도와 진행 상황 분석
        best_similarity = max(g.similarity for g in self.guesses)
        
        # 정체 상태 감지 (최근 3번 시도에서 개선이 없음)
        recent_attempts = self.guesses[-3:] if len(self.guesses) >= 3 else self.guesses
        recent_max = max(g.similarity for g in recent_attempts) if recent_attempts else 0
        is_stuck = len(self.guesses) >= 3 and recent_max <= best_similarity + 0.01
        
        # 지능형 탐색 전략 결정
        if best_similarity < 0.1:
            return self._wide_semantic_exploration()
        elif best_similarity < 0.25 or is_stuck:
            if is_stuck:
                print("   ⚠️ 정체 상태 - 의미 공간 확장 탐색")
            return self._semantic_gradient_search()
        elif best_similarity < 0.5:
            return self._focused_semantic_search()
        else:
            return self._precision_semantic_search()

    def _wide_semantic_exploration(self) -> str:
        """넓은 의미 공간 탐색"""
        print("   🌐 넓은 의미 공간 탐색")
        
        # 의미적으로 서로 다른 핵심 개념들
        semantic_seeds = [
            # 추상 개념
            ["생각", "마음", "정신", "의식", "감정", "느낌"],
            # 물리적 존재
            ["사물", "물건", "물체", "존재", "실체", "형태"],
            # 관계와 연결
            ["관계", "연결", "결합", "만남", "소통", "교류"],
            # 변화와 과정
            ["변화", "과정", "발전", "성장", "진행", "흐름"],
            # 공간과 위치
            ["공간", "장소", "위치", "지역", "영역", "범위"],
            # 시간과 순서
            ["시간", "순간", "시기", "때", "기간", "순서"],
            # 행동과 활동
            ["행동", "활동", "움직임", "작업", "노력", "실행"],
            # 상태와 조건
            ["상태", "조건", "상황", "환경", "분위기", "기분"]
        ]
        
        # 이미 시도한 단어들과 의미적으로 다른 영역 선택
        tried_concepts = set()
        for guess in self.guesses:
            for i, concept_group in enumerate(semantic_seeds):
                if guess.word in concept_group:
                    tried_concepts.add(i)
        
        # 시도하지 않은 의미 영역에서 선택
        untried_concepts = [i for i in range(len(semantic_seeds)) if i not in tried_concepts]
        
        if untried_concepts:
            concept_idx = random.choice(untried_concepts)
            concept_words = [w for w in semantic_seeds[concept_idx] 
                           if w in self.vocab and w not in self.tried_words]
            if concept_words:
                next_word = random.choice(concept_words)
                print(f"   🎯 새로운 의미 영역 탐색: '{next_word}'")
                return next_word
        
        # 모든 핵심 개념을 시도했다면, 파생어 탐색
        return self._explore_word_derivatives()
    
    def _explore_word_derivatives(self) -> str:
        """기존 단어들의 파생어 탐색"""
        derivatives = []
        
        for guess in self.guesses:
            word = guess.word
            # 어근 기반 파생어
            if len(word) > 1:
                root = word[:-1]
                for vocab_word in self.vocab:
                    if (vocab_word.startswith(root) and vocab_word != word and 
                        vocab_word not in self.tried_words and len(vocab_word) <= len(word) + 2):
                        derivatives.append((vocab_word, abs(guess.similarity - 0.1)))  # 예상 유사도 차이
        
        if derivatives:
            # 유사도가 높을 것으로 예상되는 순으로 정렬
            derivatives.sort(key=lambda x: x[1])
            next_word = derivatives[0][0]
            print(f"   🎯 파생어 탐색: '{next_word}'")
            return next_word
        
        # 파생어가 없으면 랜덤
        available_words = [w for w in self.vocab if w not in self.tried_words]
        return random.choice(available_words) if available_words else "포기"

    def _semantic_gradient_search(self) -> str:
        """의미적 경사 상승법 탐색"""
        print("   📈 의미적 경사 탐색")
        
        # 상위 유사도 단어들로 방향성 찾기
        top_guesses = sorted(self.guesses, key=lambda g: g.similarity, reverse=True)[:3]
        
        # 여러 방향 동시 탐색
        search_directions = []
        
        for guess in top_guesses:
            # 1. 의미적 확장 (상위어, 하위어)
            search_directions.extend(self._get_semantic_expansions(guess.word))
            
            # 2. 연관어 탐색 (동의어, 유의어)
            search_directions.extend(self._get_semantic_associations(guess.word))
            
            # 3. 문맥적 관련어
            search_directions.extend(self._get_contextual_relations(guess.word))
        
        # 중복 제거 및 미시도 단어만
        candidates = list(set(search_directions) - self.tried_words)
        candidates = [w for w in candidates if w in self.vocab]
        
        if candidates:
            # 학습된 효과성으로 정렬
            candidates = self._sort_by_learned_effectiveness("", candidates)
            next_word = candidates[0] if candidates else random.choice(candidates)
            print(f"   🎯 의미적 방향 탐색: '{next_word}'")
            return next_word
        
        # 후보가 없으면 넓은 탐색으로 전환
        return self._wide_semantic_exploration()
    
    def _get_semantic_expansions(self, word: str) -> List[str]:
        """의미적 확장어 생성"""
        expansions = []
        
        # 어근 기반 확장
        if len(word) > 2:
            root = word[:2]  # 앞 2글자 어근
            for vocab_word in self.vocab:
                if vocab_word.startswith(root) and vocab_word != word:
                    expansions.append(vocab_word)
        
        # 의미 영역별 확장
        semantic_expansions = {
            "사람": ["인간", "개인", "타인", "누군가", "사람들", "인물", "인사"],
            "시간": ["때", "순간", "시기", "시절", "기간", "시점", "시대"],
            "장소": ["곳", "지역", "위치", "공간", "영역", "범위", "영토"],
            "방법": ["수단", "방식", "기법", "절차", "과정", "단계"],
            "상태": ["조건", "상황", "환경", "분위기", "느낌", "기분"],
            "행동": ["활동", "움직임", "작업", "행위", "실행", "진행"]
        }
        
        for category, words in semantic_expansions.items():
            if word in words:
                expansions.extend([w for w in words if w != word])
        
        return expansions[:10]
    
    def _get_semantic_associations(self, word: str) -> List[str]:
        """의미적 연관어 생성"""
        associations = []
        
        # 학습된 연관어 우선
        learned_assocs = self._get_learned_related_words(word)
        associations.extend(learned_assocs)
        
        # 언어학적 연관어
        linguistic_associations = {
            # 동의어/유의어 그룹
            "문제": ["과제", "쟁점", "이슈", "고민", "걱정", "난제"],
            "해결": ["처리", "해답", "방안", "대안", "극복", "완료"],
            "중요": ["핵심", "주요", "필수", "기본", "근본", "본질"],
            "변화": ["전환", "개선", "발전", "진보", "성장", "혁신"],
            "관계": ["연결", "결합", "소통", "교류", "상호작용", "협력"]
        }
        
        for key, words in linguistic_associations.items():
            if word == key or word in words:
                associations.extend([w for w in words if w != word])
        
        return associations[:8]
    
    def _get_contextual_relations(self, word: str) -> List[str]:
        """문맥적 관련어 생성"""
        relations = []
        
        # 문맥별 관련어 매핑
        contextual_maps = {
            # 사회/정치 문맥
            "사회": ["정치", "경제", "문화", "교육", "복지", "제도"],
            "국민": ["시민", "주민", "인민", "국가", "정부", "공동체"],
            
            # 교육/학습 문맥  
            "학습": ["교육", "공부", "연구", "지식", "이해", "습득"],
            "지식": ["정보", "학문", "경험", "기술", "능력", "실력"],
            
            # 감정/심리 문맥
            "감정": ["마음", "기분", "느낌", "정서", "심리", "의식"],
            "행복": ["기쁨", "만족", "즐거움", "웃음", "평화", "사랑"]
        }
        
        for key, words in contextual_maps.items():
            if word == key or word in words:
                relations.extend([w for w in words if w != word])
        
        return relations[:6]

    def _focused_semantic_search(self) -> str:
        """집중적 의미 탐색"""
        print("   🎯 집중 의미 탐색")
        
        # 상위 유사도 단어들 분석
        top_guesses = sorted(self.guesses, key=lambda g: g.similarity, reverse=True)[:2]
        
        # 고유사도 단어들의 공통 의미 영역 찾기
        common_semantic_field = self._find_common_semantic_field([g.word for g in top_guesses])
        
        if common_semantic_field:
            candidates = [w for w in common_semantic_field 
                         if w in self.vocab and w not in self.tried_words]
            if candidates:
                next_word = candidates[0]
                print(f"   🎯 공통 의미 영역: '{next_word}'")
                return next_word
        
        # 최고 단어 주변 집중 탐색
        best_guess = max(self.guesses, key=lambda g: g.similarity)
        
        # 다층적 연관어 탐색
        layer1 = self._get_semantic_associations(best_guess.word)
        layer2 = []
        for word in layer1[:3]:
            if word not in self.tried_words:
                layer2.extend(self._get_semantic_associations(word))
        
        all_candidates = layer1 + layer2
        candidates = [w for w in set(all_candidates) 
                     if w in self.vocab and w not in self.tried_words]
        
        if candidates:
            # 학습된 효과성으로 정렬
            candidates = self._sort_by_learned_effectiveness(best_guess.word, candidates)
            next_word = candidates[0]
            print(f"   🎯 '{best_guess.word}' 다층 연관어: '{next_word}'")
            return next_word
        
        return self._semantic_gradient_search()
    
    def _precision_semantic_search(self) -> str:
        """정밀 의미 탐색 (고유사도 상황)"""
        print("   🔬 정밀 의미 탐색")
        
        best_guess = max(self.guesses, key=lambda g: g.similarity)
        
        # 미세한 의미 차이 탐색
        precision_candidates = []
        
        # 1. 접두사/접미사 변형
        word = best_guess.word
        morphological_variants = []
        
        if len(word) > 2:
            # 접미사 변형
            root = word[:-1]
            for suffix in ['다', '하다', '되다', '이다', '적', '의', '로', '을', '를']:
                variant = root + suffix
                if variant in self.vocab and variant not in self.tried_words:
                    morphological_variants.append(variant)
        
        precision_candidates.extend(morphological_variants[:3])
        
        # 2. 학습된 초근접 단어들
        ultra_close_words = []
        for pair_key, pair_data in self.word_pairs.items():
            word1, word2 = pair_key.split('|')
            
            if (word1 == word or word2 == word):
                other_word = word2 if word1 == word else word1
                if other_word in self.vocab and other_word not in self.tried_words:
                    avg_diff = sum(pair_data['similarity_diffs']) / len(pair_data['similarity_diffs'])
                    if avg_diff < 0.03:  # 매우 유사한 단어들만
                        ultra_close_words.append((other_word, avg_diff))
        
        # 유사도 차이 순으로 정렬
        ultra_close_words.sort(key=lambda x: x[1])
        precision_candidates.extend([w[0] for w in ultra_close_words[:2]])
        
        if precision_candidates:
            next_word = precision_candidates[0]
            print(f"   🎯 '{word}' 정밀 변형: '{next_word}'")
            return next_word
        
        # 정밀 탐색 실패 시 집중 탐색으로 복귀
        return self._focused_semantic_search()
    
    def _find_common_semantic_field(self, words: List[str]) -> List[str]:
        """단어들의 공통 의미 영역 찾기"""
        if len(words) < 2:
            return []
        
        # 의미 영역별 단어 그룹
        semantic_fields = {
            "정치사회": ["정치", "사회", "국가", "정부", "국민", "시민", "공동체", "사회적", "정책", "제도"],
            "교육학습": ["교육", "학습", "공부", "지식", "학문", "연구", "이해", "습득", "경험"],
            "감정심리": ["감정", "마음", "기분", "느낌", "정서", "심리", "사랑", "행복", "슬픔"],
            "시공간": ["시간", "공간", "장소", "위치", "때", "순간", "지역", "영역", "범위"],
            "행동활동": ["행동", "활동", "움직임", "작업", "실행", "진행", "과정", "방법"]
        }
        
        for field_name, field_words in semantic_fields.items():
            if all(any(word in field_words or word.startswith(fw[:2]) for fw in field_words) for word in words):
                return [w for w in field_words if w not in words]
        
        return []

    def _get_learned_related_words(self, word: str) -> List[str]:
        """학습된 데이터에서 관련어 찾기"""
        candidates = []
        
        for pair_key, pair_data in self.word_pairs.items():
            word1, word2 = pair_key.split('|')
            
            if word1 == word and word2 in self.vocab and word2 not in self.tried_words:
                # 유사도 차이가 작을수록 관련성 높음
                avg_diff = sum(pair_data['similarity_diffs']) / len(pair_data['similarity_diffs'])
                if avg_diff < 0.1:  # 유사도 차이가 0.1 미만인 경우만
                    candidates.append(word2)
            elif word2 == word and word1 in self.vocab and word1 not in self.tried_words:
                avg_diff = sum(pair_data['similarity_diffs']) / len(pair_data['similarity_diffs'])
                if avg_diff < 0.1:
                    candidates.append(word1)
        
        return candidates
    
    def _sort_by_learned_effectiveness(self, base_word: str, candidates: List[str]) -> List[str]:
        """학습된 효과성에 따라 후보 단어들 정렬"""
        def get_effectiveness_score(candidate: str) -> float:
            # 단어 빈도 기반 점수
            if candidate in self.learning_data.get('word_frequency', {}):
                freq_data = self.learning_data['word_frequency'][candidate]
                return freq_data.get('avg_similarity', 0) * freq_data.get('count', 1)
            return 0
        
        candidates.sort(key=get_effectiveness_score, reverse=True)
        return candidates

    def _remove_word_from_vocab(self, word: str):
        """실패한 단어를 어휘에서 제거"""
        if word in self.vocab:
            self.vocab.remove(word)
            self.tried_words.add(word)
            print(f"  ⚠️ 단어 '{word}' 어휘에서 영구 제거")

    def navigate_to_game(self) -> bool:
        try: self.driver.get("https://semantle-ko.newsjel.ly/"); time.sleep(1); return True
        except Exception: return False

    def submit_word(self, word: str) -> bool:
        try:
            self.driver.execute_script(f"document.getElementById('guess_input').value = '{word}'; document.querySelector('.input-wrapper button').click();")
            time.sleep(0.005)  # 초극소 대기
            return True
        except Exception: return False

    def parse_result(self, word: str, attempt: int) -> GuessResult:
        # 초극소 대기 시간
        time.sleep(0.005)
        
        # 단일 시도로 빠르게 처리
        try:
            # 테이블 존재 확인
            table_exists = self.driver.execute_script("return document.getElementById('guesses_table') !== null;")
            if not table_exists:
                print(f"  - 테이블을 찾을 수 없음 - 단어 '{word}' 제거")
                self._remove_word_from_vocab(word)
                return None

            # last-input 클래스 행에서 최신 입력 찾기
            script = f"""
            var table = document.getElementById('guesses_table');
            if (!table) return null;

            // last-input 클래스가 있는 행 찾기 (최신 입력)
            var lastInputRow = table.querySelector('tbody tr.last-input');
            if (lastInputRow) {{
                var cells = lastInputRow.querySelectorAll('td');
                if (cells.length >= 4) {{
                    var cellWord = cells[1] ? cells[1].textContent.trim() : '';
                    console.log('last-input 행 단어:', cellWord, '찾는 단어:', '{word}');
                    
                    if (cellWord === '{word}') {{
                        var similarity = cells[2] ? cells[2].textContent.trim() : '';
                        var rank = cells[3] ? cells[3].textContent.trim() : '1000위 이상';
                        console.log('찾음! 유사도:', similarity, '순위:', rank);
                        
                        return {{
                            word: cellWord,
                            similarity: similarity,
                            rank: rank
                        }};
                    }}
                }}
            }}
            
            // last-input이 없으면 전체 테이블에서 검색
            var rows = table.querySelectorAll('tbody tr:not(.delimiter)');
            for (var i = rows.length - 1; i >= 0; i--) {{
                var cells = rows[i].querySelectorAll('td');
                if (cells.length >= 4) {{
                    var cellWord = cells[1] ? cells[1].textContent.trim() : '';
                    if (cellWord === '{word}') {{
                        var similarity = cells[2] ? cells[2].textContent.trim() : '';
                        var rank = cells[3] ? cells[3].textContent.trim() : '1000위 이상';
                        return {{
                            word: cellWord,
                            similarity: similarity,
                            rank: rank
                        }};
                    }}
                }}
            }}
            return null;
            """

            result = self.driver.execute_script(script)
            if result:
                sim_text = result['similarity'].strip()
                
                # 빠른 여러 형태의 유사도 값 처리
                if '%' in sim_text:
                    similarity = float(sim_text.replace('%', '')) / 100.0
                elif sim_text.replace('.', '').replace('-', '').isdigit():
                    sim_value = float(sim_text)
                    similarity = sim_value / 100.0 if sim_value > 1.0 else sim_value
                else:
                    similarity = 0.0
                
                guess = GuessResult(word, similarity, result['rank'], attempt)
                self.guesses.append(guess)
                self.guesses.sort(key=lambda g: g.similarity, reverse=True)
                self.tried_words.add(word)
                
                # 단어 관계 학습 업데이트
                self._learn_word_relationships(word, similarity)
                
                return guess
            else:
                print(f"  - 단어 '{word}' 결과 찾을 수 없음 - 단어 제거")
                self._remove_word_from_vocab(word)
                return None
        except Exception as e:
            print(f"  - 파싱 오류: {e} - 단어 '{word}' 제거")
            self._remove_word_from_vocab(word)
            return None

    def _learn_word_relationships(self, word: str, similarity: float):
        """단어 간 유사도 관계를 학습 (지속적 + 세션)"""
        # 현재 세션 데이터 업데이트
        if word not in self.session_relationships:
            self.session_relationships[word] = []
        
        # 이미 시도한 단어들과의 관계 업데이트
        for guess in self.guesses:
            if guess.word != word:
                similarity_diff = abs(similarity - guess.similarity)
                self.session_relationships[word].append((guess.word, similarity_diff))
                
                # 지속적 데이터에도 저장 (양방향)
                pair_key = f"{min(word, guess.word)}|{max(word, guess.word)}"
                if pair_key not in self.word_pairs:
                    self.word_pairs[pair_key] = {
                        'similarity_diffs': [],
                        'co_occurrence_count': 0
                    }
                
                self.word_pairs[pair_key]['similarity_diffs'].append(similarity_diff)
                self.word_pairs[pair_key]['co_occurrence_count'] += 1
                
                # 최대 100개 기록만 유지
                if len(self.word_pairs[pair_key]['similarity_diffs']) > 100:
                    self.word_pairs[pair_key]['similarity_diffs'] = self.word_pairs[pair_key]['similarity_diffs'][-50:]
        
        # 단어 빈도 업데이트
        if 'word_frequency' not in self.learning_data:
            self.learning_data['word_frequency'] = {}
        
        if word not in self.learning_data['word_frequency']:
            self.learning_data['word_frequency'][word] = {'count': 0, 'avg_similarity': 0, 'best_similarity': 0}
        
        freq_data = self.learning_data['word_frequency'][word]
        freq_data['count'] += 1
        freq_data['avg_similarity'] = (freq_data['avg_similarity'] * (freq_data['count'] - 1) + similarity) / freq_data['count']
        freq_data['best_similarity'] = max(freq_data['best_similarity'], similarity)

    def solve(self):
        if not self.navigate_to_game(): return
        print("\n" + "="*50)
        print("🎯 실제 유사도 학습 기반 의미적 솔버 시작")
        print(f"📚 단어 풀: {len(self.vocab)}개")
        print("="*50 + "\n")
        
        start_time = time.time()
        failed_words = set()  # 파싱 실패한 단어들 추적
        
        for attempt in range(1, 501):
            word = self.select_next_word()
            if word == "포기": print("⚠️ 모든 단어를 시도하여 더 이상 추측할 수 없습니다."); break

            # 이미 실패한 단어는 스킵
            if word in failed_words:
                print(f"⚠️ 단어 '{word}' 이미 파싱 실패로 스킵됨. 다른 단어 선택...")
                self.tried_words.add(word)  # 시도 목록에 추가하여 다시 선택되지 않도록
                continue

            print(f"🎯 시도 {attempt}: '{word}'")
            if not self.submit_word(word):
                print("❌ 제출 실패. 3초 후 재시도..."); time.sleep(3); continue

            result = self.parse_result(word, attempt)
            if not result:
                print(f"❌ 단어 '{word}' 처리 실패 - 어휘에서 제거됨")
                continue

            print(f"   📊 결과: 유사도 {result.similarity:.4f} | 순위: {result.rank}")
            if result.similarity == 1.0:
                print(f"\n🎉 정답! '{word}' (시도: {attempt}, 소요시간: {time.time() - start_time:.1f}초)")
                self._save_session_results(success=True, final_answer=word)
                return word
        print("솔버가 500회 시도 후 정답을 찾지 못했습니다.")

    def _save_session_results(self, success: bool = False, final_answer: str = None):
        """세션 결과 저장 및 학습 데이터 업데이트"""
        # 게임 횟수 업데이트
        self.learning_data['games_played'] += 1
        
        # 성공 패턴 저장
        if success and final_answer:
            session_pattern = {
                'answer': final_answer,
                'attempts': len(self.guesses),
                'strategy_sequence': [],  # 사용한 전략 순서
                'key_words': [g.word for g in sorted(self.guesses, key=lambda x: x.similarity, reverse=True)[:5]],
                'timestamp': datetime.now().isoformat()
            }
            
            if 'successful_patterns' not in self.learning_data:
                self.learning_data['successful_patterns'] = []
            
            self.learning_data['successful_patterns'].append(session_pattern)
            
            # 최대 100개 성공 패턴만 유지
            if len(self.learning_data['successful_patterns']) > 100:
                self.learning_data['successful_patterns'] = self.learning_data['successful_patterns'][-50:]
        
        # 데이터 저장
        self._save_learning_data()
        self._save_word_pairs()
        
        print(f"💾 학습 데이터 업데이트 완료 (total games: {self.learning_data['games_played']})")
    
    def cleanup(self):
        # 브라우저는 종료하지 않음 (사용자 요청)
        # if self.driver: 
        #     self.driver.quit()
        # 세션 종료 시 데이터 저장
        self._save_session_results()

def main():
    print("🚀 의미 기반 지능형 꼬맨틀 솔버")
    solver = None
    try:
        solver = SemanticSolver()
        solver.solve()
    except (KeyboardInterrupt, SystemExit):
        print("\n\n사용자에 의해 중단됨")
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류 발생: {e}")
    finally:
        if solver: solver.cleanup()
        print("\n프로그램을 종료합니다.")

if __name__ == "__main__":
    main()