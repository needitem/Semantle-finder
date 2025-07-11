#!/usr/bin/env python3
"""
고급 학습 메커니즘 모듈
강화학습, 전이학습, 동적 임계값 조정 등 고급 학습 기능을 제공합니다.
"""

import json
import math
import random
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict, deque

from .models import GuessResult, GameSession, SuccessPattern


class QLearningStrategy:
    """
    Q-Learning 기반 전략 선택 최적화
    각 상황에서 최적의 전략을 학습합니다.
    """
    
    def __init__(self, learning_rate: float = 0.1, discount_factor: float = 0.9, 
                 epsilon: float = 0.1):
        """
        Q-Learning 파라미터 초기화
        
        Args:
            learning_rate (float): 학습률 (0.0 ~ 1.0)
            discount_factor (float): 할인 인수 (0.0 ~ 1.0)
            epsilon (float): 탐험률 (0.0 ~ 1.0)
        """
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon
        
        # Q-테이블: (상태, 액션) -> Q값
        self.q_table: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        
        # 가능한 전략들
        self.strategies = ["넓은의미탐색", "의미적경사탐색", "집중의미탐색", "정밀의미탐색"]
        
        # 상태 히스토리 (학습용)
        self.state_action_history: List[Tuple[str, str, float]] = []
    
    def get_state_key(self, session: GameSession) -> str:
        """
        현재 게임 상태를 문자열 키로 변환합니다.
        
        Args:
            session (GameSession): 현재 게임 세션
            
        Returns:
            str: 상태 키
        """
        if not session.guesses:
            return "초기상태"
        
        best_similarity = session.get_best_similarity()
        attempts = len(session.guesses)
        is_stuck = session.is_stagnant()
        
        # 상태를 카테고리화
        sim_category = "매우낮음" if best_similarity < 0.1 else \
                      "낮음" if best_similarity < 0.25 else \
                      "중간" if best_similarity < 0.5 else \
                      "높음"
        
        attempt_category = "초기" if attempts < 10 else \
                          "중기" if attempts < 30 else \
                          "후기"
        
        stuck_status = "정체" if is_stuck else "진행"
        
        return f"{sim_category}_{attempt_category}_{stuck_status}"
    
    def select_strategy(self, session: GameSession) -> str:
        """
        Q-Learning을 사용하여 최적 전략을 선택합니다.
        
        Args:
            session (GameSession): 현재 게임 세션
            
        Returns:
            str: 선택된 전략 이름
        """
        state = self.get_state_key(session)
        
        # ε-greedy 정책
        if random.random() < self.epsilon:
            # 탐험: 랜덤 전략 선택
            strategy = random.choice(self.strategies)
        else:
            # 이용: 최고 Q값 전략 선택
            q_values = self.q_table[state]
            if not q_values:
                # Q값이 없으면 랜덤 선택
                strategy = random.choice(self.strategies)
            else:
                strategy = max(q_values.items(), key=lambda x: x[1])[0]
        
        # 히스토리에 기록
        self.state_action_history.append((state, strategy, 0.0))  # 보상은 나중에 업데이트
        
        return strategy
    
    def update_q_values(self, final_reward: float, session_length: int) -> None:
        """
        게임 종료 후 Q값을 업데이트합니다.
        
        Args:
            final_reward (float): 최종 보상 (성공=1.0, 실패=0.0)
            session_length (int): 게임 시도 횟수
        """
        # 보상 계산 (시도 횟수가 적을수록 높은 보상)
        efficiency_bonus = max(0, (100 - session_length) / 100)
        total_reward = final_reward + efficiency_bonus
        
        # 역순으로 Q값 업데이트 (시간차 학습)
        for i in reversed(range(len(self.state_action_history))):
            state, action, _ = self.state_action_history[i]
            
            # 현재 Q값
            current_q = self.q_table[state][action]
            
            # 다음 상태의 최대 Q값 (마지막이면 0)
            if i == len(self.state_action_history) - 1:
                max_next_q = 0
            else:
                next_state = self.state_action_history[i + 1][0]
                next_q_values = self.q_table[next_state]
                max_next_q = max(next_q_values.values()) if next_q_values else 0
            
            # Q값 업데이트
            new_q = current_q + self.learning_rate * (
                total_reward + self.discount_factor * max_next_q - current_q
            )
            self.q_table[state][action] = new_q
            
            # 보상 감쇠 (시간이 지날수록 영향 감소)
            total_reward *= 0.9
        
        # 히스토리 초기화
        self.state_action_history.clear()
    
    def get_q_statistics(self) -> Dict[str, Any]:
        """Q-Learning 통계를 반환합니다."""
        stats = {
            "total_states": len(self.q_table),
            "total_state_actions": sum(len(actions) for actions in self.q_table.values()),
            "epsilon": self.epsilon,
            "learning_rate": self.learning_rate,
            "top_strategies_by_state": {}
        }
        
        for state, actions in self.q_table.items():
            if actions:
                best_strategy = max(actions.items(), key=lambda x: x[1])
                stats["top_strategies_by_state"][state] = {
                    "strategy": best_strategy[0],
                    "q_value": best_strategy[1]
                }
        
        return stats


