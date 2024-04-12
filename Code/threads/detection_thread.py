import os
import pandas as pd
import time
import csv
from PyQt5.QtCore import QThread, pyqtSignal


class DetectionThread(QThread):
    file_ready = pyqtSignal(bool)
    def __init__(self, path, model):
        super().__init__()
        self.path = path
        self.model = model
        self.output_path = os.path.join(os.getcwd(), 'output', 'predictions.csv')
        self.test_path = os.path.join(os.getcwd(), '.intermediate', 'test_dataset.csv')
        
    def run(self):  # sourcery skip: avoid-builtin-shadow
        print("Detecting frames...")
        frames_directory = os.listdir(self.path)
        self.model.conf=0.50
        self.model.iou=0.05
        self.model.multi_label = False
        self.model.max_det = 18

        for counter, image in enumerate(frames_directory):
            if counter  == 25:
                print(f"{counter} images detection completed")
                break
            # print(os.path.join(self.path, image))
            prediction = self.model(os.path.join(self.path, image), size=960)

            #Sort predicted bounding boxes based on the values of x coordinate of the boxes
            output_table = prediction.pandas().xyxy[0].sort_values('xmin')  # im predictions (pandas)
            temp_output = pd.DataFrame(output_table)
            temp_output.to_csv(self.test_path)

            temp_output = pd.read_csv(self.test_path)
            size_of_table = temp_output['class'].size

            # Logic Combine digits to create a single valued number
            result = ["", "", "", ""]
            c = 0
            digits = []

            index1=0
            index2=0
            index3=0

            for i in range(size_of_table-1):
                digits.append(temp_output['class'][i])


            max_dist = 0
            for i in range(size_of_table-1):
                if(temp_output['xmin'][i+1] - temp_output['xmax'][i] > max_dist):
                    max_dist = temp_output['xmin'][i+1] - temp_output['xmax'][i]
                    index2 = i;

            i=0
            while (i < index2):
                if(temp_output['xmin'][index2] - temp_output['xmax'][i] > 0.34*max_dist):
                    index1 = i;
                i += 1

            i = size_of_table-1
            while (i > index2):
                if(temp_output['xmin'][i] - temp_output['xmax'][index2] > 1.125*max_dist):
                    index3 = i;
                i -= 1

            i = 0
            c = 0
            while (i<=index1):
                result[c] = result[c] + str(temp_output['class'][i])
                i += 1

            c = 1
            while (i<=index2):
                result[c] = result[c] + str(temp_output['class'][i])
                i += 1

            c = 2
            while (i<=index3):
                result[c] = result[c] + str(temp_output['class'][i])
                i += 1

            c = 3
            while (i<size_of_table):
                result[c] = result[c] + str(temp_output['class'][i])
                i += 1

            field_names = ['File', 'Display_1', 'Display_2', 'Display_3', 'Display_4']
            dict = {"File": image,"Display_1":result[0], "Display_2":result[1], "Display_3":result[2], "Display_4":result[3]}
            with open(self.output_path, 'a', newline='') as csv_file:
                dict_object = csv.DictWriter(csv_file, fieldnames=field_names) 
                dict_object.writerow(dict)








        #     timestamps.append(str(image.split('.')[0]))
        #     region1.append(result[0])
        #     region2.append(result[1])
        #     region3.append(result[2])
        #     region4.append(result[3])
        #     # print(result)
        # print("Time taken: ", time.time() - start)
        # output = pd.DataFrame(data={'Timestamps': timestamps, 'Region-01': region1, 'Region-02': region2, 'Region-03': region3, 'Region-04': region4})
        # output.to_csv("predicted.csv", index=False)
        # print("Detection completed successfully!")
        # self.detection_info_ready.emit([True, self.path])

