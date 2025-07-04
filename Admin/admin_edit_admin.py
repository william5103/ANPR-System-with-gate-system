import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from firebase_config import firebase_db
from PIL import Image
import winsound
import bcrypt

class AdminEditAdmin(tk.Frame):
    def __init__(self, master, user_id, user_name, admin, navigate_to=None, navigate_to_login=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.master = master
        self.user_id = user_id
        self.user_name = user_name
        self.admin = admin
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
            text="Edit Admin",
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
        self.original_admin_id = self.admin.get("admin_id", "")
        self.password_entry = None
        self.password_toggle_btn = None

        helper_texts = {
            "admin_id": "Admin ID cannot be modified",
            "admin_name": "e.g. Ali",
            "admin_ic": "e.g. 123456789012",
            "admin_email": "e.g. abc@gmail.com",
            "admin_phone": "e.g. 0123456789",
            "admin_address": "e.g. Bukit Beruang, Melaka"
        }

        for i, (label, key) in enumerate(labels):
            label_widget = tk.Label(self.form_frame, text=label, font=("Arial", 16), bg="white", anchor="w", justify="left")
            label_widget.grid(row=i*2, column=0, sticky="w", pady=(16, 0), padx=(0, 8))
            
            if key == "admin_id":
                entry = ctk.CTkEntry(self.form_frame, width=340, height=36, font=("Arial", 16), fg_color="#e3f0ff", text_color="#2c3e50", state="normal")
                entry.grid(row=i*2, column=1, pady=(16, 0), padx=(0, 8), sticky="w")
                entry.insert(0, self.original_admin_id)
                entry.configure(state="disabled")
                self.entries[key] = entry
                info_label = tk.Label(self.form_frame, text=helper_texts[key], font=("Arial", 9), fg="red", bg="white")
                info_label.grid(row=i*2+1, column=1, sticky="w", padx=(0, 8))
            elif key == "admin_password":
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
                entry.insert(0, self.admin.get(key, ""))
                self.entries[key] = entry
                # Add helper label below the entry
                helper_label = tk.Label(self.form_frame, text=helper_texts[key], font=("Arial", 10), fg="#888", bg="white", anchor="w", justify="left")
                helper_label.grid(row=i*2+1, column=1, sticky="w", padx=(0, 8), pady=(0, 8))

        btn_frame = tk.Frame(self.form_frame, bg="white")
        btn_frame.grid(row=len(labels)*2, column=0, columnspan=3, pady=30, sticky="w")
        
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
        try:
            admin_name = self.entries['admin_name'].get().strip()
            admin_ic = self.entries['admin_ic'].get().strip()
            admin_email = self.entries['admin_email'].get().strip()
            admin_phone = self.entries['admin_phone'].get().strip()
            admin_address = self.entries['admin_address'].get().strip()
            admin_password = self.entries['admin_password'].get().strip()

            # Validate required fields
            if not admin_name or not admin_ic or not admin_email or not admin_phone or not admin_address:
                self.play_warning_sound()
                messagebox.showerror("Error", "All fields are required except password.")
                return

            # Validate IC format (must be 12 digits)
            if not admin_ic.isdigit() or len(admin_ic) != 12:
                self.play_warning_sound()
                messagebox.showerror("Error", "Admin IC must be exactly 12 digits.")
                return

            # Validate phone number format (must be 10 or 11 digits)
            if not admin_phone.isdigit() or len(admin_phone) not in [10, 11]:
                self.play_warning_sound()
                messagebox.showerror("Error", "Phone number must be 10 or 11 digits.")
                return

            # Validate password only if it's been modified
            if admin_password:
                # Check password length
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

            update_data = {
                'admin_name': admin_name,
                'admin_ic': admin_ic,
                'admin_email': admin_email,
                'admin_phone': admin_phone,
                'admin_address': admin_address
            }
            if admin_password:
                hashed_pw = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                update_data['admin_password'] = hashed_pw

            if self.firebase_db.update_admin(
                admin_id=self.original_admin_id,
                update_data=update_data,
                performed_by=self.user_id
            ):
                self.play_success_sound()
                messagebox.showinfo("Success", "Admin updated successfully.")
                if self.navigate_to:
                    self.navigate_to("admin")
            else:
                self.play_warning_sound()
                messagebox.showerror("Error", "Failed to update admin.")
        except Exception as e:
            self.play_warning_sound()
            messagebox.showerror("Error", f"Failed to update admin: {e}")

    def cancel(self):
        if self.navigate_to:
            self.navigate_to("admin") 