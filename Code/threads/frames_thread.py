import sys
import shutil
import numpy as np
import os
from PyQt5 import QtGui
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel
from PyQt5.QtCore import QThread, pyqtSignal
import cv2


class FramesThread(QThread):
    # define custom signals to communicate with the main thread
    frames_ready = pyqtSignal(list)

    def __init__(self, path):
        super().__init__()
        self.path = path
        self.frames_directory = os.path.join(os.getcwd(), 'frames')

    def run(self):
        print("Creating frames...")
        file_name = self.path.split("/")[-1]
        file_name = file_name.split(".")[0]
        directory = os.path.join(self.frames_directory, file_name)
        #If the directory already exists then delete it 
        #Else create it and populate it with frames
        if (os.path.isdir(directory)):
            shutil.rmtree(directory)
        os.makedirs(directory)
        #Populating frames
        capture = cv2.VideoCapture(self.path)
        fps = capture.get(cv2.CAP_PROP_FPS)
        counter = 0
        
        while True:
            if counter == 200:
                break
            success, frame = capture.read()
            if not success:
                break
            # Deleting low resolution frame
            if np.mean(frame) < 25:
                print("Removed the frame")
                continue
            counter += 1
            cv2.imwrite(os.path.join(directory, f'{counter/fps}.jpg'), frame)
        capture.release()
        print(f"{counter} frames created successfully!")
        self.frames_ready.emit([True, directory])
