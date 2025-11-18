from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing

from typing import List,Tuple
import cv2
from skimage.morphology import skeletonize
import numpy as np
from skimage import feature
import math

"""균열 검출 영역 내 균열의 끝점, 교차점, Skeletonize 수행"""
  
# 입력된 이미지로 부터 스켈레톤 추출
# Args: img (numpy.ndarray): 균열 segmenation 결과 이미지, 2차원 array형태로 0 or 255 값 만 가지도록 하여 입력
# Returns: numpy.ndarray: 입력된 균열 이미지로 부터 skeleton 추출 0 or 1값으로 표현
def extract_skeleton(img:np.ndarray, ori_h_size, ori_w_size) -> np.ndarray:
    # image blur
    # 해상도에 따라 다르게 설정하기... 4k는 15 잘나옴, 2k는 5가 무난..
    # 이미지의 해상도 계산
    resolution = ori_w_size * ori_h_size  # 총 픽셀 수 계산
    blur_value = 5

    # 해상도에 따라 블러 값 설정
    if resolution >= 3840 * 2160:  # 4K 해상도 이상
        blur_value = 15
    elif resolution >= 2560 * 1440:  # 2K (1440p) 해상도 이상
        blur_value = 10
    elif resolution >= 1920 * 1080:  # Full HD (1080p) 해상도 이상
        blur_value = 5

    img = cv2.medianBlur(img, blur_value)
    _, binary = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)

    # skimage를 사용하여 skeleton화
    binary = binary / 255  # 이미지를 0과 1로 변환
    skeleton = skeletonize(binary, method="lee").astype(np.uint8)
    return skeleton

# 균열 skeleton으로 부터 선의 끝점을 추출, 교차점 추출된 결과를 반영하여 중복 추출 점 제거
# Args: skeleton (numpy.ndarray): 0 or 1로 표현된 2차원 array skeleton 이미지 값
# Args: branching_points (list): 교차점 추출 한 결과
# Returns: list: 끝점 x, y 좌표 list 
def extract_end_point(
        skeleton: np.ndarray,
        branching_points: List[Tuple[(int, int)]]
    ) -> List[Tuple[(int, int)]]:

    # 3x3 커널을 생성합니다. 이 커널은 주변 픽셀 값을 합산하는데 사용됩니다.
    kernel = np.array(
        [[1, 1, 1],
        [1, 1, 1],
        [1, 1, 1]], dtype=np.uint8)
    
    # 커널을 사용하여 필터링된 이미지를 생성합니다.
    filtered = cv2.filter2D(skeleton, -1, kernel)
    
    # 필터링된 이미지에서 값이 2이고, skeleton 이미지에서 값이 1인 위치를 찾습니다.
    line_end_points = (filtered == 2) & (skeleton == 1)
    y, x = np.where(line_end_points)
    line_end_points = list(zip(x, y))

    if line_end_points:
        # 첫 번째 끝점을 시작점으로 설정합니다.
        start_point = line_end_points[0]
        new_line_end_points = [start_point]

        # 각 끝점을 반복하면서 가까운 끝점을 제외하고 새로운 끝점 리스트에 추가합니다.
        for n_x, n_y in line_end_points[1:]:
            s_x, s_y = start_point

            # 현재 끝점이 시작점과 가까운 경우 무시하고, 먼 경우 추가합니다.
            if (np.abs(s_x - n_x) < 10) & (np.abs(s_y - n_y) < 10):
                continue
            else:
                start_point = (n_x, n_y)
                new_line_end_points.append(start_point)

        new_line_end_points2 = []

        if branching_points:
            # 가지치기 포인트가 존재하는 경우 각 끝점이 가지치기 포인트와 가까운지 확인합니다.
            for x, y in new_line_end_points:
                diff_arr = np.abs(np.array([x, y]) - np.array(branching_points))
                # 가지치기 포인트와 먼 끝점만 새로운 리스트에 추가합니다.
                if len(np.where((diff_arr[:, 0] < 10) & (diff_arr[:, 1] < 10))[0]) == 0:
                    new_line_end_points2.append([x, y])
        else:
            # 가지치기 포인트가 없는 경우 기존 끝점 리스트를 사용합니다.
            new_line_end_points2 = new_line_end_points
    else:
        # 끝점이 없는 경우 빈 리스트를 반환합니다.
        return []
    
    # 최종 끝점 리스트를 반환합니다.
    return new_line_end_points2

