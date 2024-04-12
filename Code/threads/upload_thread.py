from PyQt5 import QtGui
from PyQt5.QtCore import QThread, pyqtSignal
import cv2


class WorkerThread(QThread):
    # define custom signals to communicate with the main thread
    video_info_ready = pyqtSignal(str)
    frame_image_ready = pyqtSignal(QtGui.QImage)

    def __init__(self, path):
        super().__init__()
        self.path = path

    def run(self):
        info = """"""
        title = self.path.split("/")
        title = title[-1].split(".")[0]
        info += f"<strong>Title: </strong> {title}<br />"

        cap = cv2.VideoCapture(self.path)

        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        # Calculate duration of video in seconds
        duration_sec = frame_count / fps
        info += f"<strong>Duration: </strong> {duration_sec:.2f} <br />" + f"<strong>FPS: </strong>{fps}\n" + f"<strong>Location: </strong> {self.path} <br />"
        info += f"<strong>Frames: </strong> {frame_count} <br />"

        self.video_info_ready.emit(info)

        _, frame = cap.read()
        
        ret, frame = cap.read()  
        # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  
        image = QtGui.QImage(
            frame,
            frame.shape[1],
            frame.shape[0],
            QtGui.QImage.Format_RGB888
        )
        cap.release()
        self.frame_image_ready.emit(image)
