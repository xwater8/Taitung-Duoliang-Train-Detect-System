import os
import cv2
import numpy as np
import time
from datetime import datetime
from skimage.metrics import structural_similarity as ssim
from collections import deque

from eray_toolBox.bbox import BBox, draw_bbox
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



def background_subtract(blur_img, ema_denoise_frame, train_mask, train_mask_area, conf):
    diff_frame= cv2.absdiff(blur_img, ema_denoise_frame)

    th, binary_img= cv2.threshold(diff_frame, conf.binary_threshold, 255, cv2.THRESH_BINARY)

    kernel= cv2.getStructuringElement(cv2.MORPH_RECT, (5,5))
    binary_img= cv2.dilate(binary_img, kernel, binary_img)
    binary_img= cv2.erode(binary_img, kernel, binary_img)
    
    train_road_diff_count= np.count_nonzero(binary_img[train_mask==255])        
    train_area_diff_ratio= train_road_diff_count / train_mask_area
    return train_area_diff_ratio, diff_frame, binary_img

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
    roi_train_polygon= train_polygon.copy()
    roi_train_polygon[:,0]-= int(train_polygon[:,0].min())
    roi_train_polygon[:,1]-= int(train_polygon[:,1].min())
    
    train_mask= np.zeros(frame.shape[:2], dtype=np.uint8)
    cv2.fillPoly(train_mask, [train_polygon], 255)
    
    train_mask_area= cv2.contourArea(train_polygon)
    x,y,w,h= cv2.boundingRect(train_polygon)
    
    train_mask_bbox= BBox(x, y, x+w, y+h, 1.0, clsName='train_mask')
    
    has_train_event= False
    best_diff_img= None
    best_diff_img_ratio= 0.0    
    best_ssim_img_score= 100.0
    best_output_img_path= None
    best_background_img= None
    
        
    train_event_vote= deque(maxlen= conf.vote_count)
    
    while True:
        ret, frame= cap.read()
        
        if ret==False:
            logger.warning("Video stream can't be read, wait 2 seconds to reconnect...")
            time.sleep(2)
            continue
        frame= cv2.resize(frame, (0,0), fx=conf.resize_ratio, fy=conf.resize_ratio)
        # print("Frame_shape: {}".format(frame.shape))
        
        gray_img= cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur_img= cv2.GaussianBlur(gray_img, (5,5), 0)
        ema_denoise_frame= ema_denoise.apply(blur_img)
        

        roi_frame= frame[train_mask_bbox.ymin:train_mask_bbox.ymax, train_mask_bbox.xmin:train_mask_bbox.xmax]
        roi_ema_denoise_frame= ema_denoise_frame[train_mask_bbox.ymin:train_mask_bbox.ymax, train_mask_bbox.xmin:train_mask_bbox.xmax]
        roi_blur_img= blur_img[train_mask_bbox.ymin:train_mask_bbox.ymax, train_mask_bbox.xmin:train_mask_bbox.xmax]
        roi_train_mask= train_mask[train_mask_bbox.ymin:train_mask_bbox.ymax, train_mask_bbox.xmin:train_mask_bbox.xmax]
        similar_score, ssim_diff_img= ssim(roi_ema_denoise_frame, roi_blur_img, full= True)
        
        polygon_similar_score= ssim_diff_img[roi_train_mask==255].mean()
        
        
        
        cv2.polylines(roi_frame, [roi_train_polygon], isClosed=True, color=(0,0,255), thickness=2)
        cv2.putText(frame, "SSIM: {:.4f}".format(similar_score), (50,100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
        cv2.putText(frame, "Polygon SSIM: {:.4f}".format(polygon_similar_score), (50,150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
        

        # train_area_diff_ratio, diff_frame, binary_img = background_subtract(roi_blur_img, roi_ema_denoise_frame, roi_train_mask, train_mask_area, conf)


        cv2.polylines(frame, [train_polygon], isClosed=True, color=(0,0,255), thickness=2)
        draw_bbox(frame, train_mask_bbox, color=(0,255,0), thickness=2)

        #BackGround Subtraction部分
        #確認是否有火車經過, 並且記錄變化最大的那張圖片, 直到沒有變化的時候儲存圖片
        # if train_area_diff_ratio>=conf.diff_ratio_threshold:
        #     logger.debug("train_area_diff_ratio: {}".format(train_area_diff_ratio))
        #     cv2.putText(frame, "Train Approaching!: {}".format(train_area_diff_ratio), (50,50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)
        #     has_train_event= True
        # else:
        #     if has_train_event:
        #         logger.debug("Train Leaving!: {}".format(train_area_diff_ratio))
        #     has_train_event= False
            
            
            
        # if has_train_event:
        #     if train_area_diff_ratio>best_diff_img_ratio:
        #         best_diff_img_ratio= train_area_diff_ratio
        #         best_diff_img= frame.copy()
        #         best_output_img_path= os.path.join(output_img_root, "train_event_{}.jpg".format(get_datetime_str()))
        #         best_background_img= ema_denoise_frame.copy()
        # else:
        #     if best_diff_img is not None:
        #         cv2.imwrite(best_output_img_path, best_diff_img)
        #         background_img_path= best_output_img_path.replace("train_event_", "background_")
        #         cv2.imwrite(background_img_path, best_background_img)
        #         print("Save train event image: {}, background image: {}".format(best_output_img_path, background_img_path))
                
        #         best_diff_img= None
        #         best_diff_img_ratio= 0.0
        #         best_output_img_path= None
        #         best_background_img= None
                
        #SSIM similarity
        if polygon_similar_score<=conf.ssim_threshold:
            logger.debug("polygon_similar_score: {:.4f}".format(polygon_similar_score))
            cv2.putText(frame, "Train Approaching_polygon_ssim!: {:.4f}".format(polygon_similar_score), (50,50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)
            train_event_vote.append(True)
        else:
            train_event_vote.append(False)
            
        #利用投票法判斷火車是否還在範圍內持續變化, 避免重複儲存過多照片
        if any(train_event_vote):
            has_train_event=True
        
        if has_train_event and any(train_event_vote)==False:        
            has_train_event=False
            logger.debug("Train Leaving!: {}".format(polygon_similar_score))
        
            
        if has_train_event:
            if polygon_similar_score<best_ssim_img_score:
                best_ssim_img_score= polygon_similar_score
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
                best_ssim_img_score= 100.0
                best_output_img_path= None
                best_background_img= None
        
        
        if conf.show_img:
            show_img("frame", frame)
            
            if conf.show_debug_img:
                show_img("ema_denoise_frame", ema_denoise_frame)
                # show_img("diff_frame", diff_frame)
                # show_img("binary_img", binary_img)
                show_img("roi_frame", roi_frame)
                show_img("roi_ema_denoise_frame", roi_ema_denoise_frame)
                show_img("roi_blur_img", roi_blur_img)
                show_img("ssim_diff_img", ssim_diff_img)
                show_img("roi_train_mask", roi_train_mask)
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