# 균열 skeleton으로 부터 교차점 추출
# Args: skeleton (numpy.ndarray): 0 or 1로 표현된 2차원 array skeleton 이미지 값
# Returns: list: 교차점 x, y 좌표 list 
def extract_cross_point(skeleton: np.ndarray) -> List[Tuple[(int, int)]]:
    # 3x3 커널을 생성합니다. 이 커널은 주변 픽셀 값을 합산하는 데 사용됩니다.
    kernel = np.array(
        [[1, 1, 1],
        [1, 1, 1],
        [1, 1, 1]], dtype=np.uint8)
    
    # 커널을 사용하여 필터링된 이미지를 생성합니다.
    filtered = cv2.filter2D(skeleton, -1, kernel)
    
    # 필터링된 이미지에서 값이 3보다 크고, 원본 스켈레톤 이미지에서 값이 1인 지점을 찾습니다.
    branching_points = (filtered > 3) & (skeleton == 1)
    y, x = np.where(branching_points)
    branching_points = list(zip(x, y))

    # 가지치기 포인트가 존재하는 경우 처리
    if branching_points:
        # 첫 번째 가지치기 포인트를 시작점으로 설정하고 새로운 가지치기 포인트 리스트 생성
        start_point = branching_points[0]
        # new_branching_points = [list(start_point)]
        new_branching_points = [start_point]

        # 각 가지치기 포인트를 반복하면서 가까운 포인트를 제외하고 새로운 리스트에 추가합니다.
        for n_x, n_y in branching_points[1:]:
            s_x, s_y = start_point

            # 현재 포인트가 시작점과 가까운 경우 무시하고, 먼 경우 추가합니다.
            if (np.abs(s_x - n_x) < 10) & (np.abs(s_y - n_y) < 10):
                continue
            else:
                start_point = (n_x, n_y)
                # new_branching_points.append(list(start_point))
                new_branching_points.append((n_x, n_y))
    else:
        new_branching_points = []

    # 최종 가지치기 포인트 리스트 반환
    return new_branching_points


# skeleton 내 모든 교차점 및 끝점들 간의 매칭 쌍 찾기
# 두 점사이 1 픽셀 값으로 이을 수 있는 모든 경우의 수 중에서 가장 짧은 것을 채택
# Args: skeleton (numpy.ndarray): 0 or 1로 표현된 2차원 array skeleton 이미지 값
# Args: total_points (list): skeleton내 존재하는 모든 교차점과 끝점 좌표들을 합한 집합
# Returns: list : skeleton의 한 선을 구성하는 시작점과 끝점 간의 mappoing 쌍 좌표 정보 
# 상태 업데이트 큐를 사용하여 경로 계산 함수
# def calculate_paths_wrapper(args):
#     skeleton, start, target_points, len_condition = args
#     paths = []
#     for end in target_points:
#         if start != end:
#             path = bfs(skeleton, tuple(start), tuple(end))
#             if path and len(path) >= len_condition:
#                 paths.append([start, end, len(path)])
#     return paths

# def extract_mapping_point(skeleton: np.ndarray, total_points: List[Tuple[int, int]], fnUpdatePercentStatus) -> List[List[Tuple[int, int]]]:
#     manager = multiprocessing.Manager()
#     update_queue = manager.Queue()
    
#     mapping_points_final = []
#     target_points = total_points.copy()
#     len_condition_1 = 0  # 1차 반복문의 길이 조건
#     len_condition_2 = 2  # 2차 반복문의 길이 조건

