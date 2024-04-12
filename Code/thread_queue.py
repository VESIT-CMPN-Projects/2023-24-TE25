# importing required libraries
import cv2
import time
from threading import Thread  # library for implementing multi-threaded processing
import queue

#importing required libraries for YOLO Implementation
import torch
import os
import pandas as pd
import csv

#### YOLO Model Load and YOLO Model Parameter Tweaking

# Provide the link for the weights file of the custom trained YOLO Model trained on custom dataset.
model = torch.hub.load('ultralytics/yolov5', 'custom', '../V2_YOLOv5Character-20230224T134754Z-001/YOLOv5Character/yolov5/runs/train/exp3/weights/best.pt')  # custom trained model
model.conf=0.50
model.iou=0.05
model.multi_label = False
model.max_det = 18

#### YOLO Model Load and YOLO Model Parameter Tweaking Done


# defining a helper class for implementing multi-threaded processing


class WebcamStream:
    def __init__(self, stream_id=0):
        self.stream_id = stream_id   # default is 0 for primary camera
        self.q = queue.Queue()

        # opening video capture stream
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

        # self.stopped is set to False when frames are being read from self.vcap stream
        self.stopped = True

        # reference to the thread for reading next available frame from input stream
        self.t = Thread(target=self.update, args=())
        # daemon threads keep running in the background while the program is executing
        self.t.daemon = True

    # method for starting the thread for grabbing next available frame in input stream
    def start(self):
        self.stopped = False
        self.t.start()

    # method for reading next frame
    def update(self):
        while True:
            ret, frame = self.vcap.read()
            if not ret:
                break
            if not self.q.empty():
                try:
                    self.q.get_nowait()   # discard previous (unprocessed) frame
                    # print('emptying the queue')
                except queue.Empty:
                    print("empty")
                    pass
            self.q.put(frame)
            # print(f'Length:{self.q.qsize()}')
            # print("incoming frame put in queue")
        # while True:
        #     if self.stopped is True:
        #         break
        #     self.grabbed, self.frame = self.vcap.read()
        #     if self.grabbed is False:
        #         print('[Exiting] No more frames to read')
        #         self.stopped = True
        #         break
        # self.vcap.release()

    # method for returning latest read frame
    def read(self):
        # print('waiting')
        frame = self.q.get()
        # print("Got frame")
        return frame
        # return self.frame

    # method called to stop reading frames
    def stop(self):
        self.stopped = True


# initializing and starting multi-threaded webcam capture input stream
# stream_id = 0 is for primary camera
webcam_stream = WebcamStream(
    stream_id='rtsp://Guru:Guru1@192.168.29.7:8080/h264_pcm.sdp')
webcam_stream.start()

