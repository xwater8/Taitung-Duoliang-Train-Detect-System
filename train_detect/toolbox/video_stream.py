# -*- coding: utf-8 -*-
"""
Video stream capture utilities
"""
import cv2
import numpy as np
import time
from threading import Thread, Lock
from time import sleep


class IpcamCapture:
    """
    Simplified IP camera capture class
    Supports software decoding only for rtsp, webcam, and video files
    """
    max_retry_connect_times = -1
    retry_connect_sec = 5
    
    def __init__(self, URL, use_soft_decoder=True):
        """
        Initialize camera capture (software decoder only)
        
        Args:
            URL(str): rtsp, webcam, or video path
            use_soft_decoder(bool): Always use software decoder (default True)
        """
        self.read_lock = Lock()
        self.frame = None
        self.isstop = False
        self.URL = URL
        self.capture = None
        self.use_gstreamer = False
        self.count_reconnect = 0
        
        # Connect the camera
        self._connect()
        
        # Camera image parameters
        self.videoSize_wh = self._get_videoSizeWH_from_capture(self.capture)
        self.FPS = self.capture.get(cv2.CAP_PROP_FPS)
        if self.FPS > 60 or int(self.FPS) == 0:
            self.FPS = 30
        self.grab_time = (1 / self.FPS) * 0.5
        
        self.black = self._create_black_img()
        print(f"Camera width, height and fps: {self.videoSize_wh} {self.FPS}\n")

    def _get_videoSizeWH_from_capture(self, capture):
        """Get video width and height from capture"""
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        return (width, height)

    def _create_black_img(self):
        """Create black image for connection failure"""
        black_img = np.zeros((self.videoSize_wh[1], self.videoSize_wh[0], 3), dtype=np.uint8)
        return black_img

    def _connect(self):
        """Connect to camera using software decoder"""
        print(f"Connecting to {self.URL} using software decoder")
        self.capture = cv2.VideoCapture(self.URL)
        self.use_gstreamer = False
        self.status = True
        
        if not self.capture.isOpened():
            print(f"{self.URL} can't be opened")
            print(f"Please check the camera is connected: {self.URL}")
            self.capture.release()
            self.status = False

    def start(self):
        """Start the capture thread"""
        self.thread = Thread(target=self._queryframe, args=())
        print(f'{self.URL} start')
        self.thread.daemon = True
        self.thread.start()
        sleep(1)

    def release(self):
        """Release the capture"""
        if self.capture:
            self.isstop = True
            self.capture.release()
            print(f'{self.URL} stopped')
            print('camera stopped!')
        else:
            print('Capture is not initialized, cannot release.')

    def read(self):
        """Read frame from capture"""
        try:
            if self.status == False:
                return self.status, self.black.copy()
            
            if not self.use_gstreamer:
                self.read_lock.acquire()
                self.status, self.frame = self.capture.retrieve()
                self.read_lock.release()
            else:
                self.status, self.frame = self.capture.read()

            if self.frame is not None:
                return self.status, self.frame.copy()
            else:
                return self.status, self.black.copy()
        except Exception as e:
            print(e)
            return self.status, self.black.copy()

    def isOpened(self):
        """Check if capture is opened"""
        return self.capture.isOpened()

    def _queryframe(self):
        """Internal thread for grabbing frames"""
        while not self.isstop:
            if not self.use_gstreamer:
                self.read_lock.acquire()
                self.status = self.capture.grab()
                self.read_lock.release()
            
            sleep(self.grab_time)
            self._reconnect()

    def _reconnect(self):
        """Reconnect if connection is lost"""
        if not self.status:
            print(f"Camera status is {self.status}. Wait for {IpcamCapture.retry_connect_sec} second to reconnect")
            for sec_count in range(IpcamCapture.retry_connect_sec):
                sleep(1)
                print(f'{sec_count + 1} second passed', '.' * sec_count, end='\r')
            
            if (IpcamCapture.max_retry_connect_times < 0) or (self.count_reconnect < IpcamCapture.max_retry_connect_times):
                self.capture.release()
                self.count_reconnect += 1
                self._connect()
                print(f"Camera reconnect retry({self.count_reconnect}/{IpcamCapture.max_retry_connect_times}): {self.URL}")
                print(f"Camera connect: {self.capture.isOpened()}")
                
                if self.capture.isOpened():
                    print(f"Camera width, height: {self.videoSize_wh} and fps: {self.FPS}\n")
                    self.count_reconnect = 0
            else:
                print(f"Usually Lose Connection: {self.URL}")
                self.release()
