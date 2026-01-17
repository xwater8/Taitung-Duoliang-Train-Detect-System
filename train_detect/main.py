import os
import cv2
import numpy as np
import time
from datetime import datetime
from skimage.metrics import structural_similarity as ssim
from collections import deque

from train_detect.toolbox.bbox import BBox, draw_bbox
from train_detect.toolbox.log import LogTxt
from train_detect.toolbox.utils import show_img, get_fileMainName
from train_detect.toolbox.video_stream import IpcamCapture



from config import get_config


import pdb

logger= LogTxt().getLogger()


class EMA_BackgroundModel:
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





def restore_normalized_polygon_points(normalized_polygon, imgHW):
    polygon= np.zeros_like(normalized_polygon)
    polygon[:,0]= normalized_polygon[:,0]*imgHW[1]
    polygon[:,1]= normalized_polygon[:,1]*imgHW[0]
    polygon= polygon.astype(np.int32)
    return polygon



def main():    
    conf= get_config()
    os.makedirs(conf.output_train_img_folder, exist_ok=True)
    os.makedirs(conf.output_background_img_folder, exist_ok=True)
    
    video_path= conf.video_path
    cap = IpcamCapture(video_path)
    cap.start()
        
        
    ema_background_model= EMA_BackgroundModel(alpha=0.01)
    
    ret, frame= cap.read()
    frame= cv2.resize(frame, (0,0), fx=conf.resize_ratio, fy=conf.resize_ratio)
    
    #將normalized的座標進行還原
    train_polygon= restore_normalized_polygon_points(conf.train_polygon, frame.shape[:2])
    roi_train_polygon= train_polygon.copy()
    roi_train_polygon[:,0]-= int(train_polygon[:,0].min())
    roi_train_polygon[:,1]-= int(train_polygon[:,1].min())
    
    train_mask= np.zeros(frame.shape[:2], dtype=np.uint8)
    cv2.fillPoly(train_mask, [train_polygon], 255)
    
    x,y,w,h= cv2.boundingRect(train_polygon)    
    train_mask_bbox= BBox(x, y, x+w, y+h, 1.0, clsName='train_mask')
    
    has_train_event= False
    best_diff_img= None   
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
        
        gray_frame= cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur_frame= cv2.GaussianBlur(gray_frame, (5,5), 0)
        ema_background_frame= ema_background_model.apply(blur_frame)
        

        roi_frame= frame[train_mask_bbox.ymin:train_mask_bbox.ymax, train_mask_bbox.xmin:train_mask_bbox.xmax]
        roi_ema_background_frame= ema_background_frame[train_mask_bbox.ymin:train_mask_bbox.ymax, train_mask_bbox.xmin:train_mask_bbox.xmax]
        roi_blur_img= blur_frame[train_mask_bbox.ymin:train_mask_bbox.ymax, train_mask_bbox.xmin:train_mask_bbox.xmax]
        roi_train_mask= train_mask[train_mask_bbox.ymin:train_mask_bbox.ymax, train_mask_bbox.xmin:train_mask_bbox.xmax]
        similar_score, ssim_diff_img= ssim(roi_ema_background_frame, roi_blur_img, full= True)
        
        roi_gray_frame= gray_frame[train_mask_bbox.ymin:train_mask_bbox.ymax, train_mask_bbox.xmin:train_mask_bbox.xmax]
        th, roi_binary_frame= cv2.threshold(roi_gray_frame, conf.too_light_pixel_threshold, 255, cv2.THRESH_BINARY)
        too_light_pixel= np.where(roi_binary_frame==255)
        too_light_pixel_ratio= too_light_pixel[0].size / (roi_gray_frame.shape[0]*roi_gray_frame.shape[1])
        ssim_diff_img[too_light_pixel]= 1.0  #將過亮的區域視為相似度高
        polygon_similar_score= ssim_diff_img[roi_train_mask==255].mean()
        
        
        
        cv2.polylines(roi_frame, [roi_train_polygon], isClosed=True, color=(0,0,255), thickness=2)
        cv2.putText(frame, "SSIM: {:.4f}".format(similar_score), (50,100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
        cv2.putText(frame, "Polygon SSIM: {:.4f}".format(polygon_similar_score), (50,150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

        cv2.putText(frame, "Too Light Pixel ratio: {:.4f}".format(too_light_pixel_ratio), (50,200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)


        cv2.polylines(frame, [train_polygon], isClosed=True, color=(0,0,255), thickness=2)
        draw_bbox(frame, train_mask_bbox, color=(0,255,0), thickness=2)

        
        #SSIM similarity
        if (polygon_similar_score<=conf.ssim_threshold):
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
                best_output_img_path= os.path.join(conf.output_train_img_folder, "train_event_{}.jpg".format(get_datetime_str()))
                best_background_img= ema_background_frame.copy()
        else:
            if best_diff_img is not None:
                cv2.imwrite(best_output_img_path, best_diff_img)
                background_img_name= get_fileMainName(best_output_img_path).replace("train_event_", "background_") + ".jpg"
                background_img_path= os.path.join(conf.output_background_img_folder, background_img_name)
                cv2.imwrite(background_img_path, best_background_img)
                print("Save train event image: {}, background image: {}".format(best_output_img_path, background_img_path))
                
                best_diff_img= None
                best_ssim_img_score= 100.0
                best_output_img_path= None
                best_background_img= None
        
        
        
        if conf.show_img:
            show_img("frame", frame)
            if conf.show_debug_img:
                show_img("ema_background_frame", ema_background_frame)
                show_img("roi_frame", roi_frame)
                show_img("roi_ema_background_frame", roi_ema_background_frame)
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