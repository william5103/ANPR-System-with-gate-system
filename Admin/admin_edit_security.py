import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from firebase_config import firebase_db
from PIL import Image
import winsound
import bcrypt

class AdminEditSecurity(tk.Frame):
    def __init__(self, master, user_id, user_name, security, navigate_to=None, navigate_to_login=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.master = master
        self.user_id = user_id
        self.user_name = user_name
        self.security = security
        self.navigate_to = navigate_to
        self.navigate_to_login = navigate_to_login
        self.firebase_db = firebase_db
        self.show_icon = ctk.CTkImage(light_image=Image.open("Pic/show.png").resize((32, 32)), size=(32, 32))
        self.hide_icon = ctk.CTkImage(light_image=Image.open("Pic/hide.png").resize((32, 32)), size=(32, 32))
        self.build_form()

    def build_form(self):
        self.configure(bg="#f5f5f5")

        # Create main container
        main_container = tk.Frame(self, bg="#f5f5f5")
        main_container.pack(padx=20, pady=20, fill="both", expand=True)

        # Add title at the top
        title_label = ctk.CTkLabel(
            main_container,
            text="Edit Security Personnel",
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
            ("Security ID", "security_id"),
            ("Name", "security_name"),
            ("IC", "security_ic"),
            ("Email", "security_email"),
            ("Phone", "security_phone"),
            ("Address", "security_address"),
            ("Password", "security_password")
        ]

        self.entries = {}
        self.original_security_id = self.security.get("security_id", "")
        self.password_entry = None
        self.password_toggle_btn = None

        helper_texts = {
            "security_id": "Security ID cannot be modified",
            "security_name": "e.g. Ali",
            "security_ic": "e.g. 123456789012",
            "security_email": "e.g. abc@gmail.com",
            "security_phone": "e.g. 0123456789",
            "security_address": "e.g. Bukit Beruang, Melaka"
        }

        for i, (label, key) in enumerate(labels):
            label_widget = tk.Label(self.form_frame, text=label, font=("Arial", 16), bg="white", anchor="w", justify="left")
            label_widget.grid(row=i*2, column=0, sticky="w", pady=(16, 0), padx=(0, 8))
            
            if key == "security_id":
                entry = ctk.CTkEntry(self.form_frame, width=340, height=36, font=("Arial", 16), fg_color="#e3f0ff", text_color="#2c3e50", state="normal")
                entry.grid(row=i*2, column=1, pady=(16, 0), padx=(0, 8), sticky="w")
                entry.insert(0, self.original_security_id)
                entry.configure(state="disabled")
                self.entries[key] = entry
                info_label = tk.Label(self.form_frame, text=helper_texts[key], font=("Arial", 9), fg="red", bg="white")
                info_label.grid(row=i*2+1, column=1, sticky="w", padx=(0, 8))
            elif key == "security_password":
                entry = ctk.CTkEntry(self.form_frame, width=340, height=36, font=("Arial", 16), fg_color="#e3f0ff", text_color="#2c3e50", show="*")
                entry.grid(row=i*2, column=1, pady=(16, 0), padx=(0, 8), sticky="w")
                self.entries[key] = entry
                self.password_entry = entry
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
                info_label = tk.Label(self.form_frame, text="(leave blank to keep current)", font=("Arial", 9), fg="#666666", bg="white")
                info_label.grid(row=i*2+1, column=1, sticky="w", padx=(0, 8))
            else:
                entry = ctk.CTkEntry(self.form_frame, width=340, height=36, font=("Arial", 16), fg_color="#e3f0ff", text_color="#2c3e50")
                entry.grid(row=i*2, column=1, pady=(16, 0), padx=(0, 8), sticky="w")
                entry.insert(0, self.security.get(key, ""))
                self.entries[key] = entry
                # Add helper label below the entry
                helper_label = tk.Label(self.form_frame, text=helper_texts[key], font=("Arial", 10), fg="#888", bg="white", anchor="w", justify="left")
                helper_label.grid(row=i*2+1, column=1, sticky="w", padx=(0, 8), pady=(0, 8))


        btn_frame = tk.Frame(self.form_frame, bg="white")
        btn_frame.grid(row=len(labels)*2, column=0, columnspan=3, pady=30, sticky="w")
        
        self.save_button = ctk.CTkButton(
            btn_frame,
            text="Save",
            fg_color="#3b5ea8",
            text_color="#fff",
            width=120,
            height=36,
            font=("Arial", 16),
            command=self.save_security
        )
        self.save_button.pack(side="left", padx=(0, 16))
        
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

    def validate_email(self, email):
        return "@" in email and "." in email

    def save_security(self):
        try:
            security_name = self.entries['security_name'].get().strip()
            security_ic = self.entries['security_ic'].get().strip()
            security_email = self.entries['security_email'].get().strip()
            security_phone = self.entries['security_phone'].get().strip()
            security_address = self.entries['security_address'].get().strip()
            security_password = self.entries['security_password'].get().strip()

            # Validate required fields
            if not security_name or not security_email or not security_phone or not security_address:
                self.play_warning_sound()
                messagebox.showerror("Error", "Name, Email, Phone, and Address are required.")
                return

            # Validate email format
            if not self.validate_email(security_email):
                self.play_warning_sound()
                messagebox.showerror("Error", "Invalid email format. Email must contain '@' and '.'")
                return

            # Validate IC format (must be 12 digits)
            if not security_ic.isdigit() or len(security_ic) != 12:
                self.play_warning_sound()
                messagebox.showerror("Error", "Security IC must be exactly 12 digits.")
                return

            # Validate phone number format (must be 10 or 11 digits)
            if not security_phone.isdigit() or len(security_phone) not in [10, 11]:
                self.play_warning_sound()
                messagebox.showerror("Error", "Phone number must be 10 or 11 digits.")
                return

            # Validate password only if it's been modified
            if security_password:
                # Check password length
                if len(security_password) < 8:
                    self.play_warning_sound()
                    messagebox.showerror("Error", "Password must be at least 8 characters long.")
                    return

                # Check for at least one letter, one number, and one special character
                has_letter = any(c.isalpha() for c in security_password)
                has_number = any(c.isdigit() for c in security_password)
                has_special = any(not c.isalnum() for c in security_password)

                if not (has_letter and has_number and has_special):
                    self.play_warning_sound()
                    messagebox.showerror("Error", "Password must contain at least one letter, one number, and one special character.")
                    return

            # Store original values for logging
            original_values = {
                'security_name': self.security.get('security_name', ''),
                'security_ic': self.security.get('security_ic', ''),
                'security_email': self.security.get('security_email', ''),
                'security_phone': self.security.get('security_phone', ''),
                'security_address': self.security.get('security_address', '')
            }

            update_data = {
                'security_name': security_name,
                'security_ic': security_ic,
                'security_email': security_email,
                'security_phone': security_phone,
                'security_address': security_address
            }
            if security_password:
                hashed_pw = bcrypt.hashpw(security_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                update_data['security_password'] = hashed_pw

            if self.firebase_db.update_security(
                security_id=self.original_security_id,
                update_data=update_data,
                admin_id=self.user_id
            ):
                self.play_success_sound()
                messagebox.showinfo("Success", "Security personnel updated successfully.")
                if self.navigate_to:
                    self.navigate_to("security")
            else:
                self.play_warning_sound()
                messagebox.showerror("Error", "Failed to update security personnel.")
        except Exception as e:
            self.play_warning_sound()
            messagebox.showerror("Error", f"Failed to update security personnel: {e}")

    def cancel(self):
        if self.navigate_to:
            self.navigate_to("security")

    def play_warning_sound(self):
        try:
            winsound.PlaySound("SystemHand", winsound.SND_ALIAS)
        except:
            pass

    def play_success_sound(self):
        try:
            winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS)
        except:
            pass