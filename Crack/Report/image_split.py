import cv2
import os
import json
import math

import numpy as np


class ImageSplit:
    def __init__(self, image_path, json_path, split_count=24):
        self.image_path = image_path
        self.json_path = json_path
        self.split_count = split_count

    def SplitImage(self):
        # 이미지 로드
        # image = cv2.imread(self.image_path)
        img_array = np.fromfile(self.image_path, np.uint8)
        image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        if image is None:
            print(f"이미지를 로드할 수 없습니다: {self.image_path}")
            return

        # JSON 데이터 로드
        with open(self.json_path, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)

        print('🧠 Splitting Image...')

        height2, width2, _ = image.shape
        maxHeight = math.ceil(height2 / self.split_count)

        dir_path = os.path.dirname(self.image_path)
        file_name = os.path.basename(self.image_path).split('.')[0].replace("_result", "")
        save_dir = os.path.join(dir_path, f"{file_name}_split")

        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        split_data = []
        part_index = 1

        for i in range(1, self.split_count + 1):
            startHeight = (i - 1) * maxHeight
            endHeight = i * maxHeight

            # 이미지 분할 및 저장
            split_img = image[startHeight:endHeight, :]
            save_path = os.path.join(save_dir, f"{file_name}_split_{i}.png")

            ext = os.path.splitext(save_path)[1]
            result, n = cv2.imencode(ext, split_img, None)
            if result:
                with open(save_path, mode='w+b') as f:
                    n.tofile(f)

            part_counter = 1
            rows = 0
            seq_counter = 1
            current_part_data = {
                "part": f"part{part_index}-{part_counter}",
                "imagePath": save_path,
                "jsonPath": []
            }

            for idx, value in enumerate(data, start=1):
                if startHeight < value['BBOX'][1][1] <= endHeight:
                    if rows >= 38:
                        if current_part_data["jsonPath"]:
                            split_data.append(current_part_data)
                        part_counter += 1
                        rows = 0
                        current_part_data = {
                            "part": f"part{part_index}-{part_counter}",
                            "imagePath": save_path,
                            "jsonPath": []
                        }

                    current_part_data["jsonPath"].append({
                        "NO": seq_counter,
                        "CRACK_ID": value['CRACK_DETECT_ID'],
                        "ESTIMATE_WIDTH": value.get("WIDTH_ESTIMATE"),
                        "ESTIMATE_HEIGTH": value.get("LENGTH_ESTIMATE")
                    })
                    seq_counter += 1
                    rows += 1

            if current_part_data["jsonPath"]:
                split_data.append(current_part_data)

            part_index += 1

        output_json_path = os.path.join(save_dir, f"{file_name}_split_data.json")
        with open(output_json_path, 'w', encoding='utf-8') as json_file:
            json.dump(split_data, json_file, indent=4, ensure_ascii=False)

        print(f"✅ Split images and JSON data saved in {save_dir}")

        return split_data