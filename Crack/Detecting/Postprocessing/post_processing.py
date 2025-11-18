import math
from typing import List
import cv2
import numpy as np
from collections import Counter

from Crack.Detecting.Postprocessing.mask_to_bbox_polygon import mask_to_polygon, polygon_to_bbox, polygon_to_mask
from Crack.Detecting.Postprocessing.measure_crack import final_draw_measure, final_draw_measure_width
from Crack.Detecting.Postprocessing.xy_transform import move_x_y_length_measure, move_x_y_polygon, move_x_y_width_measure, prop_x_y_bbox, prop_x_y_length_measure, prop_x_y_polygon, prop_x_y_width_measure

class PostProcessingService:

    def __init__(self, img, modi_img, ori_h_size, ori_w_size, pred_total, targetLength, ori_res_x, ori_res_y, fnUpdatePercentStatus):
        self.width = 256
        self.img = img
        self.modi_img = modi_img
        self.w_window = self.modi_img.shape[1] // self.width
        self.ori_h_size = ori_h_size
        self.ori_w_size = ori_w_size
        self.pred_total = pred_total
        self.targetLength = targetLength
        self.ori_res_x = ori_res_x
        self.ori_res_y = ori_res_y
        self.fnUpdatePercentStatus = fnUpdatePercentStatus

    # 정량화 진행
    def run(self):
        width_from_target_length = self.calculate_width(self.targetLength)
        length_from_target_length = self.calculate_height(self.targetLength)

        per_pixel_width = width_from_target_length / self.ori_res_x
        per_pixel_length = length_from_target_length / self.ori_res_y

        width_pred = [] # original 
        db_save_json_result_total = [] # 변환 이미지 크기에 대응되는 길이,폭, bbox,polygon 좌표계 저장
        ori_db_save_json_result_total = [] # 원본 이미지 크기에 대응되는 길이,폭, bbox,polygon 좌표계 저장

        ## DB에 저장될 좌표값 비율 원본으로 조절
        # polygon 값은 있지만 length seg 가 없을 경우도 있음
        y_prop = self.ori_h_size / self.modi_img.shape[0] # y좌표 비율 조정
        x_prop = self.ori_w_size / self.modi_img.shape[1] # x좌표 비율 조정
        
        try:
            # 256 단위로 이미지의 높이를 계산하여 세로 반복횟수 결정
            start_bbox_y = 0
            concatenated_rows = []  # 수평으로 연결된 이미지를 저장할 리스트
            
            for start in range(0, len(self.pred_total), self.w_window):
                # Original Masking 결과 append
                ori_seg_img_total = []
                start_bbox_x = 0

                # 256 단위로 이미지의 너비를 계산하여 가로 반복횟수 결정
                row_pred = []
                for pred in self.pred_total[start : start + self.w_window]:
                    # 균열 길이 및 폭 측정결과가 없는 균열 영역 삭제
                    pred_median_blur = cv2.medianBlur(np.uint8(pred) * 255, 5)
                    input_pred = np.where(pred_median_blur != 0, 1, 0)
                    row_pred.append(input_pred)

                # row_pred 리스트를 NumPy 배열로 변환
                row_pred_array = np.array(row_pred)
                # 모든 이미지가 동일한 크기로 맞추기 (예: 첫 번째 이미지의 크기 기준)
                target_height, target_width = row_pred_array[0].shape[:2]
                resized_images = [cv2.resize(img, (target_width, target_height)) for img in row_pred_array]

                # 이미지를 수평으로 연결
                if len(resized_images) > 0:
                    concatenated_image = cv2.hconcat(resized_images)
                    concatenated_rows.append(concatenated_image)

            # 수평으로 연결된 모든 이미지를 수직으로 연결
            if len(concatenated_rows) > 0:
                final_image = cv2.vconcat(concatenated_rows)
                blurred_image = cv2.medianBlur(np.uint8(final_image) * 255, 5)
                input_pred = np.where(blurred_image != 0, 1, 0)

                # 연결된 이미지를 사용하여 길이 측정
                # 길이 측정 결과 시각화 이미지  & 좌표 정보

                # 추가 max_width_coords
                length_seg_json, width_seg_json, polygon2, bbox2, overlay_image, l_overlay_image, w_overlay_image, max_width_coords = final_draw_measure(
                    img = input_pred, 
                    per_pixel_length = per_pixel_length, 
                    per_pixel_width = per_pixel_width,
                    ori_h_size = self.ori_res_y,
                    ori_w_size = self.ori_res_x,
                    fnUpdatePercentStatus = self.fnUpdatePercentStatus
                )
                
                if length_seg_json:
                    ori_db_save_json_result_total.append([ polygon2, bbox2, length_seg_json, width_seg_json ])

            # DB 적재를 위한 각 균열 개별 길이 및 폭 측정
            # ori_db_save_json_result_total = self.calculate_length_width_each_row(ori_db_save_json_result_total, per_pixel_width, per_pixel_length)

            # JSON 만들기
            crack_json_result = self.make_crack_row_json_data(ori_db_save_json_result_total)

            final_concat_img_ori_size = cv2.resize(np.uint8(overlay_image), (self.ori_w_size, self.ori_h_size))
            final_concat_img = cv2.addWeighted(self.img, 0.7, final_concat_img_ori_size, 0.3, 0)
            # 길이, 너비 이미지
            final_concat_l_img_ori_size = cv2.resize(np.uint8(l_overlay_image), (self.ori_w_size, self.ori_h_size))
            final_concat_length_img = cv2.addWeighted(self.img, 0.7, final_concat_l_img_ori_size, 0.3, 0)
            final_concat_w_img_ori_size = cv2.resize(np.uint8(w_overlay_image), (self.ori_w_size, self.ori_h_size))
            final_concat_width_img = cv2.addWeighted(self.img, 0.7, final_concat_w_img_ori_size, 0.3, 0)


            # final_concat_img = self.concat_img(crack_json_result)
            # 추가 max_width_coords
            return crack_json_result, final_concat_img, final_concat_length_img, final_concat_width_img, max_width_coords


        except Exception as e:
            raise e
    
    # 주어진 균열 데이터를 검사하여, 각 바운딩 박스 내에 포함된 길이 및 폭 데이터를 새로운 리스트에 추가하는 역할
    def modifiy_poly_bbox_value(self, db_save_json_result_total: List):
        new_db_save_json_result_total = []  # 새로운 결과를 저장할 리스트 초기화

        # 주어진 균열 데이터 리스트를 반복
        for ori_poly_lst, ori_bbox_lst, length_pt_lst, width_pt_lst in db_save_json_result_total:
            new_poly_lst = []  # 새로운 폴리곤 리스트 초기화
            new_bbox_lst = []  # 새로운 바운딩 박스 리스트 초기화
            new_length_lst = []  # 새로운 길이 리스트 초기화
            new_width_lst = []  # 새로운 폭 리스트 초기화

            # 각 바운딩 박스를 반복
            for ix, ((x1, y1), (x2, y2)) in enumerate(ori_bbox_lst):
                check_bbox_pt = []  # 바운딩 박스 내 점 체크 리스트 초기화
                # 길이 측정 점들을 반복
                for jx, length_pt in enumerate(length_pt_lst):
                    check_length_pt = []  # 길이 점 체크 리스트 초기화
                    # 각 점이 바운딩 박스 내에 있는지 확인
                    for x, y in length_pt:
                        check_x1 = (x >= x1 - 5)  # x좌표가 바운딩 박스 시작 x좌표보다 큰지 확인
                        check_y1 = (y >= y1 - 5)  # y좌표가 바운딩 박스 시작 y좌표보다 큰지 확인
                        check_x2 = (x <= x2 + 10)  # x좌표가 바운딩 박스 끝 x좌표보다 작은지 확인
                        check_y2 = (y <= y2 + 10)  # y좌표가 바운딩 박스 끝 y좌표보다 작은지 확인
                        check_length_pt.append(all([check_x1, check_y1, check_x2, check_y2]))  # 모든 조건이 참인지 확인 후 리스트에 추가

                    check_bbox_pt.append(all(check_length_pt))  # 바운딩 박스 내 모든 점이 포함되는지 확인 후 리스트에 추가

                if any(check_bbox_pt):  # 바운딩 박스 내 점이 하나라도 포함되면
                    check_length_ix = np.where(np.array(check_bbox_pt) == True)[0][0]  # 포함된 점의 인덱스 찾기
                    new_poly_lst.append(ori_poly_lst[ix])  # 새로운 폴리곤 리스트에 추가
                    new_bbox_lst.append(ori_bbox_lst[ix])  # 새로운 바운딩 박스 리스트에 추가
                    new_length_lst.append(length_pt_lst[check_length_ix])  # 새로운 길이 리스트에 추가
                    new_width_lst.append(width_pt_lst[check_length_ix])  # 새로운 폭 리스트에 추가
                    
            new_db_save_json_result_total.append([new_poly_lst, new_bbox_lst, new_length_lst, new_width_lst])  # 최종 결과 리스트에 추가

        return new_db_save_json_result_total  
    
    # 주어진 균열 데이터에서 각 균열의 길이와 폭을 계산하고, 이를 최종 리스트에 저장하여 반환
    def calculate_length_width_each_row(self, ori_db_save_json_result_total: List, per_pixel_width: float, per_pixel_length: float):
        total_poly_lst = []  # 전체 폴리곤 리스트 초기화
        total_bbox_lst = []  # 전체 바운딩 박스 리스트 초기화
        total_length_lst = []  # 전체 길이 리스트 초기화
        total_width_lst = []  # 전체 폭 리스트 초기화

        # 주어진 균열 데이터를 반복하면서 전체 리스트에 추가
        for poly_lst, bbox_lst, length_lst, width_lst in ori_db_save_json_result_total:
            total_poly_lst.extend(poly_lst)
            total_bbox_lst.extend(bbox_lst)
            total_length_lst.extend(length_lst)
            total_width_lst.extend(width_lst)

        final_total_poly_lst = []  # 최종 폴리곤 리스트 초기화
        final_total_bbox_lst = []  # 최종 바운딩 박스 리스트 초기화
        final_total_length_lst = []  # 최종 길이 리스트 초기화
        final_total_width_lst = []  # 최종 폭 리스트 초기화
        final_length_estimate_lst = []  # 최종 길이 추정 리스트 초기화
        final_width_estimate_lst = []  # 최종 폭 추정 리스트 초기화

        # 각 폴리곤 리스트 요소에 대해 반복
        for ix in range(len(total_poly_lst)):
            poly_lst = total_poly_lst[ix]
            bbox_lst = total_bbox_lst[ix]
            length_lst = total_length_lst[ix]
            width_lst = total_width_lst[ix]

            # 폭 리스트가 없는 경우 건너뜀
            if width_lst:

                # 균열 길이 및 폭 계산
                # crack_length = np.round(per_pixel_length * len(length_lst), 2)
                # crack_width = np.round(per_pixel_width * 0.1 * np.mean([i[1] for i in width_lst]), 5)

                crack_length2 = abs(bbox_lst[0][1] - bbox_lst[1][1])
                measure_crack_length = np.round((per_pixel_length * crack_length2) * 10, 2)

                # 최대 폭 구하기
                odd_index_values = [poly_lst[i] for i in range(1, len(poly_lst), 2)]
                counter = Counter(odd_index_values)
                # 폴리곤 y의 빈도가 가장 높은 픽셀 수 계산
                most_common_value, most_common_count = counter.most_common()[0]
                measure_crack_width = np.round((per_pixel_width * most_common_count) * 10, 4)

                # 최종 리스트에 추가
                final_total_poly_lst.append(poly_lst)
                final_total_bbox_lst.append(bbox_lst)
                final_total_length_lst.append(length_lst)
                final_total_width_lst.append(width_lst)
                final_length_estimate_lst.append(measure_crack_length)
                final_width_estimate_lst.append(measure_crack_width)

        # 최종 결과 리스트 반환
        return [final_total_poly_lst, final_total_bbox_lst, final_total_length_lst, final_total_width_lst, final_length_estimate_lst, final_width_estimate_lst]

    # 균열검출 결과를 key, value 형태의 json 데이터로 변환 
    def make_crack_row_json_data(self, ori_db_save_json_result_total: List):
        final_total_poly_lst, final_total_bbox_lst, final_total_length_lst, final_total_width_lst = ori_db_save_json_result_total[0]

        tb_crack_row_lst = []
        for ix in range(len(final_total_poly_lst)):
            tb_crack_row = {
                "CRACK_DETECT_ID": ix + 1,  # 인덱스 값을 CRACK_DETECT_ID에 할당
                "POLYGON": final_total_poly_lst[ix],
                "BBOX": final_total_bbox_lst[ix],
                "LENGTH_ESTIMATE": float(final_total_length_lst[ix]),
                "WIDTH_ESTIMATE": float(final_total_width_lst[ix])
            }
            tb_crack_row_lst.append(tb_crack_row)

        return tb_crack_row_lst
    
    
    # bbox + polygon + id
    def concat_img(self, crack_json_result):
        total_poly_lst = []
        for item in crack_json_result:
            # "POLYGON" 값을 가져와 [x, y] 쌍 리스트로 변환
            polygon = item['POLYGON']
            polygon_points = [polygon[i:i + 2] for i in range(0, len(polygon), 2)]
            total_poly_lst.append(polygon_points)

        # Segmentation 이미지 Concat
        final_concat_img = polygon_to_mask(self.ori_w_size, self.ori_h_size, total_poly_lst) # 조정된 polygon으로 mask 재생성
        final_concat_img_ori_size = cv2.resize(np.uint8(final_concat_img), (self.ori_w_size, self.ori_h_size))

        overlay = cv2.addWeighted(self.img, 0.7, final_concat_img_ori_size, 0.3, 0, final_concat_img_ori_size)

        return overlay

    # 영상에 담기는 가로 넓이
    def calculate_width(self, distance_cm, fov_degrees=67):
        # 시야각을 라디안으로 변환
        fov_radians = math.radians(fov_degrees)
        # 가로 넓이 계산
        width_cm = 2 * int(distance_cm) * math.tan(fov_radians / 2)
        return width_cm
    
    # 영상에 담기는 세로 넓이
    def calculate_height(self, distance_cm, fov_degrees=41):
        # 시야각을 라디안으로 변환
        fov_radians = math.radians(fov_degrees)
        # 세로 높이 계산
        height_cm = 2 * int(distance_cm) * math.tan(fov_radians / 2)
        return height_cm