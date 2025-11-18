from typing import List, Tuple
from collections import deque
import numpy as np

def get_neighbors(point: Tuple[int, int], skeleton: np.ndarray) -> List[Tuple[int, int]]:
    """
    주어진 좌표의 8방향 이웃 중 스켈레톤에서 값이 1인 좌표들을 반환
    
    Args:
        point (tuple): 현재 좌표 (x, y)
        skeleton (numpy.ndarray): 스켈레톤 이미지
        
    Returns:
        list: 이웃 좌표 리스트
    """
    x, y = point
    neighbors = []
    
    # 8방향 이웃 검사
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if dx == 0 and dy == 0:
                continue
            
            nx, ny = x + dx, y + dy
            if 0 <= nx < skeleton.shape[1] and 0 <= ny < skeleton.shape[0]:
                if skeleton[ny, nx] == 1:
                    neighbors.append((nx, ny))
    
    return neighbors

def is_branch_point(point: Tuple[int, int], skeleton: np.ndarray) -> bool:
    """
    해당 좌표가 분기점인지 확인 (3개 이상 연결된 지점)
    
    Args:
        point (tuple): 검사할 좌표 (x, y)
        skeleton (numpy.ndarray): 스켈레톤 이미지
        
    Returns:
        bool: 분기점 여부
    """
    neighbors = get_neighbors(point, skeleton)
    return len(neighbors) >= 3

def is_end_point(point: Tuple[int, int], skeleton: np.ndarray) -> bool:
    """
    해당 좌표가 끝점인지 확인 (1개만 연결된 지점)
    
    Args:
        point (tuple): 검사할 좌표 (x, y)
        skeleton (numpy.ndarray): 스켈레톤 이미지
        
    Returns:
        bool: 끝점 여부
    """
    neighbors = get_neighbors(point, skeleton)
    return len(neighbors) == 1

def select_topleft_start_point(end_points: List[Tuple[int, int]]) -> Tuple[int, int]:
    """
    끝점 리스트에서 가장 왼쪽 위(좌상단)에 있는 점을 선택합니다.
    좌표가 작을수록 왼쪽/위에 있다고 판단합니다.
    
    Args:
        end_points (List[Tuple[int, int]]): 끝점 좌표 리스트
        
    Returns:
        Tuple[int, int]: 선택된 좌상단 시작점 (x, y)
    """
    if not end_points:
        return None
    
    # 왼쪽 위에 있는 점을 찾기 위해 (y, x) 순으로 정렬
    # y 값이 같으면 x 값으로 비교 (y가 작을수록 위, x가 작을수록 왼쪽)
    return min(end_points, key=lambda p: (p[1], p[0]))

def extract_all_paths_with_end_points(skeleton: np.ndarray, end_points: List[Tuple[int, int]]) -> List[List[Tuple[int, int]]]:
    """
    스켈레톤 이미지에서 끝점 리스트를 받아 왼쪽 위에 있는 끝점을 시작점으로 사용하여 모든 경로 추출
    
    Args:
        skeleton (numpy.ndarray): 0 또는 1로 표현된 2D 스켈레톤 이미지
        end_points (List[Tuple[int, int]]): 끝점 좌표 리스트
        
    Returns:
        list: 모든 경로의 리스트 (각 경로는 좌표 튜플의 리스트)
    """
    # 끝점 리스트에서 왼쪽 위에 있는 점을 시작점으로 선택
    start = select_topleft_start_point(end_points)
    
    if start is None or skeleton[start[1], start[0]] == 0:
        return []  # 유효한 시작점이 없으면 빈 리스트 반환
    
    # 결과 경로 저장
    all_paths = []
    paths = []
    
    # 방문한 좌표 추적
    visited = set()
    
    # BFS 탐색을 위한 큐: (현재 좌표, 현재까지의 경로)
    queue = deque([(start, [start])])
    
    while queue:
        current, path = queue.popleft()
        
        # 이미 방문한 좌표라면 스킵
        if tuple(current) in visited:
            continue
            
        visited.add(tuple(current))
        
        # 현재 좌표가 끝점이거나 분기점이면 현재까지의 경로 저장
        if current != start and (is_end_point(current, skeleton) or is_branch_point(current, skeleton)):
            all_paths.append(path)
            
            # 분기점인 경우 계속 탐색 (각 분기를 따로 탐색)
            if is_branch_point(current, skeleton):
                # 분기점에서는 현재 좌표를 새로운 시작점으로 BFS 다시 시작
                neighbors = get_neighbors(current, skeleton)
                for neighbor in neighbors:
                    if neighbor not in visited:
                        queue.append((neighbor, [current, neighbor]))
        else:
            # 일반 경로 포인트의 경우 이웃 좌표로 경로 확장
            neighbors = get_neighbors(current, skeleton)
            for neighbor in neighbors:
                if neighbor not in visited:
                    queue.append((neighbor, path + [neighbor]))

    # 미세 균열 필터링
    for path in all_paths:
        if path and len(path) > 10:
            paths.append(path)
    
    return paths

# # 트리 탐색 너비우선탐색(BFS)
# def neighbors(point: Tuple[int, int]) -> List[Tuple[int, int]]:
#     x, y = point
#     return [(x-1, y), (x+1, y), (x, y-1), (x, y+1),  # 상하좌우
#             (x-1, y-1), (x-1, y+1), (x+1, y-1), (x+1, y+1)]  # 대각선 이동

