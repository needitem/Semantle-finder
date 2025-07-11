#!/usr/bin/env python3
"""
상세 로그 뷰어
게임 진행 과정을 시각적으로 분석합니다.
"""

import json
import os
from modules.strategy_logger import StrategyLogger


def view_game_progression(game_index: int = 0):
    """특정 게임의 진행 과정을 상세히 출력합니다."""
    
    logger = StrategyLogger()
    
    if game_index >= len(logger.logs):
        print(f"❌ 게임 인덱스 {game_index}가 범위를 벗어났습니다. (총 {len(logger.logs)}개 게임)")
        return
    
    log = logger.logs[game_index]
    
    print(f"\n🎮 게임 #{game_index + 1} 상세 분석")
    print("=" * 80)
    print(f"세션 ID: {log['session_id']}")
    print(f"결과: {'성공' if log['success'] else '실패'}")
    print(f"총 시도: {log['total_attempts']}회")
    print(f"최고 유사도: {log['best_similarity']:.2f}")
    
    # 유사도 진행 그래프
    print("\n📈 유사도 진행 과정:")
    print("-" * 80)
    
    # 10개씩 묶어서 표시
    progression = log['similarity_progression']
    for i in range(0, len(progression), 10):
        batch = progression[i:i+10]
        print(f"\n시도 {i+1}-{i+len(batch)}:")
        
        for item in batch:
            bar_length = int(item['similarity'] / 2)  # 0-100을 0-50으로 스케일
            bar = "█" * bar_length
            print(f"  {item['attempt']:3d}. {item['word']:10s} {bar:50s} {item['similarity']:6.2f}")
    
    # 전략 변경 이력
    print("\n🔄 전략 변경 이력:")
    print("-" * 80)
    for change in log['strategy_changes']:
        print(f"  시도 {change['attempt']}: {change['from']} → {change['to']}")
        print(f"    이유: {change['reason']} (유사도: {change['similarity_at_change']:.2f})")
    
    # 정체 구간
    print("\n⏸️ 정체 구간:")
    print("-" * 80)
    for period in log['stagnant_periods']:
        print(f"  시도 {period['start']}-{period['end']} ({period['duration']}회)")
        print(f"    정체 수준: {period['similarity_level']:.2f}")
    
    # 큰 도약을 보인 단어들
    print("\n🚀 큰 도약 단어 (10+ 증가):")
    print("-" * 80)
    for i in range(1, len(progression)):
        prev = progression[i-1]
        curr = progression[i]
        gain = curr['similarity'] - prev['similarity']
        
        if gain > 10:
            print(f"  {curr['word']}: +{gain:.2f} ({prev['similarity']:.2f} → {curr['similarity']:.2f})")


def analyze_word_effectiveness():
    """단어별 효과성을 분석합니다."""
    
    # 학습 데이터 로드
    if os.path.exists('kkomantle_learning.json'):
        with open('kkomantle_learning.json', 'r', encoding='utf-8') as f:
            learning_data = json.load(f)
    else:
        print("❌ 학습 데이터 파일이 없습니다.")
        return
    
    word_freq = learning_data.get('word_frequency', {})
    
    print("\n📊 단어별 효과성 분석")
    print("=" * 80)
    
    # 효과성 점수 계산
    word_scores = []
    for word, data in word_freq.items():
        if data['count'] >= 2:  # 2회 이상 사용된 단어만
            effectiveness = data['avg_similarity'] * data['count']
            word_scores.append((word, data['avg_similarity'], data['count'], effectiveness))
    
    # 효과성 순으로 정렬
    word_scores.sort(key=lambda x: x[3], reverse=True)
    
    print(f"{'단어':10s} {'평균유사도':>10s} {'사용횟수':>8s} {'효과성점수':>10s}")
    print("-" * 50)
    
    for word, avg_sim, count, effectiveness in word_scores[:20]:
        print(f"{word:10s} {avg_sim:10.2f} {count:8d} {effectiveness:10.2f}")


def find_promising_patterns():
    """유망한 패턴을 찾습니다."""
    
    logger = StrategyLogger()
    
    print("\n🔍 유망한 패턴 분석")
    print("=" * 80)
    
    # 모든 게임에서 높은 유사도를 달성한 단어 시퀀스 찾기
    high_similarity_sequences = []
    
    for log in logger.logs:
        progression = log['similarity_progression']
        
        # 50 이상의 유사도를 달성한 구간 찾기
        for i in range(len(progression)):
            if progression[i]['similarity'] > 50:
                # 이전 5개 단어 시퀀스 추출
                start_idx = max(0, i-5)
                sequence = [p['word'] for p in progression[start_idx:i+1]]
                final_sim = progression[i]['similarity']
                
                high_similarity_sequences.append({
                    'sequence': sequence,
                    'final_similarity': final_sim,
                    'words_before': i - start_idx
                })
    
    # 패턴 분석
    if high_similarity_sequences:
        print(f"\n50+ 유사도 달성 시퀀스 ({len(high_similarity_sequences)}개):")
        
        for seq in sorted(high_similarity_sequences, key=lambda x: x['final_similarity'], reverse=True)[:10]:
            print(f"\n  최종 유사도: {seq['final_similarity']:.2f}")
            print(f"  시퀀스: {' → '.join(seq['sequence'])}")


def export_csv_report():
    """CSV 형식으로 리포트를 내보냅니다."""
    
    logger = StrategyLogger()
    
    with open('game_analysis.csv', 'w', encoding='utf-8-sig') as f:
        f.write("게임번호,시도횟수,단어,유사도,순위,전략\n")
        
        for game_idx, log in enumerate(logger.logs):
            current_strategy = "초기"
            strategy_idx = 0
            
            for item in log['similarity_progression']:
                # 현재 전략 확인
                while (strategy_idx < len(log['strategy_changes']) and 
                       item['attempt'] >= log['strategy_changes'][strategy_idx]['attempt']):
                    current_strategy = log['strategy_changes'][strategy_idx]['to']
                    strategy_idx += 1
                
                f.write(f"{game_idx+1},{item['attempt']},{item['word']},{item['similarity']:.2f},{item['rank']},{current_strategy}\n")
    
    print("\n📄 CSV 리포트 저장됨: game_analysis.csv")


if __name__ == "__main__":
    print("🔍 상세 로그 분석 도구")
    print("=" * 80)
    
    # 게임 진행 과정 보기
    view_game_progression(0)  # 첫 번째 게임
    
    # 단어 효과성 분석
    analyze_word_effectiveness()
    
    # 유망한 패턴 찾기
    find_promising_patterns()
    
    # CSV 내보내기
    export_csv_report()