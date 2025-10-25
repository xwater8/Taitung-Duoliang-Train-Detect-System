import os
import cv2
import numpy as np
import time
from datetime import datetime

from eray_toolBox.log import LogTxt
from eray_toolBox.utils import show_img
from eray_toolBox.video_stream import IpcamCapture

from config import get_config


import pdb

logger= LogTxt().getLogger()


class EMA_Denoise:
    def __init__(self, alpha=0.1):
        self.alpha = alpha
        self.ema_frame = None

    def apply(self, frame):
        if self.ema_frame is None:
            self.ema_frame = frame.astype(np.float32)
        else:
            #self.ema_frame = self.alpha * frame + (1 - self.alpha) * self.ema_frame
            cv2.accumulateWeighted(frame, self.ema_frame, self.alpha)
        return self.ema_frame.astype(np.uint8)
    

def get_datetime_str():    
    now = datetime.now()
    datetime_str = now.strftime("%Y%m%d_%H%M%S")
    return datetime_str



def main():    
    conf= get_config()
    output_img_root= conf.output_img_root
    os.makedirs(output_img_root, exist_ok=True)
    
    video_path= conf.video_path
    cap = IpcamCapture(video_path, use_soft_decoder= True)
    cap.start()
    
    ema_denoise= EMA_Denoise(alpha=0.01)
    
    
    
    ret, frame= cap.read()
    frame= cv2.resize(frame, (0,0), fx=conf.resize_ratio, fy=conf.resize_ratio)
    
    #將normalized的座標進行還原
    train_polygon= np.zeros_like(conf.train_polygon)
    train_polygon[:,0]= conf.train_polygon[:,0]*frame.shape[1]
    train_polygon[:,1]= conf.train_polygon[:,1]*frame.shape[0]
    train_polygon= train_polygon.astype(np.int32)
    
    train_mask= np.zeros(frame.shape[:2], dtype=np.uint8)
    cv2.fillPoly(train_mask, [train_polygon], 255)
    
    has_train_event= False
    best_diff_img= None
    best_diff_img_ratio= 0.0    
    best_output_img_path= None
    best_background_img= None
    
    while True:
        ret, frame= cap.read()
        
        if ret==False:
            break
        frame= cv2.resize(frame, (0,0), fx=conf.resize_ratio, fy=conf.resize_ratio)
        # print("Frame_shape: {}".format(frame.shape))
        
        gray_img= cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur_img= cv2.GaussianBlur(gray_img, (5,5), 0)
        ema_denoise_frame= ema_denoise.apply(blur_img)
        diff_frame= cv2.absdiff(blur_img, ema_denoise_frame)
        
        th, binary_img= cv2.threshold(diff_frame, 30, 255, cv2.THRESH_BINARY)

        kernel= cv2.getStructuringElement(cv2.MORPH_RECT, (5,5))
        binary_img= cv2.dilate(binary_img, kernel, binary_img)
        binary_img= cv2.erode(binary_img, kernel, binary_img)



        train_mask_area= cv2.contourArea(train_polygon)
        train_road_diff_count= np.count_nonzero(binary_img[train_mask==255])        
        train_area_diff_ratio= train_road_diff_count / train_mask_area


        cv2.polylines(frame, [train_polygon], isClosed=True, color=(0,0,255), thickness=2)

        #確認是否有火車經過, 並且記錄變化最大的那張圖片, 直到沒有變化的時候儲存圖片
        if train_area_diff_ratio>=conf.diff_ratio_threshold:
            logger.debug("train_area_diff_ratio: {}".format(train_area_diff_ratio))
            cv2.putText(frame, "Train Approaching!: {}".format(train_area_diff_ratio), (50,50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)
            has_train_event= True
        else:
            if has_train_event:
                logger.debug("Train Leaving!: {}".format(train_area_diff_ratio))
            has_train_event= False
            
            
            
        if has_train_event:
            if train_area_diff_ratio>best_diff_img_ratio:
                best_diff_img_ratio= train_area_diff_ratio
                best_diff_img= frame.copy()
                best_output_img_path= os.path.join(output_img_root, "train_event_{}.jpg".format(get_datetime_str()))
                best_background_img= ema_denoise_frame.copy()
        else:
            if best_diff_img is not None:
                cv2.imwrite(best_output_img_path, best_diff_img)
                background_img_path= best_output_img_path.replace("train_event_", "background_")
                cv2.imwrite(background_img_path, best_background_img)
                print("Save train event image: {}, background image: {}".format(best_output_img_path, background_img_path))
                
                best_diff_img= None
                best_diff_img_ratio= 0.0
                best_output_img_path= None
                best_background_img= None
        
        
        if conf.show_img:
            show_img("frame", frame)
            if conf.show_debug_img:
                show_img("ema_denoise_frame", ema_denoise_frame)
                show_img("diff_frame", diff_frame)
                show_img("binary_img", binary_img)
            key = cv2.waitKey(1)
            if key==27: # ESC
                break
        
    cv2.destroyAllWindows()
    cap.release()

if __name__=="__main__":
    try:
        main()
    except:
        logger.exception("--Main Program Error, Start to restart program--")
        time.sleep(5)