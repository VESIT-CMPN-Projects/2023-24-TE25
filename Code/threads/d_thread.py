import datetime
import os
import pandas as pd
import time
import cv2
import csv
from PyQt5.QtCore import QThread, pyqtSignal

# cam-01-date
# 2023-04-10 13:53:23.885547.jpg
# 2023-04-10 13:53:23.885547.jpg
# 2023-04-10 13:53:23.885547.jpg
# 2023-04-10 13:53:23.885547.jpg


class DThread(QThread):
    def __init__(self, q, label_id, model):
        super().__init__()
        self.q = q
        self.label_id = label_id
        self.model = model
        self.model.conf = 0.50
        self.model.iou = 0.05
        self.model.multi_label = False
        self.model.max_det = 18
        self.timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.file_time = self.timestamp.replace(":", "_")
        self.file_time = self.file_time.replace(" ", "-")
        self.frames_directory = os.path.join(
            os.getcwd(), '.intermediate', f"cam-{self.label_id}-{str(self.file_time)}")

        self.output_path = os.path.join(
            os.getcwd(), 'output', f'realtime-predictions_{self.label_id}.csv')
        self.test_path = os.path.join(
            os.getcwd(), '.intermediate', f'test_dataset_{self.label_id}.csv')

        if not os.path.exists(self.frames_directory):
            os.makedirs(self.frames_directory)

    def run(self):
        self.frame = self.q.get()
        self.timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print("Detection module starting...")
        self.captured_frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1
        thickness = 2
        color = (0, 0, 255)  # BGR format

        # Get the size of the text
        text_size, _ = cv2.getTextSize(
            self.timestamp, font, font_scale, thickness)

        # Compute the position of the text
        text_x = self.frame.shape[1] - text_size[0] - 10
        text_y = self.frame.shape[0] - text_size[1] - 10
        cv2.putText(self.frame, self.timestamp, (text_x, text_y),
                    font, font_scale, color, thickness)
        img_name = self.timestamp.replace(":", "-")
        img_name = img_name.replace(" ", "_")
        cv2.imwrite(os.path.join(self.frames_directory,
                    f'{img_name}.png'), self.frame)
        result = self.model(self.captured_frame, size=960)
        print(result)

        output_table = result.pandas().xyxy[0].sort_values(
            'xmin')  # im predictions (pandas)
        temp_output = pd.DataFrame(output_table)
        temp_output.to_csv(self.test_path)

        temp_output = pd.read_csv(self.test_path)
        size_of_table = temp_output['class'].size

        field_names = ['Timestamp', 'Display_1',
                       'Display_2', 'Display_3', 'Display_4']
        if (size_of_table == 0):

            # If there are no digits present in the image
            # (i.e. if there are no custom object's present in the image).

            # CSV sheet to write NA if no digits present in the image.

            print("No Digits detected.")
            dict = {"Timestamp": "NA", "Display_1": "NA",
                    "Display_2": "NA", "Display_3": "NA", "Display_4": "NA"}
            with open(f'realtime_predicted_{self.label_id}.csv', 'a', newline='') as csv_file:
                dict_object = csv.DictWriter(csv_file, fieldnames=field_names)
        else:
            self.detect_digits(size_of_table, temp_output, field_names)

    # TODO Rename this here and in `detect_digits`
    def detect_digits(self, size_of_table, temp_output, field_names):
        result = ["", "", "", ""]
        c = 0
        digits = []

        index1 = 0
        index2 = 0
        index3 = 0

        for i in range(size_of_table-1):
            digits.append(temp_output['class'][i])

        max_dist = 0
        for i in range(size_of_table-1):
            if (temp_output['xmin'][i+1] - temp_output['xmax'][i] > max_dist):
                max_dist = temp_output['xmin'][i+1] - temp_output['xmax'][i]
                index2 = i

        i = 0
        while (i < index2):
            if (temp_output['xmin'][index2] - temp_output['xmax'][i] > 0.34*max_dist):
                index1 = i
            i += 1

        i = size_of_table-1
        while (i > index2):
            if (temp_output['xmin'][i] - temp_output['xmax'][index2] > 1.125*max_dist):
                index3 = i
            i -= 1

        i = 0
        c = 0
        while (i <= index1):
            result[c] = result[c] + str(temp_output['class'][i])
            i += 1

        c = 1
        while (i <= index2):
            result[c] = result[c] + str(temp_output['class'][i])
            i += 1

        c = 2
        while (i <= index3):
            result[c] = result[c] + str(temp_output['class'][i])
            i += 1

        c = 3
        while (i < size_of_table):
            result[c] = result[c] + str(temp_output['class'][i])
            i += 1

        dict = {"Timestamp": self.timestamp,
                "Display_1": result[0], "Display_2": result[1], "Display_3": result[2], "Display_4": result[3]}
        with open(self.output_path, 'a', newline='') as csv_file:
            dict_object = csv.DictWriter(csv_file, fieldnames=field_names)
            dict_object.writerow(dict)

        # self.detect_digits.emit(True)
