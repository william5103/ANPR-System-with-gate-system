import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from firebase_config import firebase_db
import datetime
from tkinter import ttk
import winsound

class AdminAddRecord(tk.Frame):
    def __init__(self, master, user_id, user_name, navigate_to=None, navigate_to_login=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.master = master
        self.user_id = user_id
        self.user_name = user_name
        self.navigate_to = navigate_to
        self.navigate_to_login = navigate_to_login
        self.firebase_db = firebase_db
        self.build_form()

    def build_form(self):
        self.configure(bg="#f5f5f5")

        # Create main container
        main_container = tk.Frame(self, bg="#f5f5f5")
        main_container.pack(padx=20, pady=20, fill="both", expand=True)

        # Add title at the top
        title_label = ctk.CTkLabel(
            main_container,
            text="Add Record",
            font=ctk.CTkFont(size=30, weight="bold"),
            text_color="#2c3e50",
            anchor="w"
        )
        title_label.pack(side="top", anchor="w", padx=10, pady=(0, 20))

        # Create card frame
        card_frame = ctk.CTkFrame(
            main_container,
            corner_radius=15,
            fg_color="white",
            border_width=1,
            border_color="#e0e0e0"
        )
        card_frame.pack(fill="both", expand=True)

        # Create form frame inside card
        self.form_frame = tk.Frame(card_frame, bg="white")
        self.form_frame.pack(padx=30, pady=30, fill="both", expand=True, anchor="w")

        labels = [
            ("Vehicle Plate", "vehicle_plate"),
            ("Brand & Model", "brand_model"),
            ("Owner Identity", "owner_identity"),
            ("Owner Name", "owner_name"),
            ("Owner IC", "owner_ic"),
            ("Owner Phone", "owner_phone"),
            ("Owner ID", "owner_id"),
            ("Entry Date", "entry_date"),
            ("Entry Time", "entry_time"),
            ("Entry Reason", "entry_reason")
        ];
        example_texts = {
            "vehicle_plate": "e.g. ABC1234",
            "brand_model": "e.g. Select brand and model",
            "owner_identity": "e.g. Select owner type (student/staff/visitor)",
            "owner_name": "e.g. Ali",
            "owner_ic": "e.g. 123456789012",
            "owner_phone": "e.g. 0123456789",
            "owner_id": " ",
            "entry_date": "e.g. 2025-05-06",
            "entry_time": "e.g. 23:11"
        };
        self.entries = {}
        self.row_map = {}
        self.car_brands = {
            "Perodua": ["Alza", "Aruz", "Ativa", "Axia", "Bezza", "Kancil", "Myvi"],
            "Honda": ["Accord", "City", "Civic"],
            "Toyota": ["Camry", "Corolla", "Vios", "Yaris"],
        }
        self.brand_var = tk.StringVar(value="Perodua")
        self.model_var = tk.StringVar(value=self.car_brands["Perodua"][0])
        for i, (label, key) in enumerate(labels):
            label_widget = tk.Label(self.form_frame, text=label, font=("Arial", 16), bg="white", anchor="w", justify="left");
            label_widget.grid(row=i*2, column=0, sticky="w", pady=(8, 0), padx=(0, 8));
            widget = None
            if key == "brand_model":
                dropdown_frame = tk.Frame(self.form_frame, bg="white")
                dropdown_frame.grid(row=i*2, column=1, pady=(8, 0), padx=(0, 8), sticky="w")
                brand_widget = ttk.Combobox(dropdown_frame, values=list(self.car_brands.keys()), state="readonly", font=("Arial", 16), width=18, textvariable=self.brand_var)
                brand_widget.pack(side="left", padx=(0, 10))
                brand_widget.bind("<<ComboboxSelected>>", self.update_models)
                model_widget = ttk.Combobox(dropdown_frame, values=self.car_brands[self.brand_var.get()], state="readonly", font=("Arial", 16), width=18, textvariable=self.model_var)
                model_widget.pack(side="left")
                self.entries['brand'] = brand_widget
                self.entries['model'] = model_widget
                example_label = tk.Label(self.form_frame, text="Select brand and model", font=("Arial", 9), fg="#888888", bg="white")
                example_label.grid(row=i*2+1, column=1, sticky="w", padx=(0, 8), pady=(0, 0))
                continue
            elif key == "owner_identity":
                widget = ttk.Combobox(self.form_frame, values=["student", "staff", "visitor"], state="readonly", font=("Arial", 16), width=18);
                widget.current(0);
                widget.grid(row=i*2, column=1, pady=(8, 0), padx=(0, 8), sticky="w");
                widget.bind("<<ComboboxSelected>>", self.toggle_owner_id);
                self.entries[key] = widget;
            elif key == "owner_id":
                widget = ctk.CTkEntry(self.form_frame, width=340, height=32, font=("Arial", 16), fg_color="#e3f0ff", text_color="#2c3e50");
                widget.grid(row=i*2, column=1, pady=(8, 0), padx=(0, 8), sticky="w");
                self.entries[key] = widget;
                self.row_map['owner_id'] = i*2;
                self.row_map['owner_id_label'] = label_widget;
            elif key == "entry_reason":
                self.entry_reason_var = tk.StringVar(value="registered");
                radio_frame = tk.Frame(self.form_frame, bg="white");
                radio_frame.grid(row=i*2, column=1, pady=(8, 0), padx=(0, 8), sticky="w");
                tk.Radiobutton(radio_frame, text="Registered", variable=self.entry_reason_var, value="registered", font=("Arial", 16), bg="white", command=self.toggle_other_reason).pack(side="left");
                tk.Radiobutton(radio_frame, text="Others", variable=self.entry_reason_var, value="others", font=("Arial", 16), bg="white", command=self.toggle_other_reason).pack(side="left");
                self.other_reason_label = tk.Label(self.form_frame, text="Reason:", font=("Arial", 16), bg="white", fg="#2c3e50", anchor="w", justify="left", width=10);
                self.other_reason_entry = ctk.CTkTextbox(self.form_frame, width=340, height=80, font=("Arial", 16), fg_color="#e3f0ff", text_color="#2c3e50");
                self.entries['entry_reason_radio'] = self.entry_reason_var;
                self.entries['entry_reason_other'] = self.other_reason_entry;
                self.row_map['entry_reason_row'] = i*2;
            else:
                widget = ctk.CTkEntry(self.form_frame, width=340, height=32, font=("Arial", 16), fg_color="#e3f0ff", text_color="#2c3e50");
                widget.grid(row=i*2, column=1, pady=(8, 0), padx=(0, 8), sticky="w");
                self.entries[key] = widget;

            if key in example_texts:
                example_label = tk.Label(self.form_frame, text=example_texts[key], font=("Arial", 9), fg="#888888", bg="white")
                example_label.grid(row=i*2+1, column=1, sticky="w", padx=(0, 8), pady=(0, 0));

        self.toggle_owner_id()

        btn_frame = tk.Frame(self.form_frame, bg="white")
        btn_frame.grid(row=len(labels)*2, column=0, columnspan=2, pady=30, sticky="w")
        
        ctk.CTkButton(
            btn_frame,
            text="Save",
            fg_color="#3b5ea8",
            text_color="#fff",
            width=120,
            height=32,
            font=("Arial", 16),
            command=self.save_record
        ).pack(side="left", padx=(0, 16))
        
        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            fg_color="#b0b8c9",
            text_color="white",
            hover_color="#8b93a5",
            width=120,
            height=32,
            font=("Arial", 16),
            command=self.cancel
        ).pack(side="left", padx=(0, 16))

    def toggle_owner_id(self, event=None):
        identity = self.entries['owner_identity'].get()
        owner_id_label = self.row_map['owner_id_label']
        owner_id_entry = self.entries['owner_id']
        if identity in ["student", "staff"]:
            owner_id_label.grid()
            owner_id_entry.grid()
        else:
            owner_id_label.grid_remove()
            owner_id_entry.grid_remove()
            owner_id_entry.delete(0, tk.END)

    def toggle_other_reason(self):
        row = self.row_map['entry_reason_row'] + 1
        if self.entry_reason_var.get() == "others":
            self.other_reason_label.grid(row=row, column=0, sticky="w", pady=(0,8), padx=(0,8))
            self.other_reason_entry.grid(row=row, column=1, columnspan=2, sticky="ew", pady=(0,8), padx=(0,8))
        else:
            self.other_reason_label.grid_remove()
            self.other_reason_entry.grid_remove()
            self.other_reason_entry.delete(0, tk.END)

    def play_success_sound(self):
        try:
            winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS)
        except:
            pass

    def play_warning_sound(self):
        try:
            winsound.PlaySound("SystemHand", winsound.SND_ALIAS)
        except:
            pass

    def update_models(self, event=None):
        selected_brand = self.brand_var.get()
        self.entries['model']['values'] = self.car_brands[selected_brand]
        self.model_var.set(self.car_brands[selected_brand][0])

    def save_record(self):
        data = {key: entry.get().strip() if hasattr(entry, 'get') else entry.get() for key, entry in self.entries.items() if key not in ['entry_reason_radio', 'entry_reason_other']}

        entry_reason = self.entry_reason_var.get()
        if entry_reason == "others":
            other_reason = self.other_reason_entry.get("1.0", tk.END).strip()
            if not other_reason:
                self.play_warning_sound()
                messagebox.showerror("Error", "Please specify a reason when selecting 'Others'.")
                return
            entry_reason = other_reason
        else:
            entry_reason = "registered"

        # Validate required fields including entry date and time
        if not data["vehicle_plate"] or not data["owner_identity"] or not data["entry_date"] or not data["entry_time"]:
            self.play_warning_sound()
            messagebox.showerror("Error", "Vehicle Plate, Owner Identity, Entry Date, and Entry Time are required.")
            return

        # Validate owner IC format
        owner_ic = data.get("owner_ic", "").strip()
        if owner_ic:
            if not owner_ic.isdigit() or len(owner_ic) != 12:
                self.play_warning_sound()
                messagebox.showerror("Error", "Owner IC must be exactly 12 digits.")
                return

        # Validate phone number format
        owner_phone = data.get("owner_phone", "").strip()
        if owner_phone:
            if not owner_phone.isdigit() or len(owner_phone) not in [10, 11]:
                self.play_warning_sound()
                messagebox.showerror("Error", "Owner phone number must be 10 or 11 digits.")
                return

        # Handle owner_id
        owner_id = data.get("owner_id", "").strip() if data["owner_identity"] in ["student", "staff"] else None
        if data["owner_identity"] in ["student", "staff"] and not owner_id:
            self.play_warning_sound()
            messagebox.showerror("Error", "Owner ID is required for students and staff.")
            return

        # Handle exit date or time
        exit_date = data.get("exit_date", "").strip()
        exit_time = data.get("exit_time", "").strip()
        if bool(exit_date) != bool(exit_time):
            messagebox.showerror("Error", "Both exit date and time must be provided together.")
            return

        # Validate date formats
        try:
            if data["entry_date"] and data["entry_time"]:
                datetime.datetime.strptime(f"{data['entry_date']} {data['entry_time']}", "%Y-%m-%d %H:%M")
            if exit_date and exit_time:
                datetime.datetime.strptime(f"{exit_date} {exit_time}", "%Y-%m-%d %H:%M")
        except ValueError:
            messagebox.showerror("Error", "Invalid date or time format. Use YYYY-MM-DD for date and HH:MM for time.")
            return

        try:
            # Add the record to the database
            self.firebase_db.add_record(
                vehicle_plate=data["vehicle_plate"],
                owner_identity=data["owner_identity"],
                owner_phone=data.get("owner_phone", ""),
                entry_date=data.get("entry_date", ""),
                entry_time=data.get("entry_time", ""),
                entry_reason=entry_reason,
                owner_id=owner_id,
                exit_date=exit_date,
                exit_time=exit_time,
                owner_name=data.get("owner_name", ""),
                owner_ic=data.get("owner_ic", ""),
                brand=self.brand_var.get(),
                model=self.model_var.get(),
                admin_id=self.user_id
            )

            self.play_success_sound()
            messagebox.showinfo("Success", "Record added successfully.")
            if self.navigate_to:
                self.navigate_to("record_list")
        except Exception as e:
            self.play_warning_sound()
            messagebox.showerror("Error", f"Failed to add record: {e}")

    def cancel(self):
        if self.navigate_to:
            self.navigate_to("record_list") 