class TransferLearning:
    """
    전이 학습: 다른 게임이나 도메인의 지식을 활용합니다.
    """
    
    def __init__(self):
        """전이 학습 시스템을 초기화합니다."""
        # 외부 지식 베이스 (사전 정의된 단어 관계)
        self.external_knowledge = self._load_external_knowledge()
        
        # 도메인 간 매핑
        self.domain_mappings = self._create_domain_mappings()
        
        # 전이 학습 가중치
        self.transfer_weights = {
            "semantic_similarity": 0.3,  # 의미적 유사성
            "morphological_similarity": 0.2,  # 형태적 유사성
            "contextual_similarity": 0.3,  # 문맥적 유사성
            "frequency_pattern": 0.2  # 빈도 패턴
        }
    
    def _load_external_knowledge(self) -> Dict[str, List[str]]:
        """
        외부 지식 베이스를 로드합니다.
        실제 구현에서는 외부 API나 데이터베이스에서 가져올 수 있습니다.
        """
        return {
            # 시간 관련 단어들
            "시간": ["순간", "시기", "때", "시절", "기간", "시점", "시대", "동안", "사이"],
            
            # 감정 관련 단어들
            "감정": ["마음", "기분", "느낌", "정서", "심리", "의식", "생각", "마음가짐"],
            
            # 사회 관련 단어들
            "사회": ["정치", "경제", "문화", "교육", "제도", "공동체", "시민", "국민"],
            
            # 자연 관련 단어들
            "자연": ["환경", "생태", "기후", "날씨", "계절", "생물", "식물", "동물"],
            
            # 기술 관련 단어들
            "기술": ["과학", "발명", "혁신", "개발", "연구", "실험", "발견", "진보"]
        }
    
    def _create_domain_mappings(self) -> Dict[str, str]:
        """
        서로 다른 도메인 간의 매핑을 생성합니다.
        """
        return {
            # 추상 -> 구체
            "생각": "아이디어",
            "마음": "감정",
            "시간": "순간",
            
            # 일반 -> 전문
            "연구": "실험",
            "교육": "학습",
            "문제": "과제",
            
            # 공식 -> 비공식
            "정부": "나라",
            "시민": "사람",
            "제도": "규칙"
        }
    
    def get_transferred_candidates(self, current_word: str, 
                                 current_similarity: float) -> List[Tuple[str, float]]:
        """
        전이 학습을 통해 후보 단어들을 생성합니다.
        
        Args:
            current_word (str): 현재 단어
            current_similarity (float): 현재 유사도
            
        Returns:
            List[Tuple[str, float]]: (단어, 예상유사도) 튜플의 리스트
        """
        candidates = []
        
        # 1. 의미적 전이
        semantic_candidates = self._semantic_transfer(current_word, current_similarity)
        candidates.extend(semantic_candidates)
        
        # 2. 형태적 전이
        morphological_candidates = self._morphological_transfer(current_word, current_similarity)
        candidates.extend(morphological_candidates)
        
        # 3. 문맥적 전이
        contextual_candidates = self._contextual_transfer(current_word, current_similarity)
        candidates.extend(contextual_candidates)
        
        # 중복 제거 및 점수 합산
        word_scores = defaultdict(list)
        for word, score in candidates:
            word_scores[word].append(score)
        
        # 평균 점수로 최종 후보 생성
        final_candidates = [
            (word, sum(scores) / len(scores))
            for word, scores in word_scores.items()
        ]
        
        # 점수 순으로 정렬
        final_candidates.sort(key=lambda x: x[1], reverse=True)
        
        return final_candidates[:10]  # 상위 10개만 반환
    
    def _semantic_transfer(self, word: str, similarity: float) -> List[Tuple[str, float]]:
        """의미적 전이를 수행합니다."""
        candidates = []
        
        # 외부 지식에서 관련 단어 찾기
        for category, related_words in self.external_knowledge.items():
            if word in related_words or word == category:
                for related_word in related_words:
                    if related_word != word:
                        # 유사도 추정 (카테고리 내 단어들은 비슷한 유사도를 가질 것으로 예상)
                        estimated_similarity = similarity + random.uniform(-0.05, 0.05)
                        estimated_similarity = max(0, min(1, estimated_similarity))
                        candidates.append((related_word, estimated_similarity))
        
        return candidates
    
    def _morphological_transfer(self, word: str, similarity: float) -> List[Tuple[str, float]]:
        """형태적 전이를 수행합니다."""
        candidates = []
        
        # 도메인 매핑 활용
        if word in self.domain_mappings:
            mapped_word = self.domain_mappings[word]
            # 매핑된 단어는 약간 다른 유사도를 가질 것으로 예상
            estimated_similarity = similarity + random.uniform(-0.1, 0.1)
            estimated_similarity = max(0, min(1, estimated_similarity))
            candidates.append((mapped_word, estimated_similarity))
        
        # 역방향 매핑도 확인
        for source, target in self.domain_mappings.items():
            if word == target:
                estimated_similarity = similarity + random.uniform(-0.1, 0.1)
                estimated_similarity = max(0, min(1, estimated_similarity))
                candidates.append((source, estimated_similarity))
        
        return candidates
    
    def _contextual_transfer(self, word: str, similarity: float) -> List[Tuple[str, float]]:
        """문맥적 전이를 수행합니다."""
        candidates = []
        
        # 단어의 길이나 구조를 기반으로 한 전이
        if len(word) >= 2:
            # 비슷한 길이의 단어들은 비슷한 유사도를 가질 수 있음
            for category_words in self.external_knowledge.values():
                for candidate_word in category_words:
                    if (abs(len(candidate_word) - len(word)) <= 1 and 
                        candidate_word != word):
                        # 길이가 비슷한 단어는 약간의 유사도 변화
                        estimated_similarity = similarity + random.uniform(-0.03, 0.03)
                        estimated_similarity = max(0, min(1, estimated_similarity))
                        candidates.append((candidate_word, estimated_similarity))
        
        return candidates


