import numpy as np

def rotate_frame270(frame):
    print('rotate_frame270 메소드 실행')

    rotated_img = np.rot90(frame, k=270 // 90)
    return rotated_img

def rotate_frame90(frame):
    print('rotate_frame90 메소드 실행')

    rotated_img = np.rot90(frame, k=90 // 90)
    return rotated_img