#     def update_status(queue, fnUpdatePercentStatus):
#         while not queue.empty():
#             percent = queue.get()
#             fnUpdatePercentStatus(percent)

#     # 1차 매핑
#     with ProcessPoolExecutor() as executor:
#         total_batches = len(total_points)
#         percent_per_batch = 20 / (total_batches / 5)  # 배치당 퍼센트 계산
#         args = [(skeleton, start, target_points, len_condition_1) for start in total_points]
#         futures = [executor.submit(calculate_paths_wrapper, arg) for arg in args]

#         for i, future in enumerate(as_completed(futures)):
#             paths = future.result()
#             if paths:
#                 shortest_path = sorted(paths, key=lambda x: x[-1])[0][:2]
#                 if sorted(shortest_path) not in mapping_points_final:
#                     mapping_points_final.append(sorted(shortest_path))

#             # 진행률 업데이트 (배치마다 한 번씩 업데이트)
#             if i % 5 == 0:
#                 update_queue.put(percent_per_batch)
#                 update_status(update_queue, fnUpdatePercentStatus)

#     print('extract_mapping_point 1차 완료')

#     # 1차 매핑에서 매칭되지 않은 선분 업데이트
#     skeleton_copy = skeleton.copy()
#     for start, end in mapping_points_final:
#         path = bfs(skeleton, tuple(start), tuple(end))
#         if path:  # None 체크 추가
#             for x, y in path:
#                 skeleton_copy[y, x] = 0  # 매핑된 부분 제거

#     # 2차 매핑
#     with ProcessPoolExecutor() as executor:
#         total_batches = len(total_points)
#         percent_per_batch = 20 / (total_batches / 5)  # 배치당 퍼센트 계산
#         args = [(skeleton_copy, start, target_points, len_condition_2) for start in total_points]
#         futures = [executor.submit(calculate_paths_wrapper, arg) for arg in args]

#         for i, future in enumerate(as_completed(futures)):
#             paths = future.result()
#             if paths:
#                 shortest_path = sorted(paths, key=lambda x: x[-1])[0][:2]
#                 if sorted(shortest_path) not in mapping_points_final:
#                     mapping_points_final.append(sorted(shortest_path))

#             # 진행률 업데이트 (배치마다 한 번씩 업데이트)
#             if i % 5 == 0:
#                 update_queue.put(percent_per_batch)
#                 update_status(update_queue, fnUpdatePercentStatus)

#     return mapping_points_final

# def extract_mapping_point3(skeleton: np.ndarray, total_points: List[Tuple[int, int]]) -> List[List[Tuple[int, int]]]:
#     mapping_points_final = []
#     target_points = total_points.copy()
#     len_condition_1 = 0  # 1차 반복문의 길이 조건
#     len_condition_2 = 2  # 2차 반복문의 길이 조건

#     for i, start in enumerate(total_points):
#         mapping_points = []
#         for end in target_points:
#             if start != end:
#                 path = bfs(skeleton, tuple(start), tuple(end))
#                 if path and len(path) >= len_condition_1:
#                     mapping_points.append([start, end, len(path)])

#         if mapping_points:
#             shortest_path = sorted(mapping_points, key=lambda x: x[-1])[0][:2]
#             if sorted(shortest_path) not in mapping_points_final:
#                 mapping_points_final.append(sorted(shortest_path))

#     print('extract_mapping_point 1차 완료')

#     # 1차 매핑에서 매칭되지 않은 선분 업데이트
#     skeleton_copy = skeleton.copy()
#     for start, end in mapping_points_final:
#         path = bfs(skeleton, tuple(start), tuple(end))
#         if path:  # None 체크 추가
#             for x, y in path:
#                 skeleton_copy[y, x] = 0  # 매핑된 부분 제거

