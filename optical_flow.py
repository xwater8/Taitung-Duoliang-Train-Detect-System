import cv2
import numpy as np


from eray_toolBox.utils import show_img, TimeMeasure


from pprint import pprint
import pdb

from config import get_config

def draw_flow_arrows(img, flow, step=16, scale=3, color=(0, 255, 0), thickness=1):
    """
    在圖像上繪製光流方向箭頭
    
    參數:
    img: 輸入圖像
    flow: 光流數據
    step: 箭頭間距（像素）
    scale: 箭頭長度縮放因子
    color: 箭頭顏色 (B, G, R)
    thickness: 箭頭線條粗細
    """
    h, w = img.shape[:2]
    y, x = np.mgrid[step//2:h:step, step//2:w:step].reshape(2, -1).astype(int)
    
    # 獲取對應位置的光流向量
    fx, fy = flow[y, x].T
    
    # 計算箭頭終點
    lines = np.vstack([x, y, x + fx * scale, y + fy * scale]).T.reshape(-1, 2, 2)
    lines = np.int32(lines + 0.5)
    
    # 繪製箭頭
    for (x1, y1), (x2, y2) in lines:
        # 計算向量長度，過濾太小的向量
        length = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        if length > 1:  # 只繪製有明顯移動的箭頭
            cv2.arrowedLine(img, (x1, y1), (x2, y2), color, thickness, tipLength=0.3)
    
    return img

from eray_toolBox.bbox import BBox

def main():
    conf= get_config()
    video_path= "./data/台東多良車站即時影像_20251026_0713.mkv"
    
    resize_ratio= 0.5

    cap= cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, 8700)
    
    prev_frame= cap.read()[1]
    prev_frame= cv2.resize(prev_frame, (0,0), fx=resize_ratio, fy=resize_ratio)
    hsv_img= np.zeros_like(prev_frame)
    hsv_img[...,1]=255
    
    time_measure= TimeMeasure()
        
    
    #將normalized的座標進行還原
    train_polygon= np.zeros_like(conf.train_polygon)
    train_polygon[:,0]= conf.train_polygon[:,0]*prev_frame.shape[1]
    train_polygon[:,1]= conf.train_polygon[:,1]*prev_frame.shape[0]
    train_polygon= train_polygon.astype(np.int32)
    roi_train_polygon= train_polygon.copy()
    roi_train_polygon[:,0]-= int(train_polygon[:,0].min())
    roi_train_polygon[:,1]-= int(train_polygon[:,1].min())
    
    train_mask= np.zeros(prev_frame.shape[:2], dtype=np.uint8)
    cv2.fillPoly(train_mask, [train_polygon], 255)
    
    train_mask_area= cv2.contourArea(train_polygon)
    x,y,w,h= cv2.boundingRect(train_polygon)
    
    train_mask_bbox= BBox(x, y, x+w, y+h, 1.0, clsName='train_mask')
    
    
    
    
    frame_idx=0
    while True:
        frame_idx+=1
        ret, frame= cap.read()
        if ret==False:
            break
        # if frame_idx%1==0:
        #     continue
        
        frame= cv2.resize(frame, (0,0), fx=resize_ratio, fy=resize_ratio)
        
        time_measure.start()
        prev_gray_frame= cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
        gray_frame= cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        roi_prev_gray_frame= prev_gray_frame[train_mask_bbox.ymin:train_mask_bbox.ymax, train_mask_bbox.xmin:train_mask_bbox.xmax]
        roi_gray_frame= gray_frame[train_mask_bbox.ymin:train_mask_bbox.ymax, train_mask_bbox.xmin:train_mask_bbox.xmax]
        flow = cv2.calcOpticalFlowFarneback(roi_prev_gray_frame, roi_gray_frame, None, 0.25, 1, 5, 2, 1, 1.2, 0)
        time_measure.stop()
        mag, ang = cv2.cartToPolar(flow[..., 0], flow[..., 1])
        hsv_img[train_mask_bbox.ymin:train_mask_bbox.ymax, train_mask_bbox.xmin:train_mask_bbox.xmax, 0] = ang*180/np.pi/2
        hsv_img[train_mask_bbox.ymin:train_mask_bbox.ymax, train_mask_bbox.xmin:train_mask_bbox.xmax, 2] = cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX)
        bgr = cv2.cvtColor(hsv_img, cv2.COLOR_HSV2BGR)

        
        print("Optical flow :{}".format(time_measure))
        
        # 創建帶箭頭的光流視覺化
        idxs= np.where(flow>8)
        if idxs[0].size >0:
            pdb.set_trace()
        flow_with_arrows = frame.copy()
        roi_flow_with_arrows= flow_with_arrows[train_mask_bbox.ymin:train_mask_bbox.ymax, train_mask_bbox.xmin:train_mask_bbox.xmax]
        flow_with_arrows = draw_flow_arrows(roi_flow_with_arrows, flow, step=20, scale=2, color=(0, 255, 0), thickness=1)

        show_img("Frame", frame)
        show_img("optical_flow_bgr", bgr)
        show_img("optical_flow_arrows", flow_with_arrows)
        key= cv2.waitKey(1)
        
        prev_frame= frame.copy()
        if key==27:
            break
        
        
    cap.release()
    cv2.destroyAllWindows()
    
if __name__=="__main__":
    main()