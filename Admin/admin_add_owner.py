import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from firebase_config import firebase_db
from tkinter import ttk
import winsound



class AdminAddOwner(tk.Frame):
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
            text="Add Owner",
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
            ("Owner Email", "owner_email")
        ]

        helper_texts = {
            "owner_identity": "Select owner type (student/staff)",
            "owner_id": "e.g. 1211102302",
            "owner_name": "e.g. Ali",
            "owner_ic": "e.g. 123456789012",
            "vehicle_plate": "e.g. ABC1234",
            "owner_phone": "e.g. 0123456789",
            "owner_email": "e.g. abc@gmail.com"
        }

        self.entries = {}
        self.helper_labels = {}
        self.row_map = {}

        for i, (label, key) in enumerate(labels):
            label_widget = tk.Label(self.form_frame, text=label, font=("Arial", 16), bg="white", anchor="w", justify="left")
            label_widget.grid(row=i*2, column=0, sticky="w", pady=(12, 0), padx=(0, 8))

            if key == "owner_id":
                self.row_map['owner_id_label'] = label_widget

            if key == "owner_identity":
                combo = ttk.Combobox(self.form_frame, values=["student", "staff"], state="readonly", font=("Arial", 14), width=18)
                combo.current(0)
                combo.grid(row=i*2, column=1, pady=(12, 0), padx=(0, 8), sticky="w")
                combo.bind("<<ComboboxSelected>>", self.toggle_owner_id)
                self.entries[key] = combo

            else:
                entry = ctk.CTkEntry(
                    self.form_frame,
                    width=340,
                    height=36,
                    font=("Arial", 14),
                    fg_color="#e3f0ff",
                    text_color="#2c3e50"
                )
                entry.grid(row=i*2, column=1, pady=(12, 0), padx=(0, 8), sticky="w")
                self.entries[key] = entry


            helper_label = tk.Label(self.form_frame, text=helper_texts[key], font=("Arial", 11), fg="#888", bg="white", anchor="w", justify="left")
            helper_label.grid(row=i*2+1, column=1, sticky="w", padx=(0, 8), pady=(0, 6))
            self.helper_labels[key] = helper_label

        car_brands = {
            "Perodua": ["Alza", "Aruz", "Ativa", "Axia", "Bezza", "Kancil", "Myvi"],
            "Honda": ["Accord",  "City", "Civic"],
            "Toyota": ["Camry", "Corolla", "Vios", "Yaris"]
        }
        self.brand_var = tk.StringVar(value="Perodua")
        self.model_var = tk.StringVar(value=car_brands["Perodua"][0])
        car_row = len(labels)*2
        brand_label = tk.Label(self.form_frame, text="Car Brand", font=("Arial", 16), bg="white", anchor="w", justify="left")
        brand_label.grid(row=car_row, column=0, sticky="w", pady=(12, 0), padx=(0, 8))
        brand_combo = ttk.Combobox(self.form_frame, textvariable=self.brand_var, values=list(car_brands.keys()), state="readonly", font=("Arial", 14), width=18)
        brand_combo.grid(row=car_row, column=1, pady=(12, 0), padx=(0, 8), sticky="w")
        model_label = tk.Label(self.form_frame, text="Car Model", font=("Arial", 16), bg="white", anchor="w", justify="left")
        model_label.grid(row=car_row+1, column=0, sticky="w", pady=(32, 0), padx=(0, 8))
        self.model_combo = ttk.Combobox(self.form_frame, textvariable=self.model_var, values=car_brands[self.brand_var.get()], state="readonly", font=("Arial", 14), width=18)
        self.model_combo.grid(row=car_row+1, column=1, pady=(32, 0), padx=(0, 8), sticky="w")
        def update_models(event=None):
            models = car_brands[self.brand_var.get()]
            self.model_combo["values"] = models
            self.model_var.set(models[0])
        brand_combo.bind("<<ComboboxSelected>>", update_models)

        btn_frame = tk.Frame(self.form_frame, bg="white")
        btn_frame.grid(row=car_row+2, column=0, columnspan=2, pady=24, sticky="w")

        ctk.CTkButton(
            btn_frame,
            text="Save",
            fg_color="#3b5ea8",
            text_color="#fff",
            width=90,
            height=32,
            font=("Arial", 14),
            command=self.save_owner
        ).pack(side="left", padx=(0, 12))

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
        ).pack(side="left", padx=(0, 12))

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

    def validate_email(self, email):
        return "@" in email and "." in email

    def save_owner(self):
        data = {key: entry.get().strip() if hasattr(entry, 'get') else entry.get() for key, entry in self.entries.items()}
        brand = self.brand_var.get()
        model = self.model_var.get()
        
        # Validate required fields
        if not data["owner_name"] or not data["owner_identity"] or not data["vehicle_plate"]:
            self.play_warning_sound()
            messagebox.showerror("Error", "Owner Name, Identity, and Vehicle Plate are required.")
            return

        # Validate email format if provided
        if data["owner_email"] and not self.validate_email(data["owner_email"]):
            self.play_warning_sound()
            messagebox.showerror("Error", "Invalid email format. Email must contain '@' and '.'")
            return

        # Validate owner IC format (must be 12 digits)
        owner_ic = data.get("owner_ic", "").strip()
        if owner_ic:
            if not owner_ic.isdigit() or len(owner_ic) != 12:
                self.play_warning_sound()
                messagebox.showerror("Error", "Owner IC must be exactly 12 digits.")
                return

        # Validate phone number format (must be 10 or 11 digits)
        owner_phone = data.get("owner_phone", "").strip()
        if owner_phone:
            if not owner_phone.isdigit() or len(owner_phone) not in [10, 11]:
                self.play_warning_sound()
                messagebox.showerror("Error", "Owner phone number must be 10 or 11 digits.")
                return

        # Handle owner_id for student/staff
        owner_id = data.get("owner_id", "").strip()
        if not owner_id:
            self.play_warning_sound()
            messagebox.showerror("Error", "Owner ID is required.")
            return

        try:
            # Status will be set to 'Active' and expiry_date will be set to 1 year from now by default
            self.firebase_db.add_owner(
                owner_name=data["owner_name"],
                owner_ic=data["owner_ic"],
                owner_identity=data["owner_identity"],
                owner_id=owner_id,
                owner_phone=data["owner_phone"],
                owner_email=data["owner_email"],
                vehicle_plate=data["vehicle_plate"],
                entry_reason="registered",
                brand=brand,
                model=model,
                admin_id=self.user_id
            )

            self.play_success_sound()
            messagebox.showinfo("Success", "Owner added successfully.")
            if self.navigate_to:
                self.navigate_to("owner")
        except Exception as e:
            self.play_warning_sound()
            messagebox.showerror("Error", f"Failed to add owner: {e}")

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