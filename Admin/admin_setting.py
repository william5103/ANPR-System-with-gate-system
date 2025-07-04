import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from PIL import Image
from firebase_config import firebase_db
from Reset_Password.tac_utils import create_and_send_tac, verify_tac
import re
import bcrypt

ENTRY_FG_COLOR = "#f5f7fa"
ENTRY_TEXT_COLOR = "#1a3e72"
ENTRY_FONT = ("Arial", 18)
LABEL_FONT = ("Arial", 18, "bold")
VALUE_FONT = ("Arial", 18)
BUTTON_FONT = ("Arial", 16, "bold")

class ToggleEntry(ctk.CTkFrame):
    def __init__(self, master, placeholder_text="", show=None, width=400, show_icon_path="Pic/show.png", hide_icon_path="Pic/hide.png", **kwargs):
        super().__init__(master, fg_color="transparent")
        self.show = show
        self.entry = ctk.CTkEntry(self, placeholder_text=placeholder_text, width=width, height=55, fg_color=ENTRY_FG_COLOR, text_color=ENTRY_TEXT_COLOR, font=ENTRY_FONT, show=show)
        self.entry.pack(side="left", fill="x", expand=True)
        self.visible = show is None
        self.show_icon_img = ctk.CTkImage(light_image=Image.open(show_icon_path).resize((28, 28)), size=(28, 28))
        self.hide_icon_img = ctk.CTkImage(light_image=Image.open(hide_icon_path).resize((28, 28)), size=(28, 28))
        self.toggle_btn = ctk.CTkButton(self, text="", width=40, height=40, fg_color="transparent", hover_color="#e0e0e0",image=self.hide_icon_img if not self.visible else self.show_icon_img, command=self.toggle_visibility)
        self.toggle_btn.pack(side="left", padx=(8, 0))
        if show is None:
            self.toggle_btn.pack_forget()

    def toggle_visibility(self):
        self.visible = not self.visible
        if self.visible:
            self.entry.configure(show="")
            self.toggle_btn.configure(image=self.show_icon_img)
        else:
            self.entry.configure(show="*")
            self.toggle_btn.configure(image=self.hide_icon_img)

    def get(self):
        return self.entry.get()

    def insert(self, index, value):
        self.entry.insert(index, value)

    def delete(self, start, end):
        self.entry.delete(start, end)

    def configure(self, **kwargs):
        self.entry.configure(**kwargs)