#     # 2차 매핑
#     for i, start in enumerate(total_points):
#         mapping_points = []
#         for end in target_points:
#             if start != end:
#                 path = bfs(skeleton_copy, tuple(start), tuple(end))
#                 if path and len(path) >= len_condition_2:
#                     mapping_points.append([start, end, len(path)])

#         if mapping_points:
#             shortest_path = sorted(mapping_points, key=lambda x: x[-1])[0][:2]
#             if sorted(shortest_path) not in mapping_points_final:
#                 mapping_points_final.append(sorted(shortest_path))

#     return mapping_points_final

# 원본
# def extract_mapping_point(
#         skeleton: np.ndarray,
#         total_points: List[Tuple[(int, int)]]
#     ) -> List[List[Tuple[(int, int)]]]:
#     mapping_points_final = []
#     target_points = total_points.copy()

#     for start in total_points:
#         mapping_points = []

#         for end in target_points:
#             if start!=end:
#                 path = bfs(skeleton, tuple(start), tuple(end))
#                 if path:
#                     mapping_points.append([start,end,len(path)])

#         if mapping_points:
#             mapping_points = sorted(mapping_points,key=lambda x:x[-1])[0][:2]
#             if sorted(mapping_points) not in mapping_points_final:
#                 mapping_points_final.append(sorted(mapping_points))
    
#     # 1차 쌍 찾기에서 매칭이 되지 않은 선분에 대한 나머지 구하기
#     skeleton_copy = skeleton.copy()

#     for start, end in mapping_points_final:
#         path = bfs(skeleton, tuple(start), tuple(end))
#         for x,y in path:
#             if [x, y] not in total_points:
#                 skeleton_copy[y, x] = 0

#     for start in total_points:
#         mapping_points = []
#         for end in target_points:
#             if start != end:
#                 path = bfs(skeleton_copy, tuple(start), tuple(end))
#                 if path:
#                     if len(path) > 2:
#                         mapping_points.append([start, end, len(path)])
#         if mapping_points:
#             mapping_points = sorted(mapping_points, key = lambda x : x[-1])[0][:2]
#             if sorted(mapping_points) not in mapping_points_final:
#                 mapping_points_final.append(sorted(mapping_points))

#     return mapping_points_final


# 주변의 까만색 픽셀 수 계산 함수
def count_black_pixels(img: np.ndarray, center: tuple, radius: int = 1) -> int:
    x, y = center
    x_min, x_max = max(0, x - radius), min(img.shape[1], x + radius + 1)
    y_min, y_max = max(0, y - radius), min(img.shape[0], y + radius + 1)
    neighborhood = img[y_min:y_max, x_min:x_max]
    black_pixel_count = np.sum(neighborhood == 255)  # 까만색 픽셀 수 계산
    
    aa = neighborhood.copy()
    bb = cv2.circle(aa, center, radius, (255, 255, 255), 2)  
    
    return black_pixel_count

