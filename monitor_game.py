#!/usr/bin/env python3
"""
실시간 게임 모니터링
현재 진행 중인 게임의 로그를 실시간으로 모니터링합니다.
"""

import json
import os
import time
from datetime import datetime


def monitor_current_game():
    """현재 진행 중인 게임을 실시간 모니터링합니다."""
    
    log_file = 'strategy_logs.json'
    last_size = 0
    last_attempt = 0
    
    print("🎮 실시간 게임 모니터링 시작")
    print("(Ctrl+C로 종료)")
    print("=" * 80)
    
    while True:
        try:
            if os.path.exists(log_file):
                current_size = os.path.getsize(log_file)
                
                # 파일이 변경되었으면
                if current_size != last_size:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        logs = json.load(f)
                    
                    if logs:
                        current_log = logs[-1]  # 최신 게임
                        
                        # 새로운 시도가 있으면 출력
                        progression = current_log.get('similarity_progression', [])
                        if len(progression) > last_attempt:
                            # 새로운 시도들만 출력
                            for i in range(last_attempt, len(progression)):
                                item = progression[i]
                                
                                # 이전 시도와의 차이 계산
                                if i > 0:
                                    prev_sim = progression[i-1]['similarity']
                                    gain = item['similarity'] - prev_sim
                                    gain_str = f"+{gain:.2f}" if gain > 0 else f"{gain:.2f}"
                                else:
                                    gain_str = ""
                                
                                # 유사도에 따른 색상 (터미널 색상 코드)
                                if item['similarity'] > 70:
                                    color = "\033[92m"  # 녹색
                                elif item['similarity'] > 50:
                                    color = "\033[93m"  # 노란색
                                elif item['similarity'] > 30:
                                    color = "\033[94m"  # 파란색
                                else:
                                    color = "\033[0m"   # 기본
                                
                                # 막대 그래프
                                bar_length = int(item['similarity'] / 2)
                                bar = "█" * bar_length
                                
                                print(f"{color}[{datetime.now().strftime('%H:%M:%S')}] "
                                      f"{item['attempt']:3d}. {item['word']:10s} "
                                      f"{bar:50s} {item['similarity']:6.2f} {gain_str:>8s}\033[0m")
                                
                                # 큰 도약이면 강조
                                if i > 0 and gain > 10:
                                    print(f"    🚀 큰 도약! +{gain:.2f} 증가")
                            
                            last_attempt = len(progression)
                            
                            # 현재 상태 요약
                            if progression:
                                best_sim = current_log.get('best_similarity', 0)
                                print(f"\n📊 현재 상태: 최고 {best_sim:.2f} | "
                                      f"총 {len(progression)}회 시도")
                                
                                # 전략 변경 확인
                                strategy_changes = current_log.get('strategy_changes', [])
                                if strategy_changes and strategy_changes[-1]['attempt'] == last_attempt:
                                    change = strategy_changes[-1]
                                    print(f"🔄 전략 변경: {change['from']} → {change['to']}")
                    
                    last_size = current_size
            
            time.sleep(0.5)  # 0.5초마다 확인
            
        except KeyboardInterrupt:
            print("\n\n모니터링 종료")
            break
        except Exception as e:
            print(f"오류: {e}")
            time.sleep(1)


if __name__ == "__main__":
    monitor_current_game()