# def bfs(skeleton: np.ndarray, start: Tuple[int, int], end: Tuple[int, int]):
#     """
#     스켈레톤 기반 BFS 탐색으로 시작점과 끝점 사이의 경로를 찾는 함수

#     Args:
#         skeleton (numpy.ndarray): 0 또는 1로 표현된 2D 스켈레톤 이미지
#         start (tuple): 시작 좌표 (x, y)
#         end (tuple): 끝 좌표 (x, y)

#     Returns:
#         list: 시작점과 끝점 사이의 픽셀값이 1인 좌표 리스트, 경로가 없으면 None
#     """
#     if skeleton[start[1], start[0]] == 0 or skeleton[end[1], end[0]] == 0:
#         return None  # 시작점이나 끝점이 1이 아니라면 경로 없음

#     visited = set()
#     queue = deque([(start, [start])])

#     while queue:
#         current, path = queue.popleft()

#         if current in visited:
#             continue
#         visited.add(current)

#         if current == end:
#             return path

#         for neighbor in neighbors(current):
#             x, y = neighbor
#             if 0 <= x < skeleton.shape[1] and 0 <= y < skeleton.shape[0]:
#                 if skeleton[y, x] == 1 and neighbor not in visited:
#                     queue.append((neighbor, path + [neighbor]))
    
#     return None  # 경로를 찾을 수 없는 경우

# def fnConnectLine(skeleton: np.ndarray, branch_point: List[Tuple[int, int]], end_point: List[Tuple[int, int]]) -> List[List[Tuple[int, int]]]:
#     """
#     스켈레톤 이미지에서 브랜치 포인트와 엔드 포인트를 연결하여 경로를 추출.
#     Args:
#         skeleton (numpy.ndarray): 스켈레톤 이미지 (0과 1로 구성).
#         branch_point (List[Tuple[int, int]]): 브랜치 포인트 리스트.
#         end_point (List[Tuple[int, int]]): 엔드 포인트 리스트.

#     Returns:
#         List[List[Tuple[int, int]]]: 연결된 경로 리스트.
#     """
#     print('브랜치 포인트 : ', branch_point)
#     print('엔드 포인트 : ', end_point)

#     if len(end_point) <= 1:
#         return None

#     visited = set()
#     paths = []
#     filtered_paths = []  

#     def bfs(start: Tuple[int, int]) -> List[Tuple[int, int]]:
#         """
#         BFS를 통해 연결된 경로를 탐색.
#         """
#         queue = deque([start])
#         path = []
#         visited.add(start)

#         while queue:
#             current = queue.popleft()
#             path.append(current)

#             for neighbor in neighbors(current):
#                 x, y = neighbor
#                 if (0 <= x < skeleton.shape[1] and 0 <= y < skeleton.shape[0] and
#                     skeleton[y, x] == 1 and neighbor not in visited):
#                     visited.add(neighbor)
#                     queue.append(neighbor)

#         return path
    
#     def bfs2(start: Tuple[int, int], end: Tuple[int, int]):
#         """
#         스켈레톤 기반 BFS 탐색으로 시작점과 끝점 사이의 경로를 찾는 함수

#         Args:
#             skeleton (numpy.ndarray): 0 또는 1로 표현된 2D 스켈레톤 이미지
#             start (tuple): 시작 좌표 (x, y)
#             end (tuple): 끝 좌표 (x, y)

#         Returns:
#             list: 시작점과 끝점 사이의 픽셀값이 1인 좌표 리스트, 경로가 없으면 None
#         """
#         if skeleton[start[1], start[0]] == 0 or skeleton[end[1], end[0]] == 0:
#             return None  # 시작점이나 끝점이 1이 아니라면 경로 없음

#         visited = set()
#         queue = deque([(start, [start])])

#         while queue:
#             current, path = queue.popleft()

#             if current in visited:
#                 continue
#             visited.add(current)

#             if current == end:
#                 return path

#             for neighbor in neighbors(current):
#                 x, y = neighbor
#                 if 0 <= x < skeleton.shape[1] and 0 <= y < skeleton.shape[0]:
#                     if skeleton[y, x] == 1 and neighbor not in visited:
#                         queue.append((neighbor, path + [neighbor]))
        
#         return None  # 경로를 찾을 수 없는 경우
    
#     def bfs3(start: Tuple[int, int], end: Tuple[int, int]):
#         pass

#     # 1. 브랜치 포인트가 없는 경우: 엔드포인트만 처리
#     if len(branch_point) == 0:
#         for point in end_point:
#             path = bfs(point)
#             paths.append(path)

#     # 2. 브랜치가 1개인 경우: 해당 브랜치와 엔드포인트 연결
#     elif len(branch_point) == 1:
#         for point in end_point:
#             path = bfs2(branch_point[0], point)
#             paths.append(path)

#     # 3. 브랜치가 2개 이상인 경우: 브랜치 간 연결 → 이후 엔드포인트와 가까운 브랜치 연결
#     else:
#         for point in branch_point:
#             path = bfs(point)
#             paths.append(path)

#     for path in paths:
#         if path and len(path) > 1:
#             filtered_paths.append(path)
#             print('경로 : ', path)

#     return filtered_paths