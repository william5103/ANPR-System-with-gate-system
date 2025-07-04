import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from firebase_config import firebase_db
import datetime
from tkinter import ttk
import winsound

class AdminEditOwner(tk.Frame):
    def __init__(self, master, user_id, user_name, owner, navigate_to=None, navigate_to_login=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.master = master
        self.user_id = user_id
        self.user_name = user_name
        self.owner = owner
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
            text="Edit Owner",
            font=ctk.CTkFont(size=36, weight="bold"),
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
            ("Owner Identity", "owner_identity"),
            ("Owner ID", "owner_id"),
            ("Owner Name", "owner_name"),
            ("Owner IC", "owner_ic"),
            ("Vehicle Plate", "vehicle_plate"),
            ("Owner Phone", "owner_phone"),
            ("Owner Email", "owner_email"),
            ("Status", "status")
        ]

        helper_texts = {
            "owner_identity": "Select owner type (student/staff)",
            "owner_id": "Owner ID cannot be modified",
            "owner_name": "e.g. Ali",
            "owner_ic": "e.g. 123456789012",
            "vehicle_plate": "e.g. ABC1234",
            "owner_phone": "e.g. 0123456789",
            "owner_email": "e.g. abc@gmail.com",
            "status": "Select owner status"
        }

        self.entries = {}
        self.helper_labels = {}
        self.row_map = {}
        self.original_owner_id = self.owner.get("owner_id", "")

        for i, (label, key) in enumerate(labels):
            label_widget = tk.Label(self.form_frame, text=label, font=("Arial", 16), bg="white", anchor="w", justify="left")
            label_widget.grid(row=i*2, column=0, sticky="w", pady=(16, 0), padx=(0, 8))

            if key == "owner_identity":
                combo = ttk.Combobox(self.form_frame, values=["student", "staff"], state="readonly", font=("Arial", 14), width=18)
                combo.set(self.owner.get("owner_identity", "student"))
                combo.grid(row=i*2, column=1, pady=(16, 0), padx=(0, 8), sticky="w")
                self.entries[key] = combo

            elif key == "owner_id":
                entry = ctk.CTkEntry(
                    self.form_frame,
                    width=340,
                    height=38,
                    font=("Arial", 14),
                    fg_color="#e3f0ff",
                    text_color="#2c3e50",
                    state="normal"
                )
                entry.grid(row=i*2, column=1, pady=(16, 0), padx=(0, 8), sticky="w")
                entry.insert(0, self.original_owner_id)
                entry.configure(state="disabled")
                self.entries[key] = entry

                info_label = tk.Label(self.form_frame, text="Owner ID cannot be modified", font=("Arial", 12), fg="red", bg="white")
                info_label.grid(row=i*2+1, column=1, sticky="w", padx=(0, 8))
            elif key == "status":
                combo = ttk.Combobox(self.form_frame, values=["Active", "Expired"], state="readonly", font=("Arial", 14), width=18)
                combo.set(self.owner.get("status", "Active"))
                combo.grid(row=i*2, column=1, pady=(16, 0), padx=(0, 8), sticky="w")
                self.entries[key] = combo
                

                expiry_label = tk.Label(self.form_frame, text="Expiry Date:", font=("Arial", 14), bg="white", anchor="w", justify="left")
                expiry_label.grid(row=(i+1)*2, column=0, sticky="w", pady=(16, 0), padx=(0, 8))
                
                expiry_value = self.owner.get("expiry_date", "N/A")
                expiry_display = tk.Label(
                    self.form_frame,
                    text=expiry_value,
                    font=("Arial", 14),
                    bg="white",
                    fg="#2c3e50"
                )
                expiry_display.grid(row=(i+1)*2, column=1, sticky="w", pady=(16, 0), padx=(0, 8))
                self.expiry_display = expiry_display

                expiry_helper = tk.Label(
                    self.form_frame,
                    text="Expiry date will be automatically set when status changes",
                    font=("Arial", 12),
                    fg="#888",
                    bg="white"
                )
                expiry_helper.grid(row=(i+1)*2+1, column=1, sticky="w", padx=(0, 8))

                combo.bind("<<ComboboxSelected>>", self.on_status_change)
            else:
                entry = ctk.CTkEntry(
                    self.form_frame,
                    width=340,
                    height=38,
                    font=("Arial", 14),
                    fg_color="#e3f0ff",
                    text_color="#2c3e50"
                )
                entry.grid(row=i*2, column=1, pady=(16, 0), padx=(0, 8), sticky="w")
                entry.insert(0, self.owner.get(key, ""))
                self.entries[key] = entry

            if key != "owner_id":
                helper_label = tk.Label(self.form_frame, text=helper_texts[key], font=("Arial", 12), fg="#888", bg="white", anchor="w", justify="left")
                helper_label.grid(row=i*2+1, column=1, sticky="w", padx=(0, 8), pady=(0, 8))
                self.helper_labels[key] = helper_label

        car_brands = {
            "Perodua": ["Alza", "Aruz", "Ativa", "Axia", "Bezza", "Kancil", "Myvi"],
            "Honda": ["Accord",  "City", "Civic"],
            "Toyota": ["Camry", "Corolla", "Vios", "Yaris"]
        }
        brand_value = self.owner.get("brand", "Perodua")
        model_value = self.owner.get("model", car_brands[brand_value][0])
        self.brand_var = tk.StringVar(value=brand_value)
        self.model_var = tk.StringVar(value=model_value)
        car_row = len(labels)*2 + 2
        brand_label = tk.Label(self.form_frame, text="Car Brand", font=("Arial", 14), bg="white", anchor="w", justify="left")
        brand_label.grid(row=car_row, column=0, sticky="w", pady=(16, 0), padx=(0, 8))
        brand_combo = ttk.Combobox(self.form_frame, textvariable=self.brand_var, values=list(car_brands.keys()), state="readonly", font=("Arial", 14), width=18)
        brand_combo.grid(row=car_row, column=1, pady=(16, 0), padx=(0, 8), sticky="w")
        model_label = tk.Label(self.form_frame, text="Car Model", font=("Arial", 14), bg="white", anchor="w", justify="left")
        model_label.grid(row=car_row+1, column=0, sticky="w", pady=(16, 0), padx=(0, 8))
        self.model_combo = ttk.Combobox(self.form_frame, textvariable=self.model_var, values=car_brands[self.brand_var.get()], state="readonly", font=("Arial", 14), width=18)
        self.model_combo.grid(row=car_row+1, column=1, pady=(16, 0), padx=(0, 8), sticky="w")
        def update_models(event=None):
            models = car_brands[self.brand_var.get()]
            self.model_combo["values"] = models
            if self.model_var.get() not in models:
                self.model_var.set(models[0])
        brand_combo.bind("<<ComboboxSelected>>", update_models)

        self.form_frame.grid_columnconfigure(3, weight=1)
        # Place Save and Cancel buttons further right on the same row as model dropdown
        btn_frame = tk.Frame(self.form_frame, bg="white")
        btn_frame.grid(row=car_row+1, column=4, padx=(16, 32), pady=(16, 0), sticky="e")
        self.save_button = ctk.CTkButton(
            btn_frame,
            text="Save",
            fg_color="#3b5ea8",
            text_color="#fff",
            width=90,
            height=32,
            font=("Arial", 14),
            command=self.save_owner
        )
        self.save_button.pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            fg_color="#b0b8c9",
            text_color="white",
            hover_color="#8b93a5",
            width=90,
            height=32,
            font=("Arial", 14),
            command=self.cancel
        ).pack(side="left")

    def validate_email(self, email):
        return "@" in email and "." in email

    def save_owner(self):
        try:
            # Get values from form entries
            owner_name = self.entries['owner_name'].get().strip()
            owner_ic = self.entries['owner_ic'].get().strip()
            owner_identity = self.entries['owner_identity'].get()
            vehicle_plate = self.entries['vehicle_plate'].get().strip()
            owner_phone = self.entries['owner_phone'].get().strip()
            owner_email = self.entries['owner_email'].get().strip()
            status = self.entries['status'].get()

            # Validate required fields
            if not vehicle_plate or not owner_identity:
                self.play_warning_sound()
                messagebox.showerror("Error", "Vehicle Plate and Owner Identity are required.")
                return

            # Validate email format if provided
            if owner_email and not self.validate_email(owner_email):
                self.play_warning_sound()
                messagebox.showerror("Error", "Invalid email format. Email must contain '@' and '.'")
                return

            # Validate owner IC format (must be 12 digits)
            if owner_ic:
                if not owner_ic.isdigit() or len(owner_ic) != 12:
                    self.play_warning_sound()
                    messagebox.showerror("Error", "Owner IC must be exactly 12 digits.")
                    return

            # Validate phone number format (must be 10 or 11 digits)
            if owner_phone:
                if not owner_phone.isdigit() or len(owner_phone) not in [10, 11]:
                    self.play_warning_sound()
                    messagebox.showerror("Error", "Owner phone number must be 10 or 11 digits.")
                    return

            # Set expiry date based on status
            expiry_date = None
            if status == 'Active':
                expiry_date = (datetime.datetime.now() + datetime.timedelta(days=365)).strftime('%Y-%m-%d')
            else:  # Expired
                expiry_date = datetime.datetime.now().strftime('%Y-%m-%d')

            brand = self.brand_var.get()
            model = self.model_var.get()
            if self.firebase_db.update_owner(
                owner_id=self.original_owner_id,
                owner_name=owner_name,
                owner_ic=owner_ic,
                owner_identity=owner_identity,
                owner_phone=owner_phone,
                owner_email=owner_email,
                vehicle_plate=vehicle_plate,
                entry_reason="registered",
                status=status,
                expiry_date=expiry_date,
                brand=brand,
                model=model,
                admin_id=self.user_id
            ):
                self.play_success_sound()
                messagebox.showinfo("Success", "Owner updated successfully.")
                if self.navigate_to:
                    self.navigate_to("owner")
            else:
                self.play_warning_sound()
                messagebox.showerror("Error", "Failed to update owner.")
        except Exception as e:
            self.play_warning_sound()
            messagebox.showerror("Error", f"Failed to update owner: {e}")

    def cancel(self):
        if self.navigate_to:
            self.navigate_to("owner")

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

    def on_status_change(self, event):
        new_status = self.entries['status'].get()
        if new_status == 'Active':
            # Set expiry date to 1 year from now
            new_expiry = (datetime.datetime.now() + datetime.timedelta(days=365)).strftime('%Y-%m-%d')
            self.expiry_display.config(text=new_expiry)
        else:
            # For Expired status, set to today date
            new_expiry = datetime.datetime.now().strftime('%Y-%m-%d')
            self.expiry_display.config(text=new_expiry)