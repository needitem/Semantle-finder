#!/usr/bin/env python3
"""
전략 엔진 모듈
4단계 적응형 탐색 전략을 구현하는 모듈입니다.
"""

import random
import math
from typing import List, Dict, Set, Optional, Tuple
from abc import ABC, abstractmethod
from collections import defaultdict

from .models import GuessResult, GameSession
from .strategy_logger import StrategyLogger


class SearchStrategy(ABC):
    """
    탐색 전략의 추상 기본 클래스
    모든 구체적인 전략들이 상속받아야 하는 인터페이스를 정의합니다.
    """
    
    @abstractmethod
    def select_word(self, session: GameSession, vocab: List[str], 
                   learned_data: Dict) -> Optional[str]:
        """
        전략에 따라 다음 단어를 선택합니다.
        
        Args:
            session (GameSession): 현재 게임 세션
            vocab (List[str]): 사용 가능한 어휘 목록
            learned_data (Dict): 학습된 데이터
            
        Returns:
            Optional[str]: 선택된 단어 (없으면 None)
        """
        pass
    
    @abstractmethod
    def get_strategy_name(self) -> str:
        """전략 이름을 반환합니다."""
        pass


class WideSemanticExploration(SearchStrategy):
    """
    1단계: 넓은 의미 탐색 전략
    다양한 의미 영역을 탐색하여 초기 앵커 포인트를 설정합니다.
    """
    
    def __init__(self):
        """의미 범주들을 초기화합니다."""
        # 8개의 핵심 의미 범주 정의
        self.semantic_categories = {
            "추상개념": ["생각", "마음", "정신", "의식", "감정", "느낌"],
            "물리객체": ["사물", "물건", "물체", "존재", "실체", "형태"],
            "관계연결": ["관계", "연결", "결합", "만남", "소통", "교류"],
            "변화과정": ["변화", "과정", "발전", "성장", "진행", "흐름"],
            "공간위치": ["공간", "장소", "위치", "지역", "영역", "범위"],
            "시간순서": ["시간", "순간", "시기", "때", "기간", "순서"],
            "행동활동": ["행동", "활동", "움직임", "작업", "노력", "실행"],
            "상태조건": ["상태", "조건", "상황", "환경", "분위기", "기분"]
        }
    
    def select_word(self, session: GameSession, vocab: List[str], 
                   learned_data: Dict) -> Optional[str]:
        """
        다양한 의미 영역에서 아직 시도하지 않은 단어를 선택합니다.
        
        Args:
            session (GameSession): 현재 게임 세션
            vocab (List[str]): 사용 가능한 어휘 목록
            learned_data (Dict): 학습된 데이터
            
        Returns:
            Optional[str]: 선택된 단어
        """
        # 첫 번째 시도인 경우 학습 데이터 기반 초기 단어 선택
        if not session.guesses:
            return self._select_initial_word(vocab, learned_data, session.tried_words)
        
        # 이미 시도한 의미 범주들 식별
        tried_categories = self._identify_tried_categories(session.guesses)
        
        # 먼저 학습 데이터 기반 후보 확인
        learning_candidates = self._get_learning_based_candidates(vocab, learned_data, session.tried_words, 5)
        if learning_candidates:
            selected_word = learning_candidates[0]
            print(f"   🎯 학습 기반 선택: '{selected_word}'")
            return selected_word
        
        # 아직 시도하지 않은 범주에서 단어 선택
        untried_categories = [cat for cat in self.semantic_categories.keys() 
                            if cat not in tried_categories]
        
        if untried_categories:
            # 새로운 범주에서 랜덤 선택
            selected_category = random.choice(untried_categories)
            category_words = [w for w in self.semantic_categories[selected_category]
                            if w in vocab and w not in session.tried_words]
            
            if category_words:
                selected_word = random.choice(category_words)
                print(f"   🎯 새로운 의미 영역 '{selected_category}': '{selected_word}'")
                return selected_word
        
        # 모든 범주를 시도했다면 파생어 탐색
        return self._explore_derivatives(session, vocab)
    
    def _identify_tried_categories(self, guesses: List[GuessResult]) -> Set[str]:
        """
        이미 시도한 의미 범주들을 식별합니다.
        
        Args:
            guesses (List[GuessResult]): 지금까지의 추측들
            
        Returns:
            Set[str]: 시도한 범주들의 집합
        """
        tried_categories = set()
        
        for guess in guesses:
            for category_name, category_words in self.semantic_categories.items():
                if guess.word in category_words:
                    tried_categories.add(category_name)
        
        return tried_categories
    
    def _select_initial_word(self, vocab: List[str], learned_data: Dict, 
                           tried_words: Set[str]) -> Optional[str]:
        """
        학습 데이터를 기반으로 효과적인 초기 단어를 선택합니다.
        
        Args:
            vocab (List[str]): 사용 가능한 어휘 목록
            learned_data (Dict): 학습된 데이터
            tried_words (Set[str]): 이미 시도한 단어들
            
        Returns:
            Optional[str]: 선택된 초기 단어
        """
        word_frequency = learned_data.get('word_frequency', {})
        
        # 초기 단어 후보들에 점수 부여 (로그 분석 결과 반영)
        initial_candidates = []
        # 고영향 단어들을 우선 추가
        high_impact_words = ["사례", "실패", "기원", "방법", "기업", "사업", "공부", "기술", "방안", "사랑"]
        # 기존 효과적인 단어들
        effective_words = ["사람", "순서", "공간", "지역", "영역", "과정", "절차", "수단"]
        # 일반 탐색 단어들
        general_words = ["시간", "자연", "음식", "감정", "장소", "행동", "생각", "문제", "세상", 
                        "사회", "교육", "정치", "경제", "문화", "과학", "예술", "건강"]
        
        # 모든 단어를 우선순위에 따라 결합
        initial_words = high_impact_words + effective_words + general_words
        
        for word in initial_words:
            if word in vocab and word not in tried_words:
                score = 0
                
                # 1. 학습된 평균 유사도
                if word in word_frequency:
                    freq_data = word_frequency[word]
                    avg_sim = freq_data.get('avg_similarity', 0)
                    count = freq_data.get('count', 0)
                    
                    # 자주 사용되고 평균 유사도가 높은 단어 선호
                    score = avg_sim * math.log(count + 1) * 10
                else:
                    # 새로운 단어도 탐색 가치 부여
                    score = 0.5
                
                # 2. 고영향 단어 보너스
                if word in high_impact_words:
                    score += 50  # 고영향 단어에 큰 보너스
                elif word in effective_words:
                    score += 20  # 효과적인 단어에 중간 보너스
                
                initial_candidates.append((word, score))
        
        if initial_candidates:
            # 점수순 정렬하되 상위 3개 중 확률적 선택 (다양성 유지)
            initial_candidates.sort(key=lambda x: x[1], reverse=True)
            top_candidates = initial_candidates[:3]
            
            # 가중치 기반 확률적 선택
            total_score = sum(c[1] for c in top_candidates)
            if total_score > 0:
                probabilities = [c[1] / total_score for c in top_candidates]
                selected_idx = random.choices(range(len(top_candidates)), weights=probabilities)[0]
                return top_candidates[selected_idx][0]
            else:
                return top_candidates[0][0]
        
        # 후보가 없으면 어휘에서 랜덤 선택
        available = [w for w in vocab if w not in tried_words]
        return random.choice(available) if available else None
    
    def _explore_derivatives(self, session: GameSession, vocab: List[str]) -> Optional[str]:
        """
        기존 단어들의 파생어를 탐색합니다.
        
        Args:
            session (GameSession): 현재 게임 세션
            vocab (List[str]): 사용 가능한 어휘 목록
            
        Returns:
            Optional[str]: 선택된 파생어
        """
        derivatives = []
        
        # 기존 추측에서 어근 기반 파생어 생성
        for guess in session.guesses:
            word = guess.word
            if len(word) > 1:
                root = word[:-1]  # 마지막 글자 제거
                
                # 같은 어근을 가진 단어들 찾기
                for vocab_word in vocab:
                    if (vocab_word.startswith(root) and 
                        vocab_word != word and 
                        vocab_word not in session.tried_words and 
                        len(vocab_word) <= len(word) + 2):
                        
                        # 예상 유사도 차이 계산 (작을수록 좋음)
                        expected_diff = abs(guess.similarity - 0.1)
                        derivatives.append((vocab_word, expected_diff))
        
        if derivatives:
            # 유사도가 높을 것으로 예상되는 순으로 정렬
            derivatives.sort(key=lambda x: x[1])
            selected_word = derivatives[0][0]
            # print(f"   🎯 파생어 탐색: '{selected_word}'")  # 로그 제거
            return selected_word
        
        # 파생어도 없으면 랜덤 선택
        available_words = [w for w in vocab if w not in session.tried_words]
        if available_words:
            return random.choice(available_words)
        
        return None
    
    def get_strategy_name(self) -> str:
        return "넓은의미탐색"
    
    def _get_learning_based_candidates(self, vocab: List[str], learned_data: Dict, 
                                     tried_words: Set[str], limit: int = 10) -> List[str]:
        """
        학습 데이터 기반으로 효과적인 후보 단어들을 추출합니다.
        
        Args:
            vocab (List[str]): 사용 가능한 어휘
            learned_data (Dict): 학습된 데이터
            tried_words (Set[str]): 이미 시도한 단어들
            limit (int): 반환할 최대 단어 수
            
        Returns:
            List[str]: 추천 단어 목록
        """
        word_frequency = learned_data.get('word_frequency', {})
        candidates = []
        
        # 학습된 단어들 중에서 효과적인 것들 선택
        for word, freq_data in word_frequency.items():
            if word in vocab and word not in tried_words:
                # 평균 유사도가 높고 성공 경험이 있는 단어
                if freq_data['avg_similarity'] > 30 and freq_data['count'] >= 2:
                    effectiveness = freq_data['avg_similarity'] * math.log(freq_data['count'] + 1)
                    candidates.append((word, effectiveness))
        
        # 효과성 순으로 정렬
        candidates.sort(key=lambda x: x[1], reverse=True)
        return [word for word, _ in candidates[:limit]]


