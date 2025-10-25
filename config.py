from easydict import EasyDict
import numpy as np


def get_config():
    conf= EasyDict()

    # video_path="data/台東多良車站即時影像_20251010_1457_1508.mp4"#影片的07:20有火車經過
    # video_path="data/台東多良車站即時影像_20251010_1900_1905.mp4"
    # video_path= "/home/mingming/01.Projects/999.youtube_video_analysis/data/KC Zoo Polar Bear Cam_20251010_1519_1529.mp4"
    # video_path= "rtsp://192.168.1.108:8554/youtube_train"

    conf.video_path= "rtsp://192.168.1.108:8554/youtube_train"
    conf.resize_ratio= 0.7
    conf.output_img_root= "./output"
    conf.binary_threshold= 50  #二值化閾值
    conf.diff_ratio_threshold= 0.35  #火車經過的變化率閾值
    
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