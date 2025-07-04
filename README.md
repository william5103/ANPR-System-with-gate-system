# Security Monitoring System

## Overview

This Python application provides a real-time security monitoring interface using webcams. It leverages computer vision and machine learning models to perform Automatic Number Plate Recognition (ANPR), car brand detection, and vehicle tracking for a secure entry/exit system. The system is designed to integrate with a Firebase backend for data storage and management.

## Features

*   **Real-time Video Feed**: Monitors entry and exit gates using separate webcam sources.
*   **AI-Powered Detection**:
    *   Detects cars in the camera feed using YOLOv8.
    *   Identifies and reads license plates using a combination of a specialized YOLO model and PaddleOCR.
    *   Classifies the car's brand and model using a custom-trained ResNet50 model.
*   **Firebase Integration**:
    *   Logs all vehicle entries and exits.
    *   Checks detected license plates against a blacklist.
    *   Verifies vehicle registration status (e.g., Active, Expired).
    *   Manages records for registered owners and visitors.
    *   Logs critical and informational alerts.
*   **Gate Control**: Sends signals to Arduino controllers to open gates for authorized vehicles.
*   **User-Friendly Interface**: Built with CustomTkinter, it provides an intuitive interface for security personnel, including a dialog for registering unknown visitors.

## Prerequisites

*   Python 3.8+
*   Two webcams (for Entry and Exit gates).
*   A Google Firebase project with Firestore enabled.
*   (Optional) Arduino boards connected to serial ports for physical gate control.

## Setup Instructions

### 1. Project Structure

Ensure your project files are organized as follows. You will need to create the `ANPR_model` directory and place the model files inside it.

```
.
├── ANPR_model/
│   ├── yolov8n.pt
│   ├── LPD_model/
│   │   └── weights/
│   │       └── best.pt
│   └── best_car_brand_resnet50.pth
├── Security/
│   └── security_monitoring.py
├── firebase_config.py
├── main.py
└── README.md
```

### 2. Python Environment

It is highly recommended to use a virtual environment to manage dependencies.

```bash
# Create a virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

Install all required Python packages. You can create a `requirements.txt` file with the following content:

**`requirements.txt`:**
```
customtkinter==5.2.2
Pillow==10.2.0
opencv-python==4.11.0.86
pyserial==3.5
torch==2.6.0+cu126
torchvision==0.21.0+cu126
ultralytics==8.3.81
paddleocr==2.10.0
paddlepaddle==3.0.0
firebase-admin==6.7.0
python-dotenv==1.0.1
cryptography==44.0.2
bcrypt==4.3.0
```
Use this line of code to install all the dependencies needed:
pip install customtkinter==5.2.2 Pillow==10.2.0 opencv-python==4.11.0.86 pyserial==3.5 torch==2.6.0+cu126 torchvision==0.21.0+cu126 ultralytics==8.3.81 paddleocr==2.10.0 paddlepaddle==3.0.0 firebase-admin==6.7.0 python-dotenv==1.0.1 cryptography==44.0.2 bcrypt==4.3.0


> **Note**: For GPU acceleration with PaddleOCR and PyTorch, you may need to install `paddlepaddle-gpu` and a CUDA-compatible version of PyTorch. Refer to their official documentation for instructions.


You need to obtain the following pre-trained models and place them in the `ANPR_model/` directory as shown in the project structure:

*   `yolov8n.pt`: A standard object detection model from Ultralytics.
*   `LPD_model/weights/best.pt`: A custom-trained YOLO model for license plate detection.
*   `best_car_brand_resnet50.pth`: A custom-trained ResNet50 model for car brand classification.

Dataset information:
License-Plate-Data:
> used to train the license plate detection model
>sourced from roboflow
    roboflow:
        workspace: test-vaxvp
        project: license-plate-project-adaad
        version: 1
        license: CC BY 4.0
        url: https://universe.roboflow.com/test-vaxvp/license-plate-project-adaad/dataset/1
>Contains:
    total: 23531 images
    train: 20580 images (87%)
    valid: 1973 images  ( 8%)
    test : 978 images   ( 4%)
>Preprocessing steps:
    Auto-Orient: Applied to ensure images are upright.
    Resize: All images are stretched to 640×640 pixels.
    Augmentations:
        90° Rotation: Includes Clockwise, Counter-Clockwise, and Upside Down.
        Rotation: Random rotation between -15° and +15°.
        Shear: Up to ±15° Horizontal and ±15° Vertical.
        Blur: Applied up to 0.5px.

Car-Model-Data
> used to train the car model classification model
>sourced from kaggle, roboflow and google images
    roboflow:
        url: https://universe.roboflow.com/joshua-zoddd/perodua/dataset/6
        url: https://universe.roboflow.com/joshua-zoddd/perodua/dataset/5
        url: https://universe.roboflow.com/joshua-zoddd/perodua/dataset/4
        url: https://universe.roboflow.com/joshua-zoddd/perodua/dataset/3
        url: https://universe.roboflow.com/joshua-zoddd/perodua/dataset/2
        url: https://universe.roboflow.com/joshua-zoddd/perodua/dataset/1
    Kaggle:
        url: https://www.kaggle.com/datasets/occultainsights/toyota-cars-over-20k-labeled-images
        url: https://www.kaggle.com/datasets/occultainsights/honda-cars-over-11k-labeled-images 
>Contains:
    14 classes which each classes contains about 500 images
    Total images: 7039
    Training images: 5627 (79.94%)
    Validation images: 1412 (20.06%)
>Preprocessing steps:
    Resize: All images are stretched to 224x224 pixels.
    Augmentations:
        Horizontal flip, color jitter, up to 500 images/class







