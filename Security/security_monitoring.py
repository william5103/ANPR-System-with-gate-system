import customtkinter as ctk
import tkinter as tk
from PIL import Image, ImageTk
import cv2
import time
import serial
import datetime
import torch
import torch.nn.functional as F
from torchvision import transforms, models
from ultralytics import YOLO
from paddleocr import PaddleOCR
import threading
from firebase_config import firebase_db


class SecurityMonitoring(ctk.CTkFrame):
    def __init__(self, parent, security_id=None, security_name=None):
        self.security_id = security_id
        self.security_name = security_name
        super().__init__(parent)
        self.configure(fg_color="#f0f4ff")
        self.webcam_sources = {"Entry": 0, "Exit": 1}
        self.current_cam = "Entry"
        self.cap = cv2.VideoCapture(self.webcam_sources[self.current_cam])
        
        # Initialize with empty list for recent activities instead of dummy data
        self.log_data = []
        
        # Blacklist detection tracking
        self.last_blacklist_plate = ""
        self.last_blacklist_time = 0
        self.blacklist_cooldown = 10
        self.current_car_checked = False
        self.expiration_checked = False
        
        # Add flags to prevent multiple alerts for the same car
        self.blacklist_alert_shown = False
        self.expiry_alert_shown = False
        
        # Load detection models
        try:
            self.car_model = YOLO("ANPR_model/yolov8n.pt")
            self.license_plate_model = YOLO("ANPR_model/LPD_model/weights/best.pt")
            
            # Load OCR model
            self.ocr = PaddleOCR(use_angle_cls=True, lang='en')
            
            # Load car brand model
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            self.brand_model = models.resnet50(pretrained=False)
            num_classes = 14

            self.brand_model.fc = torch.nn.Sequential(
                torch.nn.Dropout(p=0.5),
                torch.nn.Linear(self.brand_model.fc.in_features, num_classes)
            )
            
            # Load the state dict
            self.brand_model.load_state_dict(torch.load("ANPR_model/best_car_brand_resnet50.pth", map_location=self.device))
            self.brand_model.to(self.device)
            self.brand_model.eval()
            
            # Car brand class names
            self.class_names = ["Alza", "Aruz", "Ativa", "Axia", "Bezza", "Kancil", "Myvi", "Accord", "Camry", "City", "Civic", "Corolla", "Vios", "Yaris"]
            
            # Image transforms for brand model
            self.transform = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])
            
            # Detection variables
            self.LICENSE = ""
            self.MODEL = ""
            self.last_car_detection_time = 0
            self.last_no_detection_time = 0
            self.car_detected = False
            self.processing_detection = False
            
            # Single-stage detection variables
            self.initial_car_detection_time = 0
            self.waiting_for_stabilization = False
            self.stabilization_time = 2
            self.detection_stage = 0
            
            # Performance optimization
            self.detection_interval = 0.5
            self.last_detection_run = 0
            self.clear_timeout = 1
            
            # Status message for UI
            self.detection_status = ""
        except Exception as e:
            print(f"Error loading models: {e}")
            self.LICENSE = ""
            self.MODEL = "Myvi"
            self.processing_detection = True
            self.detection_status = "Error loading models"
            
        self.build_widgets()

    def build_widgets(self):
        # Main container
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=20, pady=10)

        # Header
        header = ctk.CTkFrame(main_container, fg_color="transparent")
        header.pack(fill="x", pady=(0, 18))
        ctk.CTkLabel(
            header,
            text=" Security Monitoring",
            font=ctk.CTkFont(size=30, weight="bold"),
            text_color="#2c3e50"
        ).pack(side="left", pady=(5,0))

        # Camera Card
        cam_card = ctk.CTkFrame(main_container, fg_color="white", corner_radius=14, border_width=1, border_color="#dee2e6")
        cam_card.pack(fill="both", expand=True, pady=(0, 18), padx=10)
        cam_card.grid_columnconfigure(0, weight=1)
        cam_card.grid_columnconfigure(1, weight=1)
        cam_card.grid_rowconfigure(0, weight=1)

        # Camera feed
        cam_feed = ctk.CTkFrame(cam_card, fg_color="white")
        cam_feed.grid(row=0, column=0, sticky="nsew", padx=18, pady=18)
        cam_feed.grid_rowconfigure(0, weight=1)
        cam_feed.grid_columnconfigure(0, weight=1)
        self.cam_label = ctk.CTkLabel(cam_feed, text="Camera Feed", fg_color="#e9ecef", corner_radius=10)
        self.cam_label.grid(row=0, column=0, sticky="nsew")

        # Right panel (controls)
        right_panel = ctk.CTkFrame(cam_card, fg_color="white")
        right_panel.grid(row=0, column=1, sticky="nsew", padx=18, pady=18)
        right_panel.grid_rowconfigure(0, weight=1)

        # Location label
        ctk.CTkLabel(right_panel, text="Location", font=ctk.CTkFont(size=20, weight="bold"), text_color="#1a3e72").pack(anchor="w", pady=(0, 8))
        # Location selection buttons (Entry/Exit)
        location_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        location_frame.pack(fill="x", pady=(0, 18))
        self.entry_btn = ctk.CTkButton(
            location_frame,
            text="Entry",
            fg_color="#1769aa" if self.current_cam == "Entry" else "#e0e0e0",
            text_color="#ffffff" if self.current_cam == "Entry" else "#222b3a",
            font=ctk.CTkFont(size=20, weight="bold"),
            corner_radius=8,
            height=40,
            hover_color="#1769aa" if self.current_cam == "Entry" else "#b0b0b0",
            command=lambda: self.select_location("Entry")
        )
        self.entry_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.exit_btn = ctk.CTkButton(
            location_frame,
            text="Exit",
            fg_color="#1769aa" if self.current_cam == "Exit" else "#e0e0e0",
            text_color="#ffffff" if self.current_cam == "Exit" else "#222b3a",
            font=ctk.CTkFont(size=20, weight="bold"),
            corner_radius=8,
            height=40,
            hover_color="#1769aa" if self.current_cam == "Exit" else "#b0b0b0",
            command=lambda: self.select_location("Exit")
        )
        self.exit_btn.pack(side="right", fill="x", expand=True, padx=(6, 0))

        # Emergency button
        ctk.CTkButton(
            right_panel,
            text="⚠ Emergency Open",
            fg_color="#e80e0e",
            hover_color="#b71c1c",
            text_color="white",
            font=ctk.CTkFont(size=18, weight="bold"),
            corner_radius=8,
            height=44,
            command=self.open_gate
        ).pack(fill="x", pady=(0, 18))

        # Plate detected card
        plate_card = ctk.CTkFrame(right_panel, fg_color="#f8f9fa", corner_radius=10, border_width=2, border_color="#dee2e6")
        plate_card.pack(fill="x", pady=(0, 14))
        ctk.CTkLabel(plate_card, text="Detected Plate", font=ctk.CTkFont(size=18, weight="bold"), text_color="#495057").pack(anchor="w", padx=10, pady=(10, 0))
        self.plate_label = ctk.CTkLabel(plate_card, text=self.LICENSE if self.LICENSE else "---", font=ctk.CTkFont(size=28, weight="bold"), text_color="#2c3e50")
        self.plate_label.pack(padx=10, pady=(0, 8))
        self.status_label = ctk.CTkLabel(plate_card, text=self.MODEL if self.MODEL else "---", font=ctk.CTkFont(size=16, weight="bold"), text_color="#20c997")
        self.status_label.pack(padx=10, pady=(0, 4))
        
        # Add detection status label
        self.detection_status_label = ctk.CTkLabel(plate_card, text=self.detection_status, font=ctk.CTkFont(size=14), text_color="#6c757d")
        self.detection_status_label.pack(padx=10, pady=(0, 12))
        
        # Add refresh button
        self.refresh_button = ctk.CTkButton(
            plate_card,
            text="Reset Detection",
            fg_color="#6c757d",
            hover_color="#5a6268",
            text_color="white",
            font=ctk.CTkFont(size=14),
            corner_radius=8,
            height=30,
            width=120,
            command=self.reset_detection
        )
        self.refresh_button.pack(padx=10, pady=(0, 10))

        # Recent log/history - updated to store the scrollable frame reference
        log_card = ctk.CTkFrame(right_panel, fg_color="#f8f9fa", corner_radius=10, border_width=2, border_color="#dee2e6")
        log_card.pack(fill="both", expand=False, pady=(0, 14))
        ctk.CTkLabel(log_card, text="Recent Activity", font=ctk.CTkFont(size=18, weight="bold"), text_color="#2c3e50").pack(anchor="w", padx=10, pady=(10, 0))
        self.log_scroll = ctk.CTkScrollableFrame(log_card, fg_color="#f8f9fa", width=400, height=240)
        self.log_scroll.pack(fill="x", padx=10, pady=(0, 10))

        # Refresh activity display
        self.refresh_activity_display()

        # Clock/stat card at the bottom
        clock_card = ctk.CTkFrame(right_panel, fg_color="transparent", corner_radius=10)
        clock_card.pack(side="bottom", fill="x", pady=(0, 10))
        self.clock_label = ctk.CTkLabel(clock_card, text="", font=ctk.CTkFont(size=16, weight="bold"), text_color="#495057")
        self.clock_label.pack(padx=10, pady=10, anchor="e")
        self.update_clock()
        self.update_webcam()

    def update_clock(self):
        current_date = time.strftime("%Y-%m-%d")
        current_time = time.strftime("%H:%M:%S")
        self.clock_label.configure(text=f"{current_date}\n{current_time}")
        self.after(1000, self.update_clock)

    def update_webcam(self):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            orig_frame = frame.copy()

            w = self.cam_label.winfo_width()
            h = self.cam_label.winfo_height()
            if w < 10 or h < 10:
                w, h = 500, 400

            current_time = time.time()
            if not self.processing_detection and (current_time - self.last_detection_run) > self.detection_interval:
                self.last_detection_run = current_time
                threading.Thread(target=self.process_detection, args=(orig_frame,)).start()

            frame = cv2.resize(frame, (w, h))
            img = ImageTk.PhotoImage(Image.fromarray(frame))
            self.cam_label.configure(image=img, text="")
            self.cam_label.image = img

            self.detection_status_label.configure(text=self.detection_status)

            if self.LICENSE:
                self.plate_label.configure(text=self.LICENSE)

                # Check if plate is blacklisted
                if hasattr(firebase_db, 'is_plate_blacklisted') and callable(getattr(firebase_db, 'is_plate_blacklisted')):
                    is_blacklisted = firebase_db.is_plate_blacklisted(self.LICENSE)
                    if is_blacklisted:
                        self.status_label.configure(text="Blocked", text_color="#e80e0e")
                        self.detect_and_log_blacklist(self.LICENSE)

                    
            # Check if we need to clear detection results after timeout
            if (self.last_no_detection_time > 0 and 
                current_time - self.last_no_detection_time > self.clear_timeout and
                self.LICENSE):
                self.LICENSE = ""
                self.MODEL = ""
                self.detection_status = ""
                self.detection_stage = 0
                self.plate_label.configure(text="---")
                self.status_label.configure(text="---")
                self.detection_status_label.configure(text="")
                # Reset alert flags when clearing detection results
                self.blacklist_alert_shown = False
                self.expiry_alert_shown = False
                print("Cleared detection results due to no car detection")
                
        self.after(30, self.update_webcam)
    
    def process_detection(self, frame):
        self.processing_detection = True
        
        try:
            # Car detection with YOLOv8
            car_results = self.car_model(frame, classes=[2, 3, 5, 7])
            
            current_time = time.time()
            
            # If car is detected
            if len(car_results[0].boxes) > 0:
                self.last_no_detection_time = 0
                
                # First time car detected
                if not self.car_detected:
                    self.car_detected = True
                    self.initial_car_detection_time = current_time
                    self.waiting_for_stabilization = True
                    self.detection_stage = 0
                    self.current_car_checked = False
                    self.expiration_checked = False
                    self.blacklist_alert_shown = False
                    self.expiry_alert_shown = False
                    self.detection_status = "Car detected, waiting for stabilization..."
                    print(f"Car detected, waiting {self.stabilization_time} seconds for stabilization")
                
                # Waiting for stabilization
                elif self.waiting_for_stabilization:
                    if current_time - self.initial_car_detection_time >= self.stabilization_time:
                        self.waiting_for_stabilization = False
                        self.detection_status = "Performing detection..."
                        print("Stabilization complete, starting detection")
                        # Perform detection only once
                        if self.detection_stage == 0:
                            self._perform_detection(frame, car_results)
                            self.detection_stage = 2
                            print("Detection completed - will not detect again until car leaves")
                        else:
                            self.detection_status = "Detection already completed"
            else:
                # No car detected
                if self.car_detected:
                    self.car_detected = False
                    self.waiting_for_stabilization = False
                    self.last_no_detection_time = current_time
                    self.detection_status = "No car detected, clearing results soon..."
                    print("No car detected, starting timeout to clear results")
                    self.current_car_checked = False
                    self.expiration_checked = False
                    self.detection_stage = 0
        except Exception as e:
            print(f"Error in detection process: {e}")
            self.detection_status = f"Error: {str(e)[:50]}..."
        
        self.processing_detection = False
        
    def _perform_detection(self, frame, car_results):
        try:
            # Get car bounding box
            car_box = car_results[0].boxes[0].xyxy.cpu().numpy()[0].astype(int)
            car_img = frame[car_box[1]:car_box[3], car_box[0]:car_box[2]]
            
            if car_img.size > 0:
                # Detect car brand
                try:
                    car_pil = Image.fromarray(car_img)
                    car_tensor = self.transform(car_pil).unsqueeze(0).to(self.device)
                    with torch.no_grad():
                        outputs = self.brand_model(car_tensor)
                        _, predicted = torch.max(outputs, 1)
                        confidence = F.softmax(outputs, dim=1)[0][predicted.item()].item()
                        
                        if confidence > 0.5:  # Only accept predictions with high confidence
                            model = self.class_names[predicted.item()]
                            self.MODEL = model
                            # Set brand based on model
                            if model in ["Alza", "Aruz", "Ativa", "Axia", "Bezza", "Kancil", "Myvi"]:
                                self.BRAND = "Perodua"
                            elif model in ["Accord", "City", "Civic"]:
                                self.BRAND = "Honda"
                            elif model in ["Camry", "Corolla", "Vios", "Yaris"]:
                                self.BRAND = "Toyota"
                            else:
                                self.BRAND = "Unknown"
                            print(f"Model detection: {model}, Brand: {self.BRAND}")

                            self.status_label.configure(text=f"Unknown ({model})", text_color="#ffc107")
                except Exception as e:
                    print(f"Error in brand detection: {e}")
            
            # License plate detection
            lp_results = self.license_plate_model(frame)
            
            if len(lp_results[0].boxes) > 0:
                # Get license plate bounding box
                lp_box = lp_results[0].boxes[0].xyxy.cpu().numpy()[0].astype(int)
                lp_img = frame[lp_box[1]:lp_box[3], lp_box[0]:lp_box[2]]
                
                if lp_img.size > 0:
                    # OCR on license plate
                    try:
                        lp_img_bgr = cv2.cvtColor(lp_img, cv2.COLOR_RGB2BGR)
                        ocr_result = self.ocr.ocr(lp_img_bgr, cls=True)
                        
                        if ocr_result and ocr_result[0]:
                            text = ''.join([res[1][0] for res in ocr_result[0]])
                            # Clean text (remove spaces and special characters)
                            text = ''.join(c for c in text if c.isalnum())
                            if text:
                                plate_text = text.upper()
                                self.LICENSE = plate_text
                                print(f"License detection: {plate_text}")
                                
                                # Record the detected vehicle data in Firebase
                                self.record_vehicle_data()
                    except Exception as e:
                        print(f"Error in OCR: {e}")
            
            # Update status to show detection is complete
            self.detection_status = "Detection complete"
                
        except Exception as e:
            print(f"Error in _perform_detection: {e}")
            self.detection_status = f"Detection error: {str(e)[:30]}..."

    def record_vehicle_data(self):
        if not self.LICENSE:
            return
            
        try:
            current_date = datetime.datetime.now().strftime("%Y-%m-%d")
            current_time = datetime.datetime.now().strftime("%H:%M")
            
            # Check is it at Entry gate
            if self.current_cam == "Entry":
                print(f"Recording entry for vehicle {self.LICENSE} at {current_time}")
                
                vehicle_plate = self.LICENSE
                is_blacklisted = False
                
                # Check blacklist first
                if not self.current_car_checked:
                    print(f"First blacklist check for vehicle {vehicle_plate}")
                    is_blacklisted = firebase_db.is_plate_blacklisted(vehicle_plate)
                    self.current_car_checked = True
                    print(f"Blacklist check completed - car marked as checked")
                else:
                    print(f"Skipping blacklist check for {vehicle_plate} - already checked")
                    return
                if is_blacklisted:
                    # Check if this is a new blacklisted plate after cooldown period has passed
                    current_time_sec = time.time()
                    is_new_detection = (
                        vehicle_plate != self.last_blacklist_plate or
                        (current_time_sec - self.last_blacklist_time) > self.blacklist_cooldown
                    )

                    if is_new_detection:
                        # Vehicle is blacklisted - deny entry and log critical alert
                        self.status_label.configure(text="BLACKLISTED", text_color="#e80e0e")
                        self.detection_status = "Vehicle blacklisted - entry denied"
                        print(f"Blacklisted vehicle {vehicle_plate} detected")
                        self.detect_and_log_blacklist(vehicle_plate)
                        self.update_recent_activity(vehicle_plate, "Blocked")
                        # Update the last blacklist detection
                        self.last_blacklist_plate = vehicle_plate
                        self.last_blacklist_time = current_time_sec
                    else:
                        # Already detected this blacklisted plate recently
                        self.status_label.configure(text="BLACKLISTED", text_color="#e80e0e")
                        self.detection_status = "Vehicle blacklisted - entry denied"
                    return
        
                
                # Block entry if there is an entry without exit
                records = firebase_db.search_records("vehicle_plate", vehicle_plate)
                if records:
                    active_entries = [r for r in records if 'exit_time' not in r or not r['exit_time']]
                    if active_entries:
                        warning_msg = (f"Entry denied: vehicle has not exited yet.")
                        print(warning_msg)
                        self.status_label.configure(text="ENTRY BLOCKED", text_color="#e80e0e")
                        self.detection_status = warning_msg
                        tk.messagebox.showerror("Entry Blocked", warning_msg)
                        self.update_recent_activity(vehicle_plate, "Entry Blocked")
                        return  
               
                
                # frequent entry warning
                entry_count = self.count_recent_entries(vehicle_plate, hours=24)
                if entry_count >= 3:
                    warning_msg = f"Vehicle {vehicle_plate} has entered at least {entry_count + 1} times in the last 24 hours!"
                    print(warning_msg)
                    tk.messagebox.showwarning("Frequent Entry Detected", warning_msg)
                    if hasattr(firebase_db, 'add_warning_alert'):
                        firebase_db.add_warning_alert(
                            message=warning_msg,
                            security_id=self.security_id,
                            security_name=self.security_name,
                            gate_name=self.current_cam,
                            plate=vehicle_plate
                        )
                
                # If not blacklisted look up the owner in the database
                owner_data = self.get_owner_by_plate(vehicle_plate)
                
                if owner_data:
                    owner_identity = owner_data.get('owner_identity', 'visitor')
                    owner_phone = owner_data.get('owner_phone', '01234567890')
                    owner_name = owner_data.get('owner_name', 'Unknown')
                    owner_id = owner_data.get('owner_id', None)
                    owner_ic = owner_data.get('owner_ic', None)
                    entry_reason = owner_data.get('entry_reason', 'registered')
                    owner_status = owner_data.get('status', 'Active')
                    
                    # Check if the owner's status is expired 
                    if not self.expiration_checked:
                        self.expiration_checked = True
                        
                        if owner_status.lower() == "expired":
                            # Show Expired 
                            status_text = f"Expired ({self.MODEL})"
                            self.status_label.configure(text=status_text, text_color="#e80e0e")
                            self.detection_status = f"Registration expired for {owner_name}"
                            print(f"Expired registration for vehicle {vehicle_plate}")
                            
                            self.update_recent_activity(vehicle_plate, status_text)
                            if not self.expiry_alert_shown:
                                self.expiry_alert_shown = True
                                message = f"VEHICLE REGISTRATION EXPIRED\n\nPlate: {vehicle_plate}\nOwner: {owner_name}\nStatus: EXPIRED"
                                tk.messagebox.showwarning("Expired Registration", message)
                            return
                    else:
                        print(f"Skipping expiration check for {vehicle_plate} - already checked")
                    
                    # Status is Active, allow entry
                    status_text = f"Allowed ({self.MODEL})"
                    self.detection_status = f"Welcome {owner_name}"
                    print(f"Owner found: {owner_name} ({owner_identity})")
                    self.status_label.configure(text=status_text, text_color="#20c997")
                    self.update_recent_activity(vehicle_plate, status_text)
                    
                    # Add the record to Firebase for registered owners
                    firebase_db.add_record(
                        vehicle_plate=vehicle_plate,
                        owner_identity=owner_identity,
                        owner_phone=owner_phone,
                        entry_date=current_date,
                        entry_time=current_time,
                        entry_reason=entry_reason,
                        owner_name=owner_name,
                        owner_id=owner_id,
                        owner_ic=owner_ic,
                        security_id=self.security_id,
                        brand=self.BRAND,
                        model=self.MODEL
                    )
                    # Automatically open the gate 
                    if self.current_cam == "Entry":
                        port = "COM3"
                        msg = (vehicle_plate + '\n').encode('utf-8')
                        self.send_to_arduino(msg, port)
                else:
                    status_text = f"Unknown ({self.MODEL})"
                    self.status_label.configure(text=status_text, text_color="#ffc107")
                    print(f"Unknown vehicle detected: {vehicle_plate}")
                    self.update_recent_activity(vehicle_plate, status_text)
                    visitor_info = self.show_visitor_info_dialog(vehicle_plate)
                    if visitor_info:
                        owner_identity = "visitor"
                        owner_name = visitor_info["visitor_name"]
                        owner_phone = visitor_info["visitor_phone"]
                        owner_ic = visitor_info["visitor_ic"]
                        entry_reason = visitor_info["entry_reason"]
                        owner_id = None
                        
                        status_text = "Allowed (visitor)"
                        print(f"Visitor info collected: {owner_name}")
                        
                        self.update_recent_activity(vehicle_plate, status_text)
                        
                        # Add record to Firebase only when visitor info is provided
                        firebase_db.add_record(
                            vehicle_plate=vehicle_plate,
                            owner_identity=owner_identity,
                            owner_phone=owner_phone,
                            entry_date=current_date,
                            entry_time=current_time,
                            entry_reason=entry_reason,
                            owner_name=owner_name,
                            owner_id=owner_id,
                            owner_ic=owner_ic,
                            security_id=self.security_id,
                            brand=self.BRAND,
                            model=self.MODEL
                        )
                        # Automatically open the gate and display plate if at entry
                        if self.current_cam == "Entry":
                            port = "COM3"
                            msg = (vehicle_plate + '\n').encode('utf-8')
                            self.send_to_arduino(msg, port)
                    else:
                        blocked_status = "Blocked"
                        print(f"Visitor dialog canceled for plate {vehicle_plate} - Entry blocked")
                        self.update_recent_activity(vehicle_plate, blocked_status)
                
            # Check if we're at Exit gate
            elif self.current_cam == "Exit":
                # Find the matching entry record to update with exit time
                print(f"Recording exit for vehicle {self.LICENSE} at {current_time}")
                
                # Search for records with this plate number
                records = firebase_db.search_records("vehicle_plate", self.LICENSE)

                if records:
                    # Find the most recent entry record that doesn't have an exit time
                    active_records = [r for r in records if 'exit_time' not in r or not r['exit_time']]
                    
                    if active_records:
                        # Sort by most recent entry
                        active_records.sort(key=lambda x: x.get('entry_date', '') + x.get('entry_time', ''), reverse=True)
                        record_to_update = active_records[0]
                        record_id = record_to_update.get('record_id')
                        
                        # Get owner name for status message
                        owner_name = record_to_update.get('owner_name', 'Unknown')
                        
                        # Create update data
                        update_data = {
                            'exit_date': current_date,
                            'exit_time': current_time
                        }
                        
                        # Update the record
                        firebase_db.update_record(
                            record_id=record_id,
                            update_data=update_data,
                            security_id=self.security_id
                        )

                        # Automatically open the exit gate
                        port = "COM4"
                        self.send_to_arduino(b'OpenExit\n', port)
                        
                        exit_status = "Exit Recorded"
                        self.detection_status = f"Exit recorded for {owner_name}"
                        self.status_label.configure(text=exit_status, text_color="#20c997")
                        self.update_recent_activity(self.LICENSE, exit_status)
                    else:
                        no_entry_status = "No Entry Record"
                        print(f"No active entry record found for plate {self.LICENSE}")
                        self.detection_status = "No matching entry found"
                        self.status_label.configure(text=no_entry_status, text_color="#ffc107")
                        self.update_recent_activity(self.LICENSE, no_entry_status)
                else:
                    no_record_status = "No Records"
                    print(f"No records found for plate {self.LICENSE}")
                    self.detection_status = "No records found for this vehicle"
                    self.status_label.configure(text=no_record_status, text_color="#ffc107")
                    
                    # Update recent activity log
                    self.update_recent_activity(self.LICENSE, no_record_status)
                    
        except Exception as e:
            print(f"Error recording vehicle data: {e}")
            self.detection_status = f"Database error: {str(e)[:30]}..."
            
            # Log the error in recent activity
            self.update_recent_activity(self.LICENSE if self.LICENSE else "Error", "Error")

    def get_owner_by_plate(self, plate):
        """Look up owner information based on the license plate."""
        try:
            # Search for owners with this plate number
            owners = firebase_db.search_owners("vehicle_plate", plate)
            
            if owners and len(owners) > 0:
                return owners[0]  # Return the first matching owner
            else:
                return None
        except Exception as e:
            print(f"Error looking up owner by plate: {e}")
            return None

    def select_location(self, location):
        if location != self.current_cam:
            self.cap.release()
            self.cap = cv2.VideoCapture(self.webcam_sources[location])
            self.current_cam = location
            # Update button colors and hover colors
            self.entry_btn.configure(
                fg_color="#1769aa" if location == "Entry" else "#e0e0e0",
                text_color="#ffffff" if location == "Entry" else "#222b3a",
                hover_color="#1769aa" if location == "Entry" else "#b0b0b0"
            )
            self.exit_btn.configure(
                fg_color="#1769aa" if location == "Exit" else "#e0e0e0",
                text_color="#ffffff" if location == "Exit" else "#222b3a",
                hover_color="#1769aa" if location == "Exit" else "#b0b0b0"
            )

    def log_gate_opened(self, gate_name):
        now = datetime.datetime.now()
        alert = {
            "message": f"Security '{self.security_name}' (ID: {self.security_id}) opened gate '{gate_name}'.",
            "security_id": self.security_id,
            "security_name": self.security_name,
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "seen_by": [],
            "timestamp": datetime.datetime.now(),
        }
        # Push to the 'information_alerts' collection
        try:
            firebase_db.db.collection('information_alerts').add(alert)
            print(f"Logged gate open: {alert['message']}")
        except Exception as e:
            print(f"Error logging gate open: {e}")

    def send_to_arduino(self, message, port):
        try:
            arduino = serial.Serial(port, 9600, timeout=1)
            time.sleep(2)
            arduino.write(message)
            arduino.close()
            print(f"Sent to Arduino on {port}: {message}")
        except serial.SerialException as e:
            print(f"Error: Could not connect to Arduino on {port}: {e}")

    def open_gate(self):
        location = self.current_cam.lower()
        if location == "entry":
            port = "COM3"
            message = b'Open Entry\n'
        elif location == "exit":
            port = "COM4"
            message = b'Open Exit\n'
        else:
            print("Invalid location selected.")
            return
        self.send_to_arduino(message, port)
        gate_name = self.current_cam
        self.log_gate_opened(gate_name)

    def cleanup(self):
        # Release webcam
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()


    def destroy(self):
        self.cleanup()
        super().destroy()

    def show_visitor_info_dialog(self, vehicle_plate):
        # Create a popup dialog
        dialog = tk.Toplevel()
        dialog.title("Visitor Information")
        dialog.geometry("550x480")
        dialog.configure(bg="#f0f4ff")
        dialog.grab_set()
        dialog.transient()
        dialog.resizable(False, False)
        
        # Main container frame with padding
        main_frame = tk.Frame(dialog, bg="#f0f4ff")
        main_frame.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Visitor info frame
        info_frame = ctk.CTkFrame(main_frame, corner_radius=10, fg_color="white")
        info_frame.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Title and instruction
        tk.Label(info_frame, text=f"Unregistered Vehicle: {vehicle_plate}",font=("Arial", 18, "bold"), bg="white").pack(pady=(30, 5))
        tk.Label(info_frame, text="Please enter visitor information:", font=("Arial", 15), bg="white").pack(pady=(0, 20))
        
        # Form fields
        form_frame = tk.Frame(info_frame, bg="white")
        form_frame.pack(padx=0, pady=0, fill="both", expand=True)
        form_frame.grid_columnconfigure(1, weight=1)
        
        # Visitor name
        tk.Label(form_frame, text="Visitor Name:", font=("Arial", 14), bg="white", anchor="w").grid(row=0, column=0, sticky="e", pady=10, padx=(40,10))
        visitor_name_entry = ctk.CTkEntry(form_frame, height=35, corner_radius=5, fg_color="#e3f0ff",  font=("Arial", 14), text_color="#000000")
        visitor_name_entry.grid(row=0, column=1, sticky="ew", pady=10, padx=(0,40))
        
        # Visitor IC
        tk.Label(form_frame, text="Visitor IC:", font=("Arial", 14), bg="white", anchor="w").grid(row=1, column=0, sticky="e", pady=10, padx=(40,10))
        visitor_ic_entry = ctk.CTkEntry(form_frame, height=35, corner_radius=5, fg_color="#e3f0ff",  font=("Arial", 14), text_color="#000000")
        visitor_ic_entry.grid(row=1, column=1, sticky="ew", pady=10, padx=(0,40))
        
        # Visitor phone
        tk.Label(form_frame, text="Phone Number:", font=("Arial", 14), bg="white", anchor="w").grid(row=2, column=0, sticky="e", pady=10, padx=(40,10))
        visitor_phone_entry = ctk.CTkEntry(form_frame, height=35, corner_radius=5, fg_color="#e3f0ff",  font=("Arial", 14), text_color="#000000")
        visitor_phone_entry.grid(row=2, column=1, sticky="ew", pady=10, padx=(0,40))
        
        # Entry reason
        tk.Label(form_frame, text="Entry Reason:", font=("Arial", 14), bg="white", anchor="nw").grid(row=3, column=0, sticky="ne", pady=10, padx=(40,10))
        reason_text = tk.Text(form_frame, height=3, width=30, font=("Arial", 14), bg="#e3f0ff", fg="#000000", wrap="word", borderwidth=0)
        reason_text.grid(row=3, column=1, sticky="ew", pady=10, padx=(0,40))
        
        # Buttons frame
        btn_frame = tk.Frame(info_frame, bg="white")
        btn_frame.pack(pady=20)
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)
        
        # Dictionary to store the result
        result = {
            "canceled": True,
            "visitor_name": "",
            "visitor_ic": "",
            "visitor_phone": "",
            "entry_reason": ""
        }
        
        # Confirm button action
        def on_confirm():
            # Basic validation
            name = visitor_name_entry.get().strip()
            ic = visitor_ic_entry.get().strip()
            phone = visitor_phone_entry.get().strip()
            reason = reason_text.get("1.0", "end").strip()
            
            # Validation
            errors = []
            if not name:
                errors.append("Visitor name is required")
            if ic and (not ic.isdigit() or len(ic) != 12):
                errors.append("IC must be 12 digits")
            if not phone:
                errors.append("Phone number is required")
            elif not phone.isdigit() or len(phone) not in [10, 11]:
                errors.append("Phone must be 10-11 digits")
            if not reason:
                errors.append("Entry reason is required")
                
            if errors:
                error_msg = "\n".join(errors)
                tk.messagebox.showerror("Validation Error", error_msg, parent=dialog)
                return
                
            # Update status immediately to ALLOWED
            self.status_label.configure(text="ALLOWED (visitor)", text_color="#20c997")
            self.detection_status = f"Welcome {name}"
                
            # Store the result
            result["canceled"] = False
            result["visitor_name"] = name
            result["visitor_ic"] = ic
            result["visitor_phone"] = phone
            result["entry_reason"] = reason
            dialog.destroy()
        
        # Cancel button action
        def on_cancel():
            # Update status immediately to BLOCKED
            self.status_label.configure(text="BLOCKED", text_color="#e80e0e")
            self.detection_status = "Entry denied - visitor info not provided"
            dialog.destroy()
        
        # Add buttons using grid to avoid overlap
        ctk.CTkButton(btn_frame, text="Confirm", fg_color="#1769aa", hover_color="#144c7f", 
                     command=on_confirm, width=120, height=40, font=("Arial", 14)).grid(row=0, column=0, padx=15, pady=0, sticky="e")
        ctk.CTkButton(btn_frame, text="Cancel", fg_color="#e74c3c", hover_color="#c0392b", 
                     command=on_cancel, width=120, height=40, font=("Arial", 14)).grid(row=0, column=1, padx=15, pady=0, sticky="w")
        
        # Position the dialog in the center of the screen
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f'{width}x{height}+{x}+{y}')
        
        # Wait for the dialog to be closed
        dialog.wait_window()
        
        # Return the result
        if not result["canceled"]:
            return result
        return None

    def update_recent_activity(self, plate, status):
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Add new entry at the beginning of the list
        self.log_data.insert(0, {"time": current_time, "plate": plate, "status": status})
        
        # Refresh the activity display
        self.refresh_activity_display()
    
    def refresh_activity_display(self):
        # Clear existing children
        for widget in self.log_scroll.winfo_children():
            widget.destroy()
            
        # If no log data yet, show a placeholder message
        if not self.log_data:
            placeholder = ctk.CTkLabel(
                self.log_scroll, 
                text="No recent activity",
                font=ctk.CTkFont(size=14, weight="bold"), 
                text_color="#868e96",
                fg_color="#f8f9fa"
            )
            placeholder.pack(fill="x", pady=15, padx=10)
            return
        
        # Add entries to the scrollable frame
        for entry in self.log_data:
            color = "#20c997" if ("Allowed" in entry["status"] or "Exit Recorded" in entry["status"]) else "#e80e0e"
            if "Unknown" in entry["status"]:
                color = "#ffc107"
            elif "Expired" in entry["status"]:
                color = "#e80e0e"
                
            row = ctk.CTkFrame(self.log_scroll, fg_color="#f8f9fa", corner_radius=6)
            row.pack(fill="x", pady=2, padx=2)
            
            # Format time to show only hour:minute:second
            display_time = entry["time"].split()[1] if " " in entry["time"] else entry["time"]
            
            ctk.CTkLabel(row, text=display_time, font=ctk.CTkFont(size=14), text_color="#868e96").pack(side="left", padx=(8, 8))
            ctk.CTkLabel(row, text=entry["plate"], font=ctk.CTkFont(size=16, weight="bold"), text_color="#2c3e50").pack(side="left", padx=(0, 8))
            ctk.CTkLabel(row, text=entry["status"], font=ctk.CTkFont(size=15, weight="bold"), text_color=color).pack(side="left", padx=(0, 8))

    def detect_and_log_blacklist(self, plate):
        plate = plate.strip().upper()
        if firebase_db.is_plate_blacklisted(plate):
            if self.current_cam.lower() == "entry":
                # Only show alert if not already shown for this car detection
                if not self.blacklist_alert_shown:
                    self.blacklist_alert_shown = True
                    message = f"Blacklisted vehicle '{plate}' detected at ENTRY gate!"
                    firebase_db.add_critical_alert(
                        message=message,
                        security_id=self.security_id,
                        security_name=self.security_name,
                        gate_name=self.current_cam,
                        plate=plate
                    )
                    tk.messagebox.showerror("Blacklisted Detected", f"Blacklisted vehicle '{plate}' detected at ENTRY gate! Critical alert logged.")
                else:
                    print(f"Skipping blacklist alert for {plate} - already shown for this detection")
            
    def count_recent_entries(self, plate, hours=24):
        since_time = datetime.datetime.now() - datetime.timedelta(hours=hours)
        records = firebase_db.search_records("vehicle_plate", plate)
        count = 0
        for record in records:
            entry_date = record.get('entry_date')
            entry_time = record.get('entry_time')
            if entry_date and entry_time:
                try:
                    entry_datetime = datetime.datetime.strptime(f"{entry_date} {entry_time}", "%Y-%m-%d %H:%M")
                    if entry_datetime >= since_time:
                        count += 1
                except Exception:
                    continue
        return count

    def reset_detection(self):
        self.LICENSE = ""
        self.MODEL = ""
        if hasattr(self, 'BRAND'):
            self.BRAND = ""
        self.detection_status = "Detection reset by user"
        self.detection_stage = 0
        self.car_detected = False
        self.waiting_for_stabilization = False
        self.current_car_checked = False
        self.expiration_checked = False
        
        # Reset UI elements
        self.plate_label.configure(text="---")
        self.status_label.configure(text="---", text_color="#20c997")
        self.detection_status_label.configure(text=self.detection_status)
        
        # Reset alert flags
        self.blacklist_alert_shown = False
        self.expiry_alert_shown = False
        
        print("Detection state reset by user")

