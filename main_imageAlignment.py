import os
import cv2
import numpy as np


import pdb
from pprint import pprint

from eray_toolBox.img_proc.imgAlignment import ORB_Descriptor, ImgAlignment
from eray_toolBox.utils import show_img


def get_imgTransform_corners(image_HW, transform_matrix):
    h, w= image_HW
    corners= np.array([[0,0], [w,0], [w,h], [0,h]], dtype=np.float32).reshape(-1,1,2)  # (4,1,2)
    transformed_corners= cv2.perspectiveTransform(corners, transform_matrix)  # (4,1,2)
    transformed_corners= transformed_corners.reshape(-1,2).astype(int)  # (4,2)
    return transformed_corners

def get_imgTransform_mask(image_HW, transform_matrix, target_HW):
    transformed_corners= get_imgTransform_corners(image_HW, transform_matrix)
    h,w= target_HW
    mask= np.zeros((h,w), dtype=np.uint8)
    cv2.fillConvexPoly(mask, transformed_corners, 255)
    return mask

def is_frame_in_panorama(panorama_image_HW, frame_HW, transform_matrix):
    h, w= frame_HW
    corners= np.array([[0,0], [w,0], [w,h], [0,h]], dtype=np.float32).reshape(-1,1,2)  # (4,1,2)
    transformed_corners= cv2.perspectiveTransform(corners, transform_matrix)  # (4,1,2)
    transformed_corners= transformed_corners.reshape(-1,2)  # (4,2)
    
    pano_h, pano_w= panorama_image_HW
    if np.all(transformed_corners[:,0]>=0) and np.all(transformed_corners[:,0]<pano_w) and np.all(transformed_corners[:,1]>=0) and np.all(transformed_corners[:,1]<pano_h):
        return True
    return False


def main():
    USE_FULL_PANORMAL_IMAGE= False
    video_path= "data/Red Pandas_20251011_1119_1200.mkv"
    video_path= "data/Red_Pands_cut.mkv"
    cap= cv2.VideoCapture(video_path)
    
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    
    assert(cap.isOpened()), "Can't open video_path: {}".format(video_path)
    
    descriptor= ORB_Descriptor(max_features=1500, good_match_percent=0.15, use_crossCheck= True)
    img_alignment= ImgAlignment(descriptor)
    
    panorama_image= None
    panorama_transform_matrix= np.eye(3)
    prev_image= None
    frame_idx= 0
    while True:
        frame_idx+=1
        ret, frame= cap.read()
        if not ret:
            break
        
        if frame_idx%60!=0:
            continue
        
        if prev_image is None:
            prev_image= frame.copy()
            if USE_FULL_PANORMAL_IMAGE:
                panorama_image= np.zeros((int(frame.shape[0]*1.2), int(frame.shape[1]*3), 3), dtype=np.uint8)
                panorama_image[0:frame.shape[0], -frame.shape[1]:, :]= frame.copy()
            else:
                panorama_image= frame.copy()
            continue
        
        if USE_FULL_PANORMAL_IMAGE:
            panorama_draw_image= panorama_image.copy()
            #先撰寫簡單版本的panorama_image, 用大圖直接imageAlignment, 記得要動態擴展圖片範圍
            transform_matrix= img_alignment.getAffineMatrix(frame, panorama_image)
            match_img= img_alignment.draw_matchPairs(frame, panorama_draw_image)
            
            cv2.warpPerspective(frame, transform_matrix, (panorama_image.shape[1], panorama_image.shape[0]), panorama_image, borderMode=cv2.BORDER_TRANSPARENT)
        else:
            #BUG: 不曉得為什麼當鏡頭轉到最左邊以後就無法持續在合併了
            transform_matrix= img_alignment.getAffineMatrix(frame, prev_image)
            match_img= img_alignment.draw_matchPairs(frame, prev_image)            
            panorama_transform_matrix= transform_matrix @ panorama_transform_matrix
            
            #計算轉換後的frame四個角落座標與panorama_image的座標, 判斷是否要升成一張新的大圖片
            transform_corners= get_imgTransform_corners(frame.shape[:2], panorama_transform_matrix)#(4,2)
            panorama_corners= np.array([[0,0], [panorama_image.shape[1],0], [panorama_image.shape[1],panorama_image.shape[0]], [0,panorama_image.shape[0]]], dtype=np.int32)#(4,2)
            
            all_corners= np.concatenate((transform_corners, panorama_corners), axis=0) #(8,2)
            min_x= all_corners[:,0].min()
            max_x= all_corners[:,0].max()
            min_y= all_corners[:,1].min()
            max_y= all_corners[:,1].max()
            
            offset_x= 0
            offset_y= 0
            if min_x <0:
                offset_x= -min_x
            if min_y <0:
                offset_y= -min_y
                
            height= max_y - min_y
            width= max_x - min_x
            
            if height > panorama_image.shape[0] or width > panorama_image.shape[1]:
                print("Expand panorama_image: {}x{} -> {}x{}, offset: ({},{})".format(panorama_image.shape[1], panorama_image.shape[0], width, height, offset_x, offset_y))
                new_panorama_image= np.zeros((height, width, 3), dtype=np.uint8)
                offset_panorama_matrix= np.asarray([
                    [1, 0, offset_x],
                    [0, 1, offset_y],
                    [0, 0, 1]
                ], dtype=np.float32)
                cv2.warpPerspective(panorama_image, offset_panorama_matrix, (width, height), new_panorama_image)
                panorama_image= new_panorama_image
                
                panorama_transform_matrix= offset_panorama_matrix @ panorama_transform_matrix
                cv2.warpPerspective(frame, panorama_transform_matrix, (width, height), panorama_image, borderMode=cv2.BORDER_TRANSPARENT)
            
        

        prev_image= frame.copy()
        show_img("Frame", frame)
        # show_img("panorama_image", panorama_draw_image, width= 2560, height=800)
        show_img("panorama_image", panorama_image, width= 2560, height=800)
        show_img("match_img", match_img)
        key= cv2.waitKey(1)
        if key==27:
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__=='__main__':
    main()