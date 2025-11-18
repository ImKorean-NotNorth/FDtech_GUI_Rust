from collections import Counter
import math
from .extract_point import extract_skeleton, extract_end_point, extract_cross_point, extract_width
from .bfs import extract_all_paths_with_end_points
from typing import List,Tuple
import cv2
import numpy as np

def final_draw_measure(
        img: np.ndarray,
        per_pixel_length: float,
        per_pixel_width: float,
        ori_h_size,
        ori_w_size,
        fnUpdatePercentStatus
    ) -> Tuple[(np.ndarray, List[List[Tuple[(int, int)]]])]:
    """UNET에서 나온 분류 결과를 토대로 균열 길이 측정 및 영역 표시
    Args:
        img (numpy.array): UNET 예측된 raw 분류 결과 array
        per_pixel_length (_type_, optional): 라이더로 촬영된 실제 높이 기반 픽셀 크기.
        per_pixel_width (_type_, optional): 라이더로 촬영된 실제 폭 기반 픽셀 크기.
    Returns:
        numpy.array: 균열길이가 표시된 segmentation 결과 img
    """
    img = np.uint8(img * 255)
    skeleton = extract_skeleton(img, ori_h_size, ori_w_size)
    
    # 스켈레톤 확인용 코드
    # skeleton = np.uint8(skeleton * 255)
    
    # branching_points = extract_cross_point(skeleton)
    # line_end_points = extract_end_point(skeleton, branching_points)

    # # 스켈레톤 이미지를 BGR 형식으로 변환 (색상 추가 가능)
    # skeleton_bgr = cv2.cvtColor(skeleton, cv2.COLOR_GRAY2BGR)

    # # 브랜칭 포인트에 빨간색 원 그리기
    # for point in branching_points:
    #     x, y = point  # 포인트 좌표
    #     cv2.circle(skeleton_bgr, (x, y), radius=3, color=(0, 0, 255), thickness=-1)    # 빨간색 (BGR: (0, 0, 255))

    # # 브랜칭 포인트에 빨간색 원 그리기
    # for point in line_end_points:
    #     x, y = point  # 포인트 좌표
    #     cv2.circle(skeleton_bgr, (x, y), radius=3, color=(255, 0, 0), thickness=-1)

    # 객체 단위로 분류
    num_labels, labels = cv2.connectedComponents(skeleton, connectivity=8)

    obj_mapping_points = []

    total_objects = num_labels - 1  # 객체의 총 개수 (배경 제외)

    batch_size = 0    
    if img.shape[0] >= 40000:  # 이미지 높이가 40000 이상일 경우
        batch_size = 30
    else:  # 이미지 높이가 40000 미만일 경우
        batch_size = 5

    total_batches = (total_objects + batch_size - 1) // batch_size  # 배치 수 계산
    percent_per_batch = 40 / total_batches  # 각 배치당 고정 퍼센트 계산

    for batch_start in range(1, num_labels, batch_size):  # 배치 처리 시작
        batch_end = min(batch_start + batch_size, num_labels)  # 배치 범위 설정

        for label in range(batch_start, batch_end):
            # 객체 마스크 생성
            objected_mask = (labels == label).astype(np.uint8)
            obj_branch_points = extract_cross_point(objected_mask)
            obj_end_points = extract_end_point(objected_mask, obj_branch_points)
            path = extract_all_paths_with_end_points(objected_mask, obj_end_points)
            if path: obj_mapping_points.extend(path)            


            # 브랜치 및 끝점 추가
            # if obj_branch_points:
            #     obj_total_points.extend(obj_branch_points)
            # if obj_end_points:
            #     obj_total_points.extend(obj_end_points)

            # 매핑 포인트 추가
            # obj_mapping_points.extend(extract_mapping_point3(objected_mask, obj_total_points))

        # 배치 완료 시 진행률 업데이트
        fnUpdatePercentStatus(percent_per_batch)
        
        # 배치 완료 후 진행률 동적 계산 및 업데이트
        # processed_objects = batch_end - 1  # 현재까지 처리된 객체 수
        # current_progress = (processed_objects / total_objects) * 40  # 전체 진행률 기준 40% 범위로 계산
        # fnUpdatePercentStatus(current_progress)

    # np.int64를 int로 변환
    mapping_points_final_int = [[(int(x), int(y)) for x, y in sublist] for sublist in obj_mapping_points]

    # 각 리스트의 점들을 정렬 (기존 방식 유지)
    for points in mapping_points_final_int:
        points.sort(key=lambda point: (point[0], point[1]))

    # y축 중간값을 기준으로 정렬
    def get_mid_y(points):
        return (points[0][1] + points[1][1]) / 2

    mapping_points_final_int.sort(key=lambda points: get_mid_y(points))

    # for x in mapping_points_final_int:
    #     start = tuple(x[0])  # x[0]을 튜플로 변환
    #     end = tuple(x[1])    # x[1]을 튜플로 변환
    #     path = bfs(skeleton, start, end)

    #     # 경로의 길이가 3 이상인 경우에만 bfs_point에 추가
    #     if path and len(path) > 3:
    #         bfs_point.append(path)

    # 스켈레톤 + bfs 후 균열 적용 이미지 및 길이, 높이 등 출력
    overlay_image, crack_length_lst, crack_width_lst, l_overlay_image, w_overlay_image, max_width_coords = draw_crack(
        img = img,
        skeleton = skeleton, 
        bfs_point = mapping_points_final_int, 
        per_pixel_length = per_pixel_length, 
        per_pixel_width = per_pixel_width,
    )

    polygon = paths_to_polygons(mapping_points_final_int)
    bbox = polygon_to_bbox(mapping_points_final_int)

    #max_width_coords 추가  
    return crack_length_lst, crack_width_lst, polygon, bbox, overlay_image, l_overlay_image, w_overlay_image, max_width_coords

