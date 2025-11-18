import cv2
import numpy as np

# 전처리
class PreProcessingService:
    def __init__(self, width:int, height:int):
        self.width = width
        self.height = height

    # 이미지 전처리 메서드: 이미지를 크기 조정하고 그리드로 자름
    def image_preprocessing(self, image:np.ndarray, normalization: bool = False):
        try:
            # 1. 원본 사이즈 가져오기
            ori_h_size, ori_w_size = image.shape[0], image.shape[1]
            # 2. 이미지를 그리드로 잘라서 각 조각을 정규화
            modi_img = self.resize_magnification(image, self.width, self.height)
            # 3. cut & normalize
            if normalization:
                img_cut = [(i / 127.5) - 1 for i in self.cut_img_grid(modi_img, self.width, self.height)]
            else:
                img_cut = [i for i in self.cut_img_grid(modi_img, self.width, self.height)]
            # 4. 자른 이미지 조각, 수정된 이미지, 원본 높이와 너비를 반환
            return img_cut, modi_img, ori_h_size, ori_w_size
        
        except Exception as e:
            raise e
        
    # 이미지 크기 조정 메서드: 이미지를 주어진 크기로 확대/축소
    @staticmethod
    def resize_magnification(img: np.ndarray, w_size = 320, h_size = 320):
        # 원본 이미지의 높이와 너비를 가져옴
        h, w, _ = img.shape
        
        # 높이와 너비를 새로운 크기에 맞게 조정
        h_scale = h_size * (h // h_size)
        w_scale = w_size * (w // w_size)
        
        # 이미지를 새로운 크기로 확대/축소
        modi_img = cv2.resize(img, (w_scale, h_scale), cv2.INTER_AREA)
        
        # 수정된 이미지를 반환
        return modi_img
    
    # 이미지 그리드 자르기 메서드: 이미지를 주어진 크기로 자름
    @staticmethod
    def cut_img_grid(img, w_size = 320, h_size = 320):
        img_lst = []

        # 이미지의 높이와 너비를 가져옴
        h, w, _ = img.shape
        
        # 이미지를 그리드로 잘라서 각 조각을 리스트에 추가
        for y in range(0, h, h_size):
            for x in range(0, w, w_size):
                cut_img = img[y: y + h_size, x: x + w_size]
                img_lst.append(cut_img)

        return img_lst
