#!/usr/bin/env python3
"""
전략 로그 분석 스크립트
게임 로그를 분석하여 전략 개선 방안을 도출합니다.
"""

import json
import os
from collections import defaultdict
from modules.strategy_logger import StrategyLogger


def analyze_strategy_logs():
    """전략 로그를 분석하고 보고서를 생성합니다."""
    
    # 로거 초기화
    logger = StrategyLogger()
    
    print("📊 전략 로그 분석")
    print("=" * 60)
    
    # 기본 통계
    total_games = len(logger.logs)
    successful_games = sum(1 for log in logger.logs if log['success'])
    
    print(f"\n📈 기본 통계:")
    print(f"   • 총 게임 수: {total_games}")
    print(f"   • 성공한 게임: {successful_games}")
    print(f"   • 성공률: {successful_games/max(total_games, 1)*100:.1f}%")
    
    if total_games == 0:
        print("\n⚠️ 분석할 로그가 없습니다. 먼저 게임을 실행해주세요.")
        return
    
    # 평균 시도 횟수
    avg_attempts = sum(log['total_attempts'] for log in logger.logs) / total_games
    avg_attempts_success = sum(log['total_attempts'] for log in logger.logs if log['success']) / max(successful_games, 1)
    
    print(f"   • 평균 시도 횟수: {avg_attempts:.1f}")
    print(f"   • 성공 시 평균 시도: {avg_attempts_success:.1f}")
    
    # 전략별 효과성 분석
    print("\n🎯 전략별 효과성:")
    strategy_stats = logger.analyze_strategy_effectiveness()
    
    for strategy, stats in sorted(strategy_stats.items(), 
                                 key=lambda x: x[1]['avg_similarity_gain'], 
                                 reverse=True):
        print(f"\n   {strategy}:")
        print(f"     • 사용 횟수: {stats['total_uses']}")
        print(f"     • 평균 유사도 증가: {stats['avg_similarity_gain']:.3f}")
        success_rate = stats['successful_transitions'] / max(stats['total_uses'], 1) * 100
        print(f"     • 성공적 전환율: {success_rate:.1f}%")
    
    # 단어 패턴 분석
    print("\n💡 성공적인 단어 패턴:")
    word_patterns = logger.analyze_word_patterns()
    
    # 높은 영향력 단어들
    if word_patterns['high_impact_words']:
        print("\n   고영향 단어 (유사도 0.1+ 증가):")
        impact_words = defaultdict(list)
        for item in word_patterns['high_impact_words']:
            impact_words[item['word']].append(item['gain'])
        
        # 평균 영향력 계산
        avg_impacts = []
        for word, gains in impact_words.items():
            avg_gain = sum(gains) / len(gains)
            avg_impacts.append((word, avg_gain, len(gains)))
        
        for word, avg_gain, count in sorted(avg_impacts, key=lambda x: x[1], reverse=True)[:10]:
            print(f"     • {word}: 평균 +{avg_gain:.3f} (사용 {count}회)")
    
    # 효과적인 초기 단어들
    if word_patterns['effective_initial_words']:
        print("\n   효과적인 초기 단어:")
        initial_word_freq = defaultdict(int)
        for item in word_patterns['effective_initial_words']:
            initial_word_freq[item['word']] += 1
        
        for word, count in sorted(initial_word_freq.items(), 
                                 key=lambda x: x[1], reverse=True)[:10]:
            print(f"     • {word}: {count}회")
    
    # 정체 돌파 단어들
    if word_patterns['breakthrough_words']:
        print("\n   정체 돌파 단어:")
        breakthrough_freq = defaultdict(int)
        for item in word_patterns['breakthrough_words']:
            breakthrough_freq[item['word']] += 1
        
        for word, count in sorted(breakthrough_freq.items(), 
                                 key=lambda x: x[1], reverse=True)[:5]:
            print(f"     • {word}: {count}회")
    
    # 추천사항
    print("\n🚀 개선 추천사항:")
    recommendations = logger.get_recommendations()
    
    if recommendations['best_strategies']:
        print("\n   최고 성능 전략:")
        for item in recommendations['best_strategies']:
            print(f"     • {item['strategy']}: 평균 증가 {item['avg_gain']:.3f}")
    
    if recommendations['avoid_strategies']:
        print("\n   피해야 할 전략:")
        for strategy in recommendations['avoid_strategies']:
            print(f"     • {strategy}")
    
    if recommendations['recommended_initial_words']:
        print("\n   추천 초기 단어:")
        print(f"     {', '.join(recommendations['recommended_initial_words'][:5])}")
    
    # 정체 분석
    print("\n⏸️ 정체 상태 분석:")
    stagnant_periods = []
    for log in logger.logs:
        stagnant_periods.extend(log['stagnant_periods'])
    
    if stagnant_periods:
        avg_duration = sum(p['duration'] for p in stagnant_periods) / len(stagnant_periods)
        avg_level = sum(p['similarity_level'] for p in stagnant_periods) / len(stagnant_periods)
        
        print(f"   • 평균 정체 기간: {avg_duration:.1f} 시도")
        print(f"   • 평균 정체 수준: {avg_level:.3f}")
    else:
        print("   • 정체 기간 없음")
    
    print("\n" + "=" * 60)
    print("✅ 분석 완료")


def export_detailed_report(output_file: str = 'strategy_analysis_report.json'):
    """상세 분석 리포트를 JSON 파일로 저장합니다."""
    
    logger = StrategyLogger()
    
    report = {
        'summary': {
            'total_games': len(logger.logs),
            'successful_games': sum(1 for log in logger.logs if log['success']),
            'avg_attempts': sum(log['total_attempts'] for log in logger.logs) / max(len(logger.logs), 1)
        },
        'strategy_effectiveness': logger.analyze_strategy_effectiveness(),
        'word_patterns': logger.analyze_word_patterns(),
        'recommendations': logger.get_recommendations(),
        'game_details': logger.logs
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"📄 상세 리포트 저장됨: {output_file}")


if __name__ == "__main__":
    analyze_strategy_logs()
    
    # 상세 리포트도 생성
    if os.path.exists('strategy_logs.json'):
        export_detailed_report()