class SemanticGradientSearch(SearchStrategy):
    """
    2단계: 의미적 경사 탐색 전략
    고성능 앵커 단어들을 기반으로 의미적 경사를 따라 탐색합니다.
    """
    
    def __init__(self):
        """의미적 확장 규칙들을 초기화합니다."""
        # 언어학적 연관어 그룹
        self.linguistic_associations = {
            "문제": ["과제", "쟁점", "이슈", "고민", "걱정", "난제"],
            "해결": ["처리", "해답", "방안", "대안", "극복", "완료"],
            "중요": ["핵심", "주요", "필수", "기본", "근본", "본질"],
            "변화": ["전환", "개선", "발전", "진보", "성장", "혁신"],
            "관계": ["연결", "결합", "소통", "교류", "상호작용", "협력"]
        }
        
        # 문맥적 관련어 매핑
        self.contextual_maps = {
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
    
    def select_word(self, session: GameSession, vocab: List[str], 
                   learned_data: Dict) -> Optional[str]:
        """
        상위 유사도 단어들을 기반으로 의미적 경사를 따라 탐색합니다.
        
        Args:
            session (GameSession): 현재 게임 세션
            vocab (List[str]): 사용 가능한 어휘 목록
            learned_data (Dict): 학습된 데이터
            
        Returns:
            Optional[str]: 선택된 단어
        """
        # 상위 3개 추측 선택
        top_guesses = session.get_top_guesses(3)
        
        # 여러 방향으로 동시 탐색
        all_candidates = []
        
        for guess in top_guesses:
            # 1. 의미적 확장
            expansions = self._get_semantic_expansions(guess.word, vocab, session.tried_words)
            all_candidates.extend(expansions)
            
            # 2. 연관어 탐색
            associations = self._get_semantic_associations(guess.word, vocab, session.tried_words)
            all_candidates.extend(associations)
            
            # 3. 문맥적 관련어
            contextual = self._get_contextual_relations(guess.word, vocab, session.tried_words)
            all_candidates.extend(contextual)
        
        # 중복 제거 및 동적 점수 기반 선택
        unique_candidates = list(set(all_candidates))
        if unique_candidates:
            scored_candidates = self._score_candidates(
                unique_candidates, session, learned_data)
            
            if scored_candidates:
                selected_word = scored_candidates[0][0]
                # print(f"   🎯 의미적 방향 탐색: '{selected_word}' (점수: {scored_candidates[0][1]:.2f})")  # 로그 제거
                return selected_word
        
        # 후보가 없으면 Wide 탐색으로 복귀
        wide_strategy = WideSemanticExploration()
        return wide_strategy.select_word(session, vocab, learned_data)
    
    def _get_semantic_expansions(self, word: str, vocab: List[str], 
                               tried_words: Set[str]) -> List[str]:
        """
        단어의 의미적 확장어들을 생성합니다.
        
        Args:
            word (str): 기준 단어
            vocab (List[str]): 사용 가능한 어휘
            tried_words (Set[str]): 이미 시도한 단어들
            
        Returns:
            List[str]: 확장어 목록
        """
        expansions = []
        
        # 어근 기반 확장 (앞 2글자 어근)
        if len(word) > 2:
            root = word[:2]
            for vocab_word in vocab:
                if (vocab_word.startswith(root) and 
                    vocab_word != word and 
                    vocab_word not in tried_words):
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
        
        # 해당 범주에 속하는 경우 같은 범주의 다른 단어들 추가
        for category, words in semantic_expansions.items():
            if word in words:
                for expansion_word in words:
                    if (expansion_word != word and 
                        expansion_word in vocab and 
                        expansion_word not in tried_words):
                        expansions.append(expansion_word)
        
        return expansions[:10]  # 최대 10개로 제한
    
    def _get_semantic_associations(self, word: str, vocab: List[str], 
                                 tried_words: Set[str]) -> List[str]:
        """
        단어의 의미적 연관어들을 생성합니다.
        
        Args:
            word (str): 기준 단어
            vocab (List[str]): 사용 가능한 어휘
            tried_words (Set[str]): 이미 시도한 단어들
            
        Returns:
            List[str]: 연관어 목록
        """
        associations = []
        
        # 언어학적 연관어 검색
        for key, words in self.linguistic_associations.items():
            if word == key or word in words:
                for assoc_word in words:
                    if (assoc_word != word and 
                        assoc_word in vocab and 
                        assoc_word not in tried_words):
                        associations.append(assoc_word)
        
        return associations[:8]  # 최대 8개로 제한
    
    def _get_contextual_relations(self, word: str, vocab: List[str], 
                                tried_words: Set[str]) -> List[str]:
        """
        단어의 문맥적 관련어들을 생성합니다.
        
        Args:
            word (str): 기준 단어
            vocab (List[str]): 사용 가능한 어휘
            tried_words (Set[str]): 이미 시도한 단어들
            
        Returns:
            List[str]: 문맥적 관련어 목록
        """
        relations = []
        
        # 문맥적 관련어 검색
        for key, words in self.contextual_maps.items():
            if word == key or word in words:
                for rel_word in words:
                    if (rel_word != word and 
                        rel_word in vocab and 
                        rel_word not in tried_words):
                        relations.append(rel_word)
        
        return relations[:6]  # 최대 6개로 제한
    
    def _sort_by_effectiveness(self, candidates: List[str], 
                             word_frequency: Dict) -> List[str]:
        """
        학습된 효과성에 따라 후보들을 정렬합니다.
        
        Args:
            candidates (List[str]): 후보 단어들
            word_frequency (Dict): 단어 빈도 데이터
            
        Returns:
            List[str]: 효과성 순으로 정렬된 후보들
        """
        def get_effectiveness_score(word: str) -> float:
            if word in word_frequency:
                freq_data = word_frequency[word]
                return freq_data.get('avg_similarity', 0) * freq_data.get('count', 1)
            return 0
        
        candidates.sort(key=get_effectiveness_score, reverse=True)
        return candidates
    
    def _score_candidates(self, candidates: List[str], session: GameSession, 
                         learned_data: Dict) -> List[Tuple[str, float]]:
        """
        여러 요소를 고려하여 후보 단어들에 점수를 부여합니다.
        
        Args:
            candidates (List[str]): 후보 단어들
            session (GameSession): 현재 게임 세션
            learned_data (Dict): 학습된 데이터
            
        Returns:
            List[Tuple[str, float]]: (단어, 점수) 튜플의 정렬된 리스트
        """
        word_frequency = learned_data.get('word_frequency', {})
        word_pairs = learned_data.get('word_pairs', {})
        
        scored = []
        for word in candidates:
            score = 0
            
            # 1. 기본 효과성 점수
            if word in word_frequency:
                freq_data = word_frequency[word]
                avg_sim = freq_data.get('avg_similarity', 0)
                count = freq_data.get('count', 0)
                score += avg_sim * math.log(count + 1) * 5
            
            # 2. 최근 고득점 단어와의 관계
            top_guesses = session.get_top_guesses(3)
            for guess in top_guesses:
                pair_key1 = f"{guess.word}|{word}"
                pair_key2 = f"{word}|{guess.word}"
                
                if pair_key1 in word_pairs or pair_key2 in word_pairs:
                    pair_data = word_pairs.get(pair_key1, word_pairs.get(pair_key2, {}))
                    similarity_diffs = pair_data.get('similarity_diffs', [])
                    if similarity_diffs:
                        avg_diff = sum(similarity_diffs) / len(similarity_diffs)
                        # 유사도 차이가 작을수록 높은 점수
                        score += (1 - avg_diff/100) * guess.similarity * 3
            
            # 3. 의미적 거리 점수 (어근 공유 등)
            for guess in session.guesses[-5:]:  # 최근 5개
                if len(word) > 2 and len(guess.word) > 2:
                    # 공통 어근 길이
                    common_prefix_len = 0
                    for i in range(min(len(word), len(guess.word))):
                        if word[i] == guess.word[i]:
                            common_prefix_len += 1
                        else:
                            break
                    
                    if common_prefix_len >= 2:
                        score += guess.similarity * common_prefix_len
            
            # 4. 다양성 보너스 (너무 비슷한 단어 연속 시도 방지)
            recent_words = [g.word for g in session.guesses[-3:]]
            if recent_words:
                avg_similarity_to_recent = 0
                for recent in recent_words:
                    if len(word) > 2 and len(recent) > 2:
                        common_chars = set(word) & set(recent)
                        avg_similarity_to_recent += len(common_chars) / max(len(word), len(recent))
                
                avg_similarity_to_recent /= len(recent_words)
                # 적당한 차이가 있으면 보너스
                if 0.2 < avg_similarity_to_recent < 0.7:
                    score += 1
            
            scored.append((word, score))
        
        # 점수순 정렬
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored
    
    def get_strategy_name(self) -> str:
        return "의미적경사탐색"


class FocusedSemanticSearch(SearchStrategy):
    """
    3단계: 집중 의미 탐색 전략
    고유사도 영역 주변에서 다층 연관을 사용하여 집중적으로 탐색합니다.
    """
    
    def __init__(self):
        """의미 영역별 단어 그룹을 초기화합니다."""
        self.semantic_fields = {
            "정치사회": ["정치", "사회", "국가", "정부", "국민", "시민", "공동체", "사회적", "정책", "제도"],
            "교육학습": ["교육", "학습", "공부", "지식", "학문", "연구", "이해", "습득", "경험"],
            "감정심리": ["감정", "마음", "기분", "느낌", "정서", "심리", "사랑", "행복", "슬픔"],
            "시공간": ["시간", "공간", "장소", "위치", "때", "순간", "지역", "영역", "범위"],
            "행동활동": ["행동", "활동", "움직임", "작업", "실행", "진행", "과정", "방법"]
        }
    
    def select_word(self, session: GameSession, vocab: List[str], 
                   learned_data: Dict) -> Optional[str]:
        """
        고유사도 단어들의 공통 의미 영역에서 집중적으로 탐색합니다.
        
        Args:
            session (GameSession): 현재 게임 세션
            vocab (List[str]): 사용 가능한 어휘 목록
            learned_data (Dict): 학습된 데이터
            
        Returns:
            Optional[str]: 선택된 단어
        """
        # 상위 2개 추측 분석
        top_guesses = session.get_top_guesses(2)
        
        # 공통 의미 영역 찾기
        common_field = self._find_common_semantic_field([g.word for g in top_guesses])
        
        if common_field:
            candidates = [w for w in common_field 
                         if w in vocab and w not in session.tried_words]
            if candidates:
                selected_word = candidates[0]
                print(f"   🎯 공통 의미 영역: '{selected_word}'")
                return selected_word
        
        # 최고 단어 주변 다층 탐색
        if session.guesses:
            best_guess = max(session.guesses, key=lambda g: g.similarity)
            
            # 1층: 직접 연관어
            gradient_strategy = SemanticGradientSearch()
            layer1 = gradient_strategy._get_semantic_associations(
                best_guess.word, vocab, session.tried_words)
            
            # 2층: 1층 단어들의 연관어
            layer2 = []
            for word in layer1[:3]:  # 상위 3개만
                if word not in session.tried_words:
                    layer2.extend(gradient_strategy._get_semantic_associations(
                        word, vocab, session.tried_words))
            
            # 모든 후보 결합
            all_candidates = layer1 + layer2
            unique_candidates = [w for w in set(all_candidates) 
                               if w in vocab and w not in session.tried_words]
            
            if unique_candidates:
                # 동적 점수 기반 선택
                scored_candidates = self._score_focused_candidates(
                    unique_candidates, best_guess, session, learned_data)
                
                if scored_candidates:
                    selected_word = scored_candidates[0][0]
                    print(f"   🎯 '{best_guess.word}' 다층 연관어: '{selected_word}'")
                    return selected_word
        
        # 실패 시 경사 탐색으로 복귀
        gradient_strategy = SemanticGradientSearch()
        return gradient_strategy.select_word(session, vocab, learned_data)
    
    def _find_common_semantic_field(self, words: List[str]) -> List[str]:
        """
        단어들의 공통 의미 영역을 찾습니다.
        
        Args:
            words (List[str]): 분석할 단어들
            
        Returns:
            List[str]: 공통 의미 영역의 단어들
        """
        if len(words) < 2:
            return []
        
        # 모든 단어가 속하는 의미 영역 찾기
        for field_name, field_words in self.semantic_fields.items():
            # 모든 입력 단어가 이 영역에 속하는지 확인
            if all(any(word in field_words or word.startswith(fw[:2]) 
                      for fw in field_words) for word in words):
                # 입력 단어들을 제외한 나머지 반환
                return [w for w in field_words if w not in words]
        
        return []
    
    def _score_focused_candidates(self, candidates: List[str], best_guess: GuessResult,
                                session: GameSession, learned_data: Dict) -> List[Tuple[str, float]]:
        """
        집중 탐색을 위한 후보 점수 계산
        
        Args:
            candidates (List[str]): 후보 단어들
            best_guess (GuessResult): 현재 최고 유사도 단어
            session (GameSession): 현재 게임 세션  
            learned_data (Dict): 학습된 데이터
            
        Returns:
            List[Tuple[str, float]]: (단어, 점수) 튜플의 정렬된 리스트
        """
        word_pairs = learned_data.get('word_pairs', {})
        scored = []
        
        for word in candidates:
            score = 0
            
            # 1. 최고 단어와의 학습된 관계
            pair_key1 = f"{best_guess.word}|{word}"
            pair_key2 = f"{word}|{best_guess.word}"
            
            if pair_key1 in word_pairs or pair_key2 in word_pairs:
                pair_data = word_pairs.get(pair_key1, word_pairs.get(pair_key2, {}))
                similarity_diffs = pair_data.get('similarity_diffs', [])
                if similarity_diffs:
                    avg_diff = sum(similarity_diffs) / len(similarity_diffs)
                    # 매우 유사한 관계면 높은 점수 (0-100 scale)
                    if avg_diff < 5:
                        score += 10 * (1 - avg_diff/100)
            
            # 2. 유사도 기울기 예측
            recent_guesses = session.guesses[-5:]
            if len(recent_guesses) >= 2:
                # 최근 유사도 변화율 계산
                similarities = [g.similarity for g in recent_guesses]
                gradient = (similarities[-1] - similarities[0]) / len(similarities)
                
                # 양의 기울기면 더 높은 점수
                if gradient > 0:
                    score += gradient * 5
            
            # 3. 의미적 근접성
            if len(word) > 2 and len(best_guess.word) > 2:
                # 공통 문자 비율
                common_chars = set(word) & set(best_guess.word)
                char_similarity = len(common_chars) / max(len(word), len(best_guess.word))
                score += char_similarity * best_guess.similarity * 3
            
            scored.append((word, score))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored
    
    def get_strategy_name(self) -> str:
        return "집중의미탐색"


class PrecisionSemanticSearch(SearchStrategy):
    """
    4단계: 정밀 의미 탐색 전략
    형태론적 분석을 사용하여 고유사도 상황에서 정밀하게 탐색합니다.
    """
    
    def select_word(self, session: GameSession, vocab: List[str], 
                   learned_data: Dict) -> Optional[str]:
        """
        형태론적 변형과 학습된 초근접 단어를 사용하여 정밀 탐색합니다.
        
        Args:
            session (GameSession): 현재 게임 세션
            vocab (List[str]): 사용 가능한 어휘 목록
            learned_data (Dict): 학습된 데이터
            
        Returns:
            Optional[str]: 선택된 단어
        """
        if not session.guesses:
            return None
        
        best_guess = max(session.guesses, key=lambda g: g.similarity)
        precision_candidates = []
        
        # 1. 형태론적 변형 생성
        morphological_variants = self._generate_morphological_variants(
            best_guess.word, vocab, session.tried_words)
        precision_candidates.extend(morphological_variants[:3])
        
        # 2. 학습된 초근접 단어들
        word_pairs = learned_data.get('word_pairs', {})
        ultra_close_words = self._find_ultra_close_words(
            best_guess.word, word_pairs, vocab, session.tried_words)
        precision_candidates.extend([w[0] for w in ultra_close_words[:2]])
        
        if precision_candidates:
            selected_word = precision_candidates[0]
            print(f"   🎯 '{best_guess.word}' 정밀 변형: '{selected_word}'")
            return selected_word
        
        # 정밀 탐색 실패 시 집중 탐색으로 복귀
        focused_strategy = FocusedSemanticSearch()
        return focused_strategy.select_word(session, vocab, learned_data)
    
    def _generate_morphological_variants(self, word: str, vocab: List[str], 
                                       tried_words: Set[str]) -> List[str]:
        """
        단어의 형태론적 변형들을 생성합니다.
        
        Args:
            word (str): 기준 단어
            vocab (List[str]): 사용 가능한 어휘
            tried_words (Set[str]): 이미 시도한 단어들
            
        Returns:
            List[str]: 형태론적 변형들
        """
        variants = []
        
        if len(word) > 2:
            root = word[:-1]  # 마지막 글자 제거
            
            # 한국어 일반적인 접미사들
            suffixes = ['다', '하다', '되다', '이다', '적', '의', '로', '을', '를']
            
            for suffix in suffixes:
                variant = root + suffix
                if (variant in vocab and 
                    variant not in tried_words and 
                    variant != word):
                    variants.append(variant)
        
        return variants
    
    def _find_ultra_close_words(self, word: str, word_pairs: Dict, 
                              vocab: List[str], tried_words: Set[str]) -> List[Tuple[str, float]]:
        """
        학습된 데이터에서 초근접 단어들을 찾습니다.
        
        Args:
            word (str): 기준 단어
            word_pairs (Dict): 단어 쌍 데이터
            vocab (List[str]): 사용 가능한 어휘
            tried_words (Set[str]): 이미 시도한 단어들
            
        Returns:
            List[Tuple[str, float]]: (단어, 평균차이) 튜플의 리스트
        """
        ultra_close = []
        
        for pair_key, pair_data in word_pairs.items():
            word1, word2 = pair_key.split('|')
            
            if word1 == word or word2 == word:
                other_word = word2 if word1 == word else word1
                
                if (other_word in vocab and 
                    other_word not in tried_words):
                    
                    # 평균 유사도 차이 계산
                    similarity_diffs = pair_data.get('similarity_diffs', [])
                    if similarity_diffs:
                        avg_diff = sum(similarity_diffs) / len(similarity_diffs)
                        # 매우 유사한 단어들만 (차이 < 3, 0-100 scale)
                        if avg_diff < 3:
                            ultra_close.append((other_word, avg_diff))
        
        # 유사도 차이 순으로 정렬 (작은 순)
        ultra_close.sort(key=lambda x: x[1])
        return ultra_close
    
    def get_strategy_name(self) -> str:
        return "정밀의미탐색"


class StrategyEngine:
    """
    전략 엔진: 상황에 따라 적절한 탐색 전략을 선택하고 실행합니다.
    """
    
    def __init__(self, enable_logging: bool = True):
        """
        모든 전략들을 초기화합니다.
        
        Args:
            enable_logging (bool): 로깅 활성화 여부
        """
        self.strategies = {
            "wide": WideSemanticExploration(),
            "gradient": SemanticGradientSearch(),
            "focused": FocusedSemanticSearch(),
            "precision": PrecisionSemanticSearch()
        }
        self.logger = StrategyLogger() if enable_logging else None
        self.previous_strategy = None
    
    def select_strategy(self, session: GameSession) -> SearchStrategy:
        """
        현재 상황에 따라 최적의 전략을 선택합니다.
        
        Args:
            session (GameSession): 현재 게임 세션
            
        Returns:
            SearchStrategy: 선택된 전략 객체
        """
        best_similarity = session.get_best_similarity()
        is_stuck = session.is_stagnant()
        
        # 개선된 전략 선택 로직 (0-100 scale)
        # 현재 전략과 시도 횟수 확인
        current_strategy_name = session.strategy_history[-1] if session.strategy_history else None
        attempts_with_current = 0
        if current_strategy_name:
            for i in range(len(session.strategy_history) - 1, -1, -1):
                if session.strategy_history[i] == current_strategy_name:
                    attempts_with_current += 1
                else:
                    break
        
        # 전략 전환 조건
        force_switch = False
        if attempts_with_current > 20 and is_stuck:  # 20회 이상 같은 전략으로 정체
            force_switch = True
        
        if not session.guesses or best_similarity < 10:
            # 초기 탐색
            strategy = self.strategies["wide"]
        elif force_switch or (is_stuck and attempts_with_current > 10):
            # 강제 전환 또는 정체 상태
            if current_strategy_name:
                # 순환 전략: wide -> gradient -> focused -> precision -> wide
                strategy_order = ["wide", "gradient", "focused", "precision"]
                current_idx = -1
                for i, s in enumerate(strategy_order):
                    if s in current_strategy_name.lower():
                        current_idx = i
                        break
                next_idx = (current_idx + 1) % len(strategy_order)
                strategy = self.strategies[strategy_order[next_idx]]
            else:
                strategy = self.strategies["gradient"]
        else:
            # 유사도 기반 전략 선택 with 더 동적인 전환
            if best_similarity < 15:
                strategy = self.strategies["gradient"]
            elif best_similarity < 30:
                # 최근 진전 확인
                if len(session.guesses) >= 5:
                    recent_sims = [g.similarity for g in session.guesses[-5:]]
                    improvement = recent_sims[-1] - recent_sims[0]
                    
                    if improvement > 15:  # 빠른 개선
                        strategy = self.strategies["focused"]
                    elif improvement < 5:  # 느린 개선
                        strategy = self.strategies["wide"]  # 다시 넓게 탐색
                    else:
                        strategy = self.strategies["gradient"]
                else:
                    strategy = self.strategies["gradient"]
            elif best_similarity < 50:
                # 중간 단계에서는 더 자주 전략 변경
                if len(session.guesses) >= 3:
                    recent_improvement = session.guesses[-1].similarity - session.guesses[-3].similarity
                    if recent_improvement < 3:  # 개선이 느림
                        strategy = self.strategies["gradient"]
                    else:
                        strategy = self.strategies["focused"]
                else:
                    strategy = self.strategies["focused"]
            else:
                # 높은 유사도에서는 정밀 탐색
                strategy = self.strategies["precision"]
        
        # 전략 변경 로깅
        if self.logger and self.previous_strategy and self.previous_strategy != strategy:
            reason = "정체 상태" if is_stuck else f"유사도 변화 ({best_similarity:.3f})"
            self.logger.log_strategy_change(
                self.previous_strategy.get_strategy_name(),
                strategy.get_strategy_name(),
                reason,
                best_similarity
            )
        
        self.previous_strategy = strategy
        return strategy
    
    def select_next_word(self, session: GameSession, vocab: List[str], 
                        learned_data: Dict) -> Optional[str]:
        """
        상황에 맞는 전략을 선택하고 다음 단어를 선택합니다.
        
        Args:
            session (GameSession): 현재 게임 세션
            vocab (List[str]): 사용 가능한 어휘 목록
            learned_data (Dict): 학습된 데이터
            
        Returns:
            Optional[str]: 선택된 단어
        """
        strategy = self.select_strategy(session)
        session.update_strategy(strategy.get_strategy_name())
        
        return strategy.select_word(session, vocab, learned_data)