class TACValidationPopup(tk.Toplevel):
    def __init__(self, parent, email, user_id, firebase_db, on_success):
        super().__init__(parent)
        self.email = email
        self.user_id = user_id
        self.firebase_db = firebase_db
        self.on_success = on_success
        self.title("TAC Verification")
        self.geometry("400x400")
        self.resizable(False, False)
        
        # Center the window
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
        
        self.configure(bg="white")
        self.countdown = None  # Store countdown timer
        self.resend_button = None  # Store resend button reference
        self.attempts_left = 3  # Initialize attempts counter
        self.build_widgets()
        self.tac_code = create_and_send_tac(self.email, self.firebase_db, self.user_id)
        if not self.tac_code:
            messagebox.showerror("Error", "Failed to send TAC code. Please try again.")
            self.destroy()
        else:
            self.start_countdown()

    def build_widgets(self):
        # Main container
        main_container = ctk.CTkFrame(self, fg_color="white", corner_radius=0)
        main_container.pack(fill="both", expand=True)

        # Title
        ctk.CTkLabel(
            main_container,
            text="TAC Verification",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="#1a3e72"
        ).pack(pady=(40, 20))

        ctk.CTkLabel(
            main_container,
            text="A TAC code has been sent to:",
            font=ctk.CTkFont(size=16),
            text_color="#495057"
        ).pack(pady=(10, 5))

        ctk.CTkLabel(
            main_container,
            text=self.email,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#1a3e72"
        ).pack(pady=(0, 30))

        # TAC Entry
        entry_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        entry_frame.pack(pady=(0, 5))

        self.tac_entry = ctk.CTkEntry(
            entry_frame,
            width=250,
            height=45,
            font=ctk.CTkFont(size=20),
            placeholder_text="Enter TAC Code",
            fg_color="white",
            border_color="#1a3e72",
            border_width=2,
            corner_radius=10,
            placeholder_text_color="#6B7280",
            text_color="black"
        )
        self.tac_entry.pack()

        # Error message label
        self.error_label = ctk.CTkLabel(
            main_container,
            text="",
            font=ctk.CTkFont(size=14),
            text_color="#e80e0e"
        )
        self.error_label.pack(pady=(10, 0))

        # Buttons frame
        button_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        button_frame.pack(pady=40)  # Increased padding

        # Verify button
        verify_button = ctk.CTkButton(
            button_frame,
            text="Verify",
            command=self.verify_tac,
            fg_color="#1a3e72",
            hover_color="#2d5ca5",
            height=45,
            width=140,
            corner_radius=8,
            font=ctk.CTkFont(size=16, weight="bold"),
            border_spacing=10
        )
        verify_button.pack(side="left", padx=8)

        # Resend button
        self.resend_button = ctk.CTkButton(
            button_frame,
            text="Resend TAC",
            command=self.resend_tac,
            fg_color="#e5e7eb",
            hover_color="#d1d5db",
            height=45,
            width=140,
            corner_radius=8,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#374151",
            border_spacing=10
        )
        self.resend_button.pack(side="left", padx=8)


        ctk.CTkLabel(
            main_container,
            text="Note: TAC code will expire in 10 minutes",
            font=ctk.CTkFont(size=13),
            text_color="#6B7280"
        ).pack(pady=(20, 40))

        self.tac_entry.bind("<Return>", lambda event: self.verify_tac())

    def verify_tac(self):
        entered_tac = self.tac_entry.get().strip()
        if verify_tac(self.user_id, entered_tac, self.firebase_db):
            if self.countdown:
                self.after_cancel(self.countdown)
            self.on_success()
            self.destroy()
        else:
            self.attempts_left -= 1
            if self.attempts_left > 0:
                self.error_label.configure(
                    text=f"Invalid TAC code. {self.attempts_left} attempts remaining.",
                    text_color="#e80e0e"
                )
                self.tac_entry.delete(0, tk.END)
            else:
                messagebox.showerror(
                    "Verification Failed",
                    "Maximum attempts reached. Password update cancelled."
                )
                if self.countdown:
                    self.after_cancel(self.countdown)
                self.destroy()

    def resend_tac(self):
        # Reset attempts when resending TAC
        self.attempts_left = 3
        self.tac_code = create_and_send_tac(self.email, self.firebase_db, self.user_id)
        if self.tac_code:
            self.error_label.configure(
                text="New TAC code has been sent!",
                text_color="black"
            )
            self.start_countdown()
        else:
            self.error_label.configure(
                text="Failed to send new TAC code.",
                text_color="#e80e0e"
            )

    def start_countdown(self):
        # Disable the resend button and start countdown from 60 seconds
        self.resend_button.configure(state="disabled", text="Resend TAC (60)")
        self.update_countdown(60)

    def update_countdown(self, seconds_left):
        if seconds_left > 0:
            self.resend_button.configure(text=f"Resend TAC ({seconds_left})")
            self.countdown = self.after(1000, lambda: self.update_countdown(seconds_left - 1))
        else:
            self.resend_button.configure(state="normal", text="Resend TAC")
            self.countdown = None

    def destroy(self):
        if self.countdown:
            self.after_cancel(self.countdown)
        super().destroy()

