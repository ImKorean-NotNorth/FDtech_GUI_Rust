from .utils import rotate_270
import numpy as np
import cv2
import imutils


class StitchingService():
    def __init__(self, crack_detect_id:str):
        super().__init__()
        ## DB 에서 crack_detect_id 기준 url 불러오기
        crack_detect_id_video_url = crack_detect_id
        self.bridge_type = 0 # db 에서 교각 타입 조회 => 사각교각, 원형교갹
        ## 스트리밍 Read를 위한 서명된 video url 추출
        self.video_url = self.get_file_url(object_name=crack_detect_id_video_url,expire_time=7200)
    
    def cut_images(self):
        cap = cv2.VideoCapture(self.video_url)
        cnt = 0
        stich_li = []
        while(cap.isOpened()):
            ret,frame = cap.read()
            if cnt==0:
                if self.bridge_type == "사각교각": #사각교각
                    target = rotate_270(frame)[ : , 350:2000]              
                elif self.bridge_type =="원형교각": #원형교각
                    target = rotate_270(frame)[1300:2300, :1000]
                
                height, width, channels = target.shape
                # 검은색 배경으로 채울 너비
                black_width = 1000       
                black_background = np.zeros((height, black_width, channels), dtype=np.uint8)
                # 검은색 배경과 이미지를 연결
                target = np.hstack((black_background, target))
    


def cut_images(directory, bridge_type):
    cap = cv2.VideoCapture(directory)
    cnt=0
    stich_li = []
    while(cap.isOpened()):
        ret, frame = cap.read()
        try : 
            
            if cnt==0:
                if bridge_type == "True": #사각교각
                    tg = rotate_270(frame)[ : , 350:2000]
              
                elif bridge_type =="False": #원형교각
                    tg = rotate_270(frame)[1300:2300, :1000]
                    
                target = tg
                
                #target = rotate_270(frame)[:,350:2000]
                height, width, channels = target.shape
                # 검은색 배경으로 채울 너비
                black_width = 1000       
                black_background = np.zeros((height, black_width, channels), dtype=np.uint8)
                # 검은색 배경과 이미지를 연결
                target = np.hstack((black_background, target))
                
                # 원하는 높이를 설정합니다.
                desired_height = 2000  # 원하는 높이 값으로 변경하세요.

                # 이미지의 현재 높이, 너비 및 채널 수를 가져옵니다.
                height, width, channels = target.shape

                # 이미지의 비율을 유지하면서 너비를 계산합니다.
                # 비율을 계산하고, 너비를 새로운 비율에 맞게 조정합니다.
                aspect_ratio = float(desired_height) / height
                new_width = int(width * aspect_ratio)

                # 이미지 크기를 조정합니다.
                target = cv2.resize(target, (new_width, desired_height))
                #target = rotate_img(frame)[200:3500,:2000] #1500
                stich_li.append(target)
                #img = rotate_img(frame)[:,:1500] #1500
            if cnt%10==0: #라이더 속도 증가시 줄여야함
                
                if bridge_type == "True": #사각교각
                    frm = rotate_270(frame)[ : , 350:1500] #1000,1500

                elif bridge_type =="False": #원형교각
                    frm = rotate_270(frame)[1300:2300, :1000]
                    
                frame = frm
                
                #frame = rotate_270(frame)[:,350:1500] #1000,1500
                # 원하는 높이를 설정합니다.
                desired_height = 2000  # 원하는 높이 값으로 변경하세요.

                # 이미지의 현재 높이, 너비 및 채널 수를 가져옵니다.
                height, width, channels = frame.shape

                # 이미지의 비율을 유지하면서 너비를 계산합니다.
                # 비율을 계산하고, 너비를 새로운 비율에 맞게 조정합니다.
                aspect_ratio = float(desired_height) / height
                new_width = int(width * aspect_ratio)

                # 이미지 크기를 조정합니다.
                frame = cv2.resize(frame, (new_width, desired_height))
                stich_li.append(frame)
                #status, img = stitcher.stitch([frame[(idx*2):(idx*2)+150], img])
                #img = cv2.vconcat([frame[(idx*5)+20:(idx*5)+120], img])
            cnt+=1
        except : 
            break
        
    return stich_li

