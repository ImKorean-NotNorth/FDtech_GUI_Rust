import math
import traceback
from tqdm.auto import tqdm
import numpy as np
import requests
import base64
from typing import List
import cv2
import logging

logger = logging.getLogger()

class CrackAIRequestSender:
    def __init__(self, fnUpdatePercent):
        self.serving_url = "http://121.187.18.13:18090/predictions/crack-detect" # 컨테이너와 바로통신
        self.fnUpdatePercent = fnUpdatePercent

    def send_image(self, images_lst: List, batch_size: int):
        total_response_lst = []
        try:
            # 전체 이미지 개수
            total_images = len(images_lst)

            # 한 배치에 몇 퍼센트를 할당할지 계산
            percent_per_batch = 40 / math.ceil(total_images / batch_size)

            # 초기 퍼센트
            current_batch_progress = 0

            # 빌드 전용 (tqdm 사용 + 단일 exe 파일 배포 시에는 콘솔창이 없어 오류 발생)
            for ix in range(0, len(images_lst), batch_size):
                batch = images_lst[ix : ix + batch_size]
                batch = [base64.b64encode(cv2.imencode('.png', image_array)[1]).decode("utf-8") for image_array in batch]
                payload = { "images" : batch }
                response = requests.post(self.serving_url, json = payload)
                total_response_lst.extend(response.json())

                # 진행 상황 업데이트
                current_batch_progress = percent_per_batch
                if total_images >= 5000:
                    if ix % (16 * 10) == 0:
                        self.fnUpdatePercent(current_batch_progress * 10)
                else:
                    self.fnUpdatePercent(current_batch_progress)
            
            # 디버깅 시만 사용 (빌드할 때 x)
            # for ix in tqdm(range(0, len(images_lst), batch_size)):
            #     batch = images_lst[ix : ix + batch_size]
            #     batch = [base64.b64encode(cv2.imencode('.png', image_array)[1]).decode("utf-8") for image_array in batch]
            #     payload = { "images" : batch }
            #     response = requests.post(self.serving_url, json = payload)
            #     total_response_lst.extend(response.json())

            #     # 진행 상황 업데이트
            #     current_batch_progress = percent_per_batch 
            #     self.fnUpdatePercent(current_batch_progress)
        
            return total_response_lst
        
        except Exception as e:
            trace_info = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
            logger.error(f"CrackAIRequestSender Error: {e}")
            logger.error(f"trace Info:\n{trace_info}")
    
    def send_image_with_post_process(self, images_lst: List, batch_size: int, threshold: float = 0.5):
        total_response_lst = []

        for ix in tqdm(range(0, len(images_lst), batch_size)):
            batch = images_lst[ix : ix + batch_size]
            batch = [base64.b64encode(cv2.imencode('.png', image_array)[1]).decode("utf-8") for image_array in batch]
            payload = { "images": batch }
            response = requests.post(self.serving_url, json = payload)

            result_array = []
            for image_array in response.json():
                result = np.where(np.array(image_array) > threshold, 1, 0)
                result_array.append(result)

            total_response_lst.extend(result_array)
            
        return total_response_lst