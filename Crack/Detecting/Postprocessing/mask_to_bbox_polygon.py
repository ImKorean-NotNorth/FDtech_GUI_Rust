import cv2
import numpy as np
from typing import List,Tuple

# 마스크 이미지에서 폴리곤(다각형) 윤곽선을 추출
def mask_to_polygon(mask_image: np.ndarray) -> List[List[int]]:
    mask_image = np.uint8(mask_image)

    contours, _ = cv2.findContours(mask_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    polygon_lst = []

    for contour in contours:
        if len(contour) < 3: continue  
        polygon = contour.flatten().tolist()
        polygon_lst.append(polygon)

    return polygon_lst

# 폴리곤 리스트를 이용하여 마스크 이미지를 생성
def polygon_to_mask(width, height, polygon_lst: List[List[int]]) -> List[List[int]]:
    mask_image2 = np.ones((height, width, 3), dtype=np.uint8) * 255
    
    for i, polygon in enumerate(polygon_lst, start = 1):
        points = np.array(polygon).reshape(-1, 2).astype(np.int32)
        cv2.fillPoly(mask_image2, [points], (0, 0, 255))

        # 텍스트 위치 계산
        top_left = np.min(points, axis=0)
        text_x, text_y = top_left[0], top_left[1] - 10

        # 텍스트 위치 조정 (이미지 경계를 고려하여 더 많이 이동)
        padding = 30  # 이동할 거리 (기존보다 더 크게 설정)
        
        if text_x < padding:
            text_x = padding
        if text_y < padding:
            text_y = top_left[1] + padding
        if text_x > width - (padding + 50):  # 텍스트 가로 길이(대략 50픽셀) 고려
            text_x = width - (padding + 50)
        if text_y > height - padding:  # 텍스트 세로 길이(대략 10픽셀) 고려
            text_y = height - padding

        cv2.putText(mask_image2, str(i), (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)

    return mask_image2

# 폴리곤 리스트를 이용하여 바운딩 박스(bounding box)를 계산
def polygon_to_bbox(polygon_lst: List[List[int]]) -> List[Tuple]:
    bbox_lst = []

    for polygon in polygon_lst:
        points = np.array(polygon).reshape(-1, 2).astype(np.int32)
        
        max_x = max(points[:, 0])
        min_x = min(points[:, 0])
        max_y = max(points[:, 1])
        min_y = min(points[:, 1])

        bbox_lst.append([(min_x, min_y), (max_x, max_y)])

    return bbox_lst