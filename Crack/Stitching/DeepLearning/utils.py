import numpy as np


def rotate_270(frame):
    rotated_img = np.rot90(frame, k=270 //90)
    return rotated_img