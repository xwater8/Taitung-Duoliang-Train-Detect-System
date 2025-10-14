import cv2
import numpy as np

def gamma_correction(frame, gamma=1.0):
    invGamma = 1.0 / gamma
    table = np.array([((i / 255.0) ** invGamma) * 255
                      for i in np.arange(256)]).astype("uint8")
    return cv2.LUT(frame, table)

def show_img(title, frame, width=1280, height=720):
    frame= gamma_correction(frame, 1.5)
    cv2.namedWindow(title, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(title, width, height)
    cv2.imshow(title, frame)

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

def main():
    video_path="data/台東多良車站即時影像_20251010_1457_1508.mp4"
    video_path="data/台東多良車站即時影像_20251010_1900_1905.mp4"
    # video_path="data/KC Zoo Polar Bear Cam_20251010_1519_1529.mp4"
    # video_path="data/hermosa_beach_20251010_1554_1559.mp4"
    # video_path= "data/jackson_town_20251010_1620_1625.mp4"
    cap = cv2.VideoCapture(video_path)
    ema_denoise= EMA_Denoise(alpha=0.1)
    assert(cap.isOpened()), "Can't open video_path: {}".format(video_path)
    
    while True:
        ret, frame= cap.read()
        if ret==False:
            break
        
        median_blur_frame= cv2.medianBlur(frame, 3)
        gaussian_frame= cv2.GaussianBlur(frame, (3,3), 0)
        ema_denoise_frame= ema_denoise.apply(frame)

        show_img("frame", frame)
        show_img("median_blur_frame", median_blur_frame)
        show_img("gaussian_frame", gaussian_frame)
        show_img("ema_denoise_frame", ema_denoise_frame)
        key = cv2.waitKey(10)
        if key==27: # ESC
            break
        
    cv2.destroyAllWindows()
    cap.release()
    
if __name__=="__main__":
    main()