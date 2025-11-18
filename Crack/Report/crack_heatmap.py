import json
import numpy as np
import cv2
import os 

class CrackMap:
    def __init__(self, json_file_path, image_path):
        self.json_file_path = json_file_path
        self.image_path = image_path
        self.data = self.read_json(json_file_path)

    def read_json(self, file_path):
        """JSON 파일을 읽고 데이터 반환"""
        with open(file_path, 'r') as file:
            data = json.load(file)
        return data

    def compute_centroids(self):
        """각 항목의 중심점을 계산하여 반환"""
        centroids = []
        for item in self.data:
            bbox = item['BBOX']
            centroid = [(bbox[0][0] + bbox[1][0]) / 2, (bbox[0][1] + bbox[1][1]) / 2]
            centroids.append(centroid)
        return np.array(centroids)

    def draw_crack_map(self, image_path):
        """크랙 맵을 그리고 저장하는 함수"""
        # 캔버스 크기를 자동으로 설정
        # img = cv2.imread(self.image_path, cv2.IMREAD_COLOR)
        img_array = np.fromfile(self.image_path, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        height, width, _ = img.shape
        background = np.ones((height, width, 3), dtype=np.uint8) * 255
        
        centroids = self.compute_centroids()

        # 그리드 사이즈 설정
        grid_size = width / 4
        num_cols = 4
        num_rows = int(height // grid_size) + 1
        grid_counts = np.zeros((num_rows, num_cols))

        # 그리드별 크랙 빈도 계산
        for centroid in centroids:
            col = int(centroid[0] // grid_size)
            row = int(centroid[1] // grid_size)
            if row < num_rows and col < num_cols:
                grid_counts[row, col] += 1

        max_count = grid_counts.max()

        # 빈도에 따라 색상 지정
        for row in range(num_rows):
            for col in range(num_cols):
                count = grid_counts[row, col]
                intensity = count / max_count if max_count != 0 else 0
                if intensity == 0:
                    color = (255, 255, 255)
                elif intensity <= 1/3:
                    color = (204, 255, 255)
                elif intensity <= 2/3:
                    color = (153, 204, 255)
                else:
                    color = (102, 102, 255)

                x_start = int(col * grid_size)
                y_start = int(row * grid_size)
                x_end = int(x_start + grid_size)
                y_end = int(y_start + grid_size)
                cv2.rectangle(background, (x_start, y_start), (x_end, y_end), color, -1)

        # 다각형 그리기 (검은색)
        for item in self.data:
            polygon = item['POLYGON']
            polygon = np.array(polygon).reshape((-1, 2)).astype(np.int32)
            cv2.polylines(background, [polygon], isClosed=False, color=(0, 0, 0), thickness=2)

        # 새로운 파일 저장 경로 생성
        dir_path = os.path.dirname(image_path)
        file_name = os.path.basename(image_path).split('.')[0].replace("_result", "")
        save_dir = os.path.join(dir_path, f"{file_name}_split")

        #디렉토리 확인 및 생성
        if not os.path.exists(save_dir):
            os.makedirs(save_dir, exist_ok=True)
        
        new_image_path = os.path.join(save_dir, f"{file_name}_crack_map.png")

        #파일 저장 & 확인
        ext = os.path.splitext(new_image_path)[1]
        result, n = cv2.imencode(ext, background, None)
        if result:
            with open(new_image_path, mode='w+b') as f:
                n.tofile(f)
                
        print(f"✅ Crack map saved to {new_image_path}")

        return new_image_path  # 반환값 유지