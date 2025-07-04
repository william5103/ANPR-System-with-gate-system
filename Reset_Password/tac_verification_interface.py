import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from firebase_config import firebase_db
from .reset_password_interface import ResetPasswordInterface
from .tac_utils import verify_tac
from PIL import Image

class TACVerification(ctk.CTkFrame):
    def __init__(self, master, user_id, return_callback):
        super().__init__(master)
        self.user_id = user_id
        self.return_callback = return_callback
        self.configure(fg_color="#f5f5f5")
        self.attempts_left = 3

        # Get user type from Firebase
        admin_data = firebase_db.get_admin(user_id)
        if admin_data:
            self.user_type = 'admin'
        else:
            security_data = firebase_db.get_security_person(user_id)
            if security_data:
                self.user_type = 'security'
            else:
                self.user_type = None

        # Make frame expandable
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Main content frame with dynamic sizing
        self.main_frame = ctk.CTkFrame(
            self,
            fg_color="white",
            border_width=1,
            border_color="#E0E0E0",
            corner_radius=20
        )
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        # Configure main frame grid
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Dynamic scaling parameters
        self.base_width = 1024
        self.base_height = 768
        self.scale_factor = 1.0

        # Bind resize event
        self.bind("<Configure>", self.on_resize)

        # Add animated header
        self.create_animated_header()

        # Add progress indicator
        self.create_progress_indicator()

        # Add main content
        self.create_main_content()

        # Add footer
        self.create_footer()

        self.pack(fill="both", expand=True)

    def create_animated_header(self):
        self.email_icon_original = Image.open("Pic/email_icon.png")
        initial_icon = self.email_icon_original.resize((70, 70))
        self.email_icon = ctk.CTkImage(
            light_image=initial_icon,
            size=(70, 70)
        )
        self.icon_label = ctk.CTkLabel(self.main_frame, image=self.email_icon, text="")
        self.icon_label.pack(pady=(40, 20))

        self.title_label = ctk.CTkLabel(
            self.main_frame,
            text="Account Recovery",
            font=("Montserrat", 35, "bold"),
            text_color="#2D3436"
        )
        self.title_label.pack(pady=(0, 10))

    def create_progress_indicator(self):
        self.steps = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.steps.pack(pady=20)

        steps = ["1. Verify ID", "2. Validate", "3. Reset"]
        self.step_labels = []

        for i, text in enumerate(steps):
            is_active = (i == 1)

            label = ctk.CTkLabel(
                self.steps,
                text=text,
                font=("Arial", 12, "bold"),
                text_color="#FFFFFF" if is_active else "#2D3436",
                fg_color="#4CAF50" if is_active else "#E0E0E0",
                corner_radius=15,
                padx=15,
                pady=6
            )
            label.grid(row=0, column=i, padx=8)
            self.step_labels.append(label)

    def create_main_content(self):
        self.input_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.input_frame.pack(padx=40, pady=(30, 0))

        self.tac_entry = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="Enter 6-digit code",
            fg_color="#FFFFFF",
            placeholder_text_color="#A0A0A0",
            text_color="#2D3436",
            width=350,
            height=50,
            font=("Arial", 18),
            border_width=1
        )
        self.tac_entry.pack()

        # Error message label
        self.error_label = ctk.CTkLabel(
            self.input_frame,
            text="",
            font=("Arial", 16),
            text_color="red"
        )
        self.error_label.pack(pady=(10, 0))

        # Interactive buttons
        self.create_interactive_buttons()

    def create_interactive_buttons(self):
        button_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        button_frame.pack(pady=(30, 20))

        # Back and Resend buttons
        top_row = ctk.CTkFrame(button_frame, fg_color="transparent")
        top_row.pack(pady=(0, 15))

        # Back button with hover animation
        self.back_btn = ctk.CTkButton(
            top_row,
            text="← Back",
            command=self.go_to_login,
            fg_color="transparent",  
            text_color="#3498DB",
            font=("Arial", 14),
            hover_color="#D4E9F7",
            width=160,
            height=40,
            corner_radius=8
        )
        self.back_btn.pack(side="left", padx=(0, 30))

        # Resend TAC button
        self.resend_btn = ctk.CTkButton(
            top_row,
            text="Resend TAC",
            command=self.resend_tac,
            fg_color="#E0E0E0",
            hover_color="#D0D0D0",
            text_color="#424242",
            font=("Arial", 14),
            width=160,
            height=40,
            corner_radius=8
        )
        self.resend_btn.pack(side="left")

        # CHECK button
        bottom_row = ctk.CTkFrame(button_frame, fg_color="transparent")
        bottom_row.pack(pady=(0, 20))

        # Animated verify button
        self.validate_btn = ctk.CTkButton(
            bottom_row,
            text="CHECK",
            command=self.verify_tac,
            fg_color="#2196F3",
            hover_color="#1E88E5",
            font=("Arial", 14, "bold"),
            text_color="white",
            width=350,
            height=45,
            corner_radius=8
        )
        self.validate_btn.pack()
        
        # Initialize countdown
        self.countdown = None
        self.start_countdown()

    def create_footer(self):
        security_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        security_frame.pack(pady=30)

        try:
            lock_icon = ctk.CTkImage(
                light_image=Image.open("Pic/lock_icon.png").resize((24, 24)),
                size=(24, 24)
            )
        except Exception as e:
            lock_icon = None

        info_row = ctk.CTkFrame(security_frame, fg_color="transparent")
        info_row.pack()

        if lock_icon:
            ctk.CTkLabel(info_row, image=lock_icon, text="").pack(side="left", padx=(0, 8), pady=(0, 7))

        ctk.CTkLabel(
            info_row,
            text="We take your security seriously",
            font=("Arial", 12),
            text_color="#636E72"
        ).pack(side="left")

    def resend_tac(self):
        # Get user data based on user type
        if self.user_type == 'admin':
            user_data = firebase_db.get_admin(self.user_id)
            email = user_data.get('admin_email', '')
        else:
            user_data = firebase_db.get_security_person(self.user_id)
            email = user_data.get('security_email', '')

        if not email:
            self.error_label.configure(text="Could not find user email")
            return

        from .tac_utils import create_and_send_tac
        new_tac = create_and_send_tac(email, firebase_db, self.user_id)
        
        if new_tac:
            self.error_label.configure(text="New TAC code has been sent!", text_color="black")
            self.start_countdown()
        else:
            self.error_label.configure(text="Failed to send new TAC code", text_color="#e80e0e")

    def start_countdown(self):
        # Disable the resend button and start countdown from 60 seconds
        self.resend_btn.configure(state="disabled", text="Resend TAC (60)")
        self.update_countdown(60)

    def update_countdown(self, seconds_left):
        if seconds_left > 0:
            self.resend_btn.configure(text=f"Resend TAC ({seconds_left})")
            self.countdown = self.after(1000, lambda: self.update_countdown(seconds_left - 1))
        else:
            self.resend_btn.configure(state="normal", text="Resend TAC")
            self.countdown = None

    def verify_tac(self):
        # Disable the verify button to prevent multiple clicks
        self.validate_btn.configure(state="disabled")
        
        entered_tac = self.tac_entry.get().strip()
        
        if not entered_tac:
            self.error_label.configure(text="Please enter the TAC code")
            self.validate_btn.configure(state="normal")
            return
            
        if not entered_tac.isdigit() or len(entered_tac) != 6:
            self.error_label.configure(text="TAC code must be 6 digits")
            self.validate_btn.configure(state="normal")
            return

        # Use the verify_tac function
        if verify_tac(self.user_id, entered_tac, firebase_db):
            self.show_reset_password()
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
                    "Maximum attempts reached. Password reset cancelled."
                )
                # Cancel any ongoing countdown
                if hasattr(self, 'countdown') and self.countdown:
                    self.after_cancel(self.countdown)
                # Return to login page
                self.go_to_login()
            
            self.validate_btn.configure(state="normal")

    def show_reset_password(self):
        if not self.user_type:
            messagebox.showerror("Error", "Could not determine user type")
            return
            
        self.main_frame.destroy()
        self.reset_frame = ResetPasswordInterface(
            self,
            self.user_id,
            self.user_type,
            self.return_callback
        )
        self.reset_frame.pack(fill="both", expand=True)

    def go_to_login(self):
        self.destroy()
        self.return_callback()

    def on_resize(self, event=None):
        current_width = self.winfo_width()
        current_height = self.winfo_height()

        scale_w = current_width / self.base_width
        scale_h = current_height / self.base_height
        scale = min(scale_w, scale_h)

        new_main_width = int(current_width * 0.5)
        new_main_height = int(current_height * 0.5)
        self.main_frame.configure(width=new_main_width, height=new_main_height)
        self.main_frame.place(relx=0.5, rely=0.5, anchor="center")

        icon_size = max(1, int(70 * scale))
        resized_email_icon = self.email_icon_original.resize((icon_size, icon_size))
        self.email_icon = ctk.CTkImage(light_image=resized_email_icon, size=(icon_size, icon_size))
        self.icon_label.configure(image=self.email_icon)

        self.title_label.configure(font=("Montserrat", max(1, int(35 * scale)), "bold"))

        entry_width = max(1, int(350 * scale), 350)
        entry_height = max(1, int(50 * scale))
        self.tac_entry.configure(
            width=entry_width,
            height=entry_height,
            font=("Arial", max(1, int(18 * scale)))
        )

        button_width = max(1, int(160 * scale))
        self.back_btn.configure(
            width=button_width,
            height=max(1, int(40 * scale)),
            font=("Arial", max(1, int(14 * scale)))
        )
        self.resend_btn.configure(
            width=button_width,
            height=max(1, int(40 * scale)),
            font=("Arial", max(1, int(14 * scale)))
        )
        self.validate_btn.configure(
            width=max(1, int(350 * scale)),
            height=max(1, int(45 * scale)),
            font=("Arial", max(1, int(14 * scale)), "bold")
        )

        for label in self.step_labels:
            label.configure(
                font=("Arial", max(1, int(12 * scale)), "bold"),
                padx=max(1, int(15 * scale)),
                pady=max(1, int(6 * scale))
            )