def stitching(li, bridge_type):
  try:
    print('stitching')
    res = []
    # print(len(li))
    result= cv2.copyMakeBorder(li[0],100,100,0,0,cv2.BORDER_CONSTANT,value=[0,0,0])
    result_li = []
    for idx,i in enumerate(li[1:]):
        #try:
        i = cv2.copyMakeBorder(i,100,100,0,0,cv2.BORDER_CONSTANT,value=[0,0,0])
        result1 = remove_black(result[:,-3000:])
        result = cv2.hconcat([result[:,:-3000],result1])
        result = concat_img3(i, result, 'KAZE', bridge_type)
        
    # result black remove 
    stitched = cv2.copyMakeBorder(result, 10, 10, 10, 10, cv2.BORDER_CONSTANT, (0, 0, 0))
    print('black remove done')
    # convert the stitched image to grayscale and threshold it
    # such that all pixels greater than zero are set to 255
    # (foreground) while all others remain 0 (background)
    gray = cv2.cvtColor(stitched, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY)[1]
    cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    c = max(cnts, key=cv2.contourArea)
    
    # allocate memory for the mask which will contain the
    # rectangular bounding box of the stitched image region
    mask = np.zeros(thresh.shape, dtype="uint8")
    (x, y, w, h) = cv2.boundingRect(c)
    cv2.rectangle(mask, (x, y), (x + w, y + h), 255, -1)
    minRect = mask.copy()
    sub = mask.copy()
    
    # keep looping until there are no non-zero pixels left in the
    # subtracted image
    while cv2.countNonZero(sub) > 0:
        # erode the minimum rectangular mask and then subtract
        # the thresholded image from the minimum rectangular mask
        # so we can count if there are any non-zero pixels left
        minRect = cv2.erode(minRect, None)
        sub = cv2.subtract(minRect, thresh)
    
    cnts = cv2.findContours(minRect.copy(), cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    c = max(cnts, key=cv2.contourArea)
    (x, y, w, h) = cv2.boundingRect(c)
    
    # use the bounding box coordinates to extract the our final
    # stitched image
    result = stitched[y:y + h, x:x + w]
    res.append("스티칭 성공")
    print(res[0])
    return res, result
  except Exception as e:
    res.append("스티칭 실패")
    print(res[0])
    return res, result


# cv2.VideoCapture로 스트리밍
cap = cv2.VideoCapture()

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    cv2.imshow('Video Stream', frame)



def remove_black(img):
    height, width, channel = img.shape
    # print(height, width, channel)
    gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray,3)

    ret,thresh = cv2.threshold(gray,1,255,0)
    contours,hierarchy = cv2.findContours(thresh,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)
    
    max_area = -1
    best_cnt = None

    for cnt in contours:

        area = cv2.contourArea(cnt)
        if area > max_area:
            max_area = area
            best_cnt = cnt
            
    approx = cv2.approxPolyDP(best_cnt,0.01*cv2.arcLength(best_cnt,True),True)

    df = pd.DataFrame()
    df["x"] = approx[:,-1,0]
    df["y"] = approx[:,-1,1]
    df = pd.concat([df[:2], df[-2:]])
    df = df.sort_values(by=["x"], ignore_index=True)
    approx = pd.concat([df[:2].sort_values(by="y"), df[2:].sort_values(by="y", ascending=False)]).values
    
    xmax = approx[:,0].max()
    
    x_target_max = min(approx[-1][0], approx[-2][0])
    x_target_min = max(approx[0][0], approx[1][0])
    
    src = np.array([[0,100],[0,2100],approx[-2],approx[-1]], dtype=np.float32)
    dst = np.array([[0,100],[0,2100],[x_target_max,2100],[x_target_max,100]],dtype=np.float32)
    matrix = cv2.getPerspectiveTransform(src,dst)
    
    dst = cv2.warpPerspective(img, matrix, (x_target_max, height))
    return dst



def cut_images(directory, bridge_type):
    cap = cv2.VideoCapture(directory)
    cnt=0
    stich_li = []
    while(cap.isOpened()):
        ret, frame = cap.read()
        try : 
            
            if cnt==0:
                if bridge_type == "True": #사각교각
                    tg = rotate_270(frame)[ : , 350:2000]
              
                elif bridge_type =="False": #원형교각
                    tg = rotate_270(frame)[1300:2300, :1000]
                    
                target = tg
                
                #target = rotate_270(frame)[:,350:2000]
                height, width, channels = target.shape
                # 검은색 배경으로 채울 너비
                black_width = 1000       
                black_background = np.zeros((height, black_width, channels), dtype=np.uint8)
                # 검은색 배경과 이미지를 연결
                target = np.hstack((black_background, target))
                
                # 원하는 높이를 설정합니다.
                desired_height = 2000  # 원하는 높이 값으로 변경하세요.

                # 이미지의 현재 높이, 너비 및 채널 수를 가져옵니다.
                height, width, channels = target.shape

                # 이미지의 비율을 유지하면서 너비를 계산합니다.
                # 비율을 계산하고, 너비를 새로운 비율에 맞게 조정합니다.
                aspect_ratio = float(desired_height) / height
                new_width = int(width * aspect_ratio)

                # 이미지 크기를 조정합니다.
                target = cv2.resize(target, (new_width, desired_height))
                #target = rotate_img(frame)[200:3500,:2000] #1500
                stich_li.append(target)
                #img = rotate_img(frame)[:,:1500] #1500
            if cnt%10==0: #라이더 속도 증가시 줄여야함
                
                if bridge_type == "True": #사각교각
                    frm = rotate_270(frame)[ : , 350:1500] #1000,1500

                elif bridge_type =="False": #원형교각
                    frm = rotate_270(frame)[1300:2300, :1000]
                    
                frame = frm
                
                #frame = rotate_270(frame)[:,350:1500] #1000,1500
                # 원하는 높이를 설정합니다.
                desired_height = 2000  # 원하는 높이 값으로 변경하세요.

                # 이미지의 현재 높이, 너비 및 채널 수를 가져옵니다.
                height, width, channels = frame.shape

                # 이미지의 비율을 유지하면서 너비를 계산합니다.
                # 비율을 계산하고, 너비를 새로운 비율에 맞게 조정합니다.
                aspect_ratio = float(desired_height) / height
                new_width = int(width * aspect_ratio)

                # 이미지 크기를 조정합니다.
                frame = cv2.resize(frame, (new_width, desired_height))
                stich_li.append(frame)
                #status, img = stitcher.stitch([frame[(idx*2):(idx*2)+150], img])
                #img = cv2.vconcat([frame[(idx*5)+20:(idx*5)+120], img])
            cnt+=1
        except : 
            break
        
    return stich_li
