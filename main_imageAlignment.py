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
    video_path= "data/Red Pandas_20251011_1119_1200.mkv"
    video_path= "data/Red_Pands_cut.mkv"
    cap= cv2.VideoCapture(video_path)
    
    assert(cap.isOpened()), "Can't open video_path: {}".format(video_path)
    
    descriptor= ORB_Descriptor(max_features=1500, good_match_percent=0.15, use_crossCheck= True)
    img_alignment= ImgAlignment(descriptor)
    
    panorama_image= None
    panorama_transform_matrix= np.eye(3)
    prev_image= None
    while True:
        ret, frame= cap.read()
        if not ret:
            break
        
        if prev_image is None:
            prev_image= frame.copy()
            panorama_image= np.zeros((int(frame.shape[0]*1.2), int(frame.shape[1]*3), 3), dtype=np.uint8)
            panorama_image[0:frame.shape[0], 0:frame.shape[1], :]= frame.copy()
            continue
        # process frame
        # ...
        transform_matrix= img_alignment.getAffineMatrix(frame, prev_image)
        match_img= img_alignment.draw_matchPairs(frame, prev_image)
        panorama_transform_matrix= panorama_transform_matrix @ transform_matrix

        height= int(frame.shape[0]*1.2)
        width= int(frame.shape[1]*3)
        
        
        copy_mask= get_imgTransform_mask(frame.shape[:2], panorama_transform_matrix, (height, width))
        if is_frame_in_panorama(panorama_image.shape[:2], frame.shape[:2], panorama_transform_matrix):
            print("Frame is in panorama, skip")
        else:
            print("Frame is out of panorama, stop")
            # transform_corners= get_imgTransform_corners(frame.shape[:2], panorama_transform_matrix)
            # min_x= transform_corners[:,0].min()
            # max_x= transform_corners[:,0].max()
            # min_y= transform_corners[:,1].min()
            # max_y= transform_corners[:,1].max()
            
            # offset_x= 0
            # offset_y= 0
            # if min_x <0:
            #     offset_x= -min_x
            # if min_y <0:
            #     offset_y= -min_y
            
            # offset_panorama_matrix= np.asarray([
            #     [1, 0, offset_x],
            #     [0, 1, offset_y],
            #     [0, 0, 1]
            # ], dtype=np.float32)
            # cv2.warpPerspective(panorama_image, offset_panorama_matrix, (width, height), panorama_image)
            # cv2.warpPerspective(copy_mask, offset_panorama_matrix, (width, height), copy_mask)
        
        
        transform_image= cv2.warpPerspective(frame, panorama_transform_matrix, (width, height))
        
        
            # panorama_image= cv2.addWeighted(panorama_image, 0.9, transform_image, 0.1, 0)
       
        cv2.copyTo(transform_image, copy_mask, panorama_image)
        

        prev_image= frame.copy()
        show_img("Frame", frame)
        show_img("panorama_image", panorama_image, width= 2560, height=800)
        show_img("match_img", match_img)
        key= cv2.waitKey(1)
        if key==27:
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__=='__main__':
    main()