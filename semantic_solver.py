#!/usr/bin/env python3
"""
의미 기반 지능형 꼬맨틀 솔버 메인 모듈
모든 구성 요소를 통합하여 완전한 솔버를 제공합니다.
"""

import time
import os
import re
from typing import List, Optional

from modules.models import GuessResult, GameSession
from modules.strategy_engine import StrategyEngine
from modules.learning_engine import LearningEngine
from modules.web_automation import WebAutomation, WebAutomationConfig


class SemanticSolver:
    """
    의미 기반 지능형 꼬맨틀 솔버
    
    4단계 적응형 탐색 전략과 실시간 학습을 통해
    꼬맨틀 게임을 자동으로 해결하는 솔버입니다.
    """
    
    def __init__(self, vocab_file: str = 'words.xls', 
                 learning_file: str = 'kkomantle_learning.json',
                 word_pairs_file: str = 'word_pairs.json',
                 web_config: WebAutomationConfig = None):
        """
        솔버를 초기화합니다.
        
        Args:
            vocab_file (str): 어휘 파일 경로
            learning_file (str): 학습 데이터 파일 경로
            word_pairs_file (str): 단어 쌍 데이터 파일 경로
            web_config (WebAutomationConfig): 웹 자동화 설정
        """
        print("🚀 의미 기반 지능형 꼬맨틀 솔버 초기화 중...")
        
        # 어휘 로드
        self.vocab = self._load_vocabulary(vocab_file)
        print(f"📚 어휘 로드 완료: {len(self.vocab)}개 단어")
        
        # 핵심 구성 요소들 초기화
        self.learning_engine = LearningEngine(learning_file, word_pairs_file)
        self.strategy_engine = StrategyEngine(enable_logging=True)
        self.web_automation = WebAutomation(web_config or WebAutomationConfig())
        
        # 현재 게임 세션
        self.current_session = None
        
        print("✅ 솔버 초기화 완료")
    
    def _load_vocabulary(self, vocab_file: str) -> List[str]:
        """
        어휘 파일에서 단어 목록을 로드합니다.
        
        Args:
            vocab_file (str): 어휘 파일 경로 (.txt 또는 .xls/.xlsx)
            
        Returns:
            List[str]: 단어 목록
        """
        try:
            if vocab_file.endswith(('.xls', '.xlsx')):
                # Excel 파일 처리
                import pandas as pd
                
                print(f"📊 Excel 파일에서 어휘 로드 중: {vocab_file}")
                
                # Excel 파일 읽기
                df = pd.read_excel(vocab_file, engine='openpyxl' if vocab_file.endswith('.xlsx') else None)
                
                print(f"📋 Excel 파일 구조: {df.shape[0]}행 x {df.shape[1]}열")
                print(f"📋 컬럼명: {list(df.columns)}")
                
                # 단어가 있는 열 찾기 (문자열이 많은 열)
                word_column_idx = 0
                max_text_count = 0
                
                for col_idx in range(df.shape[1]):
                    column = df.iloc[:, col_idx]
                    text_count = 0
                    
                    for value in column.head(10):  # 처음 10개만 확인
                        if pd.notna(value) and isinstance(value, str) and len(value.strip()) > 1:
                            text_count += 1
                    
                    print(f"📊 {col_idx}번 열: 텍스트 {text_count}개 (샘플: {column.dropna().head(3).tolist()})")
                    
                    if text_count > max_text_count:
                        max_text_count = text_count
                        word_column_idx = col_idx
                
                print(f"🎯 단어 열로 선택: {word_column_idx}번째 열")
                
                # 선택된 열에서 단어 추출
                words = []
                word_column = df.iloc[:, word_column_idx]
                
                for value in word_column:
                    if pd.notna(value):  # NaN 값 제외
                        word = str(value).strip()
                        
                        # 단어 뒤의 숫자 제거 (동음이의어 구분용)
                        # 예: "사위01" -> "사위", "사이99" -> "사이"
                        word = re.sub(r'\d+$', '', word).strip()
                        
                        # 빈 문자열, 주석, 순수 숫자 제외
                        if (word and not word.startswith('[') and 
                            not word.replace('.', '').isdigit() and
                            len(word) > 1):  # 1글자 제외
                            words.append(word)
                
                print(f"📈 Excel에서 {len(words)}개 단어 추출")
                
            else:
                # 텍스트 파일 처리 (기존 로직)
                print(f"📄 텍스트 파일에서 어휘 로드 중: {vocab_file}")
                
                with open(vocab_file, 'r', encoding='utf-8') as f:
                    words = []
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('['):
                            words.append(line)
            
            # 중복 제거 및 정렬
            unique_words = sorted(list(set(words)))
            
            if not unique_words:
                raise ValueError("어휘 파일이 비어있습니다.")
            
            return unique_words
                
        except FileNotFoundError:
            print(f"⚠️ 어휘 파일을 찾을 수 없습니다: {vocab_file}")
            print("기본 어휘를 사용합니다.")
            return ["사랑", "시간", "사람", "생각", "마음", "세상", "문제", "사회", 
                   "자연", "음식", "기술", "감정", "장소", "행동"]
        
        except Exception as e:
            print(f"❌ 어휘 로드 실패: {e}")
            print("기본 어휘를 사용합니다.")
            return ["사랑", "시간", "사람", "생각", "마음", "세상", "문제", "사회"]
    
    # def _remove_word_from_vocab(self, word: str) -> None:
    #     """
    #     어휘에서 실패한 단어를 제거합니다. (현재 비활성화됨)
    #     
    #     Args:
    #         word (str): 제거할 단어
    #     """
    #     # 파싱 실패시 어휘에서 제거하지 않음 - 네트워크나 일시적 문제일 수 있음
    #     pass
    
    def start_new_session(self) -> GameSession:
        """
        새로운 게임 세션을 시작합니다.
        
        Returns:
            GameSession: 새로운 게임 세션 객체
        """
        self.current_session = GameSession()
        print(f"🎮 새로운 게임 세션 시작 (세션 ID: {id(self.current_session)})")
        return self.current_session
    
    def solve_game(self, max_attempts: int = 500) -> Optional[str]:
        """
        꼬맨틀 게임을 해결합니다.
        
        Args:
            max_attempts (int): 최대 시도 횟수
            
        Returns:
            Optional[str]: 성공시 정답 단어, 실패시 None
        """
        # 웹 브라우저 설정 및 게임 사이트 접속
        if not self._setup_and_connect():
            return None
        
        # 새 세션 시작
        session = self.start_new_session()
        
        # 로깅 시작
        if self.strategy_engine.logger:
            self.strategy_engine.logger.start_session(str(id(session)))
        
        print("\n" + "="*60)
        print("🎯 의미 기반 지능형 솔버 게임 시작")
        print(f"📚 사용 가능한 어휘: {len(self.vocab)}개")
        print(f"🧠 학습된 단어 쌍: {len(self.learning_engine.word_pairs)}개")
        print("="*60 + "\n")
        
        start_time = time.time()
        
        # 메인 게임 루프
        for attempt in range(1, max_attempts + 1):
            # 다음 단어 선택
            next_word = self._select_next_word(session)
            
            if not next_word:
                print("⚠️ 더 이상 시도할 단어가 없습니다.")
                break
            
            # 매 10회마다만 시도 출력
            if attempt % 10 == 1 or attempt <= 10:
                print(f"🎯 시도 {attempt}: '{next_word}'")
            
            # 단어 제출
            if not self.web_automation.submit_word(next_word):
                print("❌ 단어 제출 실패. 다음 단어로 계속...")
                # 제출 실패한 단어도 tried_words에 추가하여 재시도 방지
                session.tried_words.add(next_word)
                continue
            
            # 결과 파싱
            result = self.web_automation.parse_result(next_word, attempt)
            
            if not result:
                print(f"❌ 단어 '{next_word}' 결과 파싱 실패 - 다음 단어로 계속")
                # 파싱 실패한 단어도 tried_words에 추가하여 재시도 방지
                session.tried_words.add(next_word)
                continue
            
            # 세션에 결과 추가
            session.add_guess(result)
            
            # 결과 로깅
            if self.strategy_engine.logger:
                self.strategy_engine.logger.log_result(result)
            
            # 학습 엔진에 관계 학습
            self.learning_engine.learn_word_relationships(result, session.guesses[:-1])
            
            # 매 10회마다만 결과 출력
            if attempt % 10 == 1 or attempt <= 10 or result.similarity > 50:
                print(f"   📊 {next_word}: {result.similarity:.2f} | {result.rank}")
            
            # 정답 확인 (유사도 100)
            if result.similarity >= 99.99:  # 부동소수점 오차 고려
                elapsed_time = time.time() - start_time
                print(f"\n🎉 정답 발견! '{next_word}'")
                print(f"📈 총 시도: {attempt}회 | 소요 시간: {elapsed_time:.1f}초")
                
                # 성공 결과 저장
                self.learning_engine.save_session_results(
                    session, success=True, final_answer=next_word)
                
                # 로깅 종료
                if self.strategy_engine.logger:
                    self.strategy_engine.logger.end_session(success=True, final_answer=next_word)
                
                return next_word
            
            # 진행 상황 표시 (매 10회마다)
            if attempt % 10 == 0:
                self._show_progress(session, attempt)
            
            # 전략 변경 알림 (디버그용)
            if len(session.strategy_history) > 1 and attempt > 1:
                if session.strategy_history[-1] != session.strategy_history[-2]:
                    print(f"\n🔄 전략 변경: {session.strategy_history[-2]} → {session.strategy_history[-1]}")
                    print(f"   현재 최고 유사도: {session.get_best_similarity():.2f}\n")
                
                # 정체 상태 로깅
                if self.strategy_engine.logger and session.is_stagnant():
                    # 정체 시작점 찾기
                    stagnant_start = attempt - 10
                    for i in range(max(0, attempt - 20), attempt):
                        if i < len(session.guesses) - 1:
                            if abs(session.guesses[i].similarity - session.guesses[i+1].similarity) > 0.02:
                                stagnant_start = i + 1
                                break
                    
                    self.strategy_engine.logger.log_stagnant_period(
                        stagnant_start, attempt, session.get_best_similarity()
                    )
        
        # 최대 시도 횟수 도달
        elapsed_time = time.time() - start_time
        print(f"\n⏰ 최대 시도 횟수 ({max_attempts}회) 도달")
        print(f"📈 소요 시간: {elapsed_time:.1f}초")
        
        # 실패 결과 저장
        self.learning_engine.save_session_results(session, success=False)
        
        # 로깅 종료
        if self.strategy_engine.logger:
            self.strategy_engine.logger.end_session(success=False)
        
        return None
    
    def _setup_and_connect(self) -> bool:
        """
        웹 브라우저를 설정하고 게임 사이트에 접속합니다.
        
        Returns:
            bool: 설정 및 접속 성공 여부
        """
        # 브라우저 설정
        if not self.web_automation.setup_driver():
            return False
        
        # 게임 사이트 접속
        if not self.web_automation.navigate_to_game():
            return False
        
        return True
    
    def _select_next_word(self, session: GameSession) -> Optional[str]:
        """
        전략 엔진을 사용하여 다음 단어를 선택합니다.
        
        Args:
            session (GameSession): 현재 게임 세션
            
        Returns:
            Optional[str]: 선택된 단어
        """
        # 사용 가능한 어휘 확인
        available_vocab = [word for word in self.vocab 
                          if word not in session.tried_words]
        
        if not available_vocab:
            return None
        
        # 학습 데이터 준비
        learned_data = {
            'word_frequency': self.learning_engine.learning_data.get('word_frequency', {}),
            'word_pairs': self.learning_engine.word_pairs
        }
        
        # 전략 엔진을 통한 단어 선택
        selected_word = self.strategy_engine.select_next_word(
            session, available_vocab, learned_data)
        
        return selected_word
    
    def _show_progress(self, session: GameSession, current_attempt: int) -> None:
        """
        현재 진행 상황을 표시합니다.
        
        Args:
            session (GameSession): 현재 게임 세션
            current_attempt (int): 현재 시도 횟수
        """
        if not session.guesses:
            return
        
        best_similarity = session.get_best_similarity()
        top_guesses = session.get_top_guesses(5)
        
        print(f"\n📊 진행 상황 (시도 {current_attempt}회)")
        print(f"🏆 최고 유사도: {best_similarity:.4f}")
        print("🔝 상위 5개 추측:")
        
        for i, guess in enumerate(top_guesses, 1):
            print(f"   {i}. {guess.word}: {guess.similarity:.4f} ({guess.rank})")
        
        # 전략 사용 현황
        if session.strategy_history:
            recent_strategies = session.strategy_history[-3:]
            print(f"🧠 최근 전략: {' → '.join(recent_strategies)}")
        
        print()
    
    def get_learning_statistics(self) -> dict:
        """
        현재 학습 상태의 통계를 반환합니다.
        
        Returns:
            dict: 학습 통계 정보
        """
        return self.learning_engine.get_learning_statistics()
    
    def save_current_state(self) -> bool:
        """
        현재 학습 상태를 파일에 저장합니다.
        
        Returns:
            bool: 저장 성공 여부
        """
        learning_saved = self.learning_engine.save_learning_data()
        pairs_saved = self.learning_engine.save_word_pairs()
        
        if learning_saved and pairs_saved:
            print("💾 학습 상태 저장 완료")
            return True
        else:
            print("⚠️ 학습 상태 저장 중 오류 발생")
            return False
    
    def cleanup(self) -> None:
        """
        솔버 리소스를 정리합니다.
        """
        # 현재 세션 결과 저장
        if self.current_session:
            self.learning_engine.save_session_results(self.current_session)
        
        # 웹 자동화 정리
        self.web_automation.cleanup()
        
        print("🧹 솔버 정리 완료")
    
    def manual_word_input(self, word: str) -> Optional[GuessResult]:
        """
        수동으로 단어를 입력하고 결과를 받아옵니다. (디버깅용)
        
        Args:
            word (str): 입력할 단어
            
        Returns:
            Optional[GuessResult]: 결과
        """
        if not self.current_session:
            self.start_new_session()
        
        if not self.web_automation.is_connected:
            print("❌ 웹 브라우저가 연결되지 않았습니다.")
            return None
        
        # 단어 제출
        if self.web_automation.submit_word(word):
            # 결과 파싱
            result = self.web_automation.parse_result(word, len(self.current_session.guesses) + 1)
            
            if result:
                # 세션에 추가
                self.current_session.add_guess(result)
                
                # 학습
                self.learning_engine.learn_word_relationships(
                    result, self.current_session.guesses[:-1])
                
                print(f"✅ 수동 입력 결과: {result.word} - {result.similarity:.4f}")
                return result
            else:
                print(f"❌ 결과 파싱 실패: {word}")
        else:
            print(f"❌ 단어 제출 실패: {word}")
        
        return None
    
    def get_word_recommendations(self, count: int = 5) -> List[str]:
        """
        현재 상황에 맞는 추천 단어들을 반환합니다.
        
        Args:
            count (int): 추천할 단어 개수
            
        Returns:
            List[str]: 추천 단어 목록
        """
        if not self.current_session:
            # 세션이 없으면 초기 다양성 단어들 반환
            initial_words = ["사람", "시간", "사랑", "자연", "음식", "기술", "감정", "장소"]
            available = [w for w in initial_words if w in self.vocab]
            return available[:count]
        
        recommendations = []
        available_vocab = [word for word in self.vocab 
                          if word not in self.current_session.tried_words]
        
        # 학습 데이터 준비
        learned_data = {
            'word_frequency': self.learning_engine.learning_data.get('word_frequency', {}),
            'word_pairs': self.learning_engine.word_pairs
        }
        
        # 여러 전략으로 추천 단어 수집
        try:
            for _ in range(count):
                word = self.strategy_engine.select_next_word(
                    self.current_session, available_vocab, learned_data)
                
                if word and word not in recommendations:
                    recommendations.append(word)
                    available_vocab.remove(word)  # 중복 방지
                
                if len(recommendations) >= count:
                    break
        except Exception as e:
            print(f"⚠️ 추천 단어 생성 중 오류: {e}")
        
        return recommendations


def main():
    """메인 함수: 솔버를 실행합니다."""
    print("🚀 의미 기반 지능형 꼬맨틀 솔버")
    print("=" * 50)
    
    solver = None
    
    try:
        # 솔버 초기화
        solver = SemanticSolver()
        
        # 학습 통계 출력
        stats = solver.get_learning_statistics()
        print(f"📊 학습 통계:")
        print(f"   • 총 게임 수: {stats['total_games']}")
        print(f"   • 학습된 단어 쌍: {stats['total_word_pairs']}")
        print(f"   • 고유 단어 수: {stats['total_unique_words']}")
        print(f"   • 성공 패턴: {stats['successful_patterns']}")
        
        if stats['most_effective_words']:
            print(f"   • 효과적인 단어: {', '.join(stats['most_effective_words'][:3])}")
        print()
        
        # 게임 실행
        result = solver.solve_game()
        
        if result:
            print(f"🎊 성공! 정답: '{result}'")
        else:
            print("😔 이번에는 정답을 찾지 못했습니다.")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ 사용자에 의해 중단됨")
    
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 리소스 정리
        if solver:
            solver.cleanup()
        
        print("\n👋 프로그램을 종료합니다.")


if __name__ == "__main__":
    main()