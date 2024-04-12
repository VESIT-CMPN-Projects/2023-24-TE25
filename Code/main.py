import os
from pyexpat import model
from random import choice
import shutil
import subprocess
import sys

import csv
import cv2



from threads.upload_thread import WorkerThread
from threads.frames_thread import FramesThread
from threads.detection_thread import DetectionThread
from threads.ip_thread import IpThread
from db import add_stream_links, get_stream_links

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QPropertyAnimation, QFileSystemWatcher
from PyQt5.QtWidgets import QLabel, QDialog, QApplication, QFileDialog, QTableWidget, QSizePolicy, QLineEdit, QRadioButton
from PyQt5.QtWidgets import QPushButton, QFrame, QMainWindow, QStackedWidget, QDesktopWidget, QInputDialog, QGridLayout, QVBoxLayout
from PyQt5 import uic
from ui import resources
import labelImg

# Comment out the below line in case you are running the filef for first time
# os.system("Pyrcc5 ./ui/resources.qrc -o ./ui/resources.py")


class WirelessExtraction(QMainWindow):
    def __init__(self, model, user_id):
        super(WirelessExtraction, self).__init__()
        uic.loadUi("./ui/interface.ui", self)
        screen = QDesktopWidget().screenGeometry()
        self.screen_width = screen.width()
        self.screen_height = screen.height()
        self.output_path = os.path.join(
            os.getcwd(), 'output', 'predictions.csv')
        self.realtime_path = os.path.join(os.getcwd(), 'output')
        print(f"{self.screen_width}x{self.screen_height}")
        self.setWindowTitle("Wireless Extraction")
        self.frames_directory = os.path.join(os.getcwd(), 'frames')

        self.model = model
        self.user_id = user_id
        print(self.user_id)
        self.paths_train = {
            'full_dataset': None,
            'train_images': None,
            'train_labels': None,
            'val_images': None,
            'val_labels': None,
        }
        self.xmls = []
        self.imgs = []

        # pages index
        self.page_controller = self.findChild(
            QStackedWidget, 'page_controller')
        self.home_page_index = 0
        self.history_page_index = 1
        self.guidelines_page_index = 2
        self.training_page_index = 3
        self.about_page_index = 4
        self.signout_page_index = 5

        self.home_page_controller = self.findChild(
            QStackedWidget, 'home_page_controller')
        self.connect_ip_index = 1
        self.upload_page_index = 2

        self.detection_page_controller = self.findChild(
            QStackedWidget, 'detection_controller')
        self.tables_page_index = 1

        self.home_menu_button = self.findChild(QPushButton, 'home_button')
        self.annotate_menu_button = self.findChild(
            QPushButton, 'history_button')
        self.guidelines_menu_button = self.findChild(
            QPushButton, 'guidelines_button')
        self.training_menu_button = self.findChild(
            QPushButton, 'training_button')
        self.about_menu_button = self.findChild(QPushButton, 'info_button')
        self.signout_menu_button = self.findChild(
            QPushButton, 'signout_button')
        self.settings_menu_button = self.findChild(
            QPushButton, 'settings_button')

        self.settings_menu_button.clicked.connect(
            lambda: self.page_controller.setCurrentIndex(self.history_page_index))

        self.grid_layout = self.findChild(QGridLayout, 'gridLayout_2')
        self.label_id = -1
        self.tifr_logo = self.findChild(QLabel, 'label_11')
        self.ves_logo = self.findChild(QLabel, 'label_12')
        # self.tifr_logo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # self.ves_logo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.home_menu_button.clicked.connect(self.go_to_home)
        self.annotate_menu_button.clicked.connect(
            lambda: subprocess.Popen(['labelimg']))
        self.guidelines_menu_button.clicked.connect(
            lambda: self.page_controller.setCurrentIndex(self.guidelines_page_index))
        self.training_menu_button.clicked.connect(
            lambda: self.page_controller.setCurrentIndex(self.training_page_index))
        self.about_menu_button.clicked.connect(
            lambda: self.page_controller.setCurrentIndex(self.about_page_index))
        self.signout_menu_button.clicked.connect(self.signout)

        # toggle button
        self.toggle_menu_button = self.findChild(QPushButton, 'toggle_button')

        self.toggle_menu_button.clicked.connect(self.toggle_menu)

        # Sidebar
        self.sidebar = self.findChild(QFrame, 'side_bar')

        # homepage
        self.connect_ip_button = self.findChild(QPushButton, 'ipcam_button')
        self.upload_button = self.findChild(QPushButton, 'upload_button')

        self.frame_image = self.findChild(QLabel, 'frame_image')
        self.video_info = self.findChild(QLabel, 'video_info')

        # self.ip_window_label = self.findChild(QLabel, 'ip_window_1')
        self.ip_window_label = []

        self.detection_table = self.findChild(QTableWidget, 'detected_values')
        self.detection_table.setStyleSheet("font: 10pt 'Segoe UI'")
        self.detection_table.setStyleSheet(
            "QTableView::item:selected { background-color: #0078d7; color: #fff; }")

        self.detection_table.setAlternatingRowColors(True)
        self.detection_table.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.Stretch)

        self.realtime_detection_table = self.findChild(
            QTableWidget, 'realtime_table')

        self.connect_ip_button.clicked.connect(self.connect_ipcam)
        self.upload_button.clicked.connect(self.upload)

        self.go_back_watch_btn = self.findChild(QPushButton, 'go_back')
        self.go_back_watch_btn.clicked.connect(self.go_back_watch)

        self.ipcam_thread = []
        self.start_detection_ip = self.findChild(
            QPushButton, 'start_detection_camera')
        self.stop_processing_button = self.findChild(
            QPushButton, 'stop_processing')
        self.stop_processing_all = self.findChild(
            QPushButton, 'stop_processing_all')

        self.stream_link_button = self.findChild(QPushButton, 'stream_link')
        self.stream_link_button.clicked.connect(self.set_stream_link)

        self.go_back_detection = self.findChild(QPushButton, 'go_back_camera')

        self.start_detection_ip.clicked.connect(self.start_detection_realtime)
        self.stop_processing_button.clicked.connect(self.stop_processing_ipcam)
        self.stop_processing_all.clicked.connect(self.stop_processing_ipcam)
        self.go_back_detection.clicked.connect(self.connect_ipcam)

        self.findChild(QPushButton, 'full_dataset_btn').clicked.connect(
            self.set_full_dataset_path)
        self.set_train_image_path()
        self.set_train_label_path()
        self.set_val_label_path()
        self.set_val_image_path()
        self.start_training_btn = self.findChild(QPushButton, 'start_training')
        self.resume_training_btn = self.findChild(
            QPushButton, 'resume_training')
        self.start_training_btn.clicked.connect(self.start_training_model)
        self.resume_training_btn.clicked.connect(self.resume_training_model)

    def __contains__(self, attribute):
        return hasattr(self, attribute)

    def go_back_watch(self):
        # print(self.detection_page_controller.currentIndex())
        print("Go back button clicked")
        self.detection_page_controller.setCurrentIndex(0)

    # To get the right path for training data
    def browse_files(self):
        return QFileDialog.getExistingDirectory(self, 'Select directory')

    def set_stream_link(self):
        self.stream_dialog = QDialog(self)
        self.stream_dialog.setWindowTitle("Add RTSP Stream link")
        layout = QVBoxLayout(self)
        self.stream_dialog.setLayout(layout)
        self.stream_text = QLineEdit("")
        self.add_streamlink_btn = QPushButton("Add Stream")
        self.add_streamlink_btn.clicked.connect(self.insert_stream)
        layout.addWidget(self.stream_text)
        layout.addWidget(self.add_streamlink_btn)

        self.stream_dialog.exec()

    def insert_stream(self):
        try:
            add_stream_links(self.user_id, self.stream_text.text())
        except Exception as e:
            print(e)
        self.stream_dialog.reject()

    def set_full_dataset_path(self):
        path = self.browse_files()
        self.paths_train["full_dataset"] = path
        self.findChild(QLabel, 'full_dataset_path').setText(path)

    def set_train_image_path(self):
        path = os.path.join(os.getcwd(), 'dataset', 'images', 'train')
        self.paths_train["train_images"] = path
        self.findChild(QLabel, 'train_image_path').setText(path)

    def set_train_label_path(self):
        path = os.path.join(os.getcwd(), 'dataset', 'labels', 'train')
        self.paths_train["train_labels"] = path
        self.findChild(QLabel, 'train_label_path').setText(path)

    def set_val_image_path(self):
        path = os.path.join(os.getcwd(), 'dataset', 'images', 'val')
        self.paths_train["val_images"] = path
        self.findChild(QLabel, 'val_image_path').setText(path)

    def set_val_label_path(self):
        path = os.path.join(os.getcwd(), 'dataset', 'labels', 'val')
        self.paths_train["val_labels"] = path
        self.findChild(QLabel, 'val_label_path').setText(path)

    def file_splitter(self, crs_path):
        # setup ratio (val ratio = rest of the files in origin dir after splitting into train and test)
        train_ratio = 0.9
        val_ratio = 0.1
        # total count of imgs
        totalImgCount = len(os.listdir(crs_path))/2

        # soring files to corresponding arrays
        for (dirname, dirs, files) in os.walk(crs_path):
            for filename in files:
                if filename.endswith('.txt'):
                    self.xmls.append(filename)
                else:
                    self.imgs.append(filename)

        # counting range for cycles
        print("Total images count: ", totalImgCount)
        countForTrain = int(len(self.imgs) * train_ratio)
        countForVal = int(len(self.imgs) * val_ratio)
        print("training images are: ", countForTrain)
        print("Validation images are: ", countForVal)
        return countForTrain, countForVal

    def mix_data(self, train_image_path, train_label_path, val_image_path, val_label_path, crs_path):
        countForTrain, countForVal = self.file_splitter(crs_path=crs_path)

        # cycle for train dir
        for _ in range(countForTrain):
            # get name of random image from origin dir
            fileJpg = choice(self.imgs)
            # get name of corresponding annotation file
            fileXml = fileJpg[:-4] + '.txt'

            # move both files into train dir
            shutil.copy(os.path.join(crs_path, fileJpg),
                        os.path.join(train_image_path, fileJpg))
            shutil.copy(os.path.join(crs_path, fileXml),
                        os.path.join(train_label_path, fileXml))

            # remove files from arrays
            self.imgs.remove(fileJpg)
            self.xmls.remove(fileXml)

        # cycle for test dir
        for _ in range(countForVal):
            # get name of random image from origin dir
            fileJpg = choice(self.imgs)
            # get name of corresponding annotation file
            fileXml = fileJpg[:-4] + '.txt'

            # move both files into train dir
            shutil.copy(os.path.join(crs_path, fileJpg),
                        os.path.join(val_image_path, fileJpg))
            shutil.copy(os.path.join(crs_path, fileXml),
                        os.path.join(val_label_path, fileXml))

            # remove files from arrays
            self.imgs.remove(fileJpg)
            self.xmls.remove(fileXml)

        # rest of files will be validation files, so rename origin dir to val dir
        # os.rename(crsPath, valPath)
        shutil.move(crs_path, val_image_path)

    def start_training_model(self):
        self.mix_data(self.paths_train["train_images"], self.paths_train["train_labels"],
                      self.paths_train["val_images"], self.paths_train["val_labels"], self.paths_train["full_dataset"])
        self.train_yolo()

    def train_yolo(self):
        os.chdir("yolov5")
        print(os.getcwd())
        command = "python train.py --img 960 --batch 16 --epochs 1 --data dataset.yaml --weights yolov5s.pt --cache"
        subprocess.Popen(command.split(), shell=True)
        os.chdir("../")

    def resume_training_model(self):
        os.chdir("yolov5")
        path, _ = QFileDialog.getOpenFileName(
            self, 'Open pth File', os.path.expanduser("~"), "PTH Files (*.pt)")
        print(path)
        command = f"python train.py --img 960 --batch 16 --epochs 100 --data dataset.yaml --weights yolov5s.pt --cache --resume {path}"
        subprocess.Popen(command.split(), shell=True)
        os.chdir("../")

    def signout(self):
        from login import LoginWindow
        self.close()
        self.login_window = LoginWindow()
        self.login_window.show()

    def start_detection_realtime(self):
        for _ in range(len(self.ipcam_thread)):
            self.ipcam_thread[_].start_detection()
        # with open("realtime_predicted.csv", "w"):
        #     pass

    def watch_changes(self, idx):
        self.detection_page_controller.setCurrentIndex(self.tables_page_index)
        if 'realtime-predictions' not in self.realtime_path:
            self.realtime_path += f"/realtime-predictions_{idx}.csv"
            print(self.realtime_path)

        self.ip_watcher = QFileSystemWatcher([self.realtime_path])
        self.ip_watcher.fileChanged.connect(lambda: self.update_table(
            self.realtime_path, self.realtime_detection_table))

    def delete_widget(self, widget):
        widget.deleteLater()
        self.ip_window_label.remove(widget)

    def stop_processing_ipcam(self):
        for _ in range(len(self.ipcam_thread)):
            self.ipcam_thread[_].stop()
            self.ipcam_thread[_].wait()

        # for _ in self.ip_window_label:
        #     self.delete_widget(_)

        for file in os.listdir(os.path.join(os.getcwd(), '.intermediate')):
            directory = os.path.join(os.getcwd(), '.intermediate', file)
            if os.path.isdir(directory):
                if len(os.listdir(directory)) == 0:
                    continue
                path = os.listdir(os.path.join(
                    os.getcwd(), '.intermediate', file))[0]
                path = os.path.join(os.getcwd(), '.intermediate', file, path)
                img = cv2.imread(path)
                height, width, depth = img.shape
                fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
                # fourcc = cv2.VideoWriter_fourcc(*'X264')/
                video = cv2.VideoWriter(os.path.join(
                    os.getcwd(), 'output', 'video', f'{file}.mp4'), fourcc, 1.0, (width, height))
                for img_name in os.listdir(os.path.join(os.getcwd(), '.intermediate', file)):
                    img_path = os.path.join(
                        os.getcwd(), '.intermediate', file, img_name)
                    # print(img_path)
                    frame = cv2.imread(img_path)
                    video.write(frame)
                video.release()
                # self.home_page_controller(0)
                shutil.rmtree(os.path.join(os.getcwd(), '.intermediate', file))

    def go_to_home(self):
        self.page_controller.setCurrentIndex(self.home_page_index)
        self.home_page_controller.setCurrentIndex(self.home_page_index)

    def connect_ipcam(self):
        if self.home_page_controller.currentIndex() != 1:
            print('Not one')
            self.home_page_controller.setCurrentIndex(1)
        self.dlg = QDialog(self)
        self.dlg.setWindowTitle("Select RTSP stream:")
        layout = QVBoxLayout(self)
        self.dlg.setLayout(layout)
        links = get_stream_links(self.user_id)
        self.rtsp_radiobuttons = []
        for link in links:
            btn = QRadioButton(link)
            self.rtsp_radiobuttons.append(btn)
        # self.rtsp_1 = QRadioButton("rtsp://192.168.4.101:8554/mjpeg/1")
        # self.rtsp_2 = QRadioButton("rtsp://192.168.4.103:8554/mjpeg/1")
        self.rtsp_1 = QRadioButton("rtsp://192.168.4.101:8554/mjpeg/1")
        self.rtsp_2 = QRadioButton("rtsp://192.168.4.103:8554/mjpeg/1")
        self.input_stream = QLineEdit("")
        submit = QPushButton("Submit")
        cancel = QPushButton("Cancel")

        self.dlg.setStyleSheet("""QDialog {
            background-color: #F2F2F2;
            border: 1px solid #CCCCCC;
            border-radius: 5px;
            padding: 10px;
            }

            QRadioButton {
            font-size: 14px;
            color: #333333;
            }

            QLineEdit {
            font-size: 14px;
            color: #333333;
            background-color: #FFFFFF;
            border: 1px solid #CCCCCC;
            border-radius: 5px;
            padding: 5px;
            }

            QRadioButton::indicator {
            width: 20px;
            height: 20px;
            border-radius: 10px;
            border: 2px solid #CCCCCC;
            }

            QRadioButton::indicator:checked {
            background-color: #555555;
            border-color: #555555;
            }

            QRadioButton::indicator:hover {
            border-color: #555555;
            }

            QPushButton {
            background-color: #555555;
            color: #FFFFFF;
            border: none;
            border-radius: 5px;
            padding: 5px;
            }

            QPushButton:hover {background-color: #333333;}""")

        for btn in self.rtsp_radiobuttons:
            layout.addWidget(btn)

        # layout.addWidget(self.rtsp_1)
        # layout.addWidget(self.rtsp_2)
        layout.addWidget(self.input_stream)
        layout.addWidget(submit)
        layout.addWidget(cancel)

        submit.clicked.connect(self.submit_streamlink)
        cancel.clicked.connect(lambda: self.dlg.reject())

        self.dlg.exec()
        # input_stream, ok = QInputDialog.getText(
        #     self, 'IP Address', 'Enter IP Address: ')
        # if ok:
        #     self.set_ipcam_position(input_stream)

    def submit_streamlink(self):
        link = next(
            (btn.text()
             for btn in self.rtsp_radiobuttons if btn.isChecked()), None
        )
        if link is None:
            link = self.input_stream.text()
        # if self.rtsp_1.isChecked():
        #     link = self.rtsp_1.text()
        # elif self.rtsp_2.isChecked():
        #     link = self.rtsp_2.text()
        # else:
        #     link = self.input_stream.text()
        self.set_ipcam_position(link)
        self.dlg.reject()

    def set_ipcam_position(self, input_stream):
        print(input_stream)
        print("Ip button camera clicked")
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(QLabel())
        button = QPushButton("Watch changes")
        button.setFont(QFont("Segoe UI", 10))
        button.setStyleSheet(
            "QPushButton {background-color: rgb(217, 217, 217); padding: 16px; padding-left: 24px; padding-right: 24px; border-radius: 12px; margin-right: 12px;} QPushButton:hover { background-color: #BBBBBB; border: 1px solid black;}")
        layout.addWidget(button)
        widget.setLayout(layout)
        self.ip_window_label.append(widget)
        # self.ip_window_label.append(QLabel())
        if len(self.ip_window_label) == 1:
            self.grid_layout.addWidget(self.ip_window_label[-1], 0, 0)
        elif len(self.ip_window_label) == 2:
            self.grid_layout.addWidget(self.ip_window_label[-1], 0, 1)
        elif len(self.ip_window_label) == 3:
            self.grid_layout.addWidget(self.ip_window_label[-1], 1, 0)
        else:
            self.grid_layout.addWidget(self.ip_window_label[-1], 1, 1)
        # rtsp://192.168.0.102:8000/h264_pcm.sdp
        self.label_id += 1
        self.ipcam_thread.append(
            IpThread(self.model, label_id=self.label_id, stream_id=input_stream))
        self.ipcam_thread[self.label_id].new_frame.connect(self.update_frame)
        self.ipcam_thread[self.label_id].start()

    def update_frame(self, data):
        frame = data[0]
        idx = data[1]
        # Convert BGR frame to RGB format for displaying in QLabel
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Create QImage from numpy array
        h, w, c = frame.shape
        bytesPerLine = c * w
        qImg = QtGui.QImage(frame.data, w, h, bytesPerLine,
                            QtGui.QImage.Format_RGB888)
        # Display QImage in QLabel
        self.ip_window_label[idx].layout().itemAt(
            0).widget().setPixmap(QtGui.QPixmap.fromImage(qImg))
        self.ip_window_label[idx].layout().itemAt(
            0).widget().setScaledContents(True)
        self.ip_window_label[idx].layout().itemAt(0).widget().setSizePolicy(
            QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.ip_window_label[idx].layout().itemAt(
            1).widget().clicked.connect(lambda: self.watch_changes(idx))

    def upload(self):
        print("Upload button clicked")
        self.load_directory()

    def load_directory(self):
        # home path
        self.home_page_controller.setCurrentIndex(self.upload_page_index)
        path, _ = os.path.expanduser("~"), "Video Files (*.mp4; *.mkv)"
        # training video info
        self.worker_thread = WorkerThread(path)
        # connect worker thread signals to slots in main thread
        self.worker_thread.video_info_ready.connect(
            self.update_video_info_label)
        self.worker_thread.frame_image_ready.connect(
            self.update_frame_image_label)
        self.worker_thread.start()
        self.frames_thread = FramesThread(path)
        self.frames_thread.frames_ready.connect(self.start_detections)
        self.frames_thread.start()

    def update_video_info_label(self, info):
        self.video_info.setText(info)

    def update_frame_image_label(self, image):
        self.frame_image.setPixmap(QtGui.QPixmap.fromImage(image))

    def start_detections(self, data):
        if data[0]:
            path = data[1]
            print(path)
            self.detector_thread = DetectionThread(path, self.model)
            self.detector_thread.start()
        self.detection_table.setRowCount(15)
        self.watcher = QFileSystemWatcher([self.output_path])
        self.watcher.fileChanged.connect(lambda: self.update_table(
            self.output_path, self.detection_table))

        # start new thread for detection

    def update_table(self, filename, table):
        with open(filename, 'r') as csvfile:
            reader = csv.reader(csvfile)
            rows = list(reader)

        # Clear table widget
        table.setRowCount(0)

        # Add rows to table widget
        for i, row in enumerate(rows):
            table.insertRow(i)
            for j, col in enumerate(row):
                item = QtWidgets.QTableWidgetItem(col)
                item.setFont(QFont("Segoe UI", 10))  # set font and font size
                # set horizontal alignment
                item.setTextAlignment(Qt.AlignCenter)
                table.setItem(i, j, item)
                # self.detection_table.setColumnWidth(j, -1)

    def toggle_menu(self):
        sidebar_width = self.sidebar.width()
        updated_width = 200 if sidebar_width == 55 else 55

        self.animation = QPropertyAnimation(self.sidebar, b"minimumWidth")
        self.animation.setDuration(250)
        self.animation.setStartValue(sidebar_width)
        self.animation.setEndValue(updated_width)
        self.animation.setEasingCurve(QtCore.QEasingCurve.InOutQuart)
        self.animation.start()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = WirelessExtraction(model,UserWarning)
    w.show()
    sys.exit(app.exec_())
