#!/usr/bin/env python3
"""
성능 최적화 모듈
병렬 처리, 캐싱, 배치 학습 등을 통한 성능 향상 기능을 제공합니다.
"""

import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from typing import List, Dict, Callable, Any, Optional, Tuple
from functools import lru_cache, wraps
import pickle
import hashlib
from collections import defaultdict
from dataclasses import dataclass

from .models import GuessResult, GameSession


@dataclass
class CacheConfig:
    """캐시 설정을 저장하는 데이터 클래스"""
    max_size: int = 1000
    ttl_seconds: int = 3600  # 1시간
    enable_disk_cache: bool = True
    cache_directory: str = ".cache"


class AdvancedCache:
    """
    고급 캐싱 시스템
    메모리와 디스크 캐싱을 지원하며 TTL(Time To Live)을 제공합니다.
    """
    
    def __init__(self, config: CacheConfig = None):
        """
        캐시 시스템을 초기화합니다.
        
        Args:
            config (CacheConfig): 캐시 설정
        """
        self.config = config or CacheConfig()
        self.memory_cache: Dict[str, Dict] = {}
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "disk_hits": 0,
            "disk_misses": 0
        }
        
        # 디스크 캐시 디렉토리 생성
        if self.config.enable_disk_cache:
            import os
            os.makedirs(self.config.cache_directory, exist_ok=True)
    
    def _generate_cache_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """캐시 키를 생성합니다."""
        key_data = f"{func_name}:{args}:{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _is_expired(self, cache_entry: Dict) -> bool:
        """캐시 항목이 만료되었는지 확인합니다."""
        return time.time() - cache_entry["timestamp"] > self.config.ttl_seconds
    
    def get(self, key: str) -> Optional[Any]:
        """
        캐시에서 값을 가져옵니다.
        
        Args:
            key (str): 캐시 키
            
        Returns:
            Optional[Any]: 캐시된 값 또는 None
        """
        # 메모리 캐시 확인
        if key in self.memory_cache:
            entry = self.memory_cache[key]
            if not self._is_expired(entry):
                self.cache_stats["hits"] += 1
                return entry["value"]
            else:
                del self.memory_cache[key]
        
        # 디스크 캐시 확인
        if self.config.enable_disk_cache:
            disk_path = f"{self.config.cache_directory}/{key}.pkl"
            try:
                import os
                if os.path.exists(disk_path):
                    with open(disk_path, 'rb') as f:
                        entry = pickle.load(f)
                    
                    if not self._is_expired(entry):
                        # 메모리 캐시로 복원
                        self.memory_cache[key] = entry
                        self.cache_stats["disk_hits"] += 1
                        return entry["value"]
                    else:
                        os.remove(disk_path)
            except Exception:
                pass
        
        self.cache_stats["misses"] += 1
        return None
    
    def set(self, key: str, value: Any) -> None:
        """
        캐시에 값을 저장합니다.
        
        Args:
            key (str): 캐시 키
            value (Any): 저장할 값
        """
        entry = {
            "value": value,
            "timestamp": time.time()
        }
        
        # 메모리 캐시 저장
        self.memory_cache[key] = entry
        
        # 메모리 캐시 크기 제한
        if len(self.memory_cache) > self.config.max_size:
            # 오래된 항목 제거 (LRU 방식)
            oldest_key = min(self.memory_cache.keys(), 
                           key=lambda k: self.memory_cache[k]["timestamp"])
            del self.memory_cache[oldest_key]
        
        # 디스크 캐시 저장
        if self.config.enable_disk_cache:
            disk_path = f"{self.config.cache_directory}/{key}.pkl"
            try:
                with open(disk_path, 'wb') as f:
                    pickle.dump(entry, f)
            except Exception:
                pass
    
    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계를 반환합니다."""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = self.cache_stats["hits"] / total_requests if total_requests > 0 else 0
        
        return {
            "hit_rate": round(hit_rate * 100, 2),
            "memory_cache_size": len(self.memory_cache),
            "stats": self.cache_stats.copy()
        }


def cached(cache_instance: AdvancedCache, ttl: int = None):
    """
    함수 캐싱 데코레이터
    
    Args:
        cache_instance (AdvancedCache): 캐시 인스턴스
        ttl (int): TTL 오버라이드 (초)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 캐시 키 생성
            cache_key = cache_instance._generate_cache_key(
                func.__name__, args, kwargs)
            
            # 캐시에서 확인
            cached_result = cache_instance.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # 함수 실행 및 캐시 저장
            result = func(*args, **kwargs)
            cache_instance.set(cache_key, result)
            
            return result
        return wrapper
    return decorator


