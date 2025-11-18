import heapq
from collections import deque
from typing import Tuple, List
import numpy as np

def neighbors(point: Tuple[int, int]):
    x, y = point
    return [(x-1, y), (x+1, y), (x, y-1), (x, y+1),
            (x-1, y-1), (x-1, y+1), (x+1, y-1), (x+1, y+1)]

def heuristic(a: Tuple[int, int], b: Tuple[int, int]) -> float:
    """맨해튼 거리 기반 휴리스틱 함수"""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def a_star(skeleton: np.ndarray, start: Tuple[int, int], end: Tuple[int, int]) -> List[Tuple[int, int]]:
    """
    A* 알고리즘을 사용하여 두 점 사이에서 픽셀 값이 1인 경로를 찾음
    """
    open_set = []
    heapq.heappush(open_set, (0, start, [start]))
    visited = set()
    
    while open_set:
        cost, current, path = heapq.heappop(open_set)
        if current == end:
            return path
        if current in visited:
            continue
        visited.add(current)
        
        for neighbor in neighbors(current):
            x, y = neighbor
            if 0 <= x < skeleton.shape[1] and 0 <= y < skeleton.shape[0] and skeleton[y, x] == 1:
                new_path = list(path)  # 리스트 복사
                new_path.append(neighbor)
                priority = len(new_path) + heuristic(neighbor, end)
                heapq.heappush(open_set, (priority, neighbor, new_path))
    
    return None
