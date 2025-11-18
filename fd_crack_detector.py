import datetime
import subprocess
import json
import multiprocessing
import sys
import os
import logging
import time
import tkinter as tk
from tkinter import messagebox
from typing import Literal
from PySide6 import QtCore
from PySide6 import QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap, QPainter, QPen, QIntValidator
from PySide6.QtWidgets import *
from PySide6.QtGui import QPalette
import debugpy
import numpy as np
import requests
import traceback
from Crack.Detecting.Postprocessing.post_processing import PostProcessingService
from Crack.Detecting.Preprocessing.pre_processing import PreProcessingService
from Crack.Report.report_vietnam import report
from Crack.Stitching.Blending.blending import BlendingService
from Crack.Model.video_data_model import VideoDataModel
from Crack.Detecting.Serving.crack_ai_request_sender import CrackAIRequestSender
import cv2



# 백그라운드 TorchServe 실행
# torchserve --start --model-store TorchServe/model_store --ts-config TorchServe/config_properties/config_model.properties --models crack-detect=hybrid_segmentor-cuda-2.mar --disable-token-auth

# 소프트웨어 usb 바인드
# def get_usb_serial_by_name(target_volume_name="CRACKDETECT"):
#     try:
#         # USB 드라이브 볼륨 정보 가져오기
#         volume_info = subprocess.run(
#             ["wmic", "volume", "get", "DriveLetter,Label,SerialNumber"],
#             capture_output=True, text=True
#         ).stdout.strip().split("\n")
        

#         for line in volume_info[1:]:  # 첫 번째 줄(헤더) 제외
#             parts = line.strip().split()
#             if len(parts) < 3:
#                 continue

#             drive_letter = parts[0]  # 예: "D:"
#             volume_label = parts[1]   # 예: "CRACKDETECT"
#             serial_number = parts[2]  # USB의 시리얼 번호

#             if volume_label.upper() == target_volume_name.upper():
#                 print(f"USB 드라이브 '{target_volume_name}' 찾음: 드라이브 {drive_letter}, 시리얼 {serial_number}")
#                 return serial_number

#         print(f"USB 드라이브 '{target_volume_name}'를 찾을 수 없습니다.")
#         return None

#     except Exception as e:
#         print("오류 발생:", e)
#         return None

# # 허용된 USB 시리얼 번호
# ALLOWED_SERIAL = "989177019"

# if get_usb_serial_by_name() != ALLOWED_SERIAL:
#     root = tk.Tk()
#     root.withdraw()  # 메인 윈도우 숨기기
#     messagebox.showerror("ERROR", "This is not the correct USB. Please use the correct USB. Cannot execute.")
#     sys.exit()

# # 실행 파일의 디렉토리 확인
if getattr(sys, 'frozen', False):
    program_directory = os.path.dirname(os.path.abspath(sys.executable))
    # macOS에서 .app 패키지의 Contents/MacOS 디렉토리를 상위 디렉토리로 이동
    if sys.platform == "darwin":  # macOS인지 확인
        program_directory = os.path.abspath(os.path.join(program_directory, "../../.."))
else: 
    program_directory = os.path.dirname(os.path.abspath(__file__))

# 로그 파일 설정
log_dir = os.path.join(program_directory, 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'app.log')

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler(log_file),
                                logging.StreamHandler()])

logger = logging.getLogger()

# 예외 핸들러 등록
def my_exception_hook(exctype, value, tb):
    trace_info = ''.join(traceback.format_exception(exctype, value, tb))
    logger.info(f"Error : {exctype}, {value}")
    logger.error(f"traceInfo :\n{trace_info}")

    sys.__excepthook__(exctype, value, tb)
sys.excepthook = my_exception_hook


# # 초기 서버 로딩 화면
# class LoadingDialog(QDialog):
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.setFixedSize(200, 100)
#         self.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.CustomizeWindowHint)

#         # 추가
#         palette = self.palette()
#         is_dark = palette.color(QPalette.Window).value() < 128

#         if is_dark:
#             self.setStyleSheet("""
#                 QDialog {
#                     background-color: #FFFFFF;
#                 }
#                 QProgressBar {
#                     background-color: #FFFFFF;
#                 }
#             """)
#         # 여기까지

#         self.layout = QVBoxLayout()
#         self.label = QLabel("Waiting AI Server Connect..")
#         self.progress_bar = QProgressBar()
#         self.progress_bar.setRange(0, 100)
        
#         self.layout.addWidget(self.label)
#         self.layout.addWidget(self.progress_bar)
#         self.setLayout(self.layout)

#         self.timer_count = 0
#         self.timer = QtCore.QTimer(self)
#         self.timer.timeout.connect(self.check_server_status)
#         self.timer.start(3000)  # 3초마다 실행

#         self.animation_timer = QtCore.QTimer(self)
#         self.animation_timer.timeout.connect(self.update_animation)
#         self.animation_timer.start(100)

#         self.current_value = 0
        
#         self.setModal(True)

        # 창을 화면 중앙에 배치
    # def center(self):
    #     frameGm = self.frameGeometry()
    #     screen = QApplication.primaryScreen().availableGeometry().center()
    #     frameGm.moveCenter(screen)
    #     self.move(frameGm.topLeft())

    # def check_server_status(self):
    #     try:
    #         if self.timer_count >= 20:
    #             self.animation_timer.stop()
    #             self.label.setText('AI Server Connect Failed.\nApp will close in 3 seconds.')
    #             QtCore.QTimer.singleShot(3000, QApplication.quit)

    #         response = requests.get("http://211.218.171.145:8181/ping")
    #         if response.status_code == 200 and "Healthy" in response.text:
    #             # 서버가 연결됨
    #             self.close()
    #             self.timer.stop()
    #         else:
    #             self.timer_count += 1
                
    #     except requests.RequestException as e:
    #         # 오류 처리 (예: 서버가 연결되지 않음)
    #         print("서버 연결 실패:", str(e))

    # def update_animation(self):
    #     self.current_value = (self.current_value + 10) % 101  # 10씩 증가하여 0~100 반복
    #     self.progress_bar.setValue(self.current_value)

    # def update_progress(self, value):
    #     self.progress_bar.setValue(value)

    # def keyPressEvent(self, event):
    #     if event.key() == QtCore.Qt.Key_Escape:
    #         event.ignore()

class CustomGraphicsView(QGraphicsView):
    def wheelEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            if event.angleDelta().y() > 0:
                self.scale(1.2, 1.2)
            else:
                self.scale(1 / 1.2, 1 / 1.2)
            event.accept()  # 이벤트 전파 차단 (스크롤 방지)
        else:
            super().wheelEvent(event)

