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
from eray_toolBox.utils import get_fileMainName



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


def restore_normalized_polygon_points(normalized_polygon, imgHW):
    polygon= np.zeros_like(normalized_polygon)
    polygon[:,0]= normalized_polygon[:,0]*imgHW[1]
    polygon[:,1]= normalized_polygon[:,1]*imgHW[0]
    polygon= polygon.astype(np.int32)
    return polygon


from optical_flow import draw_flow_arrows

def main():    
    conf= get_config()
    os.makedirs(conf.output_train_img_folder, exist_ok=True)
    os.makedirs(conf.output_background_img_folder, exist_ok=True)
    
    video_path= conf.video_path
    cap = IpcamCapture(video_path, use_soft_decoder= True)
    cap.start()
    # video_path= "data/台東多良車站即時影像_20251026_0713.mkv"
    # cap= cv2.VideoCapture(video_path)
    # cap.set(cv2.CAP_PROP_POS_FRAMES, 8700)
    
    ema_denoise= EMA_Denoise(alpha=0.01)
    
    
    
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
    prev_frame= frame.copy()
    
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
        ema_denoise_frame= ema_denoise.apply(blur_frame)
        

        roi_frame= frame[train_mask_bbox.ymin:train_mask_bbox.ymax, train_mask_bbox.xmin:train_mask_bbox.xmax]
        roi_ema_denoise_frame= ema_denoise_frame[train_mask_bbox.ymin:train_mask_bbox.ymax, train_mask_bbox.xmin:train_mask_bbox.xmax]
        roi_blur_img= blur_frame[train_mask_bbox.ymin:train_mask_bbox.ymax, train_mask_bbox.xmin:train_mask_bbox.xmax]
        roi_train_mask= train_mask[train_mask_bbox.ymin:train_mask_bbox.ymax, train_mask_bbox.xmin:train_mask_bbox.xmax]
        similar_score, ssim_diff_img= ssim(roi_ema_denoise_frame, roi_blur_img, full= True)
        
        polygon_similar_score= ssim_diff_img[roi_train_mask==255].mean()
        
        
        
        cv2.polylines(roi_frame, [roi_train_polygon], isClosed=True, color=(0,0,255), thickness=2)
        cv2.putText(frame, "SSIM: {:.4f}".format(similar_score), (50,100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
        cv2.putText(frame, "Polygon SSIM: {:.4f}".format(polygon_similar_score), (50,150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
        


        cv2.polylines(frame, [train_polygon], isClosed=True, color=(0,0,255), thickness=2)
        draw_bbox(frame, train_mask_bbox, color=(0,255,0), thickness=2)

        #使用OpticalFlow判斷火車是否經過
        prev_gray_frame= cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
        prev_gray_frame_after_mask= cv2.bitwise_and(prev_gray_frame, train_mask)
        gray_frame_after_mask= cv2.bitwise_and(gray_frame, train_mask)
        roi_gray_frame= gray_frame_after_mask[train_mask_bbox.ymin:train_mask_bbox.ymax, train_mask_bbox.xmin:train_mask_bbox.xmax]
        roi_prev_gray_frame= prev_gray_frame_after_mask[train_mask_bbox.ymin:train_mask_bbox.ymax, train_mask_bbox.xmin:train_mask_bbox.xmax]
        roi_flow = cv2.calcOpticalFlowFarneback(roi_prev_gray_frame, roi_gray_frame, None, 0.5, 2, 5, 2, 1, 1.2, 0)
        draw_flow_arrows(roi_frame, roi_flow, step=20, scale=2, color=(0, 255, 0), thickness=1)
        
        # degree=0：代表向右（x 軸正方向）
        # degree=90：代表向下（y 軸正方向）
        # degree=180：代表向左
        # degree=270：代表向上
        # 所以如果你要把角度和圖像的 x,y 座標方向對應，OpenCV 的 degree 已經是依照圖像座標系統定義，不需要再做翻轉或換算。
        mag, degree = cv2.cartToPolar(roi_flow[..., 0], roi_flow[..., 1], angleInDegrees=True)
        
        cv2.putText(frame, "Optical Flow Mag Max: {:.2f}".format(mag.max()), (50,200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
        cv2.putText(frame, "Optical Flow Mag mean: {:.2f}".format(mag[mag>=1].mean()), (50,220), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
        
        max_optical_flow_mag= mag.max()
        
        #SSIM similarity
        if (polygon_similar_score<=conf.ssim_threshold) and (max_optical_flow_mag>=conf.optical_flow_threshold):
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
                best_background_img= ema_denoise_frame.copy()
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
        
        
        prev_frame= frame.copy()
        
        if conf.show_img:
            show_img("frame", frame)
            if conf.show_debug_img:
                show_img("ema_denoise_frame", ema_denoise_frame)
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