class AdminSetting(ctk.CTkFrame):
    def __init__(self, master, user_id, user_name, user_email='', user_phone='', user_address='', *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.user_id = user_id
        self.user_name = user_name
        self.firebase_db = firebase_db
        # Fetch current admin details from database
        admin = self.firebase_db.get_admin(self.user_id)
        if admin:
            self.user_email = admin.get('admin_email', '')
            self.user_phone = admin.get('admin_phone', '')
            self.user_address = admin.get('admin_address', '')
        else:
            self.user_email = user_email
            self.user_phone = user_phone
            self.user_address = user_address
        self.configure(fg_color="#f0f4ff")
        self.build_widgets()

    def build_widgets(self):
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)

        # Admin details card
        details_card = ctk.CTkFrame(main_container, fg_color="white", corner_radius=12, border_width=1, border_color="#dee2e6")
        details_card.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(details_card, text="👤 Admin Details", font=LABEL_FONT, text_color="#1a3e72").pack(anchor="w", padx=20, pady=(16, 0))
        self.id_label = self._info_row(details_card, "Admin ID:", self.user_id)
        self.name_label = self._info_row(details_card, "Name:", self.user_name)
        self.email_label = self._info_row(details_card, "Email:", self.user_email)
        self.phone_label = self._info_row(details_card, "Phone:", self.user_phone)
        self.address_label = self._info_row(details_card, "Address:", self.user_address, last=True)

        # Change Password Card
        pw_card = ctk.CTkFrame(main_container, fg_color="white", corner_radius=12, border_width=1, border_color="#dee2e6")
        pw_card.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(pw_card, text="🔒 Change Password", font=LABEL_FONT, text_color="#1a3e72").pack(anchor="w", padx=20, pady=(16, 0))
        self.old_pw = ToggleEntry(pw_card, placeholder_text="Current Password", show="*", width=400)
        self.old_pw.pack(anchor="w", padx=20, pady=(10, 0))
        self.new_pw = ToggleEntry(pw_card, placeholder_text="New Password", show="*", width=400)
        self.new_pw.pack(anchor="w", padx=20, pady=(10, 0))
        self.confirm_pw = ToggleEntry(pw_card, placeholder_text="Confirm New Password", show="*", width=400)
        self.confirm_pw.pack(anchor="w", padx=20, pady=(10, 0))
        ctk.CTkButton(pw_card, text="Update Password", command=self.perform_password_update, fg_color="#1769aa", text_color="white", height=50, font=BUTTON_FONT).pack(anchor="w", padx=20, pady=(16, 16))
        self.pw_msg = ctk.CTkLabel(pw_card, text="", text_color="#e80e0e", font=ctk.CTkFont(size=16))
        self.pw_msg.pack(anchor="w", padx=20, pady=(0, 8))

        # Update Contact Card
        contact_card = ctk.CTkFrame(main_container, fg_color="white", corner_radius=12, border_width=1, border_color="#dee2e6")
        contact_card.pack(fill="x", pady=(0, 5))
        ctk.CTkLabel(contact_card, text="Update Email, Phone or Address", font=LABEL_FONT, text_color="#1a3e72").pack(anchor="w", padx=20, pady=(16, 0))

        # Email
        email_row = ctk.CTkFrame(contact_card, fg_color="white")
        email_row.pack(fill="x", padx=20, pady=(10, 0))
        self.email_entry = ToggleEntry(email_row, placeholder_text="Email", width=300)
        self.email_entry.insert(0, self.user_email)
        self.email_entry.pack(side="left", fill="x")
        ctk.CTkButton(email_row, text="Update Email", command=self.perform_email_update, fg_color="#1769aa", text_color="white", height=40, font=BUTTON_FONT, width=150).pack(side="left", padx=(12, 0))

        # Phone
        phone_row = ctk.CTkFrame(contact_card, fg_color="white")
        phone_row.pack(fill="x", padx=20, pady=(10, 0))
        self.phone_entry = ToggleEntry(phone_row, placeholder_text="Phone", width=300)
        self.phone_entry.insert(0, self.user_phone)
        self.phone_entry.pack(side="left", fill="x")
        ctk.CTkButton(phone_row, text="Update Phone", command=self.perform_phone_update, fg_color="#1769aa", text_color="white", height=40, font=BUTTON_FONT, width=150).pack(side="left", padx=(12, 0))

        # Address
        address_row = ctk.CTkFrame(contact_card, fg_color="white")
        address_row.pack(fill="x", padx=20, pady=(10, 0))
        self.address_entry = ctk.CTkTextbox(address_row, width=300, height=100, fg_color=ENTRY_FG_COLOR, text_color=ENTRY_TEXT_COLOR, font=ENTRY_FONT, border_width=2, border_color="#b0b0b0")
        self.address_entry.insert("1.0", self.user_address)
        self.address_entry.pack(side="left", fill="x")
        ctk.CTkButton(address_row, text="Update Address", command=self.perform_address_update, fg_color="#1769aa", text_color="white", height=40, font=BUTTON_FONT, width=150).pack(side="left", padx=(12, 0))

        self.contact_msg = ctk.CTkLabel(contact_card, text="", text_color="#e80e0e", font=ctk.CTkFont(size=16))
        self.contact_msg.pack(anchor="w", padx=20, pady=(0, 8))

    def _info_row(self, parent, label, value, last=False):
        row = ctk.CTkFrame(parent, fg_color="white")
        row.pack(fill="x", padx=20, pady=(10, 0) if not last else (10, 16))
        ctk.CTkLabel(row, text=label, font=LABEL_FONT, text_color="#495057", width=140, anchor="w").pack(side="left")
        value_label = ctk.CTkLabel(row, text=value, font=VALUE_FONT, text_color="#2c3e50", anchor="w")
        value_label.pack(side="left", padx=(10, 0))
        return value_label

    def perform_password_update(self):
        old_pw = self.old_pw.get()
        new_pw = self.new_pw.get()
        confirm_pw = self.confirm_pw.get()
        
        # Validate password fields
        if not old_pw or not new_pw or not confirm_pw:
            self.pw_msg.configure(text="Please fill in all password fields.", text_color="#e80e0e")
            return
            
        if new_pw != confirm_pw:
            self.pw_msg.configure(text="New passwords do not match.", text_color="#e80e0e")
            return
            
        # Password must be at least 8 characters, contain a letter, a number, and a special character
        if len(new_pw) < 8 or not re.search(r'[A-Za-z]', new_pw) or not re.search(r'\d', new_pw) or not re.search(r'[^A-Za-z0-9]', new_pw):
            self.pw_msg.configure(text="Password must be at least 8 characters and include a letter, a number, and a special character.", text_color="#e80e0e")
            return
            
        # Check old password
        admin = self.firebase_db.get_admin(self.user_id)
        stored_hash = admin.get('admin_password', '') if admin else None
        if not admin or not stored_hash or not bcrypt.checkpw(old_pw.encode('utf-8'), stored_hash.encode('utf-8')):
            self.pw_msg.configure(text="Current password is incorrect.", text_color="#e80e0e")
            return

        # Create and show TAC validation popup
        def on_tac_success():
            # Hash the new password before storing
            hashed_pw = bcrypt.hashpw(new_pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            success = self.firebase_db.update_admin(self.user_id, {'admin_password': hashed_pw})
            if success:
                self.pw_msg.configure(text="Password updated successfully!", text_color="#20c997")
                self.old_pw.delete(0, tk.END)
                self.new_pw.delete(0, tk.END)
                self.confirm_pw.delete(0, tk.END)
            else:
                self.pw_msg.configure(text="Failed to update password.", text_color="#e80e0e")

        TACValidationPopup(self, self.user_email, self.user_id, self.firebase_db, on_tac_success)

    def perform_email_update(self):
        email = self.email_entry.get()
        if not email:
            self.contact_msg.configure(text="Please enter an email.", text_color="#e80e0e")
            return
            
        # Validate email format
        if "@" not in email or "." not in email:
            self.contact_msg.configure(text="Invalid email format. Email must contain '@' and '.'", text_color="#e80e0e")
            return
            
        success = self.firebase_db.update_admin(self.user_id, {'admin_email': email})
        if success:
            self.contact_msg.configure(text="Email updated!", text_color="#20c997")
            self.user_email = email
            self.email_label.configure(text=email)
        else:
            self.contact_msg.configure(text="Failed to update email.", text_color="#e80e0e")

    def perform_phone_update(self):
        phone = self.phone_entry.get()
        # Phone must be 10 or 11 digits
        if not phone or not phone.isdigit() or len(phone) not in (10, 11):
            self.contact_msg.configure(text="Phone number must be 10 or 11 digits.", text_color="#e80e0e")
            return
        success = self.firebase_db.update_admin(self.user_id, {'admin_phone': phone})
        if success:
            self.contact_msg.configure(text="Phone updated!", text_color="#20c997")
            self.user_phone = phone
            self.phone_label.configure(text=phone)
        else:
            self.contact_msg.configure(text="Failed to update phone.", text_color="#e80e0e")

    def perform_address_update(self):
        address = self.address_entry.get("1.0", "end").strip()
        if not address:
            self.contact_msg.configure(text="Please enter an address.", text_color="#e80e0e")
        else:
            success = self.firebase_db.update_admin(self.user_id, {'admin_address': address})
            if success:
                self.contact_msg.configure(text="Address updated!", text_color="#20c997")
                self.user_address = address
                self.address_label.configure(text=address)
            else:
                self.contact_msg.configure(text="Failed to update address.", text_color="#e80e0e")
