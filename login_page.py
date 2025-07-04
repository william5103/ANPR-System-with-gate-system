import customtkinter as ctk
from tkinter import messagebox
from PIL import Image
from firebase_config import firebase_db
from Reset_Password.forgot_password_verification import ForgotPasswordVerification
from Reset_Password.tac_utils import create_and_send_tac
from datetime import datetime, timezone
import bcrypt
import winsound


class LoginPage(ctk.CTkFrame):
    def __init__(self, master, navigate_to_main_menu, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.master = master
        self.navigate_to_main_menu = navigate_to_main_menu
        self.configure(fg_color="white")
        self.bind("<Configure>", self.on_resize)
        self.base_width = 1024
        self.base_height = 768
        self.build_widgets()

    def build_widgets(self):
        self.image = Image.open("Pic/login.png")
        self.user_id_icon_img = Image.open("Pic/user_id_icon.png")
        self.password_icon_img = Image.open("Pic/password_icon.png")

        # Create widgets
        self.image_widget = ctk.CTkLabel(self, text="")
        self.image_widget.place(relx=0.0, rely=0.5, anchor="w")

        self.login_panel = ctk.CTkFrame(self, fg_color="white")
        self.login_panel.place(x=790, y=384, anchor="w")

        self.anpr_label = ctk.CTkLabel(self.login_panel, text="ANPR", text_color="black", justify="center")
        self.software_label = ctk.CTkLabel(self.login_panel, text="SOFTWARE", text_color="black", justify="center")

        self.user_id_frame = ctk.CTkFrame(self.login_panel, fg_color="white", corner_radius=10, border_width=2)
        self.user_id_icon = ctk.CTkLabel(self.user_id_frame, text="", fg_color="white")
        self.user_id_entry = ctk.CTkEntry(self.user_id_frame, placeholder_text="User ID", placeholder_text_color="#747171", text_color="black", fg_color="white", border_width=0)

        self.password_frame = ctk.CTkFrame(self.login_panel, fg_color="white", corner_radius=10, border_width=2)
        self.password_icon = ctk.CTkLabel(self.password_frame, text="", fg_color="white")
        self.password_entry = ctk.CTkEntry(self.password_frame, placeholder_text="Password", placeholder_text_color="#747171", text_color="black", fg_color="white", border_width=0, show="*")

        self.forgot_label = ctk.CTkLabel(self.login_panel, text="Forgot Password?", text_color="black", fg_color="white", cursor="hand2")
        self.forgot_label.bind("<Button-1>", self.forgot_password)

        self.login_button = ctk.CTkButton(self.login_panel, text="LOGIN", command=self.login_action, corner_radius=25, fg_color="#2C2CED", hover_color="#1B1B9C", text_color="white")

        # Pack widgets
        self.anpr_label.pack(pady=0)
        self.software_label.pack(pady=(0, 10))
        self.user_id_frame.pack(pady=10, padx=20, fill="x")
        self.user_id_icon.pack(side="left", padx=10)
        self.user_id_entry.pack(side="left", fill="x", expand=True, padx=(0, 10), pady=5)

        self.password_frame.pack(pady=10, padx=20, fill="x")
        self.password_icon.pack(side="left", padx=10)
        self.password_entry.pack(side="left", fill="x", expand=True, padx=(0, 10), pady=5)

        self.forgot_label.pack(padx=(20, 0), anchor="w")
        self.login_button.pack(pady=20)

        # Initial resize call
        self.on_resize()

        # Bind Return key to login_action
        self.user_id_entry.bind("<Return>", lambda event: self.login_action())
        self.password_entry.bind("<Return>", lambda event: self.login_action())

    def on_resize(self, event=None):
        current_width = self.winfo_width()
        current_height = self.winfo_height()

        scale_w = current_width / self.base_width
        scale_h = current_height / self.base_height
        scale = min(scale_w, scale_h)

        resized_width = max(1, int(self.winfo_width() * 0.72))
        resized_height = max(1, int(self.winfo_height()))
        resized_img = self.image.resize((resized_width, resized_height))
        self.image_widget.configure(image=ctk.CTkImage(light_image=resized_img, size=(resized_width, resized_height)))

        if current_width > self.base_width:
            gap = int(current_width * 0.06)
        else:
            gap = 25

        login_panel_x = resized_width + gap
        self.login_panel.place(x=login_panel_x, y=current_height // 2, anchor="w")

        # Resize icons
        icon_size = max(1, int(30 * scale * 1.5))
        resized_user_icon = self.user_id_icon_img.resize((icon_size, icon_size))
        resized_pass_icon = self.password_icon_img.resize((icon_size, icon_size))
        self.user_id_icon.configure(image=ctk.CTkImage(light_image=resized_user_icon))
        self.password_icon.configure(image=ctk.CTkImage(light_image=resized_pass_icon))

        # Resize fonts
        self.anpr_label.configure(font=("Montserrat", int(50 * scale * 1.6), "bold"))
        self.software_label.configure(font=("Montserrat", int(20 * scale * 1.6)))
        self.user_id_entry.configure(font=("Montserrat", int(10 * scale * 1.6)))
        self.password_entry.configure(font=("Montserrat", int(10 * scale * 1.6)))
        self.forgot_label.configure(font=("Arial", max(int(8 * scale * 1.6), 8)))
        self.login_button.configure(font=("Montserrat", int(18 * scale * 1.2), "bold"), width=int(190 * scale * 1.1))

    def store_warning_in_firestore(self, user_id, role):
        from datetime import datetime
        now = datetime.now()
        warning_message = f"{role.title()} user with ID of '{user_id}' failed to login 3 times within 1 minute."
        firebase_db.add_warning_alert(
            message=warning_message,
            user_id=user_id,
            role=role
        )

    def play_error_sound(self):
        try:
            winsound.PlaySound("SystemHand", winsound.SND_ALIAS)
        except:
            pass

    def play_success_sound(self):
        try:
            winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS)
        except:
            pass

    def login_action(self):
        user_id = self.user_id_entry.get().strip()
        password = self.password_entry.get().strip()
        now = datetime.now(timezone.utc)
        print("Trying login for:", user_id)

        # Lock out check
        lock_ref = firebase_db.db.collection('login_locks').document(user_id)
        lock_doc = lock_ref.get()
        if lock_doc.exists:
            lock_data = lock_doc.to_dict()
            lock_time = lock_data.get('lock_time')
            duration = lock_data.get('duration', 180)
            if hasattr(lock_time, 'to_pydatetime'):
                lock_time = lock_time.to_pydatetime()
            seconds_since_lock = (now - lock_time).total_seconds()
            if seconds_since_lock < duration:
                remaining = int(duration - seconds_since_lock)
                self.play_error_sound()
                messagebox.showwarning("Account Locked", f"Too many failed attempts. Please try again in {remaining} seconds.")
                return
            else:
                # Lockout expired, remove lock
                lock_ref.delete()

        # Track failed attempts
        if not hasattr(self, 'failed_attempts'):
            self.failed_attempts = {}
        attempts = self.failed_attempts.get(user_id, {"count": 0, "first_attempt_time": now})
        if (now - attempts["first_attempt_time"]).total_seconds() > 60:
            attempts = {"count": 0, "first_attempt_time": now}

        # Check in admins collection
        admin_data = firebase_db.get_admin(user_id)
        login_success = False
        if admin_data:
            stored_hash = admin_data.get("admin_password")
            if stored_hash:
                try:
                    if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
                        self.play_success_sound()  # Play success sound
                        messagebox.showinfo("Login Success", f"Welcome, {admin_data['admin_name']}")
                        self.navigate_to_main_menu(
                            user_id=user_id,
                            role="admin",
                            user_name=admin_data["admin_name"]
                        )
                        self.failed_attempts[user_id] = {"count": 0, "first_attempt_time": now}
                        # Remove lock from Firestore if exists
                        firebase_db.db.collection('login_locks').document(user_id).delete()
                        return
                except Exception as e:
                    print("Bcrypt error (admin):", e)

        # Check in security collection
        security_data = firebase_db.get_security_person(user_id)
        print("Security data:", security_data)
        if security_data:
            stored_hash = security_data.get("security_password")
            print("Stored hash:", stored_hash)
            if stored_hash:
                try:
                    if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
                        print("Login success!")
                        self.play_success_sound()
                        messagebox.showinfo("Login Success", f"Welcome, {security_data['security_name']}")
                        self.navigate_to_main_menu(
                            user_id=user_id,
                            role="security",
                            user_name=security_data["security_name"]
                        )
                        self.failed_attempts[user_id] = {"count": 0, "first_attempt_time": now}
                        # Remove lock from Firestore if exists
                        firebase_db.db.collection('login_locks').document(user_id).delete()
                        return
                except Exception as e:
                    print("Bcrypt error (security):", e)
            else:
                print("Password check failed")
        else:
            print("No security data found")

        # Failed login
        attempts["count"] += 1
        self.failed_attempts[user_id] = attempts
        if attempts["count"] >= 3:
            # Only log warning if user_id exists in admin or security
            if admin_data or security_data:
                self.store_warning_in_firestore(user_id, "admin" if admin_data else "security")
            # Lock the user for 3 minutes
            firebase_db.db.collection('login_locks').document(user_id).set({
                'user_id': user_id,
                'lock_time': now,
                'duration': 180
            })
            self.play_error_sound()
            messagebox.showwarning("Account Locked", "Too many failed attempts. Your account is locked for 3 minutes.")
            return
        
        self.play_error_sound()
        messagebox.showwarning("Login Failed", "Invalid User ID or Password")

    def forgot_password(self, event=None):
        self.destroy()
        forgot_password_interface = ForgotPasswordVerification(
            self.master,
            self.return_to_login,
            self.send_tac_code
        )
        forgot_password_interface.pack(fill="both", expand=True)

    def return_to_login(self):
        for widget in self.master.winfo_children():
            widget.destroy()
        new_login = LoginPage(self.master, self.navigate_to_main_menu)
        new_login.pack(fill="both", expand=True)

    def send_tac_code(self, user_id):
        # Retrieve the user email
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
                return None

        if not email:
            messagebox.showerror("Error", "No email address found for this user")
            return None

        tac_code = create_and_send_tac(email, firebase_db, user_id)
        if not tac_code:
            messagebox.showerror("Error", "Failed to send TAC code. Please try again later.")
            return None

        return user_id, user_type