# processing frames in input stream
num_frames_processed = 0
start = time.time()
while True:
    if webcam_stream.stopped is True:
        break
    else:
        frame = webcam_stream.read()
        # replace next 2 lines with YOLO processing
        # adding a delay for simulating time taken for processing a frame
        

        #### YOLO MODEL Implementation and Combining Digits Algorithm.

        ## YOLO MODEL pre-processing, extracting and predictions done here.

        # OpenCV uses BGR as its default colour order for images, matplotlib uses RGB.
        # When you display an image loaded with OpenCv in matplotlib the channels will be back to front.
        # So below step is necessary for this reason.

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        

        cv2.imshow('frame', frame)
        cv2.imwrite("frame_folder/frame"+str(num_frames_processed)+".jpg", frame)


        # Inference
        results = model(frame, size = 960)

        # Results
        # Uncomment the below line if you want to show bounding boxes around the digits
        # in the image and display it.

        # results.show()  # or .show(), .save(), .crop(), .pandas(), etc.

        #Sort predicted bounding boxes based on the values of x coordinate of the boxes
        output_table = results.pandas().xyxy[0].sort_values('xmin')  # im predictions (pandas)


        # Print the co-ordinates of the custom object's bounding boxes along with the custom object's
        # confidence score and class name.

        # print(output_table)

        # To write the test image predicted output in the .csv file
        test_output = pd.DataFrame(output_table)
        test_output.to_csv('Test_Output_Predicted_Annotations/' + 'output.csv')

        # To read the created .csv file
        test_output_read = pd.read_csv('Test_Output_Predicted_Annotations/' + 'output.csv')

        # total no. of records(each record corresponds to one digits) in the file
        size_of_table = test_output_read['class'].size
        # print("Total number of digits : ", size_of_table)


        if(size_of_table == 0):

            # If there are no digits present in the image
            # (i.e. if there are no custom object's present in the image).

            ## CSV sheet to write NA if no digits present in the image.

            print("No Digits detected.")
            field_names = ['Display_1', 'Display_2', 'Display_3', 'Display_4']
            dict = {"Display_1":"NA", "Display_2":"NA", "Display_3":"NA", "Display_4":"NA"}
            with open('Test_Output_Predicted_Annotations/Predicted_Values.csv', 'a') as csv_file:
                dict_object = csv.DictWriter(csv_file, fieldnames=field_names) 
        
                dict_object.writerow(dict)
        else:

            # If there are digits present in the image
            # (i.e. if there are custom object's present in the image).


            ## Algorithm (Logic) to Combine digits to create a single valued number.
            ## Algorithm capable to Combine digits from almost all types of display resolutions and sizes.

            print("Digits detected.")

            result = ["", "", "", ""]
            c = 0
            digits = []

            index1=0
            index2=0
            index3=0
            # print("Done")

            # for i in range(size_of_table):
            #     print(test_output_read['xmin'][i], test_output_read['ymin'][i], test_output_read['xmax'][i], test_output_read['ymax'][i], test_output_read['confidence'][i], test_output_read['class'][i])
            for i in range(size_of_table-1):
                digits.append(test_output_read['class'][i])

            # print("Done")
            
            max_dist = 0
            for i in range(size_of_table-1):
                if(test_output_read['xmin'][i+1] - test_output_read['xmax'][i] > max_dist):
                    max_dist = test_output_read['xmin'][i+1] - test_output_read['xmax'][i]
                    index2 = i;
            # print("Done")
            
            i=0
            while(i < index2):
                if(test_output_read['xmin'][index2] - test_output_read['xmax'][i] > 0.34*max_dist):
                    index1 = i;
                i = i+1
            # print("Done")
            
            i = size_of_table-1
            while (i > index2):
                if(test_output_read['xmin'][i] - test_output_read['xmax'][index2] > 1.125*max_dist):
                    index3 = i;
                i = i-1
            # print("Done")
            
            i = 0
            c = 0
            while(i<=index1):
                result[c] = result[c] + str(test_output_read['class'][i])
                i = i+1
            # print("Done")

            c = 1
            while(i<=index2):
                result[c] = result[c] + str(test_output_read['class'][i])
                i = i+1
            # print("Done")

            c = 2
            while(i<=index3):
                result[c] = result[c] + str(test_output_read['class'][i])
                i = i+1
            # print("Done")

            c = 3
            while(i<size_of_table):
                result[c] = result[c] + str(test_output_read['class'][i])
                i = i+1

            # print("Done")
            # print(index1)
            # print(index2)
            # print(index3)


            # print("First Value : ", result[0]);
            # print("Second Value : ", result[1]);
            # print("Third Value : ", result[2]);
            # print("Fourth Value : ", result[3]);
            print("Done")
            # print(test_output_read['xmin'][i], test_output_read['ymin'][i], test_output_read['xmax'][i], test_output_read['ymax'][i]) 



            ## CSV sheet which contains all the outputs from the testing set.

            field_names = ['Display_1', 'Display_2', 'Display_3', 'Display_4']
            dict = {"Display_1":result[0], "Display_2":result[1], "Display_3":result[2], "Display_4":result[3]}
            with open('Test_Output_Predicted_Annotations/Predicted_Values.csv', 'a') as csv_file:
                dict_object = csv.DictWriter(csv_file, fieldnames=field_names) 
            
                dict_object.writerow(dict)


        #### YOLO Model and Algorithm for Combining the digits and writing it in the .csv file
        #### working and implementation Done.



        # time.sleep(delay)
        num_frames_processed += 1
        os.remove("frame_folder/frame"+str(num_frames_processed-1)+".jpg")
        key = cv2.waitKey(1)
        if key == ord('q'):
            break
end = time.time()
webcam_stream.stop()  # stop the webcam stream

# printing time elapsed and fps
elapsed = end-start
fps = num_frames_processed/elapsed
print("FPS: {} , Elapsed Time: {} , Frames Processed: {}".format(
    fps, elapsed, num_frames_processed))

# closing all windows
cv2.destroyAllWindows()