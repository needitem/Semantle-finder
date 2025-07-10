#!/usr/bin/env python3
"""
데이터 구조 모듈
꼬맨틀 솔버에서 사용하는 핵심 데이터 구조와 클래스를 정의합니다.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime


@dataclass
class GuessResult:
    """
    추측 결과를 저장하는 데이터 클래스
    
    Attributes:
        word (str): 추측한 단어
        similarity (float): 유사도 점수 (0.0 ~ 1.0)
        rank (str): 유사도 순위 정보
        attempt (int): 시도 번호
    """
    word: str
    similarity: float
    rank: str = ""
    attempt: int = 0
    
    def __post_init__(self):
        """데이터 검증을 수행합니다."""
        if not isinstance(self.word, str) or not self.word.strip():
            raise ValueError("단어는 비어있지 않은 문자열이어야 합니다.")
        
        if not 0.0 <= self.similarity <= 1.0:
            raise ValueError("유사도는 0.0과 1.0 사이의 값이어야 합니다.")
        
        if self.attempt < 0:
            raise ValueError("시도 번호는 0 이상이어야 합니다.")


@dataclass
class WordPairData:
    """
    단어 쌍의 유사도 차이 데이터를 저장하는 클래스
    
    Attributes:
        similarity_diffs (List[float]): 유사도 차이들의 리스트
        co_occurrence_count (int): 함께 나타난 횟수
        last_updated (datetime): 마지막 업데이트 시간
    """
    similarity_diffs: List[float]
    co_occurrence_count: int
    last_updated: Optional[datetime] = None
    
    def __post_init__(self):
        """마지막 업데이트 시간을 설정합니다."""
        if self.last_updated is None:
            self.last_updated = datetime.now()
    
    def add_similarity_diff(self, diff: float) -> None:
        """
        새로운 유사도 차이를 추가합니다.
        
        Args:
            diff (float): 추가할 유사도 차이
        """
        self.similarity_diffs.append(diff)
        self.co_occurrence_count += 1
        self.last_updated = datetime.now()
        
        # 메모리 절약을 위해 최대 100개 기록만 유지
        if len(self.similarity_diffs) > 100:
            self.similarity_diffs = self.similarity_diffs[-50:]
    
    def get_average_diff(self) -> float:
        """
        평균 유사도 차이를 계산합니다.
        
        Returns:
            float: 평균 유사도 차이
        """
        if not self.similarity_diffs:
            return 0.0
        return sum(self.similarity_diffs) / len(self.similarity_diffs)


@dataclass
class SuccessPattern:
    """
    성공한 게임의 패턴을 저장하는 클래스
    
    Attributes:
        answer (str): 정답 단어
        attempts (int): 시도 횟수
        key_words (List[str]): 핵심 단어들 (상위 유사도)
        strategy_sequence (List[str]): 사용된 전략 순서
        timestamp (datetime): 게임 완료 시간
        final_similarity_scores (List[float]): 최종 상위 유사도 점수들
    """
    answer: str
    attempts: int
    key_words: List[str]
    strategy_sequence: List[str]
    timestamp: datetime
    final_similarity_scores: Optional[List[float]] = None
    
    def __post_init__(self):
        """데이터 검증을 수행합니다."""
        if not self.answer.strip():
            raise ValueError("정답은 비어있지 않은 문자열이어야 합니다.")
        
        if self.attempts <= 0:
            raise ValueError("시도 횟수는 1 이상이어야 합니다.")
        
        if not self.key_words:
            raise ValueError("핵심 단어 목록은 비어있을 수 없습니다.")


@dataclass
class WordFrequencyData:
    """
    단어의 사용 빈도와 성과를 저장하는 클래스
    
    Attributes:
        count (int): 사용된 횟수
        avg_similarity (float): 평균 유사도
        best_similarity (float): 최고 유사도
        total_similarity (float): 총 유사도 합계 (평균 계산용)
        last_used (datetime): 마지막 사용 시간
    """
    count: int = 0
    avg_similarity: float = 0.0
    best_similarity: float = 0.0
    total_similarity: float = 0.0
    last_used: Optional[datetime] = None
    
    def update_with_new_similarity(self, similarity: float) -> None:
        """
        새로운 유사도로 통계를 업데이트합니다.
        
        Args:
            similarity (float): 새로운 유사도 점수
        """
        self.count += 1
        self.total_similarity += similarity
        self.avg_similarity = self.total_similarity / self.count
        self.best_similarity = max(self.best_similarity, similarity)
        self.last_used = datetime.now()
    
    def get_effectiveness_score(self) -> float:
        """
        효과성 점수를 계산합니다.
        
        Returns:
            float: 효과성 점수 (평균 유사도 * 사용 횟수 + 최고 유사도 보너스)
        """
        base_score = self.avg_similarity * self.count
        best_bonus = self.best_similarity * 0.5
        return base_score + best_bonus


class GameSession:
    """
    현재 게임 세션의 상태를 관리하는 클래스
    """
    
    def __init__(self):
        """게임 세션을 초기화합니다."""
        self.guesses: List[GuessResult] = []
        self.tried_words: set = set()
        self.session_start: datetime = datetime.now()
        self.session_relationships: Dict[str, List[tuple]] = {}
        self.current_strategy: Optional[str] = None
        self.strategy_history: List[str] = []
    
    def add_guess(self, guess_result: GuessResult) -> None:
        """
        새로운 추측 결과를 추가합니다.
        
        Args:
            guess_result (GuessResult): 추측 결과
        """
        self.guesses.append(guess_result)
        self.tried_words.add(guess_result.word)
        
        # 유사도 순으로 정렬 (높은 순)
        self.guesses.sort(key=lambda g: g.similarity, reverse=True)
    
    def get_best_similarity(self) -> float:
        """
        현재까지의 최고 유사도를 반환합니다.
        
        Returns:
            float: 최고 유사도 (추측이 없으면 0.0)
        """
        if not self.guesses:
            return 0.0
        return max(g.similarity for g in self.guesses)
    
    def get_recent_guesses(self, count: int = 3) -> List[GuessResult]:
        """
        최근 추측들을 반환합니다.
        
        Args:
            count (int): 반환할 추측 개수
            
        Returns:
            List[GuessResult]: 최근 추측들
        """
        return self.guesses[-count:] if len(self.guesses) >= count else self.guesses
    
    def is_stagnant(self, window_size: int = 3, threshold: float = 0.01) -> bool:
        """
        정체 상태인지 확인합니다.
        
        Args:
            window_size (int): 확인할 최근 추측 개수
            threshold (float): 개선 임계값
            
        Returns:
            bool: 정체 상태 여부
        """
        if len(self.guesses) < window_size:
            return False
        
        recent_guesses = self.get_recent_guesses(window_size)
        recent_max = max(g.similarity for g in recent_guesses)
        best_similarity = self.get_best_similarity()
        
        return recent_max <= best_similarity + threshold
    
    def update_strategy(self, strategy_name: str) -> None:
        """
        현재 전략을 업데이트합니다.
        
        Args:
            strategy_name (str): 전략 이름
        """
        self.current_strategy = strategy_name
        if not self.strategy_history or self.strategy_history[-1] != strategy_name:
            self.strategy_history.append(strategy_name)
    
    def get_session_duration(self) -> float:
        """
        세션 진행 시간을 초 단위로 반환합니다.
        
        Returns:
            float: 세션 진행 시간 (초)
        """
        return (datetime.now() - self.session_start).total_seconds()
    
    def get_top_guesses(self, count: int = 3) -> List[GuessResult]:
        """
        상위 유사도 추측들을 반환합니다.
        
        Args:
            count (int): 반환할 추측 개수
            
        Returns:
            List[GuessResult]: 상위 유사도 추측들
        """
        sorted_guesses = sorted(self.guesses, key=lambda g: g.similarity, reverse=True)
        return sorted_guesses[:count]