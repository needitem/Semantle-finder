#!/usr/bin/env python3
"""
전략 로거 모듈
게임 진행 과정과 전략 선택을 상세히 기록하여 분석 가능하게 합니다.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import defaultdict

from .models import GuessResult, GameSession


class StrategyLogger:
    """
    전략 실행 과정을 기록하고 분석하는 로거
    """
    
    def __init__(self, log_file: str = 'strategy_logs.json'):
        """
        로거를 초기화합니다.
        
        Args:
            log_file (str): 로그 파일 경로
        """
        self.log_file = log_file
        self.current_session_log = None
        self.logs = self._load_logs()
    
    def _load_logs(self) -> List[Dict]:
        """기존 로그를 로드합니다."""
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def start_session(self, session_id: str) -> None:
        """
        새로운 게임 세션 로깅을 시작합니다.
        
        Args:
            session_id (str): 세션 ID
        """
        self.current_session_log = {
            'session_id': session_id,
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'success': False,
            'final_answer': None,
            'total_attempts': 0,
            'best_similarity': 0,
            'strategy_changes': [],
            'word_selections': [],
            'similarity_progression': [],
            'stagnant_periods': []
        }
    
    def log_word_selection(self, attempt: int, word: str, strategy: str, 
                          selection_reason: Dict[str, Any], candidates_considered: int) -> None:
        """
        단어 선택 과정을 기록합니다.
        
        Args:
            attempt (int): 시도 횟수
            word (str): 선택된 단어
            strategy (str): 사용된 전략
            selection_reason (Dict): 선택 이유 (점수, 요소별 기여도 등)
            candidates_considered (int): 고려된 후보 단어 수
        """
        if self.current_session_log:
            self.current_session_log['word_selections'].append({
                'attempt': attempt,
                'word': word,
                'strategy': strategy,
                'selection_reason': selection_reason,
                'candidates_considered': candidates_considered,
                'timestamp': datetime.now().isoformat()
            })
    
    def log_result(self, result: GuessResult) -> None:
        """
        추측 결과를 기록합니다.
        
        Args:
            result (GuessResult): 추측 결과
        """
        if self.current_session_log:
            self.current_session_log['similarity_progression'].append({
                'word': result.word,
                'similarity': result.similarity,
                'rank': result.rank,
                'attempt': result.attempt
            })
            
            # 최고 유사도 업데이트
            if result.similarity > self.current_session_log['best_similarity']:
                self.current_session_log['best_similarity'] = result.similarity
    
    def log_strategy_change(self, from_strategy: str, to_strategy: str, 
                           reason: str, current_similarity: float) -> None:
        """
        전략 변경을 기록합니다.
        
        Args:
            from_strategy (str): 이전 전략
            to_strategy (str): 새로운 전략
            reason (str): 변경 이유
            current_similarity (float): 현재 최고 유사도
        """
        if self.current_session_log:
            self.current_session_log['strategy_changes'].append({
                'from': from_strategy,
                'to': to_strategy,
                'reason': reason,
                'similarity_at_change': current_similarity,
                'attempt': len(self.current_session_log['similarity_progression'])
            })
    
    def log_stagnant_period(self, start_attempt: int, end_attempt: int, 
                           similarity_level: float) -> None:
        """
        정체 기간을 기록합니다.
        
        Args:
            start_attempt (int): 정체 시작 시도
            end_attempt (int): 정체 종료 시도
            similarity_level (float): 정체 시 유사도
        """
        if self.current_session_log:
            self.current_session_log['stagnant_periods'].append({
                'start': start_attempt,
                'end': end_attempt,
                'duration': end_attempt - start_attempt,
                'similarity_level': similarity_level
            })
    
    def end_session(self, success: bool, final_answer: Optional[str] = None) -> None:
        """
        게임 세션을 종료하고 로그를 저장합니다.
        
        Args:
            success (bool): 성공 여부
            final_answer (Optional[str]): 정답 (성공시)
        """
        if self.current_session_log:
            self.current_session_log['end_time'] = datetime.now().isoformat()
            self.current_session_log['success'] = success
            self.current_session_log['final_answer'] = final_answer
            self.current_session_log['total_attempts'] = len(
                self.current_session_log['similarity_progression'])
            
            # 로그 저장
            self.logs.append(self.current_session_log)
            self._save_logs()
            
            # 세션 로그 초기화
            self.current_session_log = None
    
    def _save_logs(self) -> None:
        """로그를 파일에 저장합니다."""
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(self.logs, f, ensure_ascii=False, indent=2)
    
    def analyze_strategy_effectiveness(self) -> Dict[str, Any]:
        """
        전략별 효과성을 분석합니다.
        
        Returns:
            Dict: 전략별 통계
        """
        strategy_stats = defaultdict(lambda: {
            'total_uses': 0,
            'successful_transitions': 0,
            'avg_similarity_gain': 0,
            'similarity_gains': []
        })
        
        for log in self.logs:
            # 전략 변경 분석
            for i, change in enumerate(log['strategy_changes']):
                strategy = change['to']
                strategy_stats[strategy]['total_uses'] += 1
                
                # 전략 변경 후 유사도 증가 측정
                change_attempt = change['attempt']
                if change_attempt < len(log['similarity_progression']) - 1:
                    before_sim = log['similarity_progression'][change_attempt]['similarity']
                    after_sim = log['similarity_progression'][min(change_attempt + 5, 
                                                                len(log['similarity_progression']) - 1)]['similarity']
                    gain = after_sim - before_sim
                    
                    strategy_stats[strategy]['similarity_gains'].append(gain)
                    if gain > 5:  # 의미있는 증가 (0-100 scale)
                        strategy_stats[strategy]['successful_transitions'] += 1
        
        # 평균 계산
        for strategy, stats in strategy_stats.items():
            if stats['similarity_gains']:
                stats['avg_similarity_gain'] = sum(stats['similarity_gains']) / len(stats['similarity_gains'])
            del stats['similarity_gains']  # 메모리 절약
        
        return dict(strategy_stats)
    
    def analyze_word_patterns(self) -> Dict[str, Any]:
        """
        성공적인 단어 선택 패턴을 분석합니다.
        
        Returns:
            Dict: 단어 패턴 분석 결과
        """
        successful_patterns = {
            'high_impact_words': [],  # 큰 유사도 증가를 가져온 단어들
            'effective_initial_words': [],  # 효과적인 초기 단어들
            'breakthrough_words': []  # 정체 상태를 돌파한 단어들
        }
        
        for log in self.logs:
            if not log['similarity_progression']:
                continue
                
            # 큰 유사도 증가를 가져온 단어 찾기
            for i in range(1, len(log['similarity_progression'])):
                prev = log['similarity_progression'][i-1]
                curr = log['similarity_progression'][i]
                
                gain = curr['similarity'] - prev['similarity']
                if gain > 10:  # 10 이상 증가 (0-100 scale)
                    successful_patterns['high_impact_words'].append({
                        'word': curr['word'],
                        'gain': gain,
                        'from_similarity': prev['similarity']
                    })
            
            # 효과적인 초기 단어 (첫 10회 시도)
            if len(log['similarity_progression']) > 10:
                initial_words = log['similarity_progression'][:10]
                for word_data in initial_words:
                    if word_data['similarity'] > 15:  # 0-100 scale
                        successful_patterns['effective_initial_words'].append({
                            'word': word_data['word'],
                            'similarity': word_data['similarity'],
                            'attempt': word_data['attempt']
                        })
            
            # 정체 돌파 단어
            for period in log['stagnant_periods']:
                if period['end'] < len(log['similarity_progression']) - 1:
                    breakthrough_word = log['similarity_progression'][period['end'] + 1]
                    if breakthrough_word['similarity'] > period['similarity_level'] + 5:  # 0-100 scale
                        successful_patterns['breakthrough_words'].append({
                            'word': breakthrough_word['word'],
                            'stagnant_level': period['similarity_level'],
                            'new_level': breakthrough_word['similarity']
                        })
        
        return successful_patterns
    
    def get_recommendations(self) -> Dict[str, Any]:
        """
        로그 분석을 기반으로 전략 개선 추천사항을 생성합니다.
        
        Returns:
            Dict: 추천사항
        """
        strategy_stats = self.analyze_strategy_effectiveness()
        word_patterns = self.analyze_word_patterns()
        
        recommendations = {
            'best_strategies': [],
            'avoid_strategies': [],
            'recommended_initial_words': [],
            'strategy_transition_rules': []
        }
        
        # 최고/최악 전략 식별
        for strategy, stats in strategy_stats.items():
            if stats['avg_similarity_gain'] > 5:  # 0-100 scale
                recommendations['best_strategies'].append({
                    'strategy': strategy,
                    'avg_gain': stats['avg_similarity_gain'],
                    'success_rate': stats['successful_transitions'] / max(stats['total_uses'], 1)
                })
            elif stats['avg_similarity_gain'] < -2:  # 0-100 scale
                recommendations['avoid_strategies'].append(strategy)
        
        # 추천 초기 단어
        word_freq = defaultdict(int)
        for word_info in word_patterns['effective_initial_words']:
            word_freq[word_info['word']] += 1
        
        recommendations['recommended_initial_words'] = [
            word for word, count in sorted(word_freq.items(), 
                                          key=lambda x: x[1], reverse=True)[:10]
        ]
        
        return recommendations