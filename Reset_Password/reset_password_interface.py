import customtkinter as ctk
from tkinter import messagebox
from PIL import Image
from firebase_config import firebase_db
import bcrypt
import re


class ResetPasswordInterface(ctk.CTkFrame):
    def __init__(self, master, user_id, user_type, return_callback):
        super().__init__(master)
        self.user_id = user_id
        self.user_type = user_type
        self.return_callback = return_callback
        self.configure(fg_color="#f5f5f5")

        self.show_icon_original = Image.open("Pic/show.png")
        self.hide_icon_original = Image.open("Pic/hide.png")
        self.show_icon = ctk.CTkImage(light_image=self.show_icon_original, size=(38, 35))
        self.hide_icon = ctk.CTkImage(light_image=self.hide_icon_original, size=(38, 35))

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

    def toggle_password_visibility(self, entry, button):
        if entry.cget("show") == "*":
            entry.configure(show="")
            button.configure(image=self.show_icon)
        else:
            entry.configure(show="*")
            button.configure(image=self.hide_icon)

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
            is_active = (i == 2)
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
        self.password_container = ctk.CTkFrame(
            self.main_frame, fg_color="transparent", width=400, height=50
        )
        self.password_container.pack(padx=40, pady=15)
        self.password_entry = ctk.CTkEntry(
            self.password_container,
            placeholder_text="New Password",
            placeholder_text_color="#A0A0A0",
            show="*",
            text_color="#2D3436",
            width=400,
            height=50,
            font=("Arial", 22),
            corner_radius=10,
            fg_color="#FFFFFF",
            border_width=1
        )
        self.password_entry.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.password_toggle_btn = ctk.CTkButton(
            self.password_container,
            image=self.show_icon,
            text="",
            width=35,
            height=35,
            fg_color="transparent",
            hover=False,
            border_width=0,
            corner_radius=0,
            command=lambda: self.toggle_password_visibility(self.password_entry, self.password_toggle_btn)
        )

        self.password_toggle_btn.place(relx=1.0, rely=0.5, x=-5, anchor="e")


        self.confirm_container = ctk.CTkFrame(
            self.main_frame, fg_color="transparent", width=400, height=50
        )
        self.confirm_container.pack(padx=40, pady=15)
        self.confirm_entry = ctk.CTkEntry(
            self.confirm_container,
            placeholder_text="Confirm Password",
            placeholder_text_color="#A0A0A0",
            show="*",
            text_color="#2D3436",
            width=400,
            height=50,
            font=("Arial", 22),
            corner_radius=10,
            fg_color="#FFFFFF",
            border_width=1
        )
        self.confirm_entry.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.confirm_toggle_btn = ctk.CTkButton(
            self.confirm_container,
            image=self.show_icon,  # initial image
            text="",
            width=35,
            height=35,
            fg_color="transparent",
            hover=False,
            border_width=0,
            corner_radius=0,
            command=lambda: self.toggle_password_visibility(self.confirm_entry, self.confirm_toggle_btn)
        )
        self.confirm_toggle_btn.place(relx=1.0, rely=0.5, x=-5, anchor="e")

        self.create_interactive_buttons()

    def create_interactive_buttons(self):
        button_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        button_frame.pack(pady=20)

        # Back button with hover animation
        self.back_btn = ctk.CTkButton(
            button_frame,
            text="← Back",
            command=self.return_callback,
            fg_color="transparent",
            text_color="#3498DB",
            font=("Arial", 14),
            hover_color="#EBF5FB",
            width=120,
            height=40,
            corner_radius=10
        )
        self.back_btn.grid(row=0, column=0, padx=(0, 55))

        # Animated verify button
        self.reset_btn = ctk.CTkButton(
            button_frame,
            text="CONFIRM",
            command=self.reset_password,
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
        self.reset_btn.grid(row=1, column=1, padx=(50, 0))

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


    def validate_password(self, password):
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not re.search(r"[a-zA-Z]", password):
            return False, "Password must contain at least one letter"
            
        if not re.search(r"\d", password):
            return False, "Password must contain at least one number"
            
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            return False, "Password must contain at least one special character"
            
        return True, "Password is valid"

    def reset_password(self):
        # Get and clean inputs
        password = self.password_entry.get().strip()
        confirm = self.confirm_entry.get().strip()

        self.password_entry.delete(0, "end")
        self.password_entry.insert(0, password)
        self.confirm_entry.delete(0, "end")
        self.confirm_entry.insert(0, confirm)
        
        # Validate empty fields first
        if not password or not confirm:
            messagebox.showerror("Error", "Password fields cannot be empty!")
            self.password_entry.delete(0, "end")
            self.confirm_entry.delete(0, "end")
            return
            
        # Validate password requirements
        is_valid, message = self.validate_password(password)
        if not is_valid:
            messagebox.showerror("Error", message)
            self.password_entry.delete(0, "end")
            self.confirm_entry.delete(0, "end")
            return
            
        # Check password match
        if password != confirm:
            messagebox.showerror("Error", "Passwords do not match. Please try again!")
            self.password_entry.delete(0, "end")
            self.confirm_entry.delete(0, "end")
            return

        if self.user_type == "admin":
            collection = "admins"
            field = "admin_password"
            id_field = "admin_id"
        else:
            collection = "security"
            field = "security_password"
            id_field = "security_id"
        docs = firebase_db.db.collection(collection).where(id_field, "==", self.user_id).stream()
        doc_list = list(docs)
        if not doc_list:
            messagebox.showerror("Error", "User ID not found in the database.")
            return
        doc_id = doc_list[0].id
        # Hash the new password before storing
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        firebase_db.db.collection(collection).document(doc_id).update({field: hashed_pw})
        messagebox.showinfo("Success", "Password reset successfully!")
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

        container_width = max(1, int(400 * scale))
        container_height = max(1, int(60 * scale))

        self.password_container.configure(width=container_width, height=container_height)
        self.confirm_container.configure(width=container_width, height=container_height)

        entry_width = max(1, int(400 * scale))
        entry_height = max(1, int(55 * scale))
        entry_font_size = max(1, int(18 * scale))

        self.password_entry.configure(
            width=entry_width,
            height=entry_height,
            font=("Arial", entry_font_size)
        )
        self.confirm_entry.configure(
            width=entry_width,
            height=entry_height,
            font=("Arial", entry_font_size)
        )

        toggle_width = max(1, int(35 * scale))
        toggle_height = max(1, int(35 * scale))
        resized_show_icon = self.show_icon_original.resize((toggle_width, toggle_height))
        resized_hide_icon = self.hide_icon_original.resize((toggle_width, toggle_height))
        self.show_icon = ctk.CTkImage(light_image=resized_show_icon, size=(toggle_width, toggle_height))
        self.hide_icon = ctk.CTkImage(light_image=resized_hide_icon, size=(toggle_width, toggle_height))
        # Update the toggle buttons based on the current state of the entry (shown as "*" or not)
        if self.password_entry.cget("show") == "*":
            self.password_toggle_btn.configure(image=self.show_icon)
        else:
            self.password_toggle_btn.configure(image=self.hide_icon)
        if self.confirm_entry.cget("show") == "*":
            self.confirm_toggle_btn.configure(image=self.show_icon)
        else:
            self.confirm_toggle_btn.configure(image=self.hide_icon)

        self.back_btn.configure(
            width=max(1, int(120 * scale)),
            height=max(1, int(40 * scale)),
            font=("Arial", max(1, int(14 * scale)))
        )
        self.reset_btn.configure(
            width=max(1, int(180 * scale)),
            height=max(1, int(45 * scale)),
            font=("Arial", max(1, int(14 * scale)), "bold")
        )

        for label in self.step_labels:
            label.configure(
                font=("Arial", max(1, int(12 * scale)), "bold"),
                padx=max(1, int(15 * scale)),
                pady=max(1, int(6 * scale))
            )


