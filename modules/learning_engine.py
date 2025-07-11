#!/usr/bin/env python3
"""
학습 엔진 모듈
실시간 관계 학습과 지식 지속성을 담당하는 모듈입니다.
"""

import json
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from .models import (GuessResult, GameSession, WordPairData, 
                   SuccessPattern, WordFrequencyData)


class LearningEngine:
    """
    학습 엔진: 단어 간 관계 학습과 성공 패턴 인식을 담당합니다.
    """
    
    def __init__(self, learning_file: str = 'kkomantle_learning.json',
                 word_pairs_file: str = 'word_pairs.json'):
        """
        학습 엔진을 초기화합니다.
        
        Args:
            learning_file (str): 학습 데이터 파일 경로
            word_pairs_file (str): 단어 쌍 데이터 파일 경로
        """
        self.learning_file = learning_file
        self.word_pairs_file = word_pairs_file
        
        # 학습 데이터 로드
        self.learning_data = self._load_learning_data()
        self.word_pairs = self._load_word_pairs()
        
        print(f"🧠 기존 학습 데이터: {len(self.word_pairs)}개 단어 쌍, "
              f"{len(self.learning_data.get('successful_patterns', []))}개 성공 패턴")
    
    def _load_learning_data(self) -> Dict:
        """
        지속적 학습 데이터를 로드합니다.
        
        Returns:
            Dict: 학습 데이터 딕셔너리
        """
        if os.path.exists(self.learning_file):
            try:
                with open(self.learning_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"✅ 학습 데이터 로드 완료: {self.learning_file}")
                    return data
            except Exception as e:
                print(f"⚠️ 학습 데이터 로드 실패: {e}")
        
        # 기본 구조 반환
        return {
            'games_played': 0,
            'successful_patterns': [],
            'category_effectiveness': {},
            'word_frequency': {},
            'best_strategies': [],
            'last_updated': datetime.now().isoformat()
        }
    
    def _load_word_pairs(self) -> Dict[str, Dict]:
        """
        단어 쌍 유사도 데이터를 로드합니다.
        
        Returns:
            Dict[str, Dict]: 단어 쌍 데이터 딕셔너리
        """
        if os.path.exists(self.word_pairs_file):
            try:
                with open(self.word_pairs_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"✅ 단어 쌍 데이터 로드 완료: {self.word_pairs_file}")
                    return data
            except Exception as e:
                print(f"⚠️ 단어 쌍 데이터 로드 실패: {e}")
        
        return {}
    
    def save_learning_data(self) -> bool:
        """
        학습 데이터를 파일에 저장합니다.
        
        Returns:
            bool: 저장 성공 여부
        """
        try:
            # 마지막 업데이트 시간 갱신
            self.learning_data['last_updated'] = datetime.now().isoformat()
            
            with open(self.learning_file, 'w', encoding='utf-8') as f:
                json.dump(self.learning_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"⚠️ 학습 데이터 저장 실패: {e}")
            return False
    
    def save_word_pairs(self) -> bool:
        """
        단어 쌍 데이터를 파일에 저장합니다.
        
        Returns:
            bool: 저장 성공 여부
        """
        try:
            with open(self.word_pairs_file, 'w', encoding='utf-8') as f:
                json.dump(self.word_pairs, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"⚠️ 단어 쌍 데이터 저장 실패: {e}")
            return False
    
    def learn_word_relationships(self, new_guess: GuessResult, 
                               existing_guesses: List[GuessResult]) -> None:
        """
        새로운 추측을 기반으로 단어 간 관계를 학습합니다.
        
        Args:
            new_guess (GuessResult): 새로운 추측 결과
            existing_guesses (List[GuessResult]): 기존 추측들
        """
        # 기존 추측들과의 관계 학습
        for existing_guess in existing_guesses:
            if existing_guess.word != new_guess.word:
                similarity_diff = abs(new_guess.similarity - existing_guess.similarity)
                
                # 단어 쌍 키 생성 (사전식 순서로 정렬)
                pair_key = self._create_pair_key(new_guess.word, existing_guess.word)
                
                # 단어 쌍 데이터 업데이트
                self._update_word_pair(pair_key, similarity_diff)
        
        # 단어 빈도 데이터 업데이트
        self._update_word_frequency(new_guess.word, new_guess.similarity)
    
    def _create_pair_key(self, word1: str, word2: str) -> str:
        """
        단어 쌍의 고유 키를 생성합니다.
        
        Args:
            word1 (str): 첫 번째 단어
            word2 (str): 두 번째 단어
            
        Returns:
            str: 단어 쌍 키
        """
        # 사전식 순서로 정렬하여 일관성 보장
        return f"{min(word1, word2)}|{max(word1, word2)}"
    
    def _update_word_pair(self, pair_key: str, similarity_diff: float) -> None:
        """
        단어 쌍의 유사도 차이 데이터를 업데이트합니다.
        
        Args:
            pair_key (str): 단어 쌍 키
            similarity_diff (float): 유사도 차이
        """
        if pair_key not in self.word_pairs:
            self.word_pairs[pair_key] = {
                'similarity_diffs': [],
                'co_occurrence_count': 0,
                'last_updated': datetime.now().isoformat()
            }
        
        # 유사도 차이 추가
        self.word_pairs[pair_key]['similarity_diffs'].append(similarity_diff)
        self.word_pairs[pair_key]['co_occurrence_count'] += 1
        self.word_pairs[pair_key]['last_updated'] = datetime.now().isoformat()
        
        # 메모리 절약을 위해 최대 100개 기록만 유지
        if len(self.word_pairs[pair_key]['similarity_diffs']) > 100:
            self.word_pairs[pair_key]['similarity_diffs'] = \
                self.word_pairs[pair_key]['similarity_diffs'][-50:]
    
    def _update_word_frequency(self, word: str, similarity: float) -> None:
        """
        단어의 사용 빈도와 성과 데이터를 업데이트합니다.
        
        Args:
            word (str): 단어
            similarity (float): 유사도 점수
        """
        if 'word_frequency' not in self.learning_data:
            self.learning_data['word_frequency'] = {}
        
        if word not in self.learning_data['word_frequency']:
            self.learning_data['word_frequency'][word] = {
                'count': 0,
                'avg_similarity': 0.0,
                'best_similarity': 0.0,
                'total_similarity': 0.0,
                'last_used': datetime.now().isoformat()
            }
        
        # 빈도 데이터 업데이트
        freq_data = self.learning_data['word_frequency'][word]
        freq_data['count'] += 1
        
        # 기존 데이터 호환성 확인
        if 'total_similarity' not in freq_data:
            freq_data['total_similarity'] = freq_data.get('avg_similarity', 0.0) * freq_data.get('count', 1)
        
        freq_data['total_similarity'] += similarity
        freq_data['avg_similarity'] = freq_data['total_similarity'] / freq_data['count']
        freq_data['best_similarity'] = max(freq_data['best_similarity'], similarity)
        freq_data['last_used'] = datetime.now().isoformat()
    
    def get_related_words(self, target_word: str, similarity_threshold: float = 10) -> List[str]:
        """
        학습된 데이터에서 특정 단어와 관련성이 높은 단어들을 찾습니다.
        
        Args:
            target_word (str): 대상 단어
            similarity_threshold (float): 유사도 차이 임계값
            
        Returns:
            List[str]: 관련성이 높은 단어들의 리스트
        """
        related_words = []
        
        for pair_key, pair_data in self.word_pairs.items():
            word1, word2 = pair_key.split('|')
            
            # 대상 단어가 포함된 쌍 찾기
            if word1 == target_word or word2 == target_word:
                other_word = word2 if word1 == target_word else word1
                
                # 평균 유사도 차이 계산
                similarity_diffs = pair_data.get('similarity_diffs', [])
                if similarity_diffs:
                    avg_diff = sum(similarity_diffs) / len(similarity_diffs)
                    
                    # 임계값보다 유사도 차이가 작은 경우 관련성 높음
                    if avg_diff < similarity_threshold:
                        related_words.append((other_word, avg_diff))
        
        # 유사도 차이 순으로 정렬 (작은 순)
        related_words.sort(key=lambda x: x[1])
        return [word for word, _ in related_words]
    
    def calculate_effectiveness_score(self, word: str) -> float:
        """
        단어의 효과성 점수를 계산합니다.
        
        Args:
            word (str): 대상 단어
            
        Returns:
            float: 효과성 점수
        """
        word_frequency = self.learning_data.get('word_frequency', {})
        
        if word in word_frequency:
            freq_data = word_frequency[word]
            base_score = freq_data.get('avg_similarity', 0) * freq_data.get('count', 1)
            best_bonus = freq_data.get('best_similarity', 0) * 0.5
            return base_score + best_bonus
        
        return 0.0
    
    def record_successful_game(self, session: GameSession, final_answer: str) -> None:
        """
        성공한 게임의 패턴을 기록합니다.
        
        Args:
            session (GameSession): 완료된 게임 세션
            final_answer (str): 최종 정답
        """
        # 상위 5개 단어 추출
        top_guesses = session.get_top_guesses(5)
        key_words = [guess.word for guess in top_guesses]
        final_scores = [guess.similarity for guess in top_guesses]
        
        # 성공 패턴 생성
        success_pattern = {
            'answer': final_answer,
            'attempts': len(session.guesses),
            'key_words': key_words,
            'strategy_sequence': session.strategy_history.copy(),
            'timestamp': datetime.now().isoformat(),
            'final_similarity_scores': final_scores,
            'session_duration': session.get_session_duration()
        }
        
        # 성공 패턴 저장
        if 'successful_patterns' not in self.learning_data:
            self.learning_data['successful_patterns'] = []
        
        self.learning_data['successful_patterns'].append(success_pattern)
        
        # 최대 100개 성공 패턴만 유지 (메모리 절약)
        if len(self.learning_data['successful_patterns']) > 100:
            self.learning_data['successful_patterns'] = \
                self.learning_data['successful_patterns'][-50:]
        
        # 게임 횟수 증가
        self.learning_data['games_played'] += 1
        
        print(f"🎉 성공 패턴 저장: {final_answer} ({len(session.guesses)}회 시도)")
    
    def analyze_strategy_effectiveness(self) -> Dict[str, float]:
        """
        전략별 효과성을 분석합니다.
        
        Returns:
            Dict[str, float]: 전략별 평균 시도 횟수
        """
        strategy_stats = {}
        
        for pattern in self.learning_data.get('successful_patterns', []):
            strategies = pattern.get('strategy_sequence', [])
            attempts = pattern.get('attempts', 0)
            
            for strategy in strategies:
                if strategy not in strategy_stats:
                    strategy_stats[strategy] = {'total_attempts': 0, 'count': 0}
                
                strategy_stats[strategy]['total_attempts'] += attempts
                strategy_stats[strategy]['count'] += 1
        
        # 평균 계산
        effectiveness = {}
        for strategy, stats in strategy_stats.items():
            if stats['count'] > 0:
                effectiveness[strategy] = stats['total_attempts'] / stats['count']
        
        return effectiveness
    
    def get_successful_words_for_similarity_range(self, min_sim: float, 
                                                max_sim: float) -> List[str]:
        """
        특정 유사도 범위에서 성공적이었던 단어들을 반환합니다.
        
        Args:
            min_sim (float): 최소 유사도
            max_sim (float): 최대 유사도
            
        Returns:
            List[str]: 해당 범위에서 효과적이었던 단어들
        """
        successful_words = []
        
        for pattern in self.learning_data.get('successful_patterns', []):
            key_words = pattern.get('key_words', [])
            final_scores = pattern.get('final_similarity_scores', [])
            
            # 유사도 범위에 맞는 단어들 찾기
            for word, score in zip(key_words, final_scores):
                if min_sim <= score <= max_sim:
                    successful_words.append(word)
        
        # 빈도순으로 정렬하여 반환
        word_counts = {}
        for word in successful_words:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        return sorted(word_counts.keys(), key=lambda w: word_counts[w], reverse=True)
    
    def save_session_results(self, session: GameSession, success: bool = False, 
                           final_answer: str = None) -> None:
        """
        세션 결과를 저장하고 학습 데이터를 업데이트합니다.
        
        Args:
            session (GameSession): 게임 세션
            success (bool): 성공 여부
            final_answer (str): 최종 정답 (성공한 경우)
        """
        # 성공한 경우 패턴 기록
        if success and final_answer:
            self.record_successful_game(session, final_answer)
        
        # 전략 효과성 업데이트
        self._update_strategy_effectiveness(session)
        
        # 데이터 저장
        save_success = self.save_learning_data() and self.save_word_pairs()
        
        if save_success:
            print(f"💾 학습 데이터 업데이트 완료 (총 게임: {self.learning_data['games_played']})")
        else:
            print("⚠️ 학습 데이터 저장 중 오류 발생")
    
    def _update_strategy_effectiveness(self, session: GameSession) -> None:
        """
        전략 효과성 데이터를 업데이트합니다.
        
        Args:
            session (GameSession): 게임 세션
        """
        if 'strategy_effectiveness' not in self.learning_data:
            self.learning_data['strategy_effectiveness'] = {}
        
        # 사용된 전략들에 대한 통계 업데이트
        for strategy in session.strategy_history:
            if strategy not in self.learning_data['strategy_effectiveness']:
                self.learning_data['strategy_effectiveness'][strategy] = {
                    'usage_count': 0,
                    'total_attempts': 0,
                    'avg_attempts': 0.0
                }
            
            stats = self.learning_data['strategy_effectiveness'][strategy]
            stats['usage_count'] += 1
            stats['total_attempts'] += len(session.guesses)
            stats['avg_attempts'] = stats['total_attempts'] / stats['usage_count']
    
    def get_learning_statistics(self) -> Dict:
        """
        현재 학습 상태의 통계를 반환합니다.
        
        Returns:
            Dict: 학습 통계 정보
        """
        stats = {
            'total_games': self.learning_data.get('games_played', 0),
            'total_word_pairs': len(self.word_pairs),
            'total_unique_words': len(self.learning_data.get('word_frequency', {})),
            'successful_patterns': len(self.learning_data.get('successful_patterns', [])),
            'strategy_effectiveness': self.analyze_strategy_effectiveness(),
            'last_updated': self.learning_data.get('last_updated', 'Unknown')
        }
        
        # 가장 효과적인 단어 상위 5개
        word_frequency = self.learning_data.get('word_frequency', {})
        if word_frequency:
            effective_words = sorted(
                word_frequency.items(), 
                key=lambda x: self.calculate_effectiveness_score(x[0]),
                reverse=True
            )[:5]
            stats['most_effective_words'] = [word for word, _ in effective_words]
        else:
            stats['most_effective_words'] = []
        
        return stats