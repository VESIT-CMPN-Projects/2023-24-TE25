# importing required libraries
import cv2
from threading import Thread  # library for implementing multi-threaded processing
import queue
import numpy as np

#importing required libraries for YOLO Implementation
import torch
import os
import datetime
import pandas as pd
import csv

from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot
from .d_thread import DThread

class IpThread(QThread):
    new_frame = pyqtSignal(list)
    detection_completed = pyqtSignal(bool)
    def __init__(self, model, label_id, stream_id = 0):
        super().__init__()
        self.stream_id = stream_id
        self.model = model
        self.stopped = False
        self.label_id = label_id
        self.output_path = os.path.join(os.getcwd(), 'output', 'realtime-predictions.csv')
        # print(self.output_path)
        self.test_path = os.path.join(os.getcwd(), '.intermediate', 'test_dataset.csv')
        self.start_detections = False   
        self.q = queue.Queue()
        # self.timestamp = None
        self.detections = DThread(self.q, self.label_id, self.model)
        

    
    def run(self):
        self.vcap = cv2.VideoCapture(self.stream_id)
        # self.vcap.set(cv2.CAP_PROP_BUFFERSIZE, 0)
        if self.vcap.isOpened() is False:
            print("[Exiting]: Error accessing webcam stream.")
            exit(0)
        fps_input_stream = int(self.vcap.get(5))
        print("FPS of webcam hardware/input stream: {}".format(fps_input_stream))
            
        # reading a single frame from vcap stream for initializing
        self.grabbed, self.frame = self.vcap.read()
        if self.grabbed is False:
            print('[Exiting] No more frames to read')
            exit(0)
            
        while True:
            if self.stopped:
                break
            ret, self.frame = self.vcap.read()
            if not ret:
                break
            if not self.q.empty():
                try:
                    self.q.get_nowait()   # discard previous (unprocessed) frame
                    # print('emptying the queue')
                except queue.Empty:
                    print("empty")
            self.q.put(self.frame)
            self.new_frame.emit([self.frame, self.label_id])
            if self.start_detections:
                self.detections.start()
    
    def start_detection(self):
        self.start_detections = True        
            
    def read(self):
        return self.q.get()
    
    def stop(self):
        self.stopped = True
        