class EditVideoPreviewWindow(QDialog):
    def __init__(self, path, startTime, endTime, maximumEndTime, cropL, cropT, cropR, cropB, defaultFrameSecond, parent):
        self.path = path
        self.startTime = startTime
        self.endTime = endTime
        self.maximumEndTime = maximumEndTime
        self.cropL = cropL
        self.cropT = cropT
        self.cropR = cropR
        self.cropB = cropB
        self.frameInterval = float(defaultFrameSecond)
        self.parent = parent

        super().__init__()
        self.setGeometry(600, 600, 1200, 600)

        # 창을 화면 중앙에 배치
        frameGm = self.frameGeometry() 
        screen = QApplication.primaryScreen().availableGeometry().center() 
        frameGm.moveCenter(screen) 
        self.move(frameGm.topLeft())

        # 창 헤더 등록
        self.setWindowTitle('FDTech Crack Detect v1.0 - Video Editing Preview Window')
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        
        previewQh = QHBoxLayout()
        previewQh.setStretch(0, 1)
        previewQh.setStretch(1, 1)

        # 블렌딩 실행
        img, ori_x, ori_y = BlendingService(
            path, 
            self.convert_minutes_to_seconds(int(self.startTime.split(':')[0]), int(self.startTime.split(':')[1])), 
            self.convert_minutes_to_seconds(int(self.endTime.split(':')[0]), int(self.endTime.split(':')[1])),
            cropL, cropT, cropR, cropB
        ).run_blend_image_save()

        # OpenCV 이미지(numpy 배열)를 QPixmap으로 변환
        height, width, channel = img.shape
        bytes_per_line = channel * width
        q_image = QImage(img.data, width, height, bytes_per_line, QImage.Format_BGR888)  # OpenCV 이미지는 BGR 형식
        pixmap = QPixmap.fromImage(q_image)

        self.scene = QGraphicsScene()
        self.scene.addPixmap(pixmap)
        
        self.view = CustomGraphicsView()
        self.view.setScene(self.scene)

        # 전체 이미지 출력
        self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
        # 드래그
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)
        # 확대/축소
        self.view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

        self.preview_frame = QFrame()
        self.preview_time_gb = QGroupBox('Time Edit')

        self.preview_lv = QVBoxLayout()


        self.preview_time_lv = QVBoxLayout()
        editPreviewVideoTimeStart_label = QLabel('Start Time')
        self.editPreviewVideoTimeStart_input = QTimeEdit()
        self.editPreviewVideoTimeStart_input.setDisplayFormat("mm:ss")
        self.editPreviewVideoTimeStart_input.setTime(QtCore.QTime(0, int(self.startTime.split(':')[0]), int(self.startTime.split(':')[1])))
        self.editPreviewVideoTimeStart_input.timeChanged.connect(self.fnChangeTime)
        self.editPreviewVideoTimeStart_input.setStyleSheet('background-color: rgb(255, 255, 255);')
        
        editPreviewVideoTimeEnd_label = QLabel('End Time')
        self.editPreviewVideoTimeEnd_input = QTimeEdit()
        self.editPreviewVideoTimeEnd_input.setDisplayFormat("mm:ss")
        self.editPreviewVideoTimeEnd_input.setTime(QtCore.QTime(0, int(self.endTime.split(':')[0]), int(self.endTime.split(':')[1])))
        self.editPreviewVideoTimeEnd_input.timeChanged.connect(self.fnChangeTime)
        self.editPreviewVideoTimeEnd_input.setStyleSheet('background-color: rgb(255, 255, 255);')

        self.preview_time_lv.addWidget(editPreviewVideoTimeStart_label)
        self.preview_time_lv.addWidget(self.editPreviewVideoTimeStart_input)
        self.preview_time_lv.addWidget(editPreviewVideoTimeEnd_label)
        self.preview_time_lv.addWidget(self.editPreviewVideoTimeEnd_input)
        self.preview_time_gb.setLayout(self.preview_time_lv)

        # Crop ----------------------------------------------------------------------------------
        self.preview_crop_gb = QGroupBox('Crop Edit')
        self.preview_crop_lv = QVBoxLayout()

        left_lh = QHBoxLayout()
        leftLabel = QLabel('Left')
        self.leftInput = QtWidgets.QSpinBox() 
        self.leftInput.setRange(0, int(ori_x)) 
        self.leftInput.setValue(int(cropL))
        self.leftInput.setSingleStep(10)
        self.leftInput.valueChanged.connect(self.fnUpdateCrop)
        left_lh.addWidget(leftLabel)
        left_lh.addWidget(self.leftInput)
        
        top_lh = QHBoxLayout()
        topLabel = QLabel('Top')
        self.topInput = QtWidgets.QSpinBox() 
        self.topInput.setRange(0, int(ori_y)) 
        self.topInput.setValue(int(cropT))
        self.topInput.setSingleStep(10)
        self.topInput.valueChanged.connect(self.fnUpdateCrop)
        top_lh.addWidget(topLabel)
        top_lh.addWidget(self.topInput)

        right_lh = QHBoxLayout()
        rigthLabel = QLabel('Right')
        self.rightInput = QtWidgets.QSpinBox() 
        self.rightInput.setRange(0, int(ori_x)) 
        self.rightInput.setValue(int(cropR))
        self.rightInput.setSingleStep(10)
        self.rightInput.valueChanged.connect(self.fnUpdateCrop)
        right_lh.addWidget(rigthLabel)
        right_lh.addWidget(self.rightInput)

        bottom_lh = QHBoxLayout()
        bottomLabel = QLabel('Bottom')
        self.bottomInput = QtWidgets.QSpinBox() 
        self.bottomInput.setRange(0, int(ori_y)) 
        self.bottomInput.setValue(int(cropB))
        self.bottomInput.setSingleStep(10)
        self.bottomInput.valueChanged.connect(self.fnUpdateCrop)
        bottom_lh.addWidget(bottomLabel)
        bottom_lh.addWidget(self.bottomInput)

        self.preview_crop_lv.addLayout(left_lh)
        self.preview_crop_lv.addLayout(top_lh)
        self.preview_crop_lv.addLayout(right_lh)
        self.preview_crop_lv.addLayout(bottom_lh)

        self.preview_crop_gb.setLayout(self.preview_crop_lv)

        # Frame Interval Edit ----------------------------------------------------------------------------------
        self.preview_frameInterval_gb = QGroupBox('Extract Frame Edit')
        self.preview_frameInterval_lv = QVBoxLayout()

        frameIntervalLabel = QLabel('Interval Second')
        self.frameInterval_input = QtWidgets.QDoubleSpinBox()  # QDoubleSpinBox로 변경
        self.frameInterval_input.setDecimals(1)  # 소수점 자리수를 1로 설정
        self.frameInterval_input.setValue(self.frameInterval)  # 초기값 설정
        self.frameInterval_input.setMinimum(0.1)
        self.frameInterval_input.setSingleStep(0.1)  # 증가/감소 스텝을 0.1로 설정
        self.frameInterval_input.valueChanged.connect(self.fnIntervalSecond)  # 값 변경 이벤트 연결


        self.preview_frameInterval_lv.addWidget(frameIntervalLabel)
        self.preview_frameInterval_lv.addWidget(self.frameInterval_input)
        self.preview_frameInterval_gb.setLayout(self.preview_frameInterval_lv)


        self.preview_generate_button = QPushButton('Regenerate Image')
        self.preview_generate_button.clicked.connect(self.fnRegenerateBtn)
        self.preview_save_button = QPushButton('Save Image')
        self.preview_save_button.clicked.connect(self.fnSaveImageBtn)
        self.preview_confirm_button = QPushButton('Confirm')
        self.preview_confirm_button.clicked.connect(self.fnConfirmBtn)
        self.preview_exit_button = QPushButton('Exit')
        self.preview_exit_button.clicked.connect(self.fnExitBtn)

        self.preview_lv.addWidget(self.preview_time_gb)
        self.preview_lv.addWidget(self.preview_crop_gb)
        self.preview_lv.addWidget(self.preview_frameInterval_gb)
        self.preview_lv.addWidget(self.preview_generate_button)
        self.preview_lv.addWidget(self.preview_save_button)
        self.preview_lv.addWidget(self.preview_confirm_button)
        self.preview_lv.addWidget(self.preview_exit_button)
        self.preview_lv.setStretch(0, 2)
        self.preview_lv.setStretch(1, 3)
        self.preview_lv.setStretch(2, 1)

        self.preview_frame.setLayout(self.preview_lv)

        previewQh.addWidget(self.view)
        previewQh.addWidget(self.preview_frame)
        previewQh.setStretch(0, 3)
        previewQh.setStretch(1, 1)
        
        self.setLayout(previewQh)

    # Regenerate Image 실행 함수
    def fnRegenerateBtn(self):
        # 1. BlendingService 실행 및 새로운 이미지 생성
        a, b, c = BlendingService(
            self.path, 
            self.convert_minutes_to_seconds(int(self.editPreviewVideoTimeStart_input.text().split(':')[0]), int(self.editPreviewVideoTimeStart_input.text().split(':')[1])), 
            self.convert_minutes_to_seconds(int(self.editPreviewVideoTimeEnd_input.text().split(':')[0]), int(self.editPreviewVideoTimeEnd_input.text().split(':')[1])),  
            self.cropL, self.cropT, self.cropR, self.cropB, 
            float(self.frameInterval)
        ).run_blend_image_save()
        
        # 2. OpenCV 이미지(numpy 배열)를 QPixmap으로 변환
        height, width, channel = a.shape
        bytes_per_line = channel * width
        q_image = QImage(a.data, width, height, bytes_per_line, QImage.Format_BGR888)  # OpenCV 이미지는 BGR 형식
        pixmap = QPixmap.fromImage(q_image)
        
        # 3. 새로운 이미지를 기존 scene에 업데이트
        if hasattr(self, 'scene'):  # 기존 scene이 존재하면 초기화
            self.scene.clear()
        else:
            self.scene = QGraphicsScene()  # scene이 없으면 새로 생성

        self.scene.addPixmap(pixmap)  # 새로운 이미지 추가

        # 4. view에 scene 설정 (뷰가 이미 설정된 경우에는 다시 연결 필요 없음)
        if not hasattr(self, 'view'):  # view가 초기화되어 있지 않으면 생성
            self.view = CustomGraphicsView()
        self.view.setScene(self.scene)  # scene을 view에 연결


    # 시간 변경 validation 
    def fnChangeTime(self):
        timeLengthList = self.maximumEndTime.split(':')
        if self.editPreviewVideoTimeStart_input.time() >= QtCore.QTime(0, int(timeLengthList[0]), int(timeLengthList[1])):
            QMessageBox.information(self, 'Invalid Time', 'Start time must be less than the duration of the video')
            self.editPreviewVideoTimeStart_input.setTime(QtCore.QTime(0, 0, 0))
            return 

        if (self.editPreviewVideoTimeEnd_input.time() >= QtCore.QTime(0, int(timeLengthList[0]), int(timeLengthList[1]))):
            self.editPreviewVideoTimeEnd_input.setTime(QtCore.QTime(0, int(timeLengthList[0]), int(timeLengthList[1])))
            return 
        
        if self.editPreviewVideoTimeStart_input.time() > self.editPreviewVideoTimeEnd_input.time():
            QMessageBox.information(self, 'Invalid Time', 'Start time must be less than end time')
            self.editPreviewVideoTimeStart_input.setTime(QtCore.QTime(0, 0, 0))
            return

    # crop 변경 함수
    def fnUpdateCrop(self):
        self.cropL = self.leftInput.value()
        self.cropT = self.topInput.value()
        self.cropR = self.rightInput.value()
        self.cropB = self.bottomInput.value()

    # IntervalSecond 변경 함수
    def fnIntervalSecond(self):
        self.frameInterval = self.frameInterval_input.text()

    # Save 함수
    def fnSaveImageBtn(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Image Save", "", "PNG File (*.png)")
        if file_path:
            try:
                # QPixmap 또는 QImage 저장
                for item in self.scene.items():
                    # 항목이 QGraphicsPixmapItem인지 확인
                    if isinstance(item, QGraphicsPixmapItem):
                        # Pixmap 가져오기
                        item.pixmap().save(file_path)
                # 저장 성공 메시지
                QMessageBox.information(self, "Image Save", f"Image saved successfully:\n\n{file_path}")

            except Exception as e:
                print(f"이미지 저장 중 오류 발생: {e}")

    # Confirm 함수
    def fnConfirmBtn(self):
        # 부모 윈도우 제어
        if self.editPreviewVideoTimeStart_input.text() == '00:00' or self.editPreviewVideoTimeEnd_input.text() == '00:00':
            self.parent.editVideoNone_radio.setChecked(True)
            self.parent.editVideoTime_radio.setChecked(False)
            self.parent.editVideoTimeStart_input.setEnabled(False)
            self.parent.editVideoTimeEnd_input.setEnabled(False)
            self.parent.editVideoTimeStart_input.setTime(QtCore.QTime(0, 0, 0))
            self.parent.editVideoTimeEnd_input.setTime(QtCore.QTime(0, 0, 0))

        if self.editPreviewVideoTimeStart_input.text() != '00:00' or self.editPreviewVideoTimeEnd_input.text() != '00:00':
            self.parent.editVideoTime_radio.setChecked(True)
            self.parent.editVideoTimeStart_input.setEnabled(True)
            self.parent.editVideoTimeEnd_input.setEnabled(True)
            self.parent.editVideoTimeStart_input.setTime(QtCore.QTime(0, int(self.editPreviewVideoTimeStart_input.text().split(':')[0]), int(self.editPreviewVideoTimeStart_input.text().split(':')[1])))
            self.parent.editVideoTimeEnd_input.setTime(QtCore.QTime(0, int(self.editPreviewVideoTimeEnd_input.text().split(':')[0]), int(self.editPreviewVideoTimeEnd_input.text().split(':')[1])))
        
        if self.cropL != 0 or self.cropT != 0 or self.cropR != 0 or self.cropB != 0:
            self.parent.leftInput.setValue(self.cropL)
            self.parent.topInput.setValue(self.cropT)
            self.parent.rightInput.setValue(self.cropR)
            self.parent.bottomInput.setValue(self.cropB)

        if self.frameInterval_input.text() != 4.0:
            self.parent.editVideoInterval_input.setText(str(self.frameInterval))

        self.accept()

    # Exit 함수
    def fnExitBtn(self):
        self.reject()

    # mm:ss -> 초
    def convert_minutes_to_seconds(self, minute, second): 
        minutes = minute * 60 
        second += minutes 
        return second




# 영상 편집 사이드바 창
class EditVideoWindow(QDialog):
    def __init__(self, path, parent):
        print('EditVideoWindow 실행')
        super().__init__()

        # 창 크기 설정
        self.setGeometry(600, 600, 900, 600)

        # 창을 화면 중앙에 배치
        frameGm = self.frameGeometry() 
        screen = QApplication.primaryScreen().availableGeometry().center() 
        frameGm.moveCenter(screen) 
        self.move(frameGm.topLeft())

        # 창 헤더 등록
        self.setWindowTitle('FDTech Crack Detect v1.1 - Video Editing Window')
        self.setWindowModality(QtCore.Qt.ApplicationModal)

        # 경로 파일 불러오기
        self.path = path
        self.cap = cv2.VideoCapture(self.path) 

        if not self.cap.isOpened():
            print("동영상을 열 수 없습니다.")
            sys.exit()
        
        # 부모 윈도우 참조
        self.parent = parent
        
        # 기본 추출 프레임 초
        self.defaultFrameSecond = '4.0'

        # 영상 정보 가져오기
        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS))                      # FPS 가져오기
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))     # 전체 프레임 수
        self.total_seconds = self.total_frames / self.fps                   # 전체 시간 (초)

        self.start_frame = 0                                                # 시작 프레임
        self.end_frame = self.total_frames                                  # 종료 프레임

        self.selectedFileWidth = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)     # 해상도 너비
        self.selectedFileHeight = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)   # 해상도 높이    
        
        # UI
        editVideoWindowMain_lv = QVBoxLayout()
        playSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        # 1. 비디오
        self.editVideoWindowVideo_view = QGraphicsView()
        self.editVideoWindowVideo_scene = QGraphicsScene()
        
        self.editVideoWindowVideo_view.setScene(self.editVideoWindowVideo_scene)

        # 2. 동영상 슬라이더바
        editVideoWindowFeature_gb = QGroupBox('Video Edit Controller')
        editVideoWindowFeature_lv = QVBoxLayout()

        # 2-1. 시간 선택 및 슬라이더바
        videoEditFirst_gb = QGroupBox()
        videoEditFirst_lh = QHBoxLayout()

        # 2-1-2. 슬라이더바
        timeSlider_lh = QHBoxLayout()
        sliderBar = QSlider(Qt.Horizontal, self)

        sliderBar.setMinimum(self.start_frame)
        sliderBar.setMaximum(self.end_frame)
        sliderBar.valueChanged.connect(self.update_frame)

        self.timeStart_label = QLabel('0:00')
        self.timeSplit_label = QLabel(' / ')
        self.timeEnd_label = QLabel('0:00')

        ## 동영상 길이 계산
        self.duration = int(self.total_frames / self.fps)
        self.endTime = self.convert_seconds_to_minutes(self.duration)
        self.timeEnd_label.setText(self.endTime)

        timeSlider_lh.addWidget(sliderBar)
        timeSlider_lh.addWidget(self.timeStart_label)
        timeSlider_lh.addWidget(self.timeSplit_label)
        timeSlider_lh.addWidget(self.timeEnd_label)

        videoEditFirst_lh.addLayout(timeSlider_lh)
        videoEditFirst_gb.setLayout(videoEditFirst_lh)

        # 2-2. edit
        editArea_lh = QHBoxLayout()
        videoEditSecond_gb = QGroupBox('Time Editor')

        # 2-2-1. 시간 선택
        editTime_lv = QVBoxLayout()
        editVideoTimeFirst_lh = QHBoxLayout()
        editVideoTime_lh = QHBoxLayout()
        
        self.editVideoNone_radio = QRadioButton("None")
        self.editVideoNone_radio.setChecked(True)
        self.editVideoNone_radio.clicked.connect(self.fnCheckRadio)

        self.editVideoTime_radio = QRadioButton("Use Time Editor")
        self.editVideoTime_radio.clicked.connect(self.fnCheckRadio)

        editVideoTimeStart_label = QLabel('Start Time')
        self.editVideoTimeStart_input = QTimeEdit()
        self.editVideoTimeStart_input.setDisplayFormat("mm:ss")
        self.editVideoTimeStart_input.setTime(QtCore.QTime(0, 0, 0))
        self.editVideoTimeStart_input.setEnabled(False)
        self.editVideoTimeStart_input.timeChanged.connect(self.fnChangeTime)
        self.editVideoTimeStart_input.setStyleSheet('background-color: rgb(255, 255, 255);')

        editVideoTimeEnd_label = QLabel('End Time')
        self.editVideoTimeEnd_input = QTimeEdit()
        self.editVideoTimeEnd_input.setDisplayFormat("mm:ss")
        self.editVideoTimeEnd_input.setTime(QtCore.QTime(0, 0, 0))
        self.editVideoTimeEnd_input.setEnabled(False)
        self.editVideoTimeEnd_input.timeChanged.connect(self.fnChangeTime)
        self.editVideoTimeEnd_input.setStyleSheet('background-color: rgb(255, 255, 255);')
        
        editVideoTime_lh.addWidget(editVideoTimeStart_label)
        editVideoTime_lh.addWidget(self.editVideoTimeStart_input)
        editVideoTime_lh.addWidget(editVideoTimeEnd_label)
        editVideoTime_lh.addWidget(self.editVideoTimeEnd_input)
        
        editVideoTime_lh.setStretch(0, 1)
        editVideoTime_lh.setStretch(1, 3)
        editVideoTime_lh.setStretch(2, 1)
        editVideoTime_lh.setStretch(3, 3)

        editVideoTimeFirst_lh.addWidget(self.editVideoNone_radio)
        editVideoTimeFirst_lh.addWidget(self.editVideoTime_radio)
        editVideoTimeFirst_lh.addSpacerItem(playSpacer)

        editTime_lv.addLayout(editVideoTimeFirst_lh)
        editTime_lv.addLayout(editVideoTime_lh)
        
        videoEditSecond_gb.setLayout(editTime_lv)

        # 프레임 추출 주기
        videoEditInterval_gb = QGroupBox('')
        videoEditInterval_lh = QHBoxLayout()
        videoEditInterval_label = QLabel('Extract Frame Interval Second')
        self.editVideoInterval_input = QtWidgets.QLineEdit()  # QDoubleSpinBox로 변경
        self.editVideoInterval_input.setReadOnly(True)
        self.editVideoInterval_input.setText(self.defaultFrameSecond)
        videoEditInterval_lh.addWidget(videoEditInterval_label)
        videoEditInterval_lh.addWidget(self.editVideoInterval_input)
        videoEditInterval_lh.setStretch(0, 2)
        videoEditInterval_lh.setStretch(1, 1)
        videoEditInterval_gb.setLayout(videoEditInterval_lh)

        # 2-2-2-1. 해상도
        videoEditThird_gb = QGroupBox('Crop Editor')
        editVideoWindowFeature_edit_lv = QVBoxLayout()
        
        editVideoWindowFeature_resolution_lh = QHBoxLayout()
        resolution_label = QLabel('Origin Resolution : ')
        self.resolution_x_label = QLabel('0')
        resolution_split_label = QLabel(':')
        self.resolution_y_label = QLabel('0')

        self.resolution_x_label.setText(str(int(self.selectedFileWidth)))
        self.resolution_y_label.setText(str(int(self.selectedFileHeight)))

        editVideoWindowFeature_resolution_lh.addWidget(resolution_label)
        editVideoWindowFeature_resolution_lh.addWidget(self.resolution_x_label)
        editVideoWindowFeature_resolution_lh.addWidget(resolution_split_label)
        editVideoWindowFeature_resolution_lh.addWidget(self.resolution_y_label)
        editVideoWindowFeature_resolution_lh.addStretch()

        editVideoWindowFeature_editResolution_lh = QHBoxLayout()

        editResolution_label = QLabel('Crop Resolution : ')
        self.editResolution_x_label = QLabel(self.resolution_x_label.text())
        editResolution_split_label = QLabel(':')
        self.editResolution_y_label = QLabel(self.resolution_y_label.text())

        editVideoWindowFeature_editResolution_lh.addWidget(editResolution_label)
        editVideoWindowFeature_editResolution_lh.addWidget(self.editResolution_x_label)
        editVideoWindowFeature_editResolution_lh.addWidget(editResolution_split_label)
        editVideoWindowFeature_editResolution_lh.addWidget(self.editResolution_y_label)
        editVideoWindowFeature_editResolution_lh.addStretch()

        # 2-2-2-2. Crop
        videoEditSecond_lh = QHBoxLayout()

        # Crop 영역 UI 창
        # 초기 영역값 ex: 0, 0, 2640, 1360
        self.init_crop_left = 0
        self.init_crop_top = 0
        self.init_crop_right = int(self.selectedFileWidth)
        self.init_crop_bottom = int(self.selectedFileHeight)
        
        # 변경 영역값
        self.crop_left = 0
        self.crop_top = 0
        self.crop_right = 0
        self.crop_bottom = 0

        left_lh = QHBoxLayout()
        leftLabel = QLabel('Left')
        self.leftInput = QtWidgets.QSpinBox() 
        self.leftInput.setRange(0, int(self.selectedFileWidth)) 
        self.leftInput.setSingleStep(10)
        self.leftInput.valueChanged.connect(self.update_crop)
        left_lh.addWidget(leftLabel)
        left_lh.addWidget(self.leftInput)

        top_lh = QHBoxLayout()
        topLabel = QLabel('Top')
        self.topInput = QtWidgets.QSpinBox() 
        self.topInput.setRange(0, int(self.selectedFileHeight)) 
        self.topInput.setSingleStep(10)
        self.topInput.valueChanged.connect(self.update_crop)
        top_lh.addWidget(topLabel)
        top_lh.addWidget(self.topInput)

        right_lh = QHBoxLayout()
        rigthLabel = QLabel('Right')
        self.rightInput = QtWidgets.QSpinBox() 
        self.rightInput.setRange(0, int(self.selectedFileWidth)) 
        self.rightInput.setSingleStep(10)
        self.rightInput.valueChanged.connect(self.update_crop)
        right_lh.addWidget(rigthLabel)
        right_lh.addWidget(self.rightInput)

        bottom_lh = QHBoxLayout()
        bottomLabel = QLabel('Bottom')
        self.bottomInput = QtWidgets.QSpinBox() 
        self.bottomInput.setRange(0, int(self.selectedFileHeight)) 
        self.bottomInput.setSingleStep(10)
        self.bottomInput.valueChanged.connect(self.update_crop)
        bottom_lh.addWidget(bottomLabel)
        bottom_lh.addWidget(self.bottomInput)

        videoEditSecond_lh.addLayout(left_lh)
        videoEditSecond_lh.addLayout(top_lh)
        videoEditSecond_lh.addLayout(right_lh)
        videoEditSecond_lh.addLayout(bottom_lh)

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)  # 수평선 설정
        divider.setFrameShadow(QFrame.Sunken)  # 선 스타일 (깊이감 있는 효과)

        editVideoWindowFeature_edit_lv.addLayout(editVideoWindowFeature_resolution_lh)
        editVideoWindowFeature_edit_lv.addLayout(editVideoWindowFeature_editResolution_lh)
        editVideoWindowFeature_edit_lv.addWidget(divider)
        editVideoWindowFeature_edit_lv.addLayout(videoEditSecond_lh)

        videoEditThird_gb.setLayout(editVideoWindowFeature_edit_lv)
       
        editArea_left_lv = QVBoxLayout()
        editArea_left_lv.addWidget(videoEditSecond_gb)
        editArea_left_lv.addWidget(videoEditInterval_gb)

        editArea_lh.addLayout(editArea_left_lv)
        editArea_lh.addWidget(videoEditThird_gb)
        
        # 레이아웃 배치
        editVideoWindowFeature_lv.addWidget(videoEditFirst_gb)
        editVideoWindowFeature_lv.addLayout(editArea_lh)

        editVideoWindowFeature_gb.setLayout(editVideoWindowFeature_lv)

        # 3. 확인, 취소 버튼
        editVideoWindowButton_lh = QHBoxLayout()
        previewButton = QPushButton('Preview')
        previewButton.clicked.connect(lambda: QtCore.QTimer.singleShot(200, self.fnPreviewBtn))
        confirmButton = QPushButton('Confirm')
        confirmButton.setDefault(True)
        confirmButton.clicked.connect(lambda: QtCore.QTimer.singleShot(200, self.fnConfirmBtn))
        cancelButton = QPushButton('Exit')
        cancelButton.clicked.connect(lambda: QtCore.QTimer.singleShot(200, self.fnExitBtn))
        buttonSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        editVideoWindowButton_lh.addWidget(previewButton)
        editVideoWindowButton_lh.addSpacerItem(buttonSpacer)
        editVideoWindowButton_lh.addWidget(confirmButton)
        editVideoWindowButton_lh.addWidget(cancelButton)

        # 4. 메인 레이아웃 
        editVideoWindowMain_lv.addWidget(self.editVideoWindowVideo_view)
        editVideoWindowMain_lv.addWidget(editVideoWindowFeature_gb)
        editVideoWindowMain_lv.addLayout(editVideoWindowButton_lh)

        self.setLayout(editVideoWindowMain_lv)
        self.update_frame(0)

    # 동영상 시간 지정 Radio 함수
    def fnCheckRadio(self):
        if self.editVideoTime_radio.isChecked():
            self.editVideoTimeStart_input.setEnabled(True)
            self.editVideoTimeEnd_input.setEnabled(True)
            self.editVideoTimeEnd_input.setFocus()
        else:
            self.editVideoTimeStart_input.setTime(QtCore.QTime(0, 0, 0))
            self.editVideoTimeEnd_input.setTime(QtCore.QTime(0, 0, 0))
            self.editVideoTimeStart_input.setEnabled(False)
            self.editVideoTimeEnd_input.setEnabled(False)

    # 초 -> mm:ss
    def convert_seconds_to_minutes(self, duration): 
        minutes = duration // 60 
        seconds = duration % 60 
        return f"{minutes}:{seconds:02d}"

    def update_time(self): 
        position = self.cap.get(cv2.CAP_PROP_POS_MSEC) / 1000 
        self.timeStart_label.setText(self.format_time(position)) 
        
    def format_time(self, seconds): 
        minutes = int(seconds // 60) 
        seconds = int(seconds % 60) 
        return f'{minutes}:{seconds:02d}'
    
    # Slider 업데이트 함수
    def update_frame(self, frame_idx):
        if frame_idx < self.start_frame:  # 최소 프레임 이하일 경우 보정
            frame_idx = self.start_frame
        elif frame_idx > self.end_frame:  # 최대 프레임 초과 시 보정
            frame_idx = self.end_frame

        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = self.cap.read()
        self.update_time()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            height, width, channel = frame.shape
            bytes_per_line = 3 * width
            qimage = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
            self.pixmap = QPixmap.fromImage(qimage)

            # QPainter로 Crop 영역 그리기
            self.draw_crop_rectangle()

            self.editVideoWindowVideo_scene.clear()
            self.editVideoWindowVideo_scene.addPixmap(self.pixmap)
        else:
            print("프레임을 불러올 수 없습니다.")
            self.timeStart_label.setText(self.endTime) 

    # Crop 영역을 그리는 함수
    def draw_crop_rectangle(self):
        # QPainter로 Crop 영역 그리기
        self.editVideoWindowVideo_painter = QPainter(self.pixmap)
        self.editVideoWindowVideo_painter.setPen(QPen(Qt.red, 7, Qt.SolidLine))
        
        # Crop 영역 좌표 조정
        self.editVideoWindowVideo_painter.drawRect(
            self.init_crop_left + self.crop_left, 
            self.init_crop_top + self.crop_top,
            self.init_crop_right - self.crop_left - self.crop_right,
            self.init_crop_bottom - self.crop_top - self.crop_bottom
        )
        self.editVideoWindowVideo_painter.end()

    # Crop 업데이트 함수
    def update_crop(self):
        self.current_frame = 0
        
        self.crop_left = self.leftInput.value()
        self.crop_top = self.topInput.value()
        self.crop_right = self.rightInput.value()
        self.crop_bottom = self.bottomInput.value()

        self.editResolution_x_label.setText(str(self.init_crop_right - (self.crop_left + self.crop_right)))
        self.editResolution_y_label.setText(str(self.init_crop_bottom - (self.crop_top + self.crop_bottom)))

        self.draw_crop_rectangle()  # 이 부분을 추가하여 크롭 영역을 다시 그림
        self.update_frame(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
    
    # Preview 버튼 함수
    def fnPreviewBtn(self):
        previewWindow = EditVideoPreviewWindow(
            self.path, 
            self.editVideoTimeStart_input.text(), self.editVideoTimeEnd_input.text(),
            self.endTime,
            self.crop_left, self.crop_top, self.crop_right, self.crop_bottom,
            float(self.editVideoInterval_input.text()),
            self
        )
        previewWindow.exec()

    # Confirm 함수
    def fnConfirmBtn(self):
        isCroped = self.leftInput.value() != 0 or self.topInput.value() != 0 or self.rightInput.value() != 0 or self.bottomInput.value() != 0
        isTimeChanged = self.editVideoTimeStart_input.time() != QtCore.QTime(0, 0, 0, 0) or self.editVideoTimeEnd_input.time() != QtCore.QTime(0, 0, 0, 0)
        isFrameSecondChanged = self.editVideoInterval_input.text() != self.defaultFrameSecond

        if isTimeChanged or isCroped or isFrameSecondChanged:
            if isTimeChanged:
                self.parent.editInfoTime_input.setText(
                    f'{self.editVideoTimeStart_input.time().toString("mm:ss")} ~ {self.editVideoTimeEnd_input.time().toString("mm:ss")}')
            if isCroped:
                self.parent.editInfoResolution_input.setText(
                    f'{self.editResolution_x_label.text()} : {self.editResolution_y_label.text()}'
                )
                self.parent.cropList = []
                self.parent.cropList.append(self.leftInput.value())
                self.parent.cropList.append(self.topInput.value())
                self.parent.cropList.append(self.rightInput.value())
                self.parent.cropList.append(self.bottomInput.value())
            if isFrameSecondChanged:
                self.parent.editInfoFrameSecond_input.setText(self.editVideoInterval_input.text())

            self.parent.editInfo_radio.setChecked(True)
        else:
            QMessageBox.information(self, 'No changes', 'Enter the changed value or press the ‘Exit’ button.')
            return
        
        self.accept()

    # Exit 함수
    def fnExitBtn(self):
        self.reject()

    # 시간 변경 validation 
    def fnChangeTime(self):
        timeLengthList = self.endTime.split(':')
        if self.editVideoTimeStart_input.time() >= QtCore.QTime(0, int(timeLengthList[0]), int(timeLengthList[1])):
            QMessageBox.information(self, 'Invalid Time', 'Start time must be less than the duration of the video')
            self.editVideoTimeStart_input.setTime(QtCore.QTime(0, 0, 0))
            return 

        if (self.editVideoTimeEnd_input.time() >= QtCore.QTime(0, int(timeLengthList[0]), int(timeLengthList[1]))):
            self.editVideoTimeEnd_input.setTime(QtCore.QTime(0, int(timeLengthList[0]), int(timeLengthList[1])))
            return 
        
        if self.editVideoTimeStart_input.time() > self.editVideoTimeEnd_input.time():
            QMessageBox.information(self, 'Invalid Time', 'Start time must be less than end time')
            self.editVideoTimeStart_input.setTime(QtCore.QTime(0, 0, 0))
            return
        
    # 영상 화면 리사이즈
    def showEvent(self, event):
        super().showEvent(event)
        self.editVideoWindowVideo_view.fitInView(self.editVideoWindowVideo_scene.sceneRect(), QtCore.Qt.KeepAspectRatio)
    def resizeEvent(self, event): 
        super().resizeEvent(event)
        self.editVideoWindowVideo_view.fitInView(self.editVideoWindowVideo_scene.sceneRect(), QtCore.Qt.KeepAspectRatio)

# 메인 GUI
class MyWindow(QMainWindow):
    processNo = -1
    processStatus = 'Waiting'

    def __init__(self):
        super().__init__()

        self.image_ori_x = 0.0
        self.image_ori_y = 0.0

        # 균열검출 쓰레드 인스턴스
        self.worker = Worker(self)
        self.worker.model_status_changed.connect(self.updateTableStatus)
        self.worker.status_bar_percent.connect(self.updateStatusPercent)
        self.worker.progressBar_label_status.connect(self.updateProgressLabel)

        # 크롭 영역 리스트
        self.cropList = []
        # 비디오 데이터 리스트
        self.video_data_model_list = []

        self.initializeUi()

        #추가
        self.apply_dark_mode_if_needed() #다크모드 일경우

        self.mainLayout()

        self.threadTimer = QtCore.QTimer(self)
        self.threadTimer.start(3000)
        self.threadTimer.timeout.connect(self.fnUpdateWorkerList)
            
    # GUI 윈도우 창 크기 및 타이틀 설정
    def initializeUi(self):
        self.setGeometry(600, 600, 1400, 700)
        self.setWindowTitle("FDTech Crack Detect v1.1")

        # 창을 화면 중앙에 배치
        frameGm = self.frameGeometry() 
        screen = QApplication.primaryScreen().availableGeometry().center() 
        frameGm.moveCenter(screen) 
        self.move(frameGm.topLeft())

        QtCore.QTimer.singleShot(200, self.showLoadingDialog)

    def apply_dark_mode_if_needed(self): 
        palette = self.palette()
        is_dark = False

        # 다크모드 감지 (Qt 6.5 이상에서 공식 지원, 그 이하 버전은 수동 감지 필요)
        if palette.color(QPalette.Window).value() < 128:
            is_dark = True

        if is_dark: #다크모드 일경우 색상변경
            self.setStyleSheet("""
                * {
                    color: #000000;
                }
                QLabel {
                    color: #000000;
                }
                QTimeEdit {
                    color: #000000;
                }
            """)
        else:
            self.setStyleSheet("")  # 기본(라이트) 모드 스타일 사용
    # 여기까지

    # 로딩창 오픈 함수
    def showLoadingDialog(self):
        loading_dialog = LoadingDialog(parent=self)
        loading_dialog.show()
        loading_dialog.center()

    # 메인 레이아웃 설정
    def mainLayout(self):
        main_widget = QWidget()
        main_widget.setStyleSheet('background-color: rgb(255, 255, 255);')
        self.setCentralWidget(main_widget)

        # 메인을 수평 레이아웃으로 2등분 (바디, 사이드바) 
        main_lh = QHBoxLayout()
        main_lh.setContentsMargins(10, 10, 10, 10)
        
        # 1. 메인 좌측 프레임 및 레이아웃
        main_left_f = QFrame()
        main_left_f.setStyleSheet('background-color: rgb(238, 238, 238);')
        main_left_lv = QVBoxLayout() 

        # 1-1. 상단 테이블 ------------------------------
        videoList_gb = QGroupBox('Video List')
        videoList_lv = QVBoxLayout() 

        videoList_header_lh = QHBoxLayout() 
        videoList_header_count = QLabel('Total Count : ')
        self.videoList_header_value = QLabel('0')
        videoList_header_spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        videoList_header_lh.addWidget(videoList_header_count)
        videoList_header_lh.addWidget(self.videoList_header_value)
        videoList_header_lh.addSpacerItem(videoList_header_spacer)
        
        self.videoList_table = QTableWidget()
        self.videoList_table.setEditTriggers(QAbstractItemView.NoEditTriggers)  # 셀 edit 금지
        self.videoList_table.setSelectionBehavior(QAbstractItemView.SelectRows)  # 로우 단위 선택

        self.videoList_table.setColumnCount(4)
        self.videoList_table.setHorizontalHeaderLabels(['File Path', 'File Name', 'Status', 'Setting'])
        self.videoList_table.setColumnHidden(0, True)

        self.videoList_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        videoList_lv.addLayout(videoList_header_lh)
        videoList_lv.addWidget(self.videoList_table)

        videoList_gb.setLayout(videoList_lv)
        
        # 1-2. 하단 프로그레스바 ------------------------
        progressBar_gb = QGroupBox('Progress Bar')
        
        progressBar_lv = QVBoxLayout()
        self.progressBar_label = QLabel('Waiting')
        self.progressBar_bar = QProgressBar()
        self.progressBar_bar.setRange(0, 1000)
        self.progressBar_bar.setValue(0)

        progressBar_lv.addWidget(self.progressBar_label)
        progressBar_lv.addWidget(self.progressBar_bar)
        progressBar_gb.setLayout(progressBar_lv)
        # ---------------------------------------------

        main_left_lv.addWidget(videoList_gb)
        main_left_lv.addWidget(progressBar_gb)

        main_left_lv.setStretch(0, 5)
        main_left_lv.setStretch(1, 1)

        main_left_f.setLayout(main_left_lv)


        # 2. 메인 우측 프레임 및 레이아웃
        main_right_f = QFrame()
        main_right_f.setStyleSheet('background-color: rgb(238, 238, 238);')
        
        main_right_lv = QVBoxLayout() 

        # 2-1. File Info-----------------------------------
        fileInfo_gb = QGroupBox('1. File Info')
        fileInfo_lv = QVBoxLayout()
        
        # 2-1-1. File Name
        fileName_label = QLabel('File Name')
        self.fileName_input = QLineEdit()
        self.fileName_input.setReadOnly(True)

        fileName_lh = QHBoxLayout()
        fileName_lh.addWidget(fileName_label)
        fileName_lh.addWidget(self.fileName_input)
        fileName_lh.setStretch(0, 1)
        fileName_lh.setStretch(1, 2)

        # 2-1-2. File Path
        filePath_label = QLabel('File Path')
        self.filePath_input = QLineEdit()
        self.filePath_input.setReadOnly(True)
        
        filePath_lh = QHBoxLayout()
        filePath_lh.addWidget(filePath_label)
        filePath_lh.addWidget(self.filePath_input)
        filePath_lh.setStretch(0, 1)
        filePath_lh.setStretch(1, 2)

        # 2-1-3. File Size
        fileSize_label = QLabel('File Size')
        self.fileSize_input = QLineEdit()
        self.fileSize_input.setReadOnly(True)
        
        fileSize_lh = QHBoxLayout()
        fileSize_lh.addWidget(fileSize_label)
        fileSize_lh.addWidget(self.fileSize_input)
        fileSize_lh.setStretch(0, 1)
        fileSize_lh.setStretch(1, 2)

        # 2-1-4. Resolution
        fileResolution_label = QLabel('Resolution')
        self.fileResolution_input = QLineEdit()
        self.fileResolution_input.setReadOnly(True)
        
        fileResolution_lh = QHBoxLayout()
        fileResolution_lh.addWidget(fileResolution_label)
        fileResolution_lh.addWidget(self.fileResolution_input)
        fileResolution_lh.setStretch(0, 1)
        fileResolution_lh.setStretch(1, 2)

        # 2-1-5. Time Length
        timeLength_label = QLabel('Time Length')
        self.timeLength_input = QLineEdit()
        self.timeLength_input.setReadOnly(True)
        
        timeLength_lh = QHBoxLayout()
        timeLength_lh.addWidget(timeLength_label)
        timeLength_lh.addWidget(self.timeLength_input)
        timeLength_lh.setStretch(0, 1)
        timeLength_lh.setStretch(1, 2)

        # 2-1-6. File Load Button
        fileLoad = QPushButton('File Load')
        fileLoad.clicked.connect(self.fnFileUpload)

        fileInfo_lv.addLayout(fileName_lh)
        fileInfo_lv.addLayout(filePath_lh)
        fileInfo_lv.addLayout(fileSize_lh)
        fileInfo_lv.addLayout(fileResolution_lh)
        fileInfo_lv.addLayout(timeLength_lh)
        fileInfo_lv.addWidget(fileLoad)

        fileInfo_gb.setLayout(fileInfo_lv)

        # 2-2. Edit Info-----------------------------------
        editInfo_gb = QGroupBox('2. Video Edit Info')
        editInfo_lv = QVBoxLayout()

        editInfo_first_lh = QHBoxLayout()
        editInfo_btn = QPushButton('Open Video Edit Tool')
        editInfo_btn.clicked.connect(self.fnOpenNewWindow)
        self.editInfo_radio = QRadioButton('Edited')
        self.editInfo_radio.setChecked(False)
        self.editInfo_radio.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        
        editInfo_first_lh.addWidget(editInfo_btn)        
        editInfo_first_lh.addWidget(self.editInfo_radio)      
        editInfo_first_lh.setStretch(0, 2)
        editInfo_first_lh.setStretch(1, 1)

        editInfo_second_lh = QHBoxLayout()
        editInfoTime_label = QLabel('Edit Time')
        self.editInfoTime_input = QLineEdit()
        self.editInfoTime_input.setText('None')
        self.editInfoTime_input.setReadOnly(True)

        editInfo_second_lh.addWidget(editInfoTime_label)
        editInfo_second_lh.addWidget(self.editInfoTime_input)
        editInfo_second_lh.setStretch(0, 1)
        editInfo_second_lh.setStretch(1, 2)
        
        editInfo_third_lh = QHBoxLayout()
        editInfo_third_label = QLabel('Edit Resolution')
        self.editInfoResolution_input = QLineEdit()
        self.editInfoResolution_input.setText('None')
        self.editInfoResolution_input.setReadOnly(True)

        editInfo_third_lh.addWidget(editInfo_third_label)
        editInfo_third_lh.addWidget(self.editInfoResolution_input)
        editInfo_third_lh.setStretch(0, 1)
        editInfo_third_lh.setStretch(1, 2)

        editInfoFrameSecond_lh = QHBoxLayout()
        editInfoFrameSecond_label = QLabel('Frame Second')
        self.editInfoFrameSecond_input = QLineEdit()
        self.editInfoFrameSecond_input.setText('Default')
        self.editInfoFrameSecond_input.setReadOnly(True)

        editInfoFrameSecond_lh.addWidget(editInfoFrameSecond_label)
        editInfoFrameSecond_lh.addWidget(self.editInfoFrameSecond_input)
        editInfoFrameSecond_lh.setStretch(0, 1)
        editInfoFrameSecond_lh.setStretch(1, 2)

        editInfo_lv.addLayout(editInfo_first_lh)
        editInfo_lv.addLayout(editInfo_second_lh)
        editInfo_lv.addLayout(editInfo_third_lh)
        editInfo_lv.addLayout(editInfoFrameSecond_lh)

        editInfo_gb.setLayout(editInfo_lv)

        # 2-3. Record Info --------------------------------
        recordInfo_gb = QGroupBox('3. Record Info')
        recordInfo_lv = QVBoxLayout()

        # 2-3-1. Bridge Name 
        bridgeName_label = QLabel('Bridge Name')
        self.bridgeName_input = QLineEdit()
        self.bridgeName_input.setStyleSheet('background-color: rgb(255, 255, 255);')
        
        bridgeName_lh = QHBoxLayout()
        bridgeName_lh.addWidget(bridgeName_label)
        bridgeName_lh.addWidget(self.bridgeName_input)
        bridgeName_lh.setStretch(0, 1)
        bridgeName_lh.setStretch(1, 2)
        
        # 2-3-2. Pier Name
        pierName_label = QLabel('Pier Name')
        self.pierName_input = QLineEdit()
        self.pierName_input.setStyleSheet('background-color: rgb(255, 255, 255);')

        pierName_lh = QHBoxLayout()
        pierName_lh.addWidget(pierName_label)
        pierName_lh.addWidget(self.pierName_input)
        pierName_lh.setStretch(0, 1)
        pierName_lh.setStretch(1, 2)

        # 2-3-3. Pier Side No
        pierSideNo_label = QLabel('Pier Side No')

        self.pierSideNo_input = QLineEdit()
        self.pierSideNo_input.setStyleSheet('background-color: rgb(255, 255, 255);')

        pierSideNo_lh = QHBoxLayout()
        pierSideNo_lh.addWidget(pierSideNo_label)
        pierSideNo_lh.addWidget(self.pierSideNo_input)
        pierSideNo_lh.setStretch(0, 1)
        pierSideNo_lh.setStretch(1, 2)

        # 2-3-4. Camera No
        # 숫자 밸리데이션
        cameraNo_label = QLabel('Camera No')
        self.cameraNo_input = QtWidgets.QSpinBox()
        self.cameraNo_input.setMinimum(1)
        self.cameraNo_input.setStyleSheet('background-color: rgb(255, 255, 255);')
        
        cameraNo_lh = QHBoxLayout()
        cameraNo_lh.addWidget(cameraNo_label)
        cameraNo_lh.addWidget(self.cameraNo_input)
        cameraNo_lh.setStretch(0, 1)
        cameraNo_lh.setStretch(1, 2)

        # 2-3-5. Target Length
        targetLength_label = QLabel('Target Length')
        self.targetLength_input = QtWidgets.QSpinBox()
        self.targetLength_input.setMinimum(1)
        self.targetLength_input.setMaximum(1000)
        self.targetLength_input.setValue(70)
        self.targetLength_input.setStyleSheet('background-color: rgb(255, 255, 255);')

        targetLength_lh = QHBoxLayout()
        targetLength_lh.addWidget(targetLength_label)
        targetLength_lh.addWidget(self.targetLength_input)
        targetLength_lh.setStretch(0, 1)
        targetLength_lh.setStretch(1, 2)

        # 2-3-7. Video Upload Button
        videoUpload = QPushButton('Upload media && Start crack detection')
        videoUpload.clicked.connect(self.fnVideoUpload)

        recordInfo_lv.addLayout(bridgeName_lh)
        recordInfo_lv.addLayout(pierName_lh)
        recordInfo_lv.addLayout(pierSideNo_lh)
        recordInfo_lv.addLayout(cameraNo_lh)
        recordInfo_lv.addLayout(targetLength_lh)
        recordInfo_lv.addSpacing(10)
        recordInfo_lv.addWidget(videoUpload)

        recordInfo_gb.setLayout(recordInfo_lv)

        # 2-4. Software Info -------------------------------
        softwareInfo_gb = QGroupBox('Software Info')
        softWareInfo_lv = QVBoxLayout()

        # 2-4-1. Version 
        version_label = QLabel('Version')
        version_input = QLineEdit('1.1')
        version_input.setReadOnly(True)

        version_lh = QHBoxLayout()
        version_lh.addWidget(version_label)
        version_lh.addWidget(version_input)
        version_lh.setStretch(0, 1)
        version_lh.setStretch(1, 2)

        # 2-4-2. Last Update 
        lastUpdate_label = QLabel('Last Update')
        lastUpdate_input = QLineEdit('2025.04.04')
        lastUpdate_input.setReadOnly(True)

        lastUpdate_lh = QHBoxLayout()
        lastUpdate_lh.addWidget(lastUpdate_label)
        lastUpdate_lh.addWidget(lastUpdate_input)
        lastUpdate_lh.setStretch(0, 1)
        lastUpdate_lh.setStretch(1, 2)

        # 2-4-3. Company
        company_label = QLabel('Company')
        company_input = QLineEdit('FDTech, South Korea')
        company_input.setReadOnly(True)

        company_lh = QHBoxLayout()
        company_lh.addWidget(company_label)
        company_lh.addWidget(company_input)
        company_lh.setStretch(0, 1)
        company_lh.setStretch(1, 2)
        
        softWareInfo_lv.addLayout(version_lh)
        softWareInfo_lv.addLayout(lastUpdate_lh)
        softWareInfo_lv.addLayout(company_lh)
        
        softwareInfo_gb.setLayout(softWareInfo_lv)

        # 우측 사이드바 그룹박스 추가
        main_right_lv.addWidget(fileInfo_gb) 
        main_right_lv.addWidget(editInfo_gb) 
        main_right_lv.addWidget(recordInfo_gb) 
        main_right_lv.addWidget(softwareInfo_gb)

        # 우측 사이드바 그룹박스 비율 설정
        main_right_lv.setStretch(0, 2)
        main_right_lv.setStretch(1, 4)
        main_right_lv.setStretch(2, 1)
        
        main_right_f.setLayout(main_right_lv)

        main_lh.addWidget(main_left_f)
        main_lh.addWidget(main_right_f)
        
        # 프레임의 비율 설정 (3:1) 
        main_lh.setStretch(0, 3) 
        main_lh.setStretch(1, 1)

        main_widget.setLayout(main_lh)
    
    # 파일 업로드 함수
    def fnFileUpload(self):        
        self.image_ori_x = 0.0
        self.image_ori_y = 0.0

        fname = QFileDialog.getOpenFileName(self, '', '', 'Video and Image Files (*.mp4 *.png)')
        
        # 이미지일 경우 처리
        if fname[0][-3:].lower() == 'png':
            aa = self.show_resolution_input_dialog()
            self.image_ori_x = aa.split(" ")[0].split("x")[0]
            self.image_ori_y = aa.split(" ")[0].split("x")[1]

        # 파일 용량 정리 함수
        def human_readable_size(size, decimal_places=2):
            for unit in ['bytes', 'KB', 'MB', 'GB', 'TB']:
                if size < 1024:
                    break
                size /= 1024
            return f"{size:.{decimal_places}f} {unit}"
        
        if fname[0]:
            # 동영상 파일 열기 
            video = cv2.VideoCapture(fname[0]) 
            frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT)) 
            fps = video.get(cv2.CAP_PROP_FPS) 

            # 동영상 길이 계산 
            if fname[0][-3:].lower() == 'mp4':
                duration = int(frame_count / fps)
                self.timeLength_input.setText(self.convert_seconds_to_minutes(duration))
            else:
                self.timeLength_input.setText('None')

            # 해상도
            self.selectedFilePath = fname[0]
            self.selectedFileWidth = video.get(cv2.CAP_PROP_FRAME_WIDTH)
            self.selectedFileHeight = video.get(cv2.CAP_PROP_FRAME_HEIGHT)
            self.fileResolution_input.setText(str(int(self.selectedFileWidth)) + ' : ' + str(int(self.selectedFileHeight)))

            dir_name, file_name = os.path.split(fname[0])
            file_size = os.path.getsize(fname[0])

            self.fileName_input.setText(file_name)
            self.filePath_input.setText(dir_name)
            self.fileSize_input.setText(human_readable_size(file_size))

    # 비디오 업로드 함수
    def fnVideoUpload(self):
        # 파일 validation check
        print(self.cropList)
        
        if(self.fileName_input.text() == ''):
            QMessageBox.information(self, 'Information', 'Need to load a file')
            return
        
        # 영상정보 validation check
        if( self.bridgeName_input.text() == ''
            or self.pierName_input.text() == '' 
            or self.pierSideNo_input.text() == '' 
            or self.cameraNo_input.text() == '' 
            or self.targetLength_input.text() == '' ):
            QMessageBox.information(self, 'Information', 'Enter information in Record info')
            return

        # 테이블 데이터 추가 이후 사이드바 정보 초기화
        if self.fnAddTableRow():
            self.cropList = []

            self.fileName_input.setText('')
            self.filePath_input.setText('')
            self.fileSize_input.setText('')
            self.fileResolution_input.setText('')
            self.timeLength_input.setText('')

            self.editInfo_radio.setChecked(False)
            self.editInfoTime_input.setText('None')
            self.editInfoResolution_input.setText('None')
            self.editInfoFrameSecond_input.setText('Default')

    # 테이블 데이터 추가
    def fnAddTableRow(self):
        if(self.fnCheckRowDuplicate() == False): return

        filePath = self.filePath_input.text()
        fileName = self.fileName_input.text()
        videoInfo = ", ".join([ self.bridgeName_input.text(), self.pierName_input.text(), self.pierSideNo_input.text(), self.cameraNo_input.text(), self.targetLength_input.text() ])
        editInfo = ", ".join([ self.editInfoTime_input.text(), self.editInfoResolution_input.text(), self.editInfoFrameSecond_input.text() ])
        
        self.video_data_model = VideoDataModel(filePath, fileName, videoInfo, editInfo, self.cropList)
        self.video_data_model_list.append(self.video_data_model)

        currentCount = len(self.video_data_model_list) 
        self.videoList_table.setRowCount(currentCount) 
        self.videoList_header_value.setText(str(currentCount))

        table_c_view = QPushButton('View')
        table_c_view.clicked.connect(lambda checked, r=self.video_data_model: self.show_modal(r))

        self.videoList_table.setItem(currentCount - 1, 0, self.video_data_model.filePath)
        self.videoList_table.setItem(currentCount - 1, 1, self.video_data_model.fileName)
        self.videoList_table.setItem(currentCount - 1, 2, self.video_data_model.status)
        self.videoList_table.setCellWidget(currentCount - 1, 3, table_c_view)

        self.video_data_model.filePath.setTextAlignment(QtCore.Qt.AlignCenter)
        self.video_data_model.fileName.setTextAlignment(QtCore.Qt.AlignCenter)
        self.video_data_model.videoInfo.setTextAlignment(QtCore.Qt.AlignCenter)
        self.video_data_model.editInfo.setTextAlignment(QtCore.Qt.AlignCenter)
        self.video_data_model.status.setTextAlignment(QtCore.Qt.AlignCenter)

        return True
    
    # 테이블 데이터 중복여부 확인
    def fnCheckRowDuplicate(self):
        row_count = len(self.video_data_model_list)
        for row in range(row_count): 
            item = self.video_data_model_list[row].fileName

            if item.text() == self.fileName_input.text(): 
                QMessageBox.information(self, 'Information', 'Cannot upload duplicate file')
                return False

    # 워커 쓰레드에서 동작될 리스트 주기적으로 넘기기
    def fnUpdateWorkerList(self):
        if not self.video_data_model_list: return

        # 1. 리스트 업데이트
        self.worker.updateThreadList(self.video_data_model_list)

        # 2. 테이블 칼럼 자동 조절
        self.fnAutoTableColumnWidth()

        if not self.worker.isRunning():
            self.worker.start()           

    @QtCore.Slot(int, str)
    def updateTableStatus(self, no, new_status):
        for row, data in enumerate(self.video_data_model_list):
            if data.no == no:
                setattr(data, 'status', QTableWidgetItem(new_status))
                data.status.setText(new_status)
                data.status.setTextAlignment(QtCore.Qt.AlignCenter)
                self.videoList_table.setItem(row, 2, data.status)
                break

    @QtCore.Slot(float)
    def updateStatusPercent(self, percent):
        transPercent = int(percent * 10) 

        if percent == 0: 
            self.progressBar_bar.setValue(0)
        else:
            currValue = self.progressBar_bar.value()
            newValue = currValue + transPercent

            if(newValue >= 1000): newValue = 1000
            self.progressBar_bar.setValue(newValue)

            if newValue == 1000:
                self.progressBar_bar.setValue(0)

    @QtCore.Slot(int, str)
    def updateProgressLabel(self, no, text):
        self.progressBar_bar.valueChanged.connect(lambda value: self.updateLabel(no, text, value / 10))

    def updateLabel(self, no, text, value):
        if(value == 100):
            self.progressBar_label.setText(f' [ No: {no} ] Completed')
        elif(value == 0):
            self.progressBar_label.setText(f'Waiting')
        else:
            self.progressBar_label.setText(f' [ No: {no} ] {text} ({value}%)')


    # 테이블 칼럼 Width 사이즈 조절
    def fnAutoTableColumnWidth(self):
        header = self.videoList_table.horizontalHeader()
    
        # 첫 번째 칼럼 숨기기
        self.videoList_table.setColumnHidden(0, True)

        # 비율 설정
        total_stretch_factor = 3 + 2 + 1  # 총 비율 합
        column_ratios = [3, 2, 1]  # 3:1:1:1 비율

        # 칼럼 비율에 맞게 크기 조정
        for i in range(1, len(column_ratios) + 1):  # 첫 번째 칼럼은 숨겼으므로 1부터 시작
            header.setSectionResizeMode(i, QHeaderView.Interactive)
            header.resizeSection(i, int(header.width() * (column_ratios[i - 1] / total_stretch_factor)))
    
    # Detail View 
    def show_modal(self, row):
        videoInfoList = row.videoInfo.text().split(', ')
        editInfoList = row.editInfo.text().split(', ')

        message = (
            f"<b>{row.fileName.text()}</b><br><br>"
            f"<b>Bridge Name:</b> {videoInfoList[0]}<br>"
            f"<b>Pier Name:</b> {videoInfoList[1]}<br>"
            f"<b>Pier Side No:</b> {videoInfoList[2]}<br>"
            f"<b>Camera No:</b> {videoInfoList[3]}<br>"
            f"<b>Target Length:</b> {videoInfoList[4]}<br><br>"
            f"<b>Edit Time:</b> {editInfoList[0]}<br>"
            f"<b>Edit Resolution:</b> {editInfoList[1]}<br>"
        )
        msgBox = QMessageBox()
        msgBox.setWindowTitle("Detail View")
        msgBox.setText(message)
        msgBox.setStandardButtons(QMessageBox.Close)
        msgBox.exec()

    # 사이드바 Edit 창 열기
    def fnOpenNewWindow(self):
        if self.fileName_input.text()[-3:].lower() == 'png':
            QMessageBox.information(self, 'Unavailable', 'Image file cannot be edited')
            return
            
        if self.fileName_input.text() != '':
            if(self.editInfo_radio.isChecked()):
                msgBox = QMessageBox()
                msgBox.setWindowTitle('Already Edited')
                msgBox.setInformativeText('Do you agree that the existing changes will be lost?')
                msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                
                result = msgBox.exec()
                if result == QMessageBox.Yes:
                    # 수정값 초기화, edited 버튼 false 처리
                    self.editInfoTime_input.setText('None')
                    self.editInfoResolution_input.setText('None')
                    self.editInfoFrameSecond_input.setText('Default')

                    self.editInfo_radio.setChecked(False)
                elif result == QMessageBox.No:
                    return


            self.editWindow = EditVideoWindow(self.selectedFilePath, self)
            result = self.editWindow.exec()
            if result == QDialog.Accepted:
                print('acepted')
                self.editWindow.close()

            else:
                print('rejected')
                self.editWindow.close()

        else:
            QMessageBox.information(self, 'Information', 'Need to load a file')
            return
    
    # 이미지 파일 업로드 시 원본 사이즈 입력 모달창
    def show_resolution_input_dialog(parent=None):
        # QDialog 생성
        dialog = QDialog(parent)
        dialog.setWindowTitle("Resolution Input Dialog")  # 대화상자 제목 설정
        
        # 창 크기 설정 (가로와 세로 크기 설정)
        dialog.resize(300, 100)  # 너비 400, 높이 200으로 크기 설정

        # 창 닫기 버튼 비활성화 (X 버튼 제거)
        dialog.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)  # 닫기 버튼 제거
        dialog.setModal(True)  # 모달 설정, 다른 UI 동작 제한

        # 레이아웃 설정
        layout = QVBoxLayout(dialog)
        label = QLabel("Please select a origin resolution:", dialog)  # 안내 메시지는 영어로 유지
        layout.addWidget(label)

        # 드롭다운 메뉴(QComboBox) 생성 및 해상도 옵션 추가
        resolution_dropdown = QComboBox(dialog)
        resolution_dropdown.addItems([
            "3840x2160 (4K)",  # 4K UHD 해상도
            "2560x1440 (QHD)",  # QHD 해상도
            "1920x1080 (FHD)",  # FHD 해상도
            "1280x720 (HD)",    # HD 해상도
            "1024x768",         # XGA 해상도
            "800x600"           # SVGA 해상도
        ])  # 선택 가능한 해상도 항목
        layout.addWidget(resolution_dropdown)

        # 확인 버튼 생성
        confirm_button = QPushButton("Confirm", dialog)
        layout.addWidget(confirm_button)

        # 확인 버튼 클릭 시 동작 정의
        def on_confirm():
            dialog.accept()  # 대화상자 닫기

        # 확인 버튼에 클릭 이벤트 연결
        confirm_button.clicked.connect(on_confirm)

        # 대화상자 실행
        if dialog.exec() == QDialog.Accepted:  # 확인 버튼으로 닫힌 경우
            return resolution_dropdown.currentText()  # 선택된 해상도를 반환
        
        
    # 기능 함수 ----------------------------------------------------------------
    # 초 -> mm:ss
    def convert_seconds_to_minutes(self, duration): 
        minutes = duration // 60 
        seconds = duration % 60 
        return f"{minutes}:{seconds:02d}"
    
