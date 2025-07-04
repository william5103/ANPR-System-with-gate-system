import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from firebase_config import firebase_db
from PIL import Image
import winsound
import bcrypt

class AdminAddAdmin(tk.Frame):
    def __init__(self, master, user_id, user_name, navigate_to=None, navigate_to_login=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.master = master
        self.user_id = user_id
        self.user_name = user_name
        self.navigate_to = navigate_to
        self.navigate_to_login = navigate_to_login
        self.firebase_db = firebase_db
        self.show_icon = ctk.CTkImage(light_image=Image.open("Pic/show.png").resize((32, 32)), size=(32, 32))
        self.hide_icon = ctk.CTkImage(light_image=Image.open("Pic/hide.png").resize((32, 32)), size=(32, 32))
        self.build_form()

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

    def build_form(self):
        self.configure(bg="#f5f5f5")

        # Create main container
        main_container = tk.Frame(self, bg="#f5f5f5")
        main_container.pack(padx=20, pady=20, fill="both", expand=True)

        # Add title at the top
        title_label = ctk.CTkLabel(
            main_container,
            text="Add Admin",
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
            ("Admin ID", "admin_id"),
            ("Name", "admin_name"),
            ("IC", "admin_ic"),
            ("Email", "admin_email"),
            ("Phone", "admin_phone"),
            ("Address", "admin_address"),
            ("Password", "admin_password")
        ]

        self.entries = {}
        self.password_entry = None
        self.password_toggle_btn = None

        helper_texts = {
            "admin_id": "ADM1",
            "admin_name": "e.g. Ali",
            "admin_ic": "e.g. 123456789012",
            "admin_email": "e.g. abc@gmail.com",
            "admin_phone": "e.g. 0123456789",
            "admin_address": "e.g. Bukit Beruang, Melaka"
        }

        for i, (label, key) in enumerate(labels):
            label_widget = tk.Label(self.form_frame, text=label, font=("Arial", 16), bg="white", anchor="w", justify="left")
            label_widget.grid(row=i*2, column=0, sticky="w", pady=(16, 0), padx=(0, 8))
            show = "*" if key == "admin_password" else None
            entry = ctk.CTkEntry(self.form_frame, width=340, height=36, font=("Arial", 16), fg_color="#e3f0ff", text_color="#2c3e50", show=show)
            entry.grid(row=i*2, column=1, pady=(16, 0), padx=(0, 8), sticky="w")
            self.entries[key] = entry
            if key == "admin_password":
                self.password_entry = entry
                # Add show/hide button
                self.password_toggle_btn = ctk.CTkButton(
                    self.form_frame,
                    image=self.show_icon,
                    text="",
                    width=38,
                    height=38,
                    fg_color="transparent",
                    hover=False,
                    border_width=0,
                    corner_radius=0,
                    command=self.toggle_password_visibility
                )
                self.password_toggle_btn.grid(row=i*2, column=2, padx=(4,0), pady=(16, 0), sticky="w")
            else:

                helper_label = tk.Label(self.form_frame, text=helper_texts[key], font=("Arial", 10), fg="#888", bg="white", anchor="w", justify="left")
                helper_label.grid(row=i*2+1, column=1, sticky="w", padx=(0, 8), pady=(0, 8))

        btn_frame = tk.Frame(self.form_frame, bg="white")
        btn_frame.grid(row=len(labels)*2, column=0, columnspan=3, pady=(40, 30), sticky="w")
        
        ctk.CTkButton(
            btn_frame,
            text="Save",
            fg_color="#3b5ea8",
            text_color="#fff",
            width=120,
            height=36,
            font=("Arial", 16),
            command=self.save_admin
        ).pack(side="left", padx=(0, 16))

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            fg_color="#b0b8c9",
            text_color="white",
            hover_color="#8b93a5",
            width=120,
            height=36,
            font=("Arial", 16),
            command=self.cancel
        ).pack(side="left", padx=(0, 16))

    def toggle_password_visibility(self):
        if self.password_entry.cget("show") == "*":
            self.password_entry.configure(show="")
            self.password_toggle_btn.configure(image=self.hide_icon)
        else:
            self.password_entry.configure(show="*")
            self.password_toggle_btn.configure(image=self.show_icon)

    def save_admin(self):
        data = {key: entry.get().strip() if hasattr(entry, 'get') else entry.get() for key, entry in self.entries.items()}
        
        # Validate required fields
        if not data["admin_id"] or not data["admin_name"] or not data["admin_ic"] or not data["admin_email"] or not data["admin_phone"] or not data["admin_address"] or not data["admin_password"]:
            self.play_warning_sound()
            messagebox.showerror("Error", "All fields are required.")
            return

        # Validate IC format (must be 12 digits)
        admin_ic = data.get("admin_ic", "").strip()
        if not admin_ic.isdigit() or len(admin_ic) != 12:
            self.play_warning_sound()
            messagebox.showerror("Error", "Admin IC must be exactly 12 digits.")
            return

        # Validate phone number format (must be 10 or 11 digits)
        admin_phone = data.get("admin_phone", "").strip()
        if not admin_phone.isdigit() or len(admin_phone) not in [10, 11]:
            self.play_warning_sound()
            messagebox.showerror("Error", "Phone number must be 10 or 11 digits.")
            return

        # Validate password complexity
        admin_password = data.get("admin_password", "").strip()
        if len(admin_password) < 8:
            self.play_warning_sound()
            messagebox.showerror("Error", "Password must be at least 8 characters long.")
            return

        # Check for at least one letter, one number, and one special character
        has_letter = any(c.isalpha() for c in admin_password)
        has_number = any(c.isdigit() for c in admin_password)
        has_special = any(not c.isalnum() for c in admin_password)

        if not (has_letter and has_number and has_special):
            self.play_warning_sound()
            messagebox.showerror("Error", "Password must contain at least one letter, one number, and one special character.")
            return

        try:
            # Hash the password before saving
            hashed_pw = bcrypt.hashpw(data["admin_password"].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            # Add the admin to the database
            self.firebase_db.add_admin(
                admin_id=data["admin_id"],
                admin_name=data["admin_name"],
                admin_ic=data["admin_ic"],
                admin_address=data["admin_address"],
                admin_phone=data["admin_phone"],
                admin_email=data["admin_email"],
                admin_password=hashed_pw,
                performed_by=self.user_id
            )

            self.play_success_sound()
            messagebox.showinfo("Success", "Admin added successfully.")
            if self.navigate_to:
                self.navigate_to("admin")
        except Exception as e:
            self.play_warning_sound()
            messagebox.showerror("Error", f"Failed to add admin: {e}")

    def cancel(self):
        if self.navigate_to:
            self.navigate_to("admin") 