def paths_to_polygons(paths: List[List[Tuple[int, int]]]) -> List[List[int]]:
    polygon_lst = []

    for path in paths:
        # if len(path) < 3: continue  # 다각형은 최소한 3개의 점이 필요
        polygon = np.array(path).flatten().tolist()
        polygon_lst.append(polygon)
    return polygon_lst

# 폴리곤 리스트를 이용하여 바운딩 박스(bounding box)를 계산
def polygon_to_bbox(polygon_lst: List[List[int]]) -> List[Tuple]:
    bbox_lst = []
    for polygon in polygon_lst:
        points = np.array(polygon).reshape(-1, 2).astype(np.int32)
        
        max_x = max(points[:, 0])
        min_x = min(points[:, 0])
        max_y = max(points[:, 1])
        min_y = min(points[:, 1])

        bbox_lst.append([(int(min_x), int(min_y)), (int(max_x), int(max_y))])

    return bbox_lst

def draw_crack(
        img: np.ndarray,
        skeleton: np.ndarray,
        bfs_point: List[List[Tuple[(int,int)]]],
        per_pixel_length: float,
        per_pixel_width: float,
    ):

    # 원본 균열 이미지 (스켈레톤으로 뽑아낸 원본)
    crack_poly_img = cv2.cvtColor((skeleton * 255) - 255, cv2.COLOR_GRAY2BGR)
    crack_poly_img = crack_poly_img * 255
    
    # 균열 이미지로 시각화 작업 진행
    crack_img = crack_poly_img.copy()

    crack_length_img = crack_poly_img.copy()
    crack_width_img = crack_poly_img.copy()

    for ix, path in enumerate(bfs_point[:]):
        for i, j in path:
            # 균열 영역 그리기 (까만색)
            cv2.circle(crack_img, (i, j), 2, (0, 0, 0), -2)         # 원의 반지름을 2로 설정
            # 아이디
            # 균열 영역 주위 폴리곤 그리기 (빨강색)
            cv2.circle(crack_poly_img, (i, j), 4, (0, 0, 255), -2)  # 원의 반지름을 4로 설정
            # 길이, 높이
            # 균열 영역 주위 폴리곤 그리기 (초록색)
            cv2.circle(crack_length_img, (i, j), 4, (255, 0, 0), -2)  # 원의 반지름을 4로 설정
            # 균열 영역 주위 폴리곤 그리기 (파랑색)
            cv2.circle(crack_width_img, (i, j), 4, (0, 255, 0), -2)  # 원의 반지름을 4로 설정

    # 균열 + 폴리곤 그린 이미지 카피 (디버깅용)
    ori_crack_img_copy = crack_poly_img.copy()

    # 곤열 이미지 위에 폴리곤 합성
    cv2.addWeighted(crack_img, 0.5, crack_poly_img, 0.5, 0, crack_poly_img)

    # 길이, 폭 이미지 합성
    length_poly_img = cv2.addWeighted(crack_img, 0.5, crack_length_img, 0.5, 0)
    width_poly_img = cv2.addWeighted(crack_img, 0.5, crack_width_img, 0.5, 0)

    crack_length_lst = []
    crack_width_lst = []
    max_width_coords = []  # 가장 긴 부분의 좌표를 저장할 리스트

    for ix, path in enumerate(bfs_point[:]):
        text_x, text_y = path[len(path) // 2]
        text_x_length, text_y_length = path[len(path) // 2]
        text_x_width, text_y_width = path[len(path) // 2]

        # 균열 길이 측정
        total_crack_length = len(path)
        crack_length = np.round((per_pixel_length * 10) * total_crack_length, 2)
        crack_length_lst.append(crack_length)

        # 균열 폭 측정
        path_np = np.array(path)
        # x 및 y 좌표의 최소값과 최대값 계산
        x_min = int(np.min(path_np[:, 0]))
        y_min = int(np.min(path_np[:, 1]))
        x_max = int(np.max(path_np[:, 0]))
        y_max = int(np.max(path_np[:, 1]))

        if (x_min == x_max):
            x_max = x_min + 1
        if (y_min == y_max):
            y_max = y_min + 1

        bbox_width_img = img[y_min:y_max, x_min:x_max]

        white_pixel_count = 0
        if y_max - y_min >= x_max - x_min:
            max_white_pixel_count = 0
            max_y = 0
            for y in range(y_max - y_min):
                row_pixels = bbox_width_img[y, :]
                white_pixel_count = np.sum(row_pixels == 255)
                if white_pixel_count > max_white_pixel_count:
                    max_white_pixel_count = white_pixel_count
                    max_y = y
            max_width_coords.append((x_min, y_min + max_y, x_max, y_min + max_y))  # 수직 방향
        else:
            max_white_pixel_count = 0
            max_x = 0
            for x in range(x_max - x_min):
                col_pixels = bbox_width_img[:, x]
                white_pixel_count = np.sum(col_pixels == 255)
                if white_pixel_count > max_white_pixel_count:
                    max_white_pixel_count = white_pixel_count
                    max_x = x
            max_width_coords.append((x_min + max_x, y_min, x_min + max_x, y_max))  # 수평 방향

        crack_width = np.round(((per_pixel_width) * max_white_pixel_count) * 10, 2)
        crack_width_lst.append(crack_width)

        # 균열 아이디 출력
        length_text = f'{crack_length}mm'
        width_text = f'{crack_width}mm'
        text = f'{ix + 1}'
        (text_width, text_height), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)
        (text_width_length, text_height_length), _ = cv2.getTextSize(length_text, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)
        (text_width_width, text_height_width), _ = cv2.getTextSize(width_text, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)

        # 텍스트 시작 위치 설정 (예: 이미지의 오른쪽 하단)
        text_x = text_x - text_width   # 10은 오른쪽 여백
        text_y = text_y  # 10은 하단 여백

        text_x_length = text_x_length - text_width_length   # 10은 오른쪽 여백
        text_y_length = text_y_length  # 10은 하단 여백

        text_x_width = text_x_width - text_width_width   # 10은 오른쪽 여백
        text_y_width = text_y_width  # 10은 하단 여백

        # 이미지 경계 확인 및 조절
        if text_x < 0: text_x = 0
        if text_y - text_height < 0: text_y = text_height

        if text_x_length < 0: text_x_length = 0
        if text_y_length - text_height_length < 0: text_y_length = text_height_length

        if text_x_width < 0: text_x_width = 0
        if text_y_width - text_height_width < 0: text_y_width = text_height_width
        
        cv2.putText(crack_poly_img, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.putText(length_poly_img, length_text, (text_x_length, text_y_length), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.putText(width_poly_img, width_text, (text_x_width, text_y_width), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    
    return crack_poly_img, crack_length_lst, crack_width_lst, length_poly_img, width_poly_img, max_width_coords
    


def draw_crack_line_length(
        img:np.ndarray,
        skeleton:np.ndarray
        ,bfs_point:List[List[Tuple[(int,int)]]]
        ,colors_255:Tuple[(int,int,int)]
        ,per_pixel_length:int=None
        ,alpha1:float=.7
        ,alpha2:float=.5
        ,return_crack_length_with_img:bool=False
    ):
    """최종 균열 길이 정량화 결과 시각화

    Args:
        img (numpy.ndarray): 균열 segmenation 결과 이미지, 2차원 array형태로 0 or 255 값 만 가지도록 하여 입력
        skeleton (numpy.ndarray): 0 or 1로 표현된 2차원 array skeleton 이미지 값
        bfs_point (list): skeleton  내 모든 1값들의 좌표값 집합
        colors_255 (list): skeleton 내 각 균열 길이에 대응되는 color rgb값
        per_pixel_length (float, optional): 스티칭 된 이미지의 벽 width 실제 길이. Defaults to None.
        alpha1 (float, optional): 원본 이미지 및 균열 길이 시각화 결과 투명도 비율. Defaults to .7.
        alpha2 (float, optional): 원본 이미지 및 균열 길이 text 입력 시각화 결과 투명도 비율. Defaults to .5.
        return_crack_length_with_img(bool, optional) : crack length return 여부
    Returns:
        numpy.ndarray: 균열 길이 시각화 결과, 3차원 이미지
    """
    # 결과 시각화 확인
    image_color = cv2.cvtColor((skeleton * 255) - 255, cv2.COLOR_GRAY2BGR)
    image_color = image_color * 0
    overlay_img = image_color.copy() * 0

    for ix, path in enumerate(bfs_point[:]):
        for i, j in path:
            cv2.circle(overlay_img, (i, j), 2, (255, 0, 0), -2)  # 원의 반지름을 5로 설정
            cv2.circle(image_color, (i, j), 4, (255, 255, 255), -2)  # 원의 반지름을 5로 설정 => 

    ori_crack_img_copy = image_color.copy()
    cv2.addWeighted(overlay_img, alpha2, image_color, (1 - alpha2), 0, image_color)

    crack_length_lst = []
    for ix, path in enumerate(bfs_point[:]):
        font = cv2.FONT_HERSHEY_SIMPLEX
        text_x, text_y = path[len(path) // 2]
        
        r, g, b = (255, 10, 10)#colors_255[ix] # 균열 정량화 색 조절 가능한 부분
        crack_length = len(path)

        if per_pixel_length:
            crack_length = int(np.round(per_pixel_length * crack_length, 2))

        crack_length_lst.append(crack_length)
        text = "%dmm"%(crack_length)
        (text_width, text_height), _ = cv2.getTextSize(text, font, 0.55, 2)

        # 텍스트 시작 위치 설정 (예: 이미지의 오른쪽 하단)
        text_x = text_x - text_width   # 10은 오른쪽 여백
        text_y = text_y  # 10은 하단 여백

        # 이미지 경계 확인 및 조절
        if text_x < 0:
            text_x = 0
        if text_y - text_height < 0:
            text_y = text_height
        
        cv2.putText(image_color, text, (text_x, text_y), font, 0.55, (r-10, g-10, b-10), 2)

    if return_crack_length_with_img:
        return image_color, crack_length_lst, overlay_img
    else:
        return image_color, ori_crack_img_copy











def final_draw_measure_width(
        img:np.ndarray,
        max_length_pixel:int=50,
        per_pixel_width:float=None
    ) -> Tuple[(np.ndarray,List[List[List[Tuple]]])]:
    """UNET에서 나온 분류 결과를 토대로 균열 폭 측정하기
    
    Args:
        img (numpy.array): UNET 예측된 raw 분류 결과 array
        max_length_pixel (int, optional): 균열 폭 pixel  max 기준. Defaults to 50.
        acture_wall_width (_type_, optional): 라이더로 촬영된 실제 폭 길이. Defaults to None.
    Returns:
        numpy.array: 균열 폭이 표시된 segmentation 결과 img
    """
    img = np.uint8(img*255)
    skeleton = extract_skeleton(img)
    branching_points = extract_cross_point(skeleton)
    line_end_points = extract_end_point(skeleton,branching_points)
    width_info_lst_total = []

    if line_end_points:
        total_points = branching_points + line_end_points
        mapping_points_final = extract_mapping_point(skeleton, total_points)
        
        bfs_point = list(map(lambda x:bfs(skeleton, tuple(x[0]), tuple(x[1])), mapping_points_final))

        width_info_lst_total = extract_width(img, bfs_point, split=True)
        crack_width_seg = draw_crack_line_width(img, skeleton, width_info_lst_total, max_length_pixel, alpha1=.4, alpha2=.7, per_pixel_width=per_pixel_width)
    else:
        crack_width_seg = np.tile(np.expand_dims(img, axis=2), (1, 1, 3))

    return crack_width_seg,width_info_lst_total

def draw_crack_line_width(
        img:np.ndarray,
        skeleton:np.ndarray,
        width_info_lst_total_ori:List[List[Tuple]],
        max_length_pixel:int=50,alpha1:float=.4,alpha2:float=.7,
        per_pixel_width=None
    ):
    """
    최종 균열 폭 탐색 결과 시각화
    Args:
        img (numpy.ndarray): 균열 segmenation 결과 이미지, 2차원 array형태로 0 or 255 값 만 가지도록 하여 입력
        skeleton (numpy.ndarray): 0 or 1로 표현된 2차원 array skeleton 이미지 값
        width_info_lst_total (list): 균열 폭 탐색 결과
        alpha1 (float, optional): 원본 이미지 및 균열 길이 시각화 결과 투명도 비율. Defaults to .7.
        alpha2 (float, optional): 원본 이미지 및 균열 길이 text 입력 시각화 결과 투명도 비율. Defaults to .5.

    Returns:
        numpy.ndarray: 균열 길이 시각화 결과, 3차원 이미지
    """
    # 배경 이미지 만들기
    #image_color = np.uint8(np.zeros_like(skeleton))
    image_color = cv2.cvtColor((skeleton*255)-255, cv2.COLOR_GRAY2BGR)*0
    #image_color = np.where(image_color==0,255,image_color)
    # 균열 segmentation 결과 Gray to BGR
    img_color = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR).copy()
    # 균열 Segmntation 새로 넣은 배경
    img_color_copy = img_color*0
    
    #width_info_lst_total_ori = width_info_lst_total
    overlay_img = image_color.copy()
    
    
    final_point_lst = []
    final_width_length_lst = []
    final_rgb_lst = []
    for width_info_lst_total in width_info_lst_total_ori:
        point_lst = []
        width_length_lst = []
        rgb_lst = []
        for point,length in width_info_lst_total:
            if per_pixel_width:
                # acture_prop_crack = np.round(per_pixel_width /img.shape[1], 2)
                width_length = np.round(per_pixel_width * length, 2)
            #cv2.circle(overlay_img, point, 4, (255,0,0), -2)  # 원의 반지름을 5로 설정
            cv2.circle(overlay_img, point, 4, value_to_rgb(length, 0, max_length_pixel), -2) # max pixel 대비 균열 색조 조절 후 표시
            cv2.circle(img_color_copy, point, 4, (255, 255, 255), -2) # max pixel 대비 균열 색조 조절 후 표시
                
            point_lst.append(point)
            width_length_lst.append(width_length)
            rgb_lst.append(value_to_rgb(length, 0, max_length_pixel))
        
        # 각 균열 객체마다 폭 중간 값으로 정량화 값 추출
        if point_lst:
            length_sort = np.argsort(width_length_lst)
            # 오차를 고려해 중간값 정도 균열 폭 설정
            with_length_max = width_length_lst[length_sort[len(width_length_lst)//2]]
            # 균열 폭 max 값에 대한 r,g,b 추출
            width_rgb = value_to_rgb(max(width_length_lst), 0, max_length_pixel)
            
            final_point_lst.append(point_lst[len(width_length_lst)//2])
            final_width_length_lst.append(with_length_max)
            final_rgb_lst.append(width_rgb)
    
    # 배경 이미지에 원본 균열 이미지 덮어쓰기
    cv2.addWeighted(img_color_copy, alpha1, image_color, 1 - alpha1, 0, image_color)
    # 배경 이미지에 균열 폭 시각화 결과 덮어쓰기
    cv2.addWeighted(overlay_img, alpha2, image_color, 1 - alpha2, 0, image_color)

    
    for ix,point in enumerate(final_point_lst):
        text_x, text_y = point
        width_length_max = final_width_length_lst[ix]
        r, g, b = final_rgb_lst[ix]
        
        text = f"{width_length_max}mm"
        font = cv2.FONT_HERSHEY_SIMPLEX
        (text_width, text_height), _ = cv2.getTextSize(text, font, 0.55, 2)
        r, g, b = value_to_rgb(with_length_max, 0, max_length_pixel)
        
        # 텍스트 시작 위치 설정 (예: 이미지의 오른쪽 하단)
        text_x = text_x - text_width   # 10은 오른쪽 여백
        text_y = text_y  # 10은 하단 여백
        # 이미지 경계 확인 및 조절
        if text_x < 0: text_x = 0
        if text_y - text_height < 0: text_y = text_height
        
        cv2.putText(image_color,text,(text_x,text_y),font,0.55,(r-10,g-10,b-10),2)

    return image_color


def value_to_rgb(value, min_value, max_value):
    """입력된 값을 기준으로 빨강에서 파랑 rgb값 출력

    Args:
        value (float): 기준 값
        min_value (float): 최소 값
        max_value (float): 최대 값

    Returns:
        tuple: r,g,b 값
    """
    # 값이 범위 내에 있는지 확인
    if value < min_value:
        return (0, 0, 255)  # 파란색
    if value > max_value:
        return (255, 0, 0)  # 빨간색
    # 선형적으로 RGB 값 계산
    ratio = (value - min_value) / (max_value - min_value)
    red = int(255 * ratio)
    blue = int(255 * (1-ratio))
    return (red, 0, blue)

def is_overlapping(x, y, text_width, text_height, boxes, min_distance=10):
    for (bx, by, bw, bh) in boxes:
        if abs(x - bx) < (text_width + bw) / 2 + min_distance and abs(y - by) < (text_height + bh) / 2 + min_distance:
            return True
    return False