# Worker Thread Class ---------------------------------------------------------
class Worker(QtCore.QThread):
    model_status_changed = QtCore.Signal(int, str)
    status_bar_percent = QtCore.Signal(float)
    progressBar_label_status = QtCore.Signal(int, str)

    def __init__(self, parent):
        super().__init__()
        self.threadNo = -1
        self.threadList = []
        self.completedList = []
        self.threadStatus: Literal['Waiting', 'Running'] = 'Waiting'
        self.detailStatus: Literal['Waiting', 'Image Stitching', 'Pre Processing', 'Ai Crack Detecting', 'Post Processing', 'Generating Report', 'Completed', 'Error'] = 'Waiting'
        self._running = True
        self.parent = parent

    # 쓰레드가 실행할 함수
    def run(self):
        while self._running:
            if not self.threadList:
                self.msleep(3000)
                continue

            for data in [data for data in self.threadList if data.status.text() == 'Waiting']:
                # 상태변경 코드
                if self.threadNo == -1:
                    self.threadNo = data.no
                    break
                
                # 현재 진행 순번 일치 시 프로세스 진행
                if self.threadNo == data.no and self.threadStatus == 'Waiting':
                    debugpy.debug_this_thread()
                    self.fnUpdateThreadStatus('Running')

                    # 1. 영상 블렌딩 (blending)
                    if data.fileName.text()[-3:].lower() == 'png':
                        blending_result, ori_res_x, ori_res_y = self.fnBlendingService(data, float(self.parent.image_ori_x), float(self.parent.image_ori_y))
                    else:
                        blending_result, ori_res_x, ori_res_y = self.fnBlendingService(data)

                    # 2. 블렌딩 이미지 전처리 (preprocessing)
                    img_cut, modi_img, ori_h_size, ori_w_size = self.fnPreProcessing(blending_result)
                    # 3. AI 모델 추론 (ai)
                    pred_total = self.fnCrackDetectAiModel(img_cut, self.fnUpdatePercentStatus)
                    # 4. 추론 결과로 블렌딩 이미지 후처리 (postprocessing)
                    result_json, result_img, l_overlay_image, w_overlay_image = self.fnPostProcessing(blending_result, modi_img, ori_h_size, ori_w_size, pred_total, data, ori_res_x, ori_res_y, self.fnUpdatePercentStatus)
                    # 5. (json, img) 결과 저장 
                    self.fnSaveResults(data.fileName.text(), result_json, result_img, blending_result, program_directory, data, l_overlay_image, w_overlay_image)

                    # 상태 업데이트
                    self.fnUpdateNoStatus(self.threadNo, 'Completed')

                    # 다음 순번으로 이동
                    self.fnMoveToNextProcess()
                    self.fnUpdateThreadStatus('Waiting')
                    break

    # 1. 이미지 스티칭 -------------------------------------------------------------------
    def fnBlendingService(self, data, image_ori_x = 0, image_ori_y = 0):
        path = os.path.join(data.filePath.text(), data.fileName.text())
        
        frame_second = 4.0
        if data.editInfo.text().split(", ")[2] == 'Default':
            frame_second = frame_second
        else:
            frame_second = float(data.editInfo.text().split(", ")[2])

        # 이미지 파일 업로드 시 처리
        if data.fileName.text()[-3:].lower() == 'png':
            self.fnUpdatePercentStatus(5.0)
            image = cv2.imread(path)

            return image, image_ori_x, image_ori_y
        
        # 동영상 파일 업로드 시 처리
        else:
            self.fnUpdateNoStatus(self.threadNo, 'Image Stitching')
            self.fnUpdateProgressBarStatus(self.threadNo, 'Image Stitching')

            if(data.editInfo.text().split(', ')[0] != 'None'):
                start = self.convert_minutes_to_seconds(int(data.editInfo.text().split(', ')[0].split(' ~ ')[0].split(":")[0]), int(data.editInfo.text().split(', ')[0].split(' ~ ')[0].split(":")[1]))
                end = self.convert_minutes_to_seconds(int(data.editInfo.text().split(', ')[0].split(' ~ ')[1].split(":")[0]), int(data.editInfo.text().split(', ')[0].split(' ~ ')[1].split(":")[1]))
            else:
                start = 0
                end = 0

            if(data.cropList != []):
                blendingService = BlendingService(path, start, end, data.cropList[0], data.cropList[1], data.cropList[2], data.cropList[3], capture_period=frame_second)        
            else:
                blendingService = BlendingService(path, start, end, capture_period=frame_second)        
            
            self.fnUpdatePercentStatus(5.0)
            
            return blendingService.run_blend_image_save()
    
    # 2. 전처리
    def fnPreProcessing(self, panoramic_img):
        self.fnUpdateNoStatus(self.threadNo, 'Pre Processing')
        self.fnUpdateProgressBarStatus(self.threadNo, 'Pre Processing')

        preprocessing_service = PreProcessingService(256, 256)
        img_cut, modi_img, ori_h_size, ori_w_size = preprocessing_service.image_preprocessing(panoramic_img)
        
        self.fnUpdatePercentStatus(5.0)
        
        return img_cut, modi_img, ori_h_size, ori_w_size

    # 3. AI 균열검출
    def fnCrackDetectAiModel(self, cut_img_list, fnUpdatePercent):
        # debugpy.debug_this_thread()

        self.fnUpdateNoStatus(self.threadNo, 'AI Crack Detecting')
        self.fnUpdateProgressBarStatus(self.threadNo, 'AI Crack Detecting')

        crack_ai_request_sender = CrackAIRequestSender(fnUpdatePercent)
        pred_total = crack_ai_request_sender.send_image(cut_img_list, batch_size=16)
        
        return pred_total
    
        # 4. 후처리
    def fnPostProcessing(self, img, modi_img, ori_h_size, ori_w_size, pred_total, data, ori_res_x, ori_res_y, fnUpdatePercentStatus):
        # debugpy.debug_this_thread()
        targetLength = data.videoInfo.text().split(', ')[-1]

        self.fnUpdateNoStatus(self.threadNo, 'Post Processing')
        self.fnUpdateProgressBarStatus(self.threadNo, 'Post Processing')

        post_processing = PostProcessingService(img, modi_img, ori_h_size, ori_w_size, pred_total, targetLength, ori_res_x, ori_res_y, fnUpdatePercentStatus)        
        result_json, result_img, l_overlay_image, w_overlay_image, max_width_coords = post_processing.run()

        self.fnUpdatePercentStatus(5.0)
        


        # max_width_coords를 사용하여 이미지에 시각화
        for coords in max_width_coords:
            x1, y1, x2, y2 = coords
            # 픽셀 경계 그리기
            cv2.rectangle(result_img, (x1, y1), (x2, y2), (0, 255, 0), 1)  # 녹색 사각형으로 표시

        # 시각화된 이미지를 원본 이미지와 합성
        final_image = cv2.addWeighted(img, 0.7, result_img, 0.3, 0)

        # 이미지 파일 경로 생성
        image_path = os.path.join('/home/park/fdtech/FDCrackDetectGUI/Result', 'result1.png')

        # 이미지 저장
        cv2.imwrite(image_path, final_image)

        return result_json, final_image, l_overlay_image, w_overlay_image

    
    # 5. 결과 이미지 처리 및 저장
    def fnSaveResults(self, id, result_json, result_img, blending_result_img, program_directory, data, l_overlay_image, w_overlay_image):
        try:
            videoInfo = data.videoInfo.text().split(',')

            self.fnUpdateNoStatus(self.threadNo, 'Generating Report')
            self.fnUpdateProgressBarStatus(self.threadNo, 'Generating Report')

            # 현재 날짜와 시간 가져오기
            local_time = time.localtime()
            formatted_time = time.strftime("%y%m%d_%H%M%S", local_time)
            # now = datetime.datetime.now()
            # timestamp = now.strftime("%y%m%d_%H%M%S")

            # Result 폴더 생성
            result_dir = os.path.join(program_directory, 'Result')
            os.makedirs(result_dir, exist_ok=True)
            
            # 결과 디렉토리 생성
            name = id.split(".")[0]
            name_encoded = name.encode('utf-8').decode('utf-8')
            result_subdir = os.path.join(result_dir, f"{formatted_time}_{name_encoded}")
            os.makedirs(result_subdir, exist_ok=True)

            # 블렌딩 이미지 파일 저장
            # img_path1 = os.path.join(result_subdir, f'{name}_blending_image.png')
            # ext = os.path.splitext(img_path1)[1]
            # result, n = cv2.imencode(ext, blending_result_img, None)
            # if result:
            #     with open(img_path1, mode='w+b') as f:
            #         n.tofile(f)
            
            # JSON 파일 저장
            json_path = os.path.join(result_subdir, f'{name}_result.json')
            with open(json_path, 'w') as json_file:
                json.dump(result_json, json_file, indent=4)

            # 이미지 파일 저장
            img_path2 = os.path.join(result_subdir, f'{name}_result.png')
            ext = os.path.splitext(img_path2)[1]
            result, n = cv2.imencode(ext, result_img, None)
            if result:
                with open(img_path2, mode='w+b') as f:
                    n.tofile(f)

            # 길이 이미지 파일 저장
            img_path3 = os.path.join(result_subdir, f'{name}_result_length.png')
            ext = os.path.splitext(img_path3)[1]
            result, n = cv2.imencode(ext, l_overlay_image, None)
            if result:
                with open(img_path3, mode='w+b') as f:
                    n.tofile(f)

            # 너비 이미지 파일 저장
            img_path4 = os.path.join(result_subdir, f'{name}_result_width.png')
            ext = os.path.splitext(img_path4)[1]
            result, n = cv2.imencode(ext, w_overlay_image, None)
            if result:
                with open(img_path4, mode='w+b') as f:
                    n.tofile(f)

            # 보고서 생성
            aa = report(
                {
                    'bridgeName' : videoInfo[0],
                    'pierName' : videoInfo[1],
                    'pierSideNo' : videoInfo[2],
                    'cameraNo' : videoInfo[3],
                }, 
                img_path2,
                json_path,
                result_subdir
            )
            aa.run()

            self.fnUpdatePercentStatus(100.0)
            self.fnUpdateProgressBarStatus(self.threadNo, 'Completed')

        except Exception as e:
            self.fnUpdateProgressBarStatus(self.threadNo, 'Error')

            trace_info = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
            logger.error(f"SaveResults Error: {e}")
            logger.error(f"trace Info:\n{trace_info}")

    # ---------------------------------------------------------------------------------

    # 부모의 리스트를 받아 업데이트
    def updateThreadList(self, dataList):
        self.threadList = dataList

    # 워커 스레드 중지
    def stop(self):
        self._running = False

    # 다음 순번으로 이동
    def fnMoveToNextProcess(self):
        next_process_found = False

        
        for data in self.threadList:
            if data.no > self.threadNo and data.status.text() == 'Waiting':
                self.threadNo = data.no
                next_process_found = True
                break
        
        if not next_process_found:
            self.threadNo = -1

    # 스레드 상태 업데이트 (waiting, running)
    def fnUpdateThreadStatus(self, status):
        self.threadStatus = status
        print('현재상태: NO = ' + str(self.threadNo) + ' STATUS = ' + str(self.threadStatus))

    # 번호와 일치하는 항목의 데이터, 테이블 상태 업데이트 
    def fnUpdateNoStatus(self, no, new_status):
        self.model_status_changed.emit(no, new_status)

    # 진행상태 업데이트 
    def fnUpdatePercentStatus(self, percent):
        self.status_bar_percent.emit(percent)

    # 프로그레스바 라벨 업데이트
    def fnUpdateProgressBarStatus(self, no, currStatus):
        self.progressBar_label_status.emit(no, currStatus)

    

    # 기능 함수 ----------------------------------------------------------------
    # 초 -> mm:ss
    def convert_seconds_to_minutes(self, duration): 
        minutes = duration // 60 
        seconds = duration % 60 
        return f"{minutes}:{seconds:02d}"

    # mm:ss -> 초
    def convert_minutes_to_seconds(self, minute, second): 
        minutes = minute * 60 
        second += minutes 
        return second


# 메인 이벤트 루프 실행창
if __name__ == '__main__':
    multiprocessing.freeze_support()

    app = QApplication(sys.argv)

    # UI 윈도우창에 표시
    if not hasattr(app, 'window'):
        app.window = MyWindow()
        app.window.show()

    # 이벤트 루프 실행
    sys.exit(app.exec())

    