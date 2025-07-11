#!/usr/bin/env python3
"""
개선된 알고리즘 테스트 스크립트
학습 데이터를 사용하여 개선된 전략의 효과를 검증합니다.
"""

import json
from modules.models import GameSession, GuessResult
from modules.strategy_engine import StrategyEngine
from modules.learning_engine import LearningEngine

def test_improved_algorithm():
    """개선된 알고리즘을 테스트합니다."""
    
    # 학습 엔진 초기화
    learning_engine = LearningEngine('kkomantle_learning.json', 'word_pairs.json')
    
    # 테스트용 어휘
    test_vocab = ["사람", "시간", "사랑", "자연", "음식", "기술", "감정", "장소", "행동", "생각",
                  "문제", "세상", "사회", "교육", "정치", "경제", "문화", "과학", "예술", "건강",
                  "가족", "친구", "학교", "회사", "도시", "나라", "미래", "과거", "현재", "역사"]
    
    # 전략 엔진 초기화
    strategy_engine = StrategyEngine()
    
    # 테스트 세션 생성
    session = GameSession()
    
    # 학습 데이터 준비
    learned_data = {
        'word_frequency': learning_engine.learning_data.get('word_frequency', {}),
        'word_pairs': learning_engine.word_pairs
    }
    
    print("🧪 개선된 알고리즘 테스트")
    print("=" * 50)
    
    # 1. 초기 단어 선택 테스트
    print("\n1. 초기 단어 선택 (학습 데이터 기반):")
    for i in range(5):
        word = strategy_engine.select_next_word(session, test_vocab, learned_data)
        print(f"   시도 {i+1}: {word}")
        # 가상의 결과 추가 (테스트용)
        session.add_guess(GuessResult(word, 0.1 + i * 0.05, 100 - i * 10, i + 1))
    
    # 2. 전략 전환 테스트
    print("\n2. 유사도 변화에 따른 전략 전환:")
    similarity_levels = [0.05, 0.15, 0.25, 0.35, 0.45, 0.55, 0.65]
    
    for sim in similarity_levels:
        # 최고 유사도 단어 업데이트
        best_word = f"테스트{int(sim*100)}"
        session.add_guess(GuessResult(best_word, sim, int(100 - sim * 100), len(session.guesses) + 1))
        
        strategy = strategy_engine.select_strategy(session)
        print(f"   유사도 {sim:.2f}: {strategy.get_strategy_name()}")
    
    # 3. 정체 상태 처리 테스트
    print("\n3. 정체 상태 감지 및 전략 변경:")
    # 정체 상태 시뮬레이션
    for i in range(5):
        session.add_guess(GuessResult(f"정체{i}", 0.35, 50, len(session.guesses) + 1))
    
    if session.is_stagnant():
        print("   ✓ 정체 상태 감지됨")
        strategy = strategy_engine.select_strategy(session)
        print(f"   → 새로운 전략: {strategy.get_strategy_name()}")
    
    # 4. 학습 데이터 활용도 확인
    print("\n4. 학습 데이터 활용도:")
    word_freq = learning_engine.learning_data.get('word_frequency', {})
    word_pairs = learning_engine.word_pairs
    
    print(f"   - 학습된 단어 수: {len(word_freq)}")
    print(f"   - 학습된 단어 쌍: {len(word_pairs)}")
    
    # 상위 효과적인 단어들
    if word_freq:
        effective_words = sorted(
            [(w, d['avg_similarity']) for w, d in word_freq.items() if d['count'] > 2],
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        print("   - 상위 효과적인 단어들:")
        for word, avg_sim in effective_words:
            print(f"     • {word}: 평균 유사도 {avg_sim:.3f}")
    
    print("\n✅ 테스트 완료")

if __name__ == "__main__":
    test_improved_algorithm()