class ParallelProcessor:
    """
    병렬 처리 엔진
    단어 후보 평가, 전략 실행 등을 병렬로 처리합니다.
    """
    
    def __init__(self, max_workers: int = None):
        """
        병렬 처리기를 초기화합니다.
        
        Args:
            max_workers (int): 최대 워커 수 (None이면 CPU 코어 수)
        """
        import os
        self.max_workers = max_workers or min(32, (os.cpu_count() or 1) + 4)
        self.thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)
        self.process_pool = ProcessPoolExecutor(max_workers=min(4, self.max_workers))
    
    def evaluate_candidates_parallel(self, candidates: List[str], 
                                   evaluation_func: Callable[[str], float],
                                   use_processes: bool = False) -> List[Tuple[str, float]]:
        """
        후보 단어들을 병렬로 평가합니다.
        
        Args:
            candidates (List[str]): 평가할 후보 단어들
            evaluation_func (Callable): 평가 함수
            use_processes (bool): 프로세스 풀 사용 여부
            
        Returns:
            List[Tuple[str, float]]: (단어, 점수) 튜플의 리스트
        """
        if not candidates:
            return []
        
        executor = self.process_pool if use_processes else self.thread_pool
        
        # 병렬 작업 제출
        future_to_word = {
            executor.submit(evaluation_func, word): word 
            for word in candidates
        }
        
        results = []
        for future in as_completed(future_to_word):
            word = future_to_word[future]
            try:
                score = future.result(timeout=5)  # 5초 타임아웃
                results.append((word, score))
            except Exception as e:
                print(f"⚠️ 단어 '{word}' 평가 실패: {e}")
                results.append((word, 0.0))  # 실패시 0점
        
        # 점수 순으로 정렬
        results.sort(key=lambda x: x[1], reverse=True)
        return results
    
    def batch_strategy_evaluation(self, session: GameSession, 
                                strategies: List[str],
                                strategy_funcs: Dict[str, Callable]) -> Dict[str, Any]:
        """
        여러 전략을 병렬로 평가합니다.
        
        Args:
            session (GameSession): 현재 세션
            strategies (List[str]): 평가할 전략들
            strategy_funcs (Dict[str, Callable]): 전략별 함수들
            
        Returns:
            Dict[str, Any]: 전략별 평가 결과
        """
        future_to_strategy = {
            self.thread_pool.submit(strategy_funcs[strategy], session): strategy
            for strategy in strategies if strategy in strategy_funcs
        }
        
        results = {}
        for future in as_completed(future_to_strategy):
            strategy = future_to_strategy[future]
            try:
                result = future.result(timeout=10)
                results[strategy] = result
            except Exception as e:
                print(f"⚠️ 전략 '{strategy}' 평가 실패: {e}")
                results[strategy] = None
        
        return results
    
    def cleanup(self) -> None:
        """리소스를 정리합니다."""
        self.thread_pool.shutdown(wait=True)
        self.process_pool.shutdown(wait=True)


