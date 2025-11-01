import cv2
import numpy as np


from eray_toolBox.utils import show_img, TimeMeasure


from pprint import pprint
import pdb

from config import get_config

def main():
    conf= get_config()
    video_path= "../data/台東多良車站即時影像_20251026_0713.mkv"
    
    resize_ratio= 0.25

    cap= cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, 8700)
    
    prev_frame= cap.read()[1]
    prev_frame= cv2.resize(prev_frame, (0,0), fx=resize_ratio, fy=resize_ratio)
    hsv_img= np.zeros_like(prev_frame)
    hsv_img[...,1]=255
    
    time_measure= TimeMeasure()
    while True:
        ret, frame= cap.read()
        if ret==False:
            break
        
        frame= cv2.resize(frame, (0,0), fx=resize_ratio, fy=resize_ratio)
        
        time_measure.start()
        prev_gray_frame= cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
        gray_frame= cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        flow = cv2.calcOpticalFlowFarneback(prev_gray_frame, gray_frame, None, 0.5, 3, 15, 3, 5, 1.2, 0)
        mag, ang = cv2.cartToPolar(flow[..., 0], flow[..., 1])
        hsv_img[..., 0] = ang*180/np.pi/2
        hsv_img[..., 2] = cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX)
        bgr = cv2.cvtColor(hsv_img, cv2.COLOR_HSV2BGR)

        time_measure.stop()
        print("Optical flow :{}".format(time_measure))
        
        
        show_img("Frame", frame)
        show_img("optical_flow_bgr", bgr)
        key= cv2.waitKey(1)
        
        prev_frame= frame.copy()
        if key==27:
            break
        
    cap.release()
    cv2.destroyAllWindows()
    
if __name__=="__main__":
    main()