class AdaptiveThresholds:
    """
    적응적 임계값: 성능에 따라 전략 전환 임계값을 동적으로 조정합니다.
    """
    
    def __init__(self):
        """적응적 임계값 시스템을 초기화합니다."""
        # 기본 임계값
        self.base_thresholds = {
            "wide_to_gradient": 0.1,
            "gradient_to_focused": 0.25,
            "focused_to_precision": 0.5
        }
        
        # 현재 임계값 (동적으로 조정됨)
        self.current_thresholds = self.base_thresholds.copy()
        
        # 성능 히스토리
        self.performance_history = deque(maxlen=50)  # 최근 50게임 기록
        
        # 조정 매개변수
        self.adjustment_rate = 0.02  # 임계값 조정 폭
        self.success_rate_target = 0.7  # 목표 성공률
    
    def update_performance(self, success: bool, attempts: int, 
                         strategy_transitions: List[Tuple[str, float]]) -> None:
        """
        게임 성과를 기록하고 임계값을 조정합니다.
        
        Args:
            success (bool): 게임 성공 여부
            attempts (int): 시도 횟수
            strategy_transitions (List[Tuple[str, float]]): (전략명, 전환시점유사도) 리스트
        """
        # 성과 기록
        performance_record = {
            "success": success,
            "attempts": attempts,
            "efficiency": 1.0 / attempts if attempts > 0 else 0,
            "strategy_transitions": strategy_transitions,
            "timestamp": datetime.now()
        }
        
        self.performance_history.append(performance_record)
        
        # 충분한 데이터가 쌓이면 임계값 조정
        if len(self.performance_history) >= 10:
            self._adjust_thresholds()
    
    def _adjust_thresholds(self) -> None:
        """성능 데이터를 바탕으로 임계값을 조정합니다."""
        recent_games = list(self.performance_history)[-20:]  # 최근 20게임
        
        # 성공률 계산
        success_rate = sum(game["success"] for game in recent_games) / len(recent_games)
        
        # 평균 시도 횟수 계산
        avg_attempts = sum(game["attempts"] for game in recent_games) / len(recent_games)
        
        # 전략별 성과 분석
        strategy_performance = self._analyze_strategy_performance(recent_games)
        
        # 임계값 조정 로직
        if success_rate < self.success_rate_target:
            # 성공률이 낮으면 더 빨리 고급 전략으로 전환
            self._decrease_thresholds()
        elif avg_attempts < 20:
            # 시도 횟수가 적으면 현재 임계값이 좋음 (유지)
            pass
        else:
            # 시도 횟수가 많으면 전략 전환을 늦춤
            self._increase_thresholds()
        
        print(f"📊 임계값 조정: {self.current_thresholds}")
    
    def _analyze_strategy_performance(self, games: List[Dict]) -> Dict[str, float]:
        """전략별 성과를 분석합니다."""
        strategy_stats = defaultdict(list)
        
        for game in games:
            for strategy, similarity in game["strategy_transitions"]:
                strategy_stats[strategy].append({
                    "success": game["success"],
                    "efficiency": game["efficiency"],
                    "similarity_at_transition": similarity
                })
        
        # 전략별 평균 성과 계산
        strategy_performance = {}
        for strategy, records in strategy_stats.items():
            if records:
                avg_success = sum(r["success"] for r in records) / len(records)
                avg_efficiency = sum(r["efficiency"] for r in records) / len(records)
                strategy_performance[strategy] = avg_success * avg_efficiency
        
        return strategy_performance
    
    def _decrease_thresholds(self) -> None:
        """임계값을 낮춰서 더 빨리 고급 전략으로 전환합니다."""
        for key in self.current_thresholds:
            self.current_thresholds[key] = max(
                0.05,  # 최소값
                self.current_thresholds[key] - self.adjustment_rate
            )
    
    def _increase_thresholds(self) -> None:
        """임계값을 높여서 전략 전환을 늦춥니다."""
        for key in self.current_thresholds:
            self.current_thresholds[key] = min(
                0.8,  # 최대값
                self.current_thresholds[key] + self.adjustment_rate
            )
    
    def get_threshold(self, transition_type: str) -> float:
        """
        지정된 전환 타입의 현재 임계값을 반환합니다.
        
        Args:
            transition_type (str): 전환 타입 키
            
        Returns:
            float: 현재 임계값
        """
        return self.current_thresholds.get(transition_type, 0.25)
    
    def get_adaptation_statistics(self) -> Dict[str, Any]:
        """적응 통계를 반환합니다."""
        if not self.performance_history:
            return {"message": "충분한 데이터가 없습니다."}
        
        recent_games = list(self.performance_history)[-10:]
        
        stats = {
            "current_thresholds": self.current_thresholds.copy(),
            "base_thresholds": self.base_thresholds.copy(),
            "recent_success_rate": sum(g["success"] for g in recent_games) / len(recent_games),
            "recent_avg_attempts": sum(g["attempts"] for g in recent_games) / len(recent_games),
            "total_games_recorded": len(self.performance_history),
            "threshold_adjustments": {
                key: round(current - self.base_thresholds[key], 4)
                for key, current in self.current_thresholds.items()
            }
        }
        
        return stats


