#!/usr/bin/env python3
"""
웹 자동화 모듈
셀레니움을 사용한 꼬맨틀 게임 웹 자동화를 담당하는 모듈입니다.
"""

import time
from typing import Optional, List
from dataclasses import dataclass

from .models import GuessResult

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
except ImportError as e:
    print(f"[오류] 필수 라이브러리가 설치되지 않았습니다: {e}")
    print("웹 자동화를 위해 `pip install selenium` 명령어를 실행해주세요.")
    exit()


@dataclass
class WebAutomationConfig:
    """웹 자동화 설정을 저장하는 클래스"""
    game_url: str = "https://semantle-ko.newsjel.ly/"
    headless: bool = False  # True로 설정하면 브라우저 창이 보이지 않음
    window_size: tuple = (1200, 800)
    submit_delay: float = 0.005  # 단어 제출 후 대기 시간 (초)
    parse_delay: float = 0.005   # 결과 파싱 전 대기 시간 (초)
    page_load_timeout: int = 30  # 페이지 로드 최대 대기 시간 (초)


class WebAutomation:
    """
    꼬맨틀 게임 웹 자동화 클래스
    브라우저 제어, 단어 입력, 결과 파싱을 담당합니다.
    """
    
    def __init__(self, config: WebAutomationConfig = None):
        """
        웹 자동화 객체를 초기화합니다.
        
        Args:
            config (WebAutomationConfig): 웹 자동화 설정
        """
        self.config = config or WebAutomationConfig()
        self.driver = None
        self.is_connected = False
        
        # 선택자 정의 (CSS 선택자)
        self.selectors = {
            'input_field': '#guess_input',          # 단어 입력 필드
            'submit_button': '.input-wrapper button',  # 제출 버튼
            'results_table': '#guesses_table',       # 결과 테이블
            'last_input_row': 'tbody tr.last-input'  # 최신 입력 행
        }
    
    def setup_driver(self) -> bool:
        """
        브라우저 드라이버를 설정하고 초기화합니다.
        
        Returns:
            bool: 설정 성공 여부
        """
        try:
            # Chrome 옵션 설정
            chrome_options = Options()
            
            # 헤드리스 모드 설정 (필요시)
            if self.config.headless:
                chrome_options.add_argument("--headless")
            
            # 기본 옵션들
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument(f"--window-size={self.config.window_size[0]},{self.config.window_size[1]}")
            
            # 로그 레벨 설정 (불필요한 로그 줄이기)
            chrome_options.add_argument("--log-level=3")
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # 드라이버 생성
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(self.config.page_load_timeout)
            
            print("✅ 브라우저 설정 완료")
            return True
            
        except Exception as e:
            print(f"❌ 브라우저 설정 실패: {e}")
            print("Chrome 브라우저와 ChromeDriver가 설치되어 있는지 확인해주세요.")
            return False
    
    def navigate_to_game(self) -> bool:
        """
        꼬맨틀 게임 사이트로 이동합니다.
        
        Returns:
            bool: 이동 성공 여부
        """
        try:
            print(f"🌐 게임 사이트 접속 중: {self.config.game_url}")
            self.driver.get(self.config.game_url)
            
            # 페이지 로드 대기
            time.sleep(2)
            
            # 게임 요소들이 로드되었는지 확인
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, self.selectors['input_field']))
            )
            
            self.is_connected = True
            print("✅ 게임 사이트 접속 완료")
            return True
            
        except Exception as e:
            print(f"❌ 게임 사이트 접속 실패: {e}")
            self.is_connected = False
            return False
    
    def submit_word(self, word: str) -> bool:
        """
        단어를 입력하고 제출합니다.
        
        Args:
            word (str): 제출할 단어
            
        Returns:
            bool: 제출 성공 여부
        """
        try:
            if not self.is_connected:
                print("❌ 게임 사이트에 연결되지 않았습니다.")
                return False
            
            # JavaScript를 사용하여 빠른 입력 및 제출
            script = f"""
            var input = document.querySelector('{self.selectors['input_field']}');
            var button = document.querySelector('{self.selectors['submit_button']}');
            
            if (input && button) {{
                input.value = '{word}';
                input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                button.click();
                return true;
            }}
            return false;
            """
            
            result = self.driver.execute_script(script)
            
            if result:
                # 짧은 대기 (서버 응답 대기)
                time.sleep(self.config.submit_delay)
                
                # 제출 후 에러 메시지 확인
                error_check_script = """
                var errorElement = document.querySelector('.error, .alert, [class*="error"], [class*="alert"]');
                if (errorElement && errorElement.textContent.trim()) {
                    return errorElement.textContent.trim();
                }
                return null;
                """
                
                error_msg = self.driver.execute_script(error_check_script)
                if error_msg:
                    print(f"⚠️ 서버 오류: {error_msg}")
                    return False
                
                return True
            else:
                print(f"❌ 입력 요소를 찾을 수 없습니다: {word}")
                return False
                
        except Exception as e:
            print(f"❌ 단어 제출 실패 ({word}): {e}")
            return False
    
    def parse_result(self, word: str, attempt: int) -> Optional[GuessResult]:
        """
        최신 제출 결과를 파싱합니다.
        
        Args:
            word (str): 제출한 단어
            attempt (int): 시도 번호
            
        Returns:
            Optional[GuessResult]: 파싱된 결과 (실패시 None)
        """
        try:
            # 결과가 나타날 때까지 대기 (최대 2초)
            max_wait_time = 2.0
            wait_interval = 0.1
            waited_time = 0
            
            while waited_time < max_wait_time:
                time.sleep(wait_interval)
                waited_time += wait_interval
                
                # 결과가 나타났는지 확인
                check_script = f"""
                var allTables = document.querySelectorAll('table');
                for (var t = 0; t < allTables.length; t++) {{
                    var rows = allTables[t].querySelectorAll('tr');
                    for (var i = 0; i < rows.length; i++) {{
                        var cells = rows[i].querySelectorAll('td');
                        for (var j = 0; j < cells.length; j++) {{
                            if (cells[j].textContent.trim() === '{word}') {{
                                return true;
                            }}
                        }}
                    }}
                }}
                return false;
                """
                
                result_found = self.driver.execute_script(check_script)
                if result_found:
                    print(f"🔍 단어 '{word}' 결과 발견, 파싱 시작")
                    break
            
            if not result_found:
                print(f"⏰ 단어 '{word}' 결과 대기 시간 초과")
            
            # 모든 테이블을 검사하여 게임 데이터가 있는 테이블 찾기
            script = f"""
            var allTables = document.querySelectorAll('table');
            var gameTable = null;
            
            for (var t = 0; t < allTables.length; t++) {{
                var table = allTables[t];
                var rows = table.querySelectorAll('tr');
                
                // 테이블에 게임 데이터 행이 있는지 확인
                for (var i = 0; i < rows.length; i++) {{
                    var cells = rows[i].querySelectorAll('td');
                    
                    // 4개 셀이 있고, 두 번째 셀이 한글 단어인 경우
                    if (cells.length >= 4) {{
                        var wordCell = cells[1];
                        if (wordCell && wordCell.textContent) {{
                            var text = wordCell.textContent.trim();
                            // 한글 단어 패턴 확인 (한글 2글자 이상)
                            if (/^[가-힣]{{2,}}$/.test(text)) {{
                                gameTable = table;
                                break;
                            }}
                        }}
                    }}
                }}
                
                if (gameTable) break;
            }}
            
            if (!gameTable) {{
                console.log('게임 테이블을 찾을 수 없음');
                return null;
            }}
            
            var table = gameTable;

            // 찾은 게임 테이블에서 모든 행을 검사하여 방금 입력한 단어 찾기
            var allRows = table.querySelectorAll('tr');
            
            for (var i = allRows.length - 1; i >= 0; i--) {{
                var row = allRows[i];
                var cells = row.querySelectorAll('td');
                
                // 최소 3개 셀이 있어야 함
                if (cells.length >= 3) {{
                    // 모든 셀을 확인하여 입력한 단어 찾기
                    for (var j = 0; j < cells.length; j++) {{
                        var cellText = cells[j].textContent.trim();
                        if (cellText === '{word}') {{
                            // 단어를 찾았으면 다음 셀들에서 유사도와 순위 찾기
                            var similarity = '';
                            var rank = '1000위 이상';
                            
                            // 다음 셀이 유사도인지 확인 (소수점 숫자)
                            if (j + 1 < cells.length) {{
                                var nextCell = cells[j + 1].textContent.trim();
                                if (/^\\d*\\.?\\d+$/.test(nextCell)) {{
                                    similarity = nextCell;
                                    
                                    // 그 다음 셀이 순위인지 확인
                                    if (j + 2 < cells.length) {{
                                        rank = cells[j + 2].textContent.trim() || '1000위 이상';
                                    }}
                                }}
                            }}
                            
                            if (similarity) {{
                                return {{
                                    word: '{word}',
                                    similarity: similarity,
                                    rank: rank
                                }};
                            }}
                        }}
                    }}
                }}
            }}
            
            console.log('단어를 찾을 수 없음:', '{word}');
            return null;
            """
            
            result = self.driver.execute_script(script)
            
            if result:
                # 유사도 값 파싱 및 정규화
                similarity = self._parse_similarity(result['similarity'])
                
                if similarity is not None:
                    guess_result = GuessResult(
                        word=result['word'],
                        similarity=similarity,
                        rank=result['rank'],
                        attempt=attempt
                    )
                    # 파싱 성공 로그 제거 (너무 많음)
                    return guess_result
                else:
                    print(f"⚠️ 유사도 파싱 실패: {result['similarity']}")
                    return None
            else:
                print(f"⚠️ 단어 '{word}' 결과를 찾을 수 없음")
                
                # 페이지가 잘못된 상태인지 확인 후 게임 페이지로 재이동
                page_check_script = """
                return {
                    url: window.location.href,
                    hasInput: !!document.querySelector('input[type="text"], input[placeholder*="단어"]'),
                    hasGameTable: !!document.querySelector('table tbody tr:not([class*="stat"]):not([id*="stat"])')
                };
                """
                page_status = self.driver.execute_script(page_check_script)
                
                if not page_status.get('hasInput') or not page_status.get('hasGameTable'):
                    print(f"🔄 잘못된 페이지 감지, 게임 페이지로 재이동: {page_status}")
                    self.navigate_to_game()
                    time.sleep(1)  # 페이지 로딩 대기
                
                # 전체 테이블 구조 분석
                debug_script = f"""
                var table = document.querySelector('table');
                if (!table) return 'NO_TABLE';
                
                var rows = table.querySelectorAll('tbody tr');
                if (rows.length === 0) return 'NO_ROWS';
                
                // 모든 행 분석
                var allRows = [];
                for (var i = 0; i < rows.length; i++) {{
                    var hasThTag = rows[i].querySelector('th');
                    var cells = rows[i].querySelectorAll('td');
                    var cellTexts = [];
                    
                    for (var j = 0; j < cells.length; j++) {{
                        cellTexts.push(cells[j].textContent.trim());
                    }}
                    
                    allRows.push({{
                        index: i,
                        hasThTag: hasThTag !== null,
                        cellCount: cells.length,
                        cellTexts: cellTexts,
                        className: rows[i].className,
                        innerHTML: rows[i].innerHTML.substring(0, 200) // 처음 200자만
                    }});
                }}
                
                return {{
                    totalRows: rows.length,
                    allRows: allRows,
                    searchWord: '{word}'
                }};
                """
                
                debug_result = self.driver.execute_script(debug_script)
                print(f"🔍 디버그: {debug_result}")
                
                return None
                
        except Exception as e:
            print(f"❌ 결과 파싱 오류 ({word}): {e}")
            return None
    
    def _parse_similarity(self, similarity_text: str) -> Optional[float]:
        """
        유사도 텍스트를 파싱하여 float 값으로 변환합니다.
        
        Args:
            similarity_text (str): 원본 유사도 텍스트
            
        Returns:
            Optional[float]: 파싱된 유사도 (0.0 ~ 100.0), 실패시 None
        """
        try:
            sim_text = similarity_text.strip()
            
            # 빈 문자열 체크
            if not sim_text:
                return None
            
            # 다양한 형태의 유사도 값 처리
            if '%' in sim_text:
                # "18.00%" 형태인 경우
                numeric_part = sim_text.replace('%', '').strip()
                similarity = float(numeric_part)
            else:
                # "0.75" 또는 "75.00" 형태인 경우
                similarity = float(sim_text)
            
            # 값 범위 검증 (0.0 ~ 100.0)
            if 0.0 <= similarity <= 100.0:
                return similarity
            else:
                print(f"⚠️ 유사도 값이 범위를 벗어남: {similarity}")
                return None
                
        except ValueError as e:
            print(f"⚠️ 유사도 파싱 오류: '{similarity_text}' - {e}")
            return None
    
    def check_game_completion(self) -> Optional[str]:
        """
        게임 완료 여부를 확인합니다 (정답 찾기 성공).
        
        Returns:
            Optional[str]: 성공시 정답 단어, 실패시 None
        """
        try:
            # 성공 메시지나 완료 표시를 찾는 스크립트
            script = """
            // 유사도 1.0 (100%) 또는 정답 표시 찾기
            var table = document.querySelector('#guesses_table');
            if (!table) return null;
            
            var rows = table.querySelectorAll('tbody tr:not(.delimiter)');
            for (var i = 0; i < rows.length; i++) {
                var cells = rows[i].querySelectorAll('td');
                if (cells.length >= 3) {
                    var similarity = cells[2] ? cells[2].textContent.trim() : '';
                    
                    // 100 또는 100.00 또는 100% 정답 표시 확인
                    if (similarity === '100' || similarity === '100.0' || similarity === '100.00' ||
                        similarity === '100%' || similarity === '100.00%') {
                        var word = cells[1] ? cells[1].textContent.trim() : '';
                        return word;
                    }
                }
            }
            
            // 성공 메시지 확인
            var successElements = document.querySelectorAll('.success, .correct, .winner');
            if (successElements.length > 0) {
                return 'success_detected';
            }
            
            return null;
            """
            
            result = self.driver.execute_script(script)
            return result if result and result != 'success_detected' else None
            
        except Exception as e:
            print(f"⚠️ 게임 완료 확인 오류: {e}")
            return None
    
    def get_current_results(self) -> List[GuessResult]:
        """
        현재 테이블의 모든 결과를 가져옵니다.
        
        Returns:
            List[GuessResult]: 현재까지의 모든 추측 결과
        """
        try:
            script = """
            var table = document.querySelector('#guesses_table');
            if (!table) return [];
            
            var results = [];
            var rows = table.querySelectorAll('tbody tr:not(.delimiter)');
            
            for (var i = 0; i < rows.length; i++) {
                var cells = rows[i].querySelectorAll('td');
                if (cells.length >= 4) {
                    var attempt = cells[0] ? cells[0].textContent.trim() : '';
                    var word = cells[1] ? cells[1].textContent.trim() : '';
                    var similarity = cells[2] ? cells[2].textContent.trim() : '';
                    var rank = cells[3] ? cells[3].textContent.trim() : '';
                    
                    if (word && similarity) {
                        results.push({
                            attempt: attempt,
                            word: word,
                            similarity: similarity,
                            rank: rank
                        });
                    }
                }
            }
            
            return results;
            """
            
            results = self.driver.execute_script(script)
            guess_results = []
            
            for i, result in enumerate(results):
                similarity = self._parse_similarity(result['similarity'])
                if similarity is not None:
                    guess_result = GuessResult(
                        word=result['word'],
                        similarity=similarity,
                        rank=result['rank'],
                        attempt=i + 1
                    )
                    guess_results.append(guess_result)
            
            return guess_results
            
        except Exception as e:
            print(f"⚠️ 현재 결과 가져오기 오류: {e}")
            return []
    
    def cleanup(self) -> None:
        """
        브라우저 리소스를 정리합니다.
        참고: 사용자 요청에 따라 브라우저는 종료하지 않습니다.
        """
        # 연결 상태만 재설정
        self.is_connected = False
        print("🔧 웹 자동화 정리 완료 (브라우저는 유지)")
        
        # 브라우저 종료를 원하는 경우 아래 주석 해제
        # if self.driver:
        #     self.driver.quit()
        #     print("🔧 브라우저 종료 완료")
    
    def take_screenshot(self, filename: str = None) -> bool:
        """
        현재 화면의 스크린샷을 저장합니다.
        
        Args:
            filename (str): 저장할 파일명 (None이면 타임스탬프 사용)
            
        Returns:
            bool: 저장 성공 여부
        """
        try:
            if not filename:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"kkomantle_screenshot_{timestamp}.png"
            
            success = self.driver.save_screenshot(filename)
            if success:
                print(f"📸 스크린샷 저장: {filename}")
            return success
            
        except Exception as e:
            print(f"❌ 스크린샷 저장 실패: {e}")
            return False
    
    def get_driver_info(self) -> dict:
        """
        현재 드라이버 상태 정보를 반환합니다.
        
        Returns:
            dict: 드라이버 상태 정보
        """
        try:
            if self.driver:
                return {
                    'connected': self.is_connected,
                    'current_url': self.driver.current_url,
                    'window_size': self.driver.get_window_size(),
                    'title': self.driver.title
                }
            else:
                return {'connected': False, 'driver': None}
                
        except Exception as e:
            return {'connected': False, 'error': str(e)}