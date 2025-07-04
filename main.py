import customtkinter as ctk
from login_page import LoginPage
from Security.security_main_menu import SecurityMainMenu
from Admin.admin_main_menu import AdminMainMenu


class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("PlateVision")
        # Set window size and center it
        window_width, window_height = 1980, 1000
        self.center_window(window_width, window_height)
        ctk.set_appearance_mode("dark")

        # Initialize page attributes
        self.login_page = None
        self.security_menu = None
        self.admin_menu = None

        self.show_login_page()

    def center_window(self, width, height):
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = int((screen_width / 2) - (width / 2))
        y = int((screen_height / 2) - (height / 2))
        self.geometry(f"{width}x{height}+{x}+{y}")

    def show_login_page(self):
        # Display login page
        self.clear_screen()
        self.login_page = LoginPage(self, self.show_main_menu)
        self.login_page.pack(fill="both", expand=True)

    def show_main_menu(self, user_id, role, user_name):
        if not user_id or not role:
            print("Error: Missing user information!")
            return

        self.clear_screen()

        if role == "security":
            self.security_menu = SecurityMainMenu(
                self,
                user_id=user_id,
                user_name=user_name,
                navigate_to_login=self.show_login_page
            )
            self.security_menu.pack(fill="both", expand=True)

        else:
            self.admin_menu = AdminMainMenu(
                self,
                user_id=user_id,
                user_name=user_name,
                navigate_to_login=self.show_login_page
            )
            self.admin_menu.pack(fill="both", expand=True)


    def clear_screen(self):
        for widget in self.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
