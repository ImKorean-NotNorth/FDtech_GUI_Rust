import cv2
import numpy as np

from .utils import rotate_frame270, rotate_frame90


class BlendingService:
    def __init__(self, filePath = None, start = 0, end = 0, cLeft = 0, cTop = 0, cRight = 0, cBottom = 0, capture_period = 4.0):
        self._filePath = filePath

        self._frame_start = start
        self._frame_end = end

        self._crop_left = cLeft
        self._crop_top = cTop
        self._crop_right = cRight
        self._crop_bottom = cBottom

        self._capture_period = capture_period

    # 블렌딩 서비스 실행
    def run_blend_image_save(self):
        try:
            # 프레임 추출
            frames = self.extract_frames_by_interval(self._filePath, self._capture_period)

            # 프레임 회전
            rotate_frames = [rotate_frame270(frame) for frame in frames]

            # 편집 영역 설정
            # left = int(0 + self._crop_left)
            # top = int(0 + self._crop_top)
            # right = int(self._origin_resolution_x - self._crop_right)
            # bottom = int(self._origin_resolution_y - self._crop_bottom)

            left = int(0 + self._crop_left)
            top =  int(self._origin_resolution_y - self._crop_top)
            right = int(self._origin_resolution_x - self._crop_right)
            bottom = int(0 + self._crop_bottom)

            # 이미지 편집
            cropped_frames = [frame[left:right, bottom:top] for frame in rotate_frames]

            # 파노라마 이미지 생성
            rotated_panoramic_image = self.create_panoramic_with_overlap(cropped_frames, overlap_width=10)
            panoramic_image = cv2.cvtColor(rotate_frame90(rotated_panoramic_image), cv2.COLOR_BGR2RGB)
                        
            return panoramic_image, self._origin_resolution_x, self._origin_resolution_y

        except Exception as e:
            raise e

    # 1. 설정 주기에 따른 영상 프레임 추출 
    def extract_frames_by_interval(self, filePath, interval_sec):
        print('extract_frames_by_interval 메소드 실행')

        # 비디오 파일 로드를 위한 인스턴스 생성
        cap = cv2.VideoCapture(filePath) 

        self._origin_resolution_x = cap.get(cv2.CAP_PROP_FRAME_WIDTH)     # 해상도 너비
        self._origin_resolution_y = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)    # 해상도 높이    

        # 로드 실패 시 에러
        if not cap.isOpened():
            raise ValueError("Error opening video file")

        # 영상 fps 가져오기
        fps = cap.get(cv2.CAP_PROP_FPS)

        # 설정 주기에 따른 프레임 수 계산
        interval_frames = fps * interval_sec  

        frames = []
        frame_count = self._frame_start * fps
        frame_end = cap.get(cv2.CAP_PROP_FRAME_COUNT) if self._frame_end == 0 else self._frame_end * fps

        while True:
            # 1. 현재 프레임 위치 설정
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count) 
            # 2. 프레임 읽기
            success, frame = cap.read()
            # 3. 프레임 없을 시 루프 종료
            if not success: break
            # 4. 리스트에 프레임 추가
            frames.append(frame)
            # 5. 다음 프레임 위치로 이동 
            frame_count += interval_frames
            # 6. 현재 프레임 수가 전체 프레임 초과 시 중단
            if frame_count >= frame_end: break

        # 인스턴스 반납
        cap.release()

        print('extract_frames_by_interval 메소드 종료')
        return frames

    # 2. 이미지 블렌딩 (img1, img2를 overlap_width 폭 간격만큼 합침)
    def _blend_images(self, img1, img2, overlap_width):
        print('_blend_images 메소드 실행')

        # 2-1. img1의 높이와 넓이 조회
        height, width, _ = img1.shape

        # 2-2. 블렌딩 결과를 저장할 새로운 이미지 생성
        blended_image = np.zeros((height, width + img2.shape[1] - overlap_width, 3), dtype=np.uint8)

        # 2-3. 첫 번째 이미지를 블렌딩 이미지의 왼쪽 부분에 복사
        blended_image[:, :width] = img1

        # 2-4. 알파 값 배열 생성 (1에서 0으로 선형 변화)
        alpha = np.linspace(1, 0, overlap_width)

        # 2-5. 겹치는 부분을 점진적으로 블렌딩
        for i in range(overlap_width):
            blended_image[:, width - overlap_width + i] = img1[:, width - overlap_width + i] * alpha[i] + img2[:, i] * (1 - alpha[i])

        # 2-6. 두 번째 이미지의 나머지 부분을 블렌딩 이미지의 오른쪽에 복사
        blended_image[:, width:] = img2[:, overlap_width:]

        return blended_image
    
    # 3. 파노라마 이미지 생성
    def create_panoramic_with_overlap(self, frames, overlap_width=0):
        print('create_panoramic_with_overlap 메소드 실행')

        # 첫 번째 이미지를 파노라마 이미지로 설정
        panoramic_image = frames[0]
        # 나머지 이미지를 차례로 블렌딩
        for i in range(1, len(frames)):
            panoramic_image = self._blend_images(panoramic_image, frames[i], overlap_width)

        return panoramic_image
