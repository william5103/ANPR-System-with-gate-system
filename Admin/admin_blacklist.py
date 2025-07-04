import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from firebase_config import firebase_db
from PIL import Image
import winsound

class AdminBlacklist(tk.Frame):
    def __init__(self, master, user_id, user_name, navigate_to_login=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.master = master
        self.user_id = user_id
        self.user_name = user_name
        self.navigate_to_login = navigate_to_login
        self.firebase_db = firebase_db
        self.all_blacklist = []
        self.filtered_blacklist = []
        self.current_page = 0
        self.page_size = 15
        self.total_pages = 1
        self.prev_img = ctk.CTkImage(Image.open("Pic/prev_button.png").resize((40, 40), Image.LANCZOS))
        self.next_img = ctk.CTkImage(Image.open("Pic/next_button.png").resize((40, 40), Image.LANCZOS))
        self.add_img = ctk.CTkImage(Image.open("Pic/blacklist.png").resize((32, 32), Image.LANCZOS))
        self.build_main_area()
        self.load_blacklist()
        self.refresh_table()

    def build_main_area(self):
        self.configure(bg="#f5f5f5")
        title_frame = tk.Frame(self, bg="#f5f5f5")
        title_frame.pack(padx=20, pady=(20, 0), anchor="nw", fill="x")
        title_label = ctk.CTkLabel(
            title_frame,
            text="Blacklist Vehicles",
            font=ctk.CTkFont(size=30, weight="bold"),
            text_color="#2c3e50",
            anchor="w"
        )
        title_label.pack(side="left")
        # Centered Search and Add
        top_bar = tk.Frame(self, bg="#f5f5f5")
        top_bar.pack(fill="x", pady=20, padx=30)
        top_bar.grid_columnconfigure(0, weight=1)
        top_bar.grid_columnconfigure(1, weight=0)
        top_bar.grid_columnconfigure(2, weight=1)
        search_frame = tk.Frame(top_bar, bg="#f5f5f5")
        search_frame.grid(row=0, column=1)
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Search plate number...", width=250, height=32, fg_color="#fff", text_color="#2c3e50", font=("Arial", 16))
        self.search_entry.pack(side="left", padx=(0, 10))
        search_btn = ctk.CTkButton(search_frame, text="Search", fg_color="#3b5ea8", hover_color="#4a77d4", text_color="#fff", font=ctk.CTkFont(size=16, weight="bold"), width=90, height=32, corner_radius=18, command=self.search_blacklist)
        search_btn.pack(side="left")
        self.search_entry.bind("<Return>", lambda event: self.search_blacklist())
        self.add_button = ctk.CTkButton(
            top_bar, 
            text="Add Vehicle", 
            image=self.add_img,
            compound="left",
            fg_color="#3b5ea8",
            hover_color="#4a77d4",
            text_color="#ffffff",
            font=ctk.CTkFont(size=16, weight="bold"),
            width=140,
            height=32,
            corner_radius=18,
            command=self.add_blacklist_popup
        )
        self.add_button.grid(row=0, column=2, sticky="e", padx=(10, 0))
        # Table
        table_frame = tk.Frame(self, bg="#f5f5f5")
        table_frame.pack(fill="both", expand=True, padx=30, pady=(0, 10))
        self.table_frame = table_frame
        style = ttk.Style()
        style.theme_use('default')
        style.configure("Treeview",
                        background="#e6f0ff",
                        foreground="#000000",
                        rowheight=33,
                        fieldbackground="#e6f0ff",
                        font=("Arial", 13))
        style.configure("Treeview.Heading",
                        background="#3b5ea8",
                        foreground="#fff",
                        font=("Arial", 14, "bold"))
        style.map('Treeview.Heading', background=[('active', '#3b5ea8')])
        style.map('Treeview', background=[('selected', '#4a77d4')])
        columns = ("No", "Vehicle Plate", "Reason")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        for col in columns:
            self.tree.heading(col, text=col)
            if col == "No":
                self.tree.column(col, anchor="center", width=40)
            else:
                self.tree.column(col, anchor="center", width=220)
        self.tree.pack(fill="both", expand=True, side="left")
        self.tree.bind('<Double-1>', self.on_row_double_click)
        self.tree.bind('<Configure>', self._on_tree_resize)
        # Pagination controls
        pag_frame = tk.Frame(self, bg="#f5f5f5")
        pag_frame.pack(fill="x", pady=(0, 20), padx=30)
        pag_frame.grid_columnconfigure(0, weight=1)
        pag_frame.grid_columnconfigure(1, weight=0)
        nav_frame = tk.Frame(pag_frame, bg="#f5f5f5")
        nav_frame.grid(row=0, column=1, sticky="e")
        self.prev_button = ctk.CTkButton(nav_frame, text="", image=self.prev_img, fg_color="transparent", width=40, hover=False, command=self.previous_page)
        self.prev_button.pack(side="left")
        self.page_counter_label = tk.Label(nav_frame, text="1 of 1", font=("Arial", 13, "bold"), bg="#f5f5f5", fg="#2c3e50")
        self.page_counter_label.pack(side="left", padx=20)
        self.next_button = ctk.CTkButton(nav_frame, text="", image=self.next_img, fg_color="transparent", width=40, hover=False, command=self.next_page)
        self.next_button.pack(side="left")

    def refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        data = self.filtered_blacklist if self.filtered_blacklist else self.all_blacklist
        total_count = len(data)
        self.total_pages = (total_count + self.page_size - 1) // self.page_size or 1
        start_index = self.current_page * self.page_size
        end_index = start_index + self.page_size
        page_data = data[start_index:end_index]
        if not page_data:
            self.tree.insert("", "end", values=("-", "No vehicles found", "-"))
        else:
            for i, vehicle in enumerate(page_data, start=1 + start_index):
                values = [
                    i,
                    vehicle.get('vehicle_plate', 'N/A'),
                    vehicle.get('reason', 'N/A')
                ]
                self.tree.insert("", "end", values=values)
        self.page_counter_label.config(text=f"{self.current_page + 1} of {self.total_pages}")

    def on_row_double_click(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        index = self.tree.index(item)
        data = self.filtered_blacklist if self.filtered_blacklist else self.all_blacklist
        if index >= len(data):
            return
        vehicle = data[index]
        self.edit_blacklist_popup(vehicle)

    def _on_tree_resize(self, event):
        row_height = 32
        visible_rows = max(1, (self.tree.winfo_height() - 32) // row_height)
        if self.page_size != visible_rows:
            self.page_size = visible_rows
            # Recalculate total_pages and clamp current_page
            data = self.filtered_blacklist if self.filtered_blacklist else self.all_blacklist
            total_count = len(data)
            self.total_pages = max(1, (total_count + self.page_size - 1) // self.page_size)
            self.current_page = min(self.current_page, self.total_pages - 1)
            self.refresh_table()

    def search_blacklist(self):
        query = self.search_entry.get().strip().lower()
        if not query:
            self.filtered_blacklist = []
        else:
            self.filtered_blacklist = [v for v in self.all_blacklist if query in v.get('vehicle_plate', '').lower() or query in v.get('reason', '').lower()]
        # Recalculate total_pages and clamp current_page
        data = self.filtered_blacklist if self.filtered_blacklist else self.all_blacklist
        total_count = len(data)
        self.total_pages = max(1, (total_count + self.page_size - 1) // self.page_size)
        self.current_page = min(self.current_page, self.total_pages - 1)
        self.refresh_table()

    def load_blacklist(self):
        self.all_blacklist = self.firebase_db.get_blacklist(limit=999)
        self.filtered_blacklist = []
        data = self.all_blacklist
        total_count = len(data)
        self.total_pages = max(1, (total_count + self.page_size - 1) // self.page_size)
        self.current_page = min(self.current_page, self.total_pages - 1)
        self.refresh_table()

    def play_success_sound(self):
        try:
            winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS)
        except:
            pass

    def add_blacklist_popup(self):
        popup = tk.Toplevel(self)
        popup.title("Add Blacklist Vehicle")
        popup.geometry("420x320")
        self.center_popup(popup)
        tk.Label(popup, text="Vehicle Plate:", font=("Arial", 14)).pack(pady=(20, 5))
        plate_entry = tk.Entry(popup, font=("Arial", 14))
        plate_entry.pack(pady=5)
        tk.Label(popup, text="Reason:", font=("Arial", 14)).pack(pady=(10, 5))
        reason_text = tk.Text(popup, font=("Arial", 14), width=32, height=4, wrap="word")
        reason_text.pack(pady=5)
        btn_frame = tk.Frame(popup)
        btn_frame.pack(pady=20)
        def submit():
            vehicle_plate = plate_entry.get().strip().upper()
            reason = reason_text.get("1.0", tk.END).strip()
            if not vehicle_plate or not reason:
                self.play_warning_sound()
                messagebox.showerror("Error", "Please fill in all fields.")
                return
            if any(v['vehicle_plate'] == vehicle_plate for v in self.all_blacklist):
                self.play_warning_sound()
                messagebox.showerror("Error", "This vehicle plate is already blacklisted.")
                return
            if self.firebase_db.add_blacklist_vehicle(vehicle_plate, reason, admin_id=self.user_id):
                self.play_success_sound()
                messagebox.showinfo("Success", f"Vehicle {vehicle_plate} added to blacklist.")
                self.load_blacklist()
                popup.destroy()
            else:
                self.play_warning_sound()
                messagebox.showerror("Error", "Failed to add vehicle to blacklist.")

        add_btn = ctk.CTkButton(
            btn_frame,
            text="Add",
            command=submit,
            fg_color="#4CAF50",
            hover_color="#388E3C",
            text_color="white",
            width=80
        )
        add_btn.pack(side="left", padx=10)
        def on_press(event):
            add_btn.configure(fg_color="#256029")
        def on_release(event):
            add_btn.configure(fg_color="#4CAF50")
        add_btn.bind("<ButtonPress-1>", on_press)
        add_btn.bind("<ButtonRelease-1>", on_release)
        ctk.CTkButton(btn_frame, text="Cancel", command=popup.destroy, fg_color="#CCCCCC", hover_color="#AAAAAA", text_color="black", width=80).pack(side="left", padx=10)

    def edit_blacklist_popup(self, vehicle):
        popup = tk.Toplevel(self)
        popup.title("Edit Blacklist Vehicle")
        popup.geometry("420x340")
        self.center_popup(popup)
        tk.Label(popup, text="Vehicle Plate:", font=("Arial", 14)).pack(pady=(20, 5))
        plate_entry = tk.Entry(popup, font=("Arial", 14))
        plate_entry.insert(0, vehicle.get('vehicle_plate', ''))
        plate_entry.configure(state="disabled")
        plate_entry.pack(pady=5)
        tk.Label(popup, text="Reason:", font=("Arial", 14)).pack(pady=(10, 5))
        reason_text = tk.Text(popup, font=("Arial", 14), width=32, height=4, wrap="word")
        reason_text.insert("1.0", vehicle.get('reason', ''))
        reason_text.pack(pady=5)
        btn_frame = tk.Frame(popup)
        btn_frame.pack(pady=20)
        def save():
            reason = reason_text.get("1.0", tk.END).strip()
            if not reason:
                self.play_warning_sound()
                messagebox.showerror("Error", "Please fill in the reason.")
                return
            if self.firebase_db.update_blacklist_vehicle(vehicle['vehicle_plate'], reason, admin_id=self.user_id):
                self.play_success_sound()
                messagebox.showinfo("Success", f"Vehicle {vehicle['vehicle_plate']} updated.")
                self.load_blacklist()
                popup.destroy()
            else:
                self.play_warning_sound()
                messagebox.showerror("Error", "Failed to update blacklist vehicle.")
        def delete():
            if messagebox.askyesno("Delete", f"Are you sure you want to remove {vehicle['vehicle_plate']} from blacklist?"):
                if self.firebase_db.delete_blacklist_vehicle(vehicle['vehicle_plate'], admin_id=self.user_id):
                    self.play_success_sound()
                    messagebox.showinfo("Success", f"Vehicle {vehicle['vehicle_plate']} removed from blacklist.")
                    self.load_blacklist()
                    popup.destroy()
                else:
                    self.play_warning_sound()
                    messagebox.showerror("Error", "Failed to delete blacklist vehicle.")
        ctk.CTkButton(btn_frame, text="Save", command=save, fg_color="#F7C873", hover_color="#E6B04A", text_color="black", width=90, height=38, font=ctk.CTkFont(size=16, weight="bold"), corner_radius=12).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Delete", command=delete, fg_color="#E57373", hover_color="#C62828", text_color="white", width=90, height=38, font=ctk.CTkFont(size=16, weight="bold"), corner_radius=12).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Cancel", command=popup.destroy, fg_color="#CCCCCC", hover_color="#AAAAAA", text_color="black", width=90, height=38, font=ctk.CTkFont(size=16, weight="bold"), corner_radius=12).pack(side="left", padx=10)

    def center_popup(self, popup):
        popup.update_idletasks()
        w = popup.winfo_width()
        h = popup.winfo_height()
        ws = popup.winfo_screenwidth()
        hs = popup.winfo_screenheight()
        x = (ws // 2) - (w // 2)
        y = (hs // 2) - (h // 2)
        popup.geometry(f"+{x}+{y}")

    def handle_action(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        col = self.tree.identify_column(event.x)
        index = self.tree.index(item)
        data = self.filtered_blacklist if self.filtered_blacklist else self.all_blacklist
        if index >= len(data):
            return
        vehicle = data[index]
        if col == '#4':
            # Show a small menu for Edit/Delete
            menu = tk.Menu(self, tearoff=0)
            menu.add_command(label="Edit", command=lambda: self.edit_blacklist_popup(vehicle))
            menu.add_command(label="Delete", command=lambda: self.delete_blacklist_vehicle(vehicle['vehicle_plate']))
            menu.tk_popup(event.x_root, event.y_root)

    def bind_action_column(self):
        self.tree.bind('<Button-3>', self.handle_action)

    def next_page(self):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.refresh_table()
        else:
            self.play_warning_sound()
            messagebox.showinfo("End of Records", "You have reached the last page.")

    def previous_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.refresh_table()
        else:
            self.play_warning_sound()
            messagebox.showinfo("Top of Records", "You are already on the first page.")

    def play_warning_sound(self):
        try:
            winsound.PlaySound("SystemHand", winsound.SND_ALIAS)
        except:
            pass