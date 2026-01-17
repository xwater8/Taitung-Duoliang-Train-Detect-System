from easydict import EasyDict
import numpy as np

import os

def get_config():
    conf= EasyDict()

    # video_path="data/台東多良車站即時影像_20251010_1457_1508.mp4"#影片的07:20有火車經過
    # video_path="data/台東多良車站即時影像_20251010_1900_1905.mp4"
    # video_path= "/home/mingming/01.Projects/999.youtube_video_analysis/data/KC Zoo Polar Bear Cam_20251010_1519_1529.mp4"
    # video_path= "rtsp://192.168.1.108:8554/youtube_train"
    # conf.video_path= "data/台東多良車站即時影像_20251026_0713.mkv"
    # cap.set(cv2.CAP_PROP_POS_FRAMES, 8700)
    
    conf.video_path= "rtsp://mediamtx:8554/youtube_train"
    
    conf.resize_ratio= 0.7
    conf.output_root= "./output"
    conf.output_train_img_folder= os.path.join(conf.output_root, "train_img")
    conf.output_background_img_folder= os.path.join(conf.output_root, "background_img")
    conf.binary_threshold= 30  #二值化閾值
    conf.diff_ratio_threshold= 0.1  #火車經過的變化率閾值
    
    conf.ssim_threshold= 0.70  #SSIM相似度閾值
    conf.vote_count= 10  #投票法的窗口大小
    conf.too_light_pixel_threshold= 210  #過亮像素的閾值
    
    #火車polygon座標, 1920x1080解析度下的座標
    conf.train_polygon= np.asarray(
        [ [1089, 720],
        [1578, 429],
        [1652, 481],
        [1116, 823]], dtype=np.float32       
    )
    conf.train_polygon[:,0]/=1920.0
    conf.train_polygon[:,1]/=1080.0
    conf.show_img= True
    conf.show_debug_img= False

    return conf