class BatchLearning:
    """
    배치 학습 시스템
    효율적인 배치 업데이트를 통해 학습 성능을 향상시킵니다.
    """
    
    def __init__(self, batch_size: int = 10, update_interval: float = 5.0):
        """
        배치 학습 시스템을 초기화합니다.
        
        Args:
            batch_size (int): 배치 크기
            update_interval (float): 업데이트 간격 (초)
        """
        self.batch_size = batch_size
        self.update_interval = update_interval
        
        # 배치 버퍼
        self.word_relationship_batch: List[Dict] = []
        self.frequency_update_batch: List[Dict] = []
        self.pattern_update_batch: List[Dict] = []
        
        # 마지막 업데이트 시간
        self.last_update_time = time.time()
        
        # 통계
        self.batch_stats = {
            "total_batches_processed": 0,
            "avg_batch_processing_time": 0.0,
            "pending_updates": 0
        }
    
    def add_word_relationship_update(self, word1: str, word2: str, 
                                   similarity_diff: float) -> None:
        """
        단어 관계 업데이트를 배치에 추가합니다.
        
        Args:
            word1 (str): 첫 번째 단어
            word2 (str): 두 번째 단어
            similarity_diff (float): 유사도 차이
        """
        update = {
            "type": "word_relationship",
            "word1": word1,
            "word2": word2,
            "similarity_diff": similarity_diff,
            "timestamp": time.time()
        }
        
        self.word_relationship_batch.append(update)
        self._check_batch_size()
    
    def add_frequency_update(self, word: str, similarity: float) -> None:
        """
        단어 빈도 업데이트를 배치에 추가합니다.
        
        Args:
            word (str): 단어
            similarity (float): 유사도
        """
        update = {
            "type": "frequency",
            "word": word,
            "similarity": similarity,
            "timestamp": time.time()
        }
        
        self.frequency_update_batch.append(update)
        self._check_batch_size()
    
    def add_pattern_update(self, pattern_data: Dict) -> None:
        """
        패턴 업데이트를 배치에 추가합니다.
        
        Args:
            pattern_data (Dict): 패턴 데이터
        """
        update = {
            "type": "pattern",
            "data": pattern_data,
            "timestamp": time.time()
        }
        
        self.pattern_update_batch.append(update)
        self._check_batch_size()
    
    def _check_batch_size(self) -> None:
        """배치 크기를 확인하고 필요시 처리합니다."""
        total_pending = (len(self.word_relationship_batch) + 
                        len(self.frequency_update_batch) + 
                        len(self.pattern_update_batch))
        
        current_time = time.time()
        time_elapsed = current_time - self.last_update_time
        
        # 배치 크기나 시간 조건 만족시 처리
        if total_pending >= self.batch_size or time_elapsed >= self.update_interval:
            self._process_batches()
    
    def _process_batches(self) -> None:
        """모든 배치를 처리합니다."""
        start_time = time.time()
        
        # 단어 관계 배치 처리
        if self.word_relationship_batch:
            self._process_word_relationship_batch()
        
        # 빈도 업데이트 배치 처리
        if self.frequency_update_batch:
            self._process_frequency_batch()
        
        # 패턴 업데이트 배치 처리
        if self.pattern_update_batch:
            self._process_pattern_batch()
        
        # 통계 업데이트
        processing_time = time.time() - start_time
        self.batch_stats["total_batches_processed"] += 1
        self.batch_stats["avg_batch_processing_time"] = (
            (self.batch_stats["avg_batch_processing_time"] * 
             (self.batch_stats["total_batches_processed"] - 1) + processing_time) /
            self.batch_stats["total_batches_processed"]
        )
        
        self.last_update_time = time.time()
        
        print(f"📦 배치 처리 완료: {processing_time:.3f}초")
    
    def _process_word_relationship_batch(self) -> None:
        """단어 관계 배치를 처리합니다."""
        # 같은 단어 쌍의 업데이트들을 그룹화
        pair_updates = defaultdict(list)
        
        for update in self.word_relationship_batch:
            pair_key = f"{min(update['word1'], update['word2'])}|{max(update['word1'], update['word2'])}"
            pair_updates[pair_key].append(update['similarity_diff'])
        
        # 그룹화된 업데이트 적용
        for pair_key, similarity_diffs in pair_updates.items():
            # 실제 학습 엔진에 배치 업데이트 적용
            # (여기서는 인터페이스만 정의)
            pass
        
        self.word_relationship_batch.clear()
    
    def _process_frequency_batch(self) -> None:
        """빈도 업데이트 배치를 처리합니다."""
        # 같은 단어의 업데이트들을 그룹화
        word_updates = defaultdict(list)
        
        for update in self.frequency_update_batch:
            word_updates[update['word']].append(update['similarity'])
        
        # 그룹화된 업데이트 적용
        for word, similarities in word_updates.items():
            # 평균 유사도 계산 등의 효율적인 업데이트
            pass
        
        self.frequency_update_batch.clear()
    
    def _process_pattern_batch(self) -> None:
        """패턴 업데이트 배치를 처리합니다."""
        # 패턴 데이터 일괄 처리
        for update in self.pattern_update_batch:
            # 패턴 분석 및 저장
            pass
        
        self.pattern_update_batch.clear()
    
    def force_process_all(self) -> None:
        """모든 대기 중인 배치를 강제로 처리합니다."""
        if (self.word_relationship_batch or 
            self.frequency_update_batch or 
            self.pattern_update_batch):
            self._process_batches()
    
    def get_batch_statistics(self) -> Dict[str, Any]:
        """배치 처리 통계를 반환합니다."""
        pending_updates = (len(self.word_relationship_batch) + 
                          len(self.frequency_update_batch) + 
                          len(self.pattern_update_batch))
        
        stats = self.batch_stats.copy()
        stats["pending_updates"] = pending_updates
        stats["time_since_last_update"] = time.time() - self.last_update_time
        
        return stats


