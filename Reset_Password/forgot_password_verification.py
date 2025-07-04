import customtkinter as ctk
from PIL import Image
from .tac_verification_interface import TACVerification
from .tac_utils import create_and_send_tac
from firebase_config import firebase_db
import tkinter.messagebox as messagebox

class ForgotPasswordVerification(ctk.CTkFrame):
    def __init__(self, master, return_callback, send_tac_callback):
        super().__init__(master)
        self.send_tac_callback = send_tac_callback
        self.return_callback = return_callback
        self.user_id = None
        self.configure(fg_color="#f5f5f5")

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
        # Step indicator
        self.steps = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.steps.pack(pady=20)

        steps = ["1. Verify ID", "2. Validate", "3. Reset"]
        self.step_labels = []

        for i, text in enumerate(steps):
            is_active = (i == 0)

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

        self.user_id_entry = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="Enter your User ID",
            fg_color="#FFFFFF",
            placeholder_text_color="#A0A0A0",
            text_color="#2D3436",
            width=400,
            height=50,
            font=("Arial", 18),
            border_width=1

        )
        self.user_id_entry.pack()

        self.create_interactive_buttons()

    def create_interactive_buttons(self):
        button_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        button_frame.pack(pady=20)

        # Back button with hover animation
        self.back_btn = ctk.CTkButton(
            button_frame,
            text="← Back",
            command=self.go_to_login,
            fg_color="transparent",
            text_color="#3498DB",
            font=("Arial", 14),
            hover_color="#EBF5FB",
            width=100,
            height=40,
            corner_radius=10,
            anchor="w"
        )
        self.back_btn.grid(row=0, column=0, padx=(0, 85))

        # Animated verify button
        self.verify_btn = ctk.CTkButton(
            button_frame,
            text="VERIFY",
            command=self.submit_user_id,
            fg_color="#1E88E5",
            hover_color="#1565C0",
            font=("Arial", 14, "bold"),
            text_color="white",
            width=180,
            height=45,
            corner_radius=12,
            border_width=2,
            border_color="#1565C0"
        )
        self.verify_btn.grid(row=1, column=1, padx=(50, 0))

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


    def submit_user_id(self):
        # Disable the button so the user cannot press it again
        self.verify_btn.configure(state="disabled")

        user_id = self.user_id_entry.get().strip()
        if not user_id:
            messagebox.showerror("Error", "Please enter your User ID")
            self.verify_btn.configure(state="normal")
            return

        # Get user email from Firebase
        admin_data = firebase_db.get_admin(user_id)
        if admin_data:
            email = admin_data.get('admin_email')
            user_type = 'admin'
        else:
            security_data = firebase_db.get_security_person(user_id)
            if security_data:
                email = security_data.get('security_email')
                user_type = 'security'
            else:
                messagebox.showerror("Error", "User ID not found")
                self.verify_btn.configure(state="normal")
                return

        if not email:
            messagebox.showerror("Error", "No email address found for this user")
            self.verify_btn.configure(state="normal")
            return

        tac_code = create_and_send_tac(email, firebase_db, user_id)
        if tac_code:
            self.user_id = user_id
            self.show_tac_verification()
        else:
            messagebox.showerror("Error", "Failed to send TAC code. Please try again later.")
            self.verify_btn.configure(state="normal")

    def show_tac_verification(self):
        self.tac_frame = TACVerification(
            self,
            self.user_id,
            self.return_callback
        )
        self.tac_frame.pack(fill="both", expand=True)

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

        entry_width = max(1, int(350 * scale))
        entry_height = max(1, int(50 * scale))
        self.user_id_entry.configure(
            width=entry_width,
            height=entry_height,
            font=("Arial", max(1, int(18 * scale)))
        )

        self.back_btn.configure(
            width=max(1, int(100 * scale)),
            height=max(1, int(40 * scale)),
            font=("Arial", max(1, int(14 * scale)))
        )
        self.verify_btn.configure(
            width=max(1, int(150 * scale)),
            height=max(1, int(45 * scale)),
            font=("Arial", max(1, int(14 * scale)), "bold")
        )

        for label in self.step_labels:
            label.configure(
                font=("Arial", max(1, int(12 * scale)), "bold"),
                padx=max(1, int(15 * scale)),
                pady=max(1, int(6 * scale))
            )