class AdvancedLearningEngine:
    """
    고급 학습 엔진: 모든 고급 학습 메커니즘을 통합합니다.
    """
    
    def __init__(self, base_learning_engine):
        """
        고급 학습 엔진을 초기화합니다.
        
        Args:
            base_learning_engine: 기본 학습 엔진 인스턴스
        """
        self.base_engine = base_learning_engine
        
        # 고급 학습 컴포넌트들
        self.q_learning = QLearningStrategy()
        self.transfer_learning = TransferLearning()
        self.adaptive_thresholds = AdaptiveThresholds()
        
        # 설정
        self.enable_q_learning = True
        self.enable_transfer_learning = True
        self.enable_adaptive_thresholds = True
    
    def select_enhanced_strategy(self, session: GameSession) -> str:
        """
        고급 학습을 활용하여 전략을 선택합니다.
        
        Args:
            session (GameSession): 현재 게임 세션
            
        Returns:
            str: 선택된 전략 이름
        """
        if self.enable_q_learning and len(self.q_learning.state_action_history) > 5:
            # Q-Learning으로 전략 선택
            return self.q_learning.select_strategy(session)
        else:
            # 기본 전략 선택 로직 사용
            best_similarity = session.get_best_similarity()
            
            # 적응적 임계값 사용
            if self.enable_adaptive_thresholds:
                wide_threshold = self.adaptive_thresholds.get_threshold("wide_to_gradient")
                gradient_threshold = self.adaptive_thresholds.get_threshold("gradient_to_focused")
                focused_threshold = self.adaptive_thresholds.get_threshold("focused_to_precision")
            else:
                wide_threshold, gradient_threshold, focused_threshold = 0.1, 0.25, 0.5
            
            is_stuck = session.is_stagnant()
            
            if best_similarity < wide_threshold:
                return "넓은의미탐색"
            elif best_similarity < gradient_threshold or is_stuck:
                return "의미적경사탐색"
            elif best_similarity < focused_threshold:
                return "집중의미탐색"
            else:
                return "정밀의미탐색"
    
    def get_enhanced_word_candidates(self, current_word: str, 
                                   current_similarity: float) -> List[Tuple[str, float]]:
        """
        전이 학습을 활용하여 향상된 단어 후보를 생성합니다.
        
        Args:
            current_word (str): 현재 단어
            current_similarity (float): 현재 유사도
            
        Returns:
            List[Tuple[str, float]]: (단어, 예상유사도) 튜플의 리스트
        """
        if self.enable_transfer_learning:
            return self.transfer_learning.get_transferred_candidates(
                current_word, current_similarity)
        else:
            return []
    
    def update_advanced_learning(self, session: GameSession, success: bool, 
                               final_answer: str = None) -> None:
        """
        게임 종료 후 모든 고급 학습 시스템을 업데이트합니다.
        
        Args:
            session (GameSession): 완료된 게임 세션
            success (bool): 성공 여부
            final_answer (str): 최종 정답 (성공한 경우)
        """
        # Q-Learning 업데이트
        if self.enable_q_learning:
            final_reward = 1.0 if success else 0.0
            self.q_learning.update_q_values(final_reward, len(session.guesses))
        
        # 적응적 임계값 업데이트
        if self.enable_adaptive_thresholds:
            # 전략 전환 기록 생성
            strategy_transitions = []
            for i, strategy in enumerate(session.strategy_history):
                # 각 전략이 사용된 시점의 유사도 추정
                if i < len(session.guesses):
                    similarity_at_transition = session.guesses[i].similarity
                else:
                    similarity_at_transition = session.get_best_similarity()
                strategy_transitions.append((strategy, similarity_at_transition))
            
            self.adaptive_thresholds.update_performance(
                success, len(session.guesses), strategy_transitions)
    
    def get_comprehensive_statistics(self) -> Dict[str, Any]:
        """모든 고급 학습 시스템의 통계를 반환합니다."""
        stats = {
            "base_learning": self.base_engine.get_learning_statistics(),
            "advanced_features": {
                "q_learning_enabled": self.enable_q_learning,
                "transfer_learning_enabled": self.enable_transfer_learning,
                "adaptive_thresholds_enabled": self.enable_adaptive_thresholds
            }
        }
        
        if self.enable_q_learning:
            stats["q_learning"] = self.q_learning.get_q_statistics()
        
        if self.enable_adaptive_thresholds:
            stats["adaptive_thresholds"] = self.adaptive_thresholds.get_adaptation_statistics()
        
        if self.enable_transfer_learning:
            stats["transfer_learning"] = {
                "external_knowledge_categories": len(self.transfer_learning.external_knowledge),
                "domain_mappings": len(self.transfer_learning.domain_mappings)
            }
        
        return stats