class PerformanceMonitor:
    """
    성능 모니터링 시스템
    시스템 성능을 실시간으로 모니터링하고 최적화 제안을 제공합니다.
    """
    
    def __init__(self):
        """성능 모니터를 초기화합니다."""
        self.performance_data = {
            "function_times": defaultdict(list),
            "memory_usage": [],
            "cache_performance": {},
            "parallel_processing": {},
            "batch_processing": {}
        }
        
        self.monitoring_active = True
        self.start_time = time.time()
    
    def profile_function(self, func_name: str = None):
        """
        함수 실행 시간을 프로파일링하는 데코레이터
        
        Args:
            func_name (str): 함수 이름 (None이면 실제 함수명 사용)
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                if not self.monitoring_active:
                    return func(*args, **kwargs)
                
                name = func_name or func.__name__
                start_time = time.time()
                
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    execution_time = time.time() - start_time
                    self.performance_data["function_times"][name].append(execution_time)
                    
                    # 최근 100개 기록만 유지
                    if len(self.performance_data["function_times"][name]) > 100:
                        self.performance_data["function_times"][name] = \
                            self.performance_data["function_times"][name][-50:]
            
            return wrapper
        return decorator
    
    def record_memory_usage(self) -> None:
        """현재 메모리 사용량을 기록합니다."""
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            
            memory_data = {
                "timestamp": time.time(),
                "rss_mb": memory_info.rss / 1024 / 1024,  # MB 단위
                "vms_mb": memory_info.vms / 1024 / 1024   # MB 단위
            }
            
            self.performance_data["memory_usage"].append(memory_data)
            
            # 최근 1000개 기록만 유지
            if len(self.performance_data["memory_usage"]) > 1000:
                self.performance_data["memory_usage"] = \
                    self.performance_data["memory_usage"][-500:]
                    
        except ImportError:
            # psutil이 없으면 기본 메모리 정보만 기록
            self.performance_data["memory_usage"].append({
                "timestamp": time.time(),
                "rss_mb": "N/A",
                "vms_mb": "N/A"
            })
    
    def update_cache_performance(self, cache_stats: Dict) -> None:
        """캐시 성능 데이터를 업데이트합니다."""
        self.performance_data["cache_performance"] = cache_stats
    
    def update_parallel_performance(self, parallel_stats: Dict) -> None:
        """병렬 처리 성능 데이터를 업데이트합니다."""
        self.performance_data["parallel_processing"] = parallel_stats
    
    def update_batch_performance(self, batch_stats: Dict) -> None:
        """배치 처리 성능 데이터를 업데이트합니다."""
        self.performance_data["batch_processing"] = batch_stats
    
    def get_performance_report(self) -> Dict[str, Any]:
        """상세한 성능 리포트를 생성합니다."""
        current_time = time.time()
        uptime = current_time - self.start_time
        
        # 함수 실행 시간 통계
        function_stats = {}
        for func_name, times in self.performance_data["function_times"].items():
            if times:
                function_stats[func_name] = {
                    "avg_time": sum(times) / len(times),
                    "max_time": max(times),
                    "min_time": min(times),
                    "call_count": len(times),
                    "total_time": sum(times)
                }
        
        # 메모리 사용량 통계
        memory_stats = {}
        if self.performance_data["memory_usage"]:
            recent_memory = self.performance_data["memory_usage"][-10:]
            if recent_memory and recent_memory[0]["rss_mb"] != "N/A":
                memory_stats = {
                    "current_rss_mb": recent_memory[-1]["rss_mb"],
                    "avg_rss_mb": sum(m["rss_mb"] for m in recent_memory) / len(recent_memory),
                    "peak_rss_mb": max(m["rss_mb"] for m in self.performance_data["memory_usage"])
                }
        
        report = {
            "uptime_seconds": uptime,
            "function_performance": function_stats,
            "memory_performance": memory_stats,
            "cache_performance": self.performance_data["cache_performance"],
            "parallel_performance": self.performance_data["parallel_processing"],
            "batch_performance": self.performance_data["batch_processing"],
            "optimization_suggestions": self._generate_optimization_suggestions()
        }
        
        return report
    
    def _generate_optimization_suggestions(self) -> List[str]:
        """성능 최적화 제안을 생성합니다."""
        suggestions = []
        
        # 함수 실행 시간 분석
        function_times = self.performance_data["function_times"]
        for func_name, times in function_times.items():
            if times:
                avg_time = sum(times) / len(times)
                if avg_time > 1.0:  # 1초 이상
                    suggestions.append(f"'{func_name}' 함수 최적화 고려 (평균 {avg_time:.2f}초)")
        
        # 캐시 성능 분석
        cache_perf = self.performance_data["cache_performance"]
        if "hit_rate" in cache_perf and cache_perf["hit_rate"] < 50:
            suggestions.append(f"캐시 히트율 향상 필요 (현재 {cache_perf['hit_rate']}%)")
        
        # 메모리 사용량 분석
        memory_usage = self.performance_data["memory_usage"]
        if memory_usage and memory_usage[-1]["rss_mb"] != "N/A":
            current_memory = memory_usage[-1]["rss_mb"]
            if current_memory > 500:  # 500MB 이상
                suggestions.append(f"메모리 사용량 최적화 고려 (현재 {current_memory:.1f}MB)")
        
        return suggestions
    
    def start_monitoring(self) -> None:
        """모니터링을 시작합니다."""
        self.monitoring_active = True
    
    def stop_monitoring(self) -> None:
        """모니터링을 중지합니다."""
        self.monitoring_active = False


class PerformanceOptimizer:
    """
    성능 최적화 통합 시스템
    모든 성능 개선 컴포넌트를 통합 관리합니다.
    """
    
    def __init__(self, cache_config: CacheConfig = None, 
                 max_workers: int = None, batch_size: int = 10):
        """
        성능 최적화 시스템을 초기화합니다.
        
        Args:
            cache_config (CacheConfig): 캐시 설정
            max_workers (int): 병렬 처리 최대 워커 수
            batch_size (int): 배치 처리 크기
        """
        self.cache = AdvancedCache(cache_config)
        self.parallel_processor = ParallelProcessor(max_workers)
        self.batch_learning = BatchLearning(batch_size)
        self.monitor = PerformanceMonitor()
        
        print("🚀 성능 최적화 시스템 초기화 완료")
    
    def get_cached_function(self, ttl: int = None):
        """캐시된 함수 데코레이터를 반환합니다."""
        return cached(self.cache, ttl)
    
    def get_profiled_function(self, func_name: str = None):
        """프로파일링된 함수 데코레이터를 반환합니다."""
        return self.monitor.profile_function(func_name)
    
    def evaluate_candidates_parallel(self, candidates: List[str],
                                   evaluation_func: Callable) -> List[Tuple[str, float]]:
        """후보들을 병렬로 평가합니다."""
        return self.parallel_processor.evaluate_candidates_parallel(
            candidates, evaluation_func)
    
    def add_batch_update(self, update_type: str, **kwargs) -> None:
        """배치 업데이트를 추가합니다."""
        if update_type == "word_relationship":
            self.batch_learning.add_word_relationship_update(**kwargs)
        elif update_type == "frequency":
            self.batch_learning.add_frequency_update(**kwargs)
        elif update_type == "pattern":
            self.batch_learning.add_pattern_update(kwargs)
    
    def get_comprehensive_performance_report(self) -> Dict[str, Any]:
        """종합 성능 리포트를 생성합니다."""
        # 각 컴포넌트 통계 수집
        self.monitor.update_cache_performance(self.cache.get_stats())
        self.monitor.update_batch_performance(self.batch_learning.get_batch_statistics())
        self.monitor.record_memory_usage()
        
        return self.monitor.get_performance_report()
    
    def cleanup(self) -> None:
        """모든 리소스를 정리합니다."""
        self.batch_learning.force_process_all()
        self.parallel_processor.cleanup()
        self.monitor.stop_monitoring()
        print("🧹 성능 최적화 시스템 정리 완료")