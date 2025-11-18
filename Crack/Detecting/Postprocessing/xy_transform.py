import numpy as np
from typing import List,Tuple


def move_x_y_polygon(polygon_lst:List[List[int]], start_x:int,start_y:int) -> List[List[int]]:
    new_polygon_lst = []

    for polygon in polygon_lst:
        points = np.array(polygon).reshape(-1, 2).astype(np.int32)

        points[:, 0] += start_x # x좌표 이동
        points[:, 1] += start_y # y좌표 이동
        new_polygon_lst.append(points.reshape(-1).tolist())

    return new_polygon_lst

def move_x_y_length_measure(length_seg_json:List[Tuple], start_x:int, start_y:int) -> List:
    new_length_seg_json = []

    for length_seg in length_seg_json:
        new_length_seg = []

        for x, y in length_seg:
            x += start_x
            y += start_y
            new_length_seg.append((x, y))

        new_length_seg_json.append(new_length_seg)

    return new_length_seg_json
        
def move_x_y_width_measure(width_seg_json:List[Tuple], start_x:int, start_y:int) -> List:
    new_width_seg_json = []

    for width_seg in width_seg_json:
        new_width_seg = []

        for width_point,width_length in width_seg:
            x, y = width_point
            x += start_x
            y += start_y
            new_width_seg.append([(x, y), width_length])

        new_width_seg_json.append(new_width_seg)

    return new_width_seg_json


def prop_x_y_polygon(polygon_lst:List[List[int]], x_prop: int = 0, y_prop: int = 0) -> List[List[int]]:
    """poylgon 결과를 원본 이미지 좌표계로 비율조절하는 함수"""
    new_polygon_lst = []

    for polygon in polygon_lst:
        points = np.array(polygon).reshape(-1, 2).astype(np.float32)
        points[:, 0] *= x_prop # x좌표 조절
        points[:, 1] *= y_prop # y좌표 조절
        new_polygon_lst.append(np.int32(points).reshape(-1).tolist())

    return new_polygon_lst

def prop_x_y_bbox(bbox_lst: List[List[Tuple]], x_prop: int = 0, y_prop: int = 0) -> List[List[Tuple]]:
    """poylgon 결과를 원본 이미지 좌표계로 비율조절하는 함수"""
    new_bbox_lst = []

    for point1,point2 in bbox_lst:
        x1, y1 = point1
        x2, y2 = point2
        x1 *= x_prop
        x2 *= x_prop
        y1 *= y_prop
        y2 *= y_prop

        new_bbox_lst.append([(int(x1),int(y1)),(int(x2),int(y2))])

    return new_bbox_lst

def prop_x_y_length_measure(length_seg_json: List[Tuple], x_prop: int = 0, y_prop: int = 0) -> List:
    """길이 측정 결과를 원본 이미지 좌표계로 비율조절하는 함수"""
    new_length_seg_json = []
    
    for length_seg in length_seg_json:
        new_length_seg = []

        for x, y in length_seg:
            x *= x_prop
            y *= y_prop
            new_length_seg.append((int(x), int(y)))

        new_length_seg_json.append(new_length_seg)

    return new_length_seg_json
        
def prop_x_y_width_measure(width_seg_json: List[Tuple], x_prop: int = 0, y_prop: int = 0) -> List:
    """폭 측정 결과를 원본 이미지 좌표계로 비율조절하는 함수"""
    new_width_seg_json = []

    for width_seg in width_seg_json:
        new_width_seg = []

        for width_point,width_length in width_seg:
            x, y = width_point
            x *= x_prop
            y *= y_prop
            new_width_seg.append([(int(x), int(y)),width_length])

        new_width_seg_json.append(new_width_seg)
        
    return new_width_seg_json