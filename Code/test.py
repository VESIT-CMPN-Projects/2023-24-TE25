import cv2
import os


for file in os.listdir(os.path.join(os.getcwd(), '.intermediate')):
    if os.path.isdir(os.path.join(os.getcwd(), '.intermediate', file)):
        # imgs = []
        # for x in :
        #     img = cv2.imread(os.path.join(
        #         os.getcwd(), '.intermediate', file, x))
        #     imgs.append(img)
        path = os.listdir(os.path.join(os.getcwd(), '.intermediate', file))[0]
        path = os.path.join(os.getcwd(), '.intermediate', file, path)
        img = cv2.imread(path)
        height, width,  depth = img.shape

        fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')

        # fourcc = cv2.VideoWriter_fourcc(*'MP4V')
        video = cv2.VideoWriter(os.path.join(
            os.getcwd(), 'test', f'{file}.mp4'), fourcc, 1.0, (width, height))
        for img_name in os.listdir(os.path.join(os.getcwd(), '.intermediate', file)):
            img_path = os.path.join(
                os.getcwd(), '.intermediate', file, img_name)
            # print(img_path)
            frame = cv2.imread(img_path)
            video.write(frame)
        # for img in imgs:
        #     video.write(img)
        video.release()


# Training
"!python train.py --img 960 --batch 16 --epochs 100 --data dataset.yaml --weights yolov5s.pt --cache"

# Resume the training
"!python train.py --img 960 --batch 16 --epochs 100 --data dataset.yaml --weights yolov5s.pt --cache --resume /content/gdrive/MyDrive/YOLOv5Character/yolov5/runs/train/exp3/weights/last.pt"


# Intermediate file