# bfs 탐색 결과 활용 skeleton 내 각 선분의 구성 픽셀 좌표들과 segmentation 이미지의 edge라인을 활용하여 각 픽셀 점당 균열의 폭을 측정
# Args: img (numpy.ndarray): 균열 segmenation 결과 이미지, 2차원 array형태로 0 or 255 값 만 가지도록 하여 입력
# Args: bfs_point (list): skeleton  내 모든 1값들의 좌표값 집합
# Args: acture_wall_width (float, optional): 스티칭 된 이미지의 벽 width 실제 길이. Defaults to None.
# Args: split(bool, optional) : 균열 개별 라인마다 폭 list나눠 출력
# Returns: list: 각 픽셀 지점당 균열 폭을 픽셀값의 합으로 출력
def extract_width(
        img: np.ndarray,
        bfs_point: List[Tuple[(int, int)]],
        split: bool = False
    ) -> List[List[List[Tuple]]]:

    edges_Pw = extract_edge(img)

    window_pix = 1
    width_info_lst_total = []

    for path in bfs_point:
        width_info_lst = []

        for start in range(0, len(path), window_pix):
            query = path[start : start + 5]

            # 최소 및 최대 값을 가져옵니다.
            x_min, y_min = min(query)
            x_max, y_max = max(query)

            # 0으로 나누기 회피를 위해 조건문 추가
            if x_max != x_min:
                theta = np.abs(slope_to_angle((y_max - y_min) / (x_max - x_min)))
            else:
                theta = 0  # 또는 다른 적절한 값을 설정

            # 중간 포인트를 가져옵니다.
            matching_width_point = query[len(query) // 2]
            in_x, in_y = matching_width_point

            search_window = 2

            if theta < 45:
                range_sec = range_fir = int(in_y)

                while True:
                    range_fir -= search_window
                    range_fir = max(0, range_fir)

                    if sum(edges_Pw[range_fir: int(in_y), int(in_x)] == 255) > 0:
                        break

                    if (range_fir == 0):
                        break            
                    
                while True:
                    range_sec += search_window                
                    range_sec = min(range_sec,img.shape[0])
                    if sum(edges_Pw[int(in_y): range_sec, int(in_x)] == 255) > 0:
                        break
                    if (range_sec == img.shape[0]):
                        break

                if (sum(edges_Pw[range_fir: int(in_y), int(in_x)] == 255) > 0) & (sum(edges_Pw[int(in_y): range_sec, int(in_x)] == 255) > 0):
                    est_width = range_sec - range_fir
                    width_info_lst.append([matching_width_point,est_width])

            else:
                range_sec = range_fir = int(in_x)
                while True:
                    range_fir -= search_window                
                    range_fir = max(0, range_fir)
                    if sum(edges_Pw[int(in_y), range_fir: int(in_x)] == 255) > 0:
                        break
                    if (range_fir == 0):
                        break

                while True:
                    range_sec += search_window             
                    range_sec = min(range_sec, img.shape[0])     
                    if sum(edges_Pw[int(in_y), int(in_x): range_sec] == 255) > 0:
                        break
                    if (range_sec == img.shape[0]):
                        break

                if (sum(edges_Pw[int(in_y), range_fir: int(in_x)] == 255) > 0) & (sum(edges_Pw[int(in_y), int(in_x): range_sec] == 255) > 0):
                    est_width = range_sec - range_fir
                    width_info_lst.append([matching_width_point,est_width])

        width_threshold = np.median([i[-1] for i in width_info_lst]) * 1.5
        
        new_width_info_lst = []
        fir_est_width = np.median([i[-1] for i in width_info_lst])
        for point,est_width in width_info_lst[:]:
            if est_width > width_threshold:
                est_width = fir_est_width
            else:
                fir_est_width = est_width

            new_width_info_lst.append([point, est_width])

        if split:
            width_info_lst_total.append(new_width_info_lst)
        else:    
            width_info_lst_total.extend(new_width_info_lst)

    return width_info_lst_total

# 입력된 segmentation 결과 이미지로 부터 edge라인 추출
# Args: img (numpy.ndarray): 균열 segmenation 결과 이미지, 2차원 array형태로 0 or 255 값 만 가지도록 하여 입력
# Returns: numpy.ndarray: 0 or 255로 구성된 edge 추출 결과 2차원 이미지
def extract_edge(img: np.ndarray) -> np.ndarray:
    edges_Pw = feature.canny(np.array(img), 0.1)
    edges_Pw.dtype = 'uint8'
    edges_Pw *= 255
    
    # 이미지 반전 (검은색 배경, 흰색 와곽선 -> 흰색 배경, 검은색 와곽선)
    inverted_edges_Pw = cv2.bitwise_not(edges_Pw)

    return inverted_edges_Pw

# 기울기 값으로 부터 기울기 각도 구하는 함수 
# Args: m (float): 기울기 값
# Returns: float: 각도 값
def slope_to_angle(m:float) -> float:
    # 라디안으로 각도 구하기
    radians = math.atan(m)
    # 라디안을 도로 변환
    degrees = math.degrees(radians)

    return degrees