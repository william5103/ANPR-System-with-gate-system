import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image
import customtkinter as ctk
from firebase_config import firebase_db
import datetime
import winsound


class AdminOwner(tk.Frame):
    def __init__(self, master, user_id, user_name, navigate_to_login=None, navigate_to=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.master = master
        self.user_id = user_id
        self.user_name = user_name
        self.navigate_to_login = navigate_to_login
        self.navigate_to = navigate_to

        # Pagination attributes
        self.current_page = 0
        self.page_size = 15
        self.all_owners = []
        self.total_pages = 0

        self.firebase_db = firebase_db
        self.prev_img = ctk.CTkImage(Image.open("Pic/prev_button.png").resize((40, 40), Image.LANCZOS))
        self.next_img = ctk.CTkImage(Image.open("Pic/next_button.png").resize((40, 40), Image.LANCZOS))
        self.add_img = ctk.CTkImage(Image.open("Pic/add_vehicle.png").resize((32, 32), Image.LANCZOS))
        self.build_main_area()
        self.check_expired_owners()
        self.load_all_owners()
        self.refresh_table()

    def build_main_area(self):
        self.configure(bg="#f5f5f5")

        # Add title at the top
        title_frame = tk.Frame(self, bg="#f5f5f5")
        title_frame.pack(padx=20, pady=(20, 0), anchor="nw", fill="x")
        
        title_label = ctk.CTkLabel(
            title_frame,
            text="Owner",
            font=ctk.CTkFont(size=30, weight="bold"),
            text_color="#2c3e50",
            anchor="w"
        )
        title_label.pack(side="left")

        # Main area frame
        self.main_area = tk.Frame(self, bg="#f5f5f5")
        self.main_area.pack(fill="both", expand=True)

        # Top bar with status, search and add button
        top_bar = tk.Frame(self.main_area, bg="#f5f5f5")
        top_bar.pack(fill="x", pady=20, padx=30)
        
        # Configure grid columns for centering
        top_bar.grid_columnconfigure(0, weight=0)
        top_bar.grid_columnconfigure(1, weight=1)
        top_bar.grid_columnconfigure(2, weight=0)
        top_bar.grid_columnconfigure(3, weight=1)
        top_bar.grid_columnconfigure(4, weight=0)


        status_frame = tk.Frame(top_bar, bg="#f5f5f5")
        status_frame.grid(row=0, column=0, sticky="w")
        tk.Label(status_frame, text="Status:", font=("Arial", 14), bg="#f5f5f5", fg="#2c3e50").pack(side="left", padx=(0, 5))
        self.status_var = tk.StringVar(value="All")
        status_combo = ttk.Combobox(status_frame, textvariable=self.status_var, values=["All", "Active", "Expired"], 
                                  state="readonly", font=("Arial", 14), width=10)
        status_combo.pack(side="left")
        status_combo.bind("<<ComboboxSelected>>", lambda event: self.search_owners())

        # search
        search_frame = tk.Frame(top_bar, bg="#f5f5f5")
        search_frame.grid(row=0, column=2)
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Search owners...", width=250, height=32, fg_color="#fff", text_color="#2c3e50", font=("Arial", 16))
        self.search_entry.pack(side="left", padx=(0, 10))
        
        self.search_button = ctk.CTkButton(search_frame, text="Search", fg_color="#3b5ea8", hover_color="#4a77d4", text_color="#fff", font=("Arial", 16, "bold"), command=self.search_owners)
        self.search_button.pack(side="left")
        self.search_entry.bind("<Return>", lambda event: self.search_owners())

        # Add button
        self.add_button = ctk.CTkButton(
            top_bar,
            text="Add Owner",
            image=self.add_img,
            compound="left",
            fg_color="#3b5ea8",
            hover_color="#4a77d4",
            text_color="#fff",
            font=ctk.CTkFont(size=16, weight="bold"),
            width=140,
            height=32,
            corner_radius=18,
            command=self.nav_add_owner
        )
        self.add_button.grid(row=0, column=4, sticky="e")

        # Table area
        table_frame = tk.Frame(self.main_area, bg="#f5f5f5")
        table_frame.pack(fill="both", expand=True, padx=30, pady=(0, 10))
        table_frame.update_idletasks()
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

        columns = ("No", "Owner ID", "Owner Name", "IC Number", "Owner Identity", "Vehicle Plate", "Brand", "Model", "Phone Number", "Email", "Status")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        for col in columns:
            self.tree.heading(col, text=col)
            if col == "No":
                self.tree.column(col, anchor="center", width=50)
            elif col == "Status":
                self.tree.column(col, anchor="center", width=100)
            else:
                self.tree.column(col, anchor="center", width=120)
        self.tree.pack(fill="both", expand=True, side="left")

        self.tree.bind("<Double-1>", self.on_row_double_click)


        self.tree.bind('<Configure>', self._on_tree_resize)

        # Pagination controls
        pag_frame = tk.Frame(self.main_area, bg="#f5f5f5")
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

    def _on_tree_resize(self, event):
        row_height = 32
        visible_rows = max(1, (self.tree.winfo_height() - 32) // row_height)
        if self.page_size != visible_rows:
            self.page_size = visible_rows
            total_count = len(self.all_owners)
            self.total_pages = max(1, (total_count + self.page_size - 1) // self.page_size)
            self.current_page = min(self.current_page, self.total_pages - 1)
            self.refresh_table()

    def refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        start_index = self.current_page * self.page_size
        end_index = start_index + self.page_size
        page_owners = self.all_owners[start_index:end_index]
        if not page_owners:
            self.tree.insert("", "end", values=("-", "No owners found", "-", "-", "-", "-", "-", "-", "-"))
        else:
            for i, owner in enumerate(page_owners, start=1):
                values = [
                    i,
                    owner.get('owner_id', 'N/A'),
                    owner.get('owner_name', 'N/A'),
                    owner.get('owner_ic', 'N/A'),
                    owner.get('owner_identity', 'N/A'),
                    owner.get('vehicle_plate', 'N/A'),
                    owner.get('brand', 'N/A'),
                    owner.get('model', 'N/A'),
                    owner.get('owner_phone', 'N/A'),
                    owner.get('owner_email', 'N/A'),
                    owner.get('status', 'N/A')
                ]
                self.tree.insert("", "end", values=values, tags=(str(start_index + i - 1),))
        self.page_counter_label.config(text=f"{self.current_page + 1} of {self.total_pages}")

    def on_row_double_click(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        index = self.tree.index(item)
        owner_index = self.current_page * self.page_size + index
        if owner_index >= len(self.all_owners):
            return
        owner = self.all_owners[owner_index]
        self.show_owner_dialog(owner)

    def show_owner_dialog(self, owner):
        dialog = tk.Toplevel()
        dialog.title("Owner Details")
        dialog.geometry("420x600")
        dialog.configure(bg="#f0f4ff")
        dialog.grab_set()
        dialog.transient(self)
        dialog.resizable(False, False)

        # Main container frame
        main_frame = tk.Frame(dialog, bg="#f0f4ff")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Details frame for owner information
        details_frame = tk.Frame(main_frame, bg="#f0f4ff")
        details_frame.pack(fill="both", expand=True)

        def add_row(row, label, value, bold=False):
            font = ("Arial", 12, "bold") if bold else ("Arial", 12)
            fg = "#3b5ea8" if bold else "#2c3e50"
            
            # Label column
            label_frame = tk.Frame(details_frame, bg="#f0f4ff", width=120)
            label_frame.grid(row=row, column=0, sticky="w", pady=4)
            label_frame.grid_propagate(False)
            tk.Label(label_frame, text=label, font=font, bg="#f0f4ff", fg="#2c3e50", anchor="w").pack(fill="x")
            
            # Value column
            value_frame = tk.Frame(details_frame, bg="#f0f4ff")
            value_frame.grid(row=row, column=1, sticky="w", pady=4, padx=(10,0))
            tk.Label(value_frame, text=value, font=font, bg="#f0f4ff", fg=fg, anchor="w").pack(fill="x")

        # Add owner information rows
        add_row(0, "Owner ID:", owner.get('owner_id', 'N/A'), bold=True)
        add_row(1, "Owner Name:", owner.get('owner_name', 'N/A'), bold=True)
        add_row(2, "IC Number:", owner.get('owner_ic', 'N/A'))
        add_row(3, "Identity:", owner.get('owner_identity', 'N/A'))
        add_row(4, "Phone:", owner.get('owner_phone', 'N/A'))
        add_row(5, "Email:", owner.get('owner_email', 'N/A'))
        add_row(6, "Vehicle Plate:", owner.get('vehicle_plate', 'N/A'))
        add_row(7, "Brand:", owner.get('brand', 'N/A'))
        add_row(8, "Model:", owner.get('model', 'N/A'))
        add_row(9, "Entry Reason:", owner.get('entry_reason', 'N/A'))
        add_row(10, "Status:", owner.get('status', 'Active'), bold=True)
        add_row(11, "Expiry Date:", owner.get('expiry_date', 'N/A'), bold=True)

        # Button frame at the bottom
        btn_frame = tk.Frame(dialog, bg="#f0f4ff")
        btn_frame.pack(side="bottom", pady=20)

        button_style = {
            "width": 100,
            "height": 35,
            "corner_radius": 8,
            "font": ("Arial", 12)
        }

        ctk.CTkButton(
            btn_frame,
            text="Edit",
            fg_color="#6a9ef5",
            hover_color="#4a77d4",
            text_color="#ffffff",
            command=lambda: self._dialog_action(dialog, "edit", owner),
            **button_style
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            btn_frame,
            text="Delete",
            fg_color="#ff8080",
            hover_color="#ff6666",
            text_color="#ffffff",
            command=lambda: self._dialog_action(dialog, "delete", owner),
            **button_style
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            btn_frame,
            text="Close",
            fg_color="#b0b8c9",
            hover_color="#9ca3af",
            text_color="#ffffff",
            command=dialog.destroy,
            **button_style
        ).pack(side="left", padx=10)

        # Center the dialog on the screen
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f'{width}x{height}+{x}+{y}')

    def _dialog_action(self, dialog, action, owner):
        dialog.destroy()
        if action == "edit":
            if self.navigate_to:
                self.navigate_to("edit_owner", owner=owner)
        elif action == "delete":
            self.delete_owner(owner)

    def search_owners(self):
        query = self.search_entry.get().strip().lower()
        status_filter = self.status_var.get()

        all_owners = self.firebase_db.get_owners(limit=999999)
        results = []
        seen_ids = set()
        fields = ['owner_id', 'owner_name', 'vehicle_plate', 'owner_ic', 'owner_email', 'owner_phone', 'entry_reason', 'owner_identity']
        
        for owner in all_owners:
            if status_filter != "All" and owner.get('status', 'Active') != status_filter:
                continue

            if not query:
                unique_id = owner.get('owner_id', '')
                if unique_id and unique_id not in seen_ids:
                    results.append(owner)
                    seen_ids.add(unique_id)
                continue

            for field in fields:
                value = str(owner.get(field, '')).lower()
                if query in value:
                    unique_id = owner.get('owner_id', '')
                    if unique_id and unique_id not in seen_ids:
                        results.append(owner)
                        seen_ids.add(unique_id)
                    break
                    
        self.all_owners = results
        total_count = len(self.all_owners)
        self.total_pages = max(1, (total_count + self.page_size - 1) // self.page_size)
        self.current_page = min(self.current_page, self.total_pages - 1)
        self.refresh_table()

    def load_all_owners(self):
        self.all_owners = self.firebase_db.get_owners(limit=999999)
        total_count = len(self.all_owners)
        self.total_pages = max(1, (total_count + self.page_size - 1) // self.page_size)
        self.current_page = min(self.current_page, self.total_pages - 1)

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

    def nav_add_owner(self):
        if self.navigate_to:
            self.navigate_to("add_owner")

    def delete_owner(self, owner):
        # Confirm deletion with user
        confirm = messagebox.askyesno("Delete Owner", "Are you sure you want to delete this owner?")
        if confirm:
            try:
                owner_id = owner.get('owner_id')
                if not owner_id:
                    self.play_warning_sound()
                    messagebox.showerror("Error", "Owner ID not found.")
                    return

                if self.firebase_db.delete_owner(owner_id, admin_id=self.user_id):
                    self.play_success_sound()
                    messagebox.showinfo("Success", "Owner deleted successfully.")
                    # Refresh the owners list
                    self.load_all_owners()
                    self.refresh_table()
                else:
                    self.play_warning_sound()
                    messagebox.showerror("Error", "Failed to delete owner.")
            except Exception as e:
                self.play_warning_sound()
                messagebox.showerror("Error", f"An error occurred while deleting the owner: {e}")

    def cancel(self):
        if self.navigate_to:
            self.navigate_to("owner")

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

    def check_expired_owners(self):
        try:
            today = datetime.datetime.now().strftime('%Y-%m-%d')
            all_owners = self.firebase_db.get_owners(limit=999999)
            
            for owner in all_owners:
                if owner.get('status') == 'Active':
                    expiry_date = owner.get('expiry_date')
                    if expiry_date and expiry_date < today:
                        # Update to expired status
                        self.firebase_db.update_owner(
                            owner_id=owner.get('owner_id'),
                            status='Expired',
                            admin_id=self.user_id
                        )
        except Exception as e:
            print(f"Error checking expired owners: {e}")