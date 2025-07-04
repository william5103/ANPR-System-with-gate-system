import tkinter as tk
from tkinter import messagebox
from PIL import Image
import customtkinter as ctk
from firebase_config import firebase_db
import datetime
from tkinter import ttk
import winsound

class SecurityRecord(tk.Frame):
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
        self.all_records = []
        self.total_pages = 0

        # Widget variables initialization
        self.top_bar = None
        self.bottom_frame = None
        self.back_icon = None
        self.back_button = None
        self.record_label = None
        self.icon_image = None
        self.user_button = None
        self.add_button = None
        self.user_menu_frame = None
        self.search_frame = None
        self.search_container = None
        self.search_icon = None
        self.search_entry = None
        self.table_frame = None
        self.table_text = None
        self.prev_icon = None
        self.pagination_frame = None
        self.next_icon = None
        self.next_button = None
        self.prev_button = None
        self.page_counter_label = None
        self.pagination_subframe = None

        # Icon images for Action buttons
        self.view_icon = None
        self.edit_icon = None
        self.delete_icon = None

        # Load button images
        self.prev_img = ctk.CTkImage(Image.open("Pic/prev_button.png").resize((40, 40), Image.LANCZOS))
        self.next_img = ctk.CTkImage(Image.open("Pic/next_button.png").resize((40, 40), Image.LANCZOS))
        self.add_img = ctk.CTkImage(Image.open("Pic/add_record.png").resize((32, 32), Image.LANCZOS))

        # Remove extra Frame borders
        self.config(bg="#f5f5f5", bd=0, highlightthickness=0)
        self.configure(bg="#f5f5f5")
        self.firebase_db = firebase_db
        self.build_main_area()
        self.load_all_records()
        self.refresh_table()

    def build_main_area(self):
        self.configure(bg="#f5f5f5")

        # Add title at the top
        title_label = ctk.CTkLabel(
            self,
            text="Records",
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color="#2c3e50",
            anchor="w"
        )
        title_label.pack(anchor="w", padx=30, pady=(20, 10))

        # Top bar with search and add button
        top_bar = tk.Frame(self, bg="#f5f5f5")
        top_bar.pack(fill="x", pady=(0, 20), padx=30)
        top_bar.grid_columnconfigure(0, weight=1)
        top_bar.grid_columnconfigure(1, weight=0)
        top_bar.grid_columnconfigure(2, weight=1)

        search_frame = tk.Frame(top_bar, bg="#f5f5f5")
        search_frame.grid(row=0, column=1, padx=(60, 0))
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Search records...", width=250, height=32, fg_color="#fff", text_color="#2c3e50", font=("Arial", 16))
        self.search_entry.pack(side="left", padx=(0, 10))
        self.search_button = ctk.CTkButton(search_frame, text="Search", fg_color="#3b5ea8", hover_color="#4a77d4", text_color="#fff", font=("Arial", 16, "bold"), command=self.search_records)
        self.search_button.pack(side="left", padx=(0, 0))
        self.search_entry.bind("<Return>", lambda event: self.search_records())

        self.add_button = ctk.CTkButton(
            top_bar,
            text="Add Record",
            image=self.add_img,
            compound="left",
            fg_color="#3b5ea8",
            hover_color="#4a77d4",
            text_color="#fff",
            font=("Arial", 16, "bold"),
            width=140,
            height=32,
            corner_radius=18,
            command=self.nav_add_record
        )
        self.add_button.grid(row=0, column=2, sticky="e", padx=(10, 0))

        # Table area
        table_frame = tk.Frame(self, bg="#f5f5f5")
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

        columns = ("No", "Vehicle Plate", "Brand", "Model", "Owner Identity", "Entry Date", "Entry Time", "Exit Date", "Exit Time", "Entry Reason")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=140)
        self.tree.pack(fill="both", expand=True, side="left")

        # Bind double-click event
        self.tree.bind("<Double-1>", self.on_row_double_click)
        self.tree.bind("<Configure>", self._on_tree_resize)

        # Pagination frame at the bottom
        pagination_frame = tk.Frame(self, bg="#f5f5f5")
        pagination_frame.pack(fill="x", padx=30, pady=10)

        pagination_buttons = tk.Frame(pagination_frame, bg="#f5f5f5")
        pagination_buttons.pack(side="right")

        # Previous button
        self.prev_button = ctk.CTkButton(
            pagination_buttons,
            text="",
            image=self.prev_img,
            fg_color="transparent",
            width=40,
            hover=False,
            command=self.previous_page
        )
        self.prev_button.pack(side="left", padx=5)

        # Page counter
        self.page_counter_label = tk.Label(
            pagination_buttons,
            text="1 of 1",
            bg="#f5f5f5",
            font=("Arial", 12)
        )
        self.page_counter_label.pack(side="left", padx=10)

        # Next button
        self.next_button = ctk.CTkButton(
            pagination_buttons,
            text="",
            image=self.next_img,
            fg_color="transparent",
            width=40,
            hover=False,
            command=self.next_page
        )
        self.next_button.pack(side="left", padx=5)

    def _on_tree_resize(self, event):
        row_height = 32
        visible_rows = max(1, (self.tree.winfo_height() - 32) // row_height)
        if self.page_size != visible_rows:
            self.page_size = visible_rows
            total_count = len(self.all_records)
            self.total_pages = max(1, (total_count + self.page_size - 1) // self.page_size)
            self.current_page = min(self.current_page, self.total_pages - 1)
            self.refresh_table()

    def refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        # Pagination
        start_index = self.current_page * self.page_size
        end_index = start_index + self.page_size
        page_records = self.all_records[start_index:end_index]
        if not page_records:
            self.tree.insert("", "end", values=("-", "No records found", "-", "-", "-", "-", "-", "-", "-", "-"))
        else:
            for i, record in enumerate(page_records, start=1):
                entry_dt = record.get('entry_datetime')
                if isinstance(entry_dt, datetime.datetime):
                    entry_date = entry_dt.strftime('%Y-%m-%d')
                    entry_time = entry_dt.strftime('%H:%M')
                elif isinstance(entry_dt, str) and ' ' in entry_dt:
                    entry_date, entry_time = entry_dt.split(' ', 1)
                else:
                    entry_date = record.get('entry_date', 'N/A')
                    entry_time = record.get('entry_time', 'N/A')

                exit_dt = record.get('exit_datetime')
                if isinstance(exit_dt, datetime.datetime):
                    exit_date = exit_dt.strftime('%Y-%m-%d')
                    exit_time = exit_dt.strftime('%H:%M')
                elif isinstance(exit_dt, str) and ' ' in exit_dt:
                    exit_date, exit_time = exit_dt.split(' ', 1)
                else:
                    exit_date = record.get('exit_date', 'N/A')
                    exit_time = record.get('exit_time', 'N/A')

                values = [
                    i,
                    record.get('vehicle_plate', 'N/A'),
                    record.get('brand', 'N/A'),
                    record.get('model', 'N/A'),
                    record.get('owner_identity', 'N/A'),
                    entry_date,
                    entry_time,
                    exit_date,
                    exit_time,
                    record.get('entry_reason', 'N/A')
                ]
                self.tree.insert("", "end", values=values, tags=(str(start_index + i - 1),))
        self.page_counter_label.config(text=f"{self.current_page + 1} of {self.total_pages}")

    def on_row_double_click(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        index = self.tree.index(item)
        record_index = self.current_page * self.page_size + index
        if record_index >= len(self.all_records):
            return
        record = self.all_records[record_index]
        self.show_record_dialog(record)

    def show_record_dialog(self, record):
        dialog = tk.Toplevel()
        dialog.title("Record Details")
        dialog.geometry("420x660")
        dialog.configure(bg="#f0f4ff")
        dialog.grab_set()
        dialog.transient(self)
        dialog.resizable(False, False)

        # Main container frame
        main_frame = tk.Frame(dialog, bg="#f0f4ff")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # title
        title_label = ctk.CTkLabel(
            main_frame,
            text="Security Action Details",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#3b5ea8"
        )
        title_label.pack(anchor="w", pady=(0, 20))

        # Details frame for record information
        details_frame = tk.Frame(main_frame, bg="#f0f4ff")
        details_frame.pack(fill="both", expand=True)

        def add_row(row, label, value, bold=False):
            font = ("Arial", 12, "bold") if bold else ("Arial", 12)
            fg = "#3b5ea8" if bold else "#2c3e50"

            label_frame = tk.Frame(details_frame, bg="#f0f4ff", width=120)
            label_frame.grid(row=row, column=0, sticky="w", pady=4)
            label_frame.grid_propagate(False)
            tk.Label(label_frame, text=label, font=font, bg="#f0f4ff", fg="#2c3e50", anchor="w").pack(fill="x")

            value_frame = tk.Frame(details_frame, bg="#f0f4ff")
            value_frame.grid(row=row, column=1, sticky="w", pady=4, padx=(10,0))
            if label.strip() == "Entry Reason:":
                tk.Label(value_frame, text=value, font=font, bg="#f0f4ff", fg=fg, anchor="w", wraplength=250, justify="left").pack(fill="x")
            else:
                tk.Label(value_frame, text=value, font=font, bg="#f0f4ff", fg=fg, anchor="w").pack(fill="x")

        entry_date = record.get('entry_date', 'N/A')
        entry_time = record.get('entry_time', 'N/A')
        exit_date = record.get('exit_date', 'N/A')
        exit_time = record.get('exit_time', 'N/A')

        # Add record information rows
        add_row(0, "Record ID:", record.get('record_id', 'N/A'), bold=False)
        add_row(1, "Vehicle Plate:", record.get('vehicle_plate', 'N/A'), bold=True)
        add_row(2, "Owner Identity:", record.get('owner_identity', 'N/A'), bold=True)
        add_row(3, "Owner ID:", record.get('owner_id', 'N/A'), bold=False)
        add_row(4, "Owner Name:", record.get('owner_name', 'N/A'), bold=False)
        add_row(5, "Owner IC:", record.get('owner_ic', 'N/A'), bold=False)
        add_row(6, "Owner Phone:", record.get('owner_phone', 'N/A'), bold=False)
        add_row(7, "Brand:", record.get('brand', 'N/A'), bold=False)
        add_row(8, "Model:", record.get('model', 'N/A'), bold=False)
        add_row(9, "Entry Date:", entry_date, bold=False)
        add_row(10, "Entry Time:", entry_time, bold=False)
        add_row(11, "Exit Date:", exit_date, bold=False)
        add_row(12, "Exit Time:", exit_time, bold=False)
        add_row(13, "Entry Reason:", record.get('entry_reason', 'N/A'), bold=False)

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
            command=lambda: self._dialog_action(dialog, "edit", record),
            **button_style
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            btn_frame,
            text="Delete",
            fg_color="#ff8080",
            hover_color="#ff6666",
            text_color="#ffffff",
            command=lambda: self._dialog_action(dialog, "delete", record),
            **button_style
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            btn_frame,
            text="Close",
            fg_color="#3b5ea8",
            hover_color="#4a77d4",
            text_color="#ffffff",
            command=dialog.destroy,
            **button_style
        ).pack(side="left", padx=10)

        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f'{width}x{height}+{x}+{y}')

    def _dialog_action(self, dialog, action, record):
        dialog.destroy()
        if action == "edit":
            if self.navigate_to:
                self.navigate_to("edit_record", record=record, admin_id=self.user_id)
        elif action == "delete":
            self.delete_record(record)

    def search_records(self):
        query = self.search_entry.get().strip().lower()
        if not query:
            self.load_all_records()
        else:
            all_records = self.firebase_db.get_records(limit=999999)
            results = []
            seen_ids = set()
            fields = ['vehicle_plate', 'owner_identity', 'entry_reason']
            for rec in all_records:
                for field in fields:
                    value = str(rec.get(field, '')).lower()
                    if query in value:
                        rec_id = rec.get('record_id')
                        if rec_id and rec_id not in seen_ids:
                            results.append(rec)
                            seen_ids.add(rec_id)
                        break
            self.all_records = results
            # Sort by entry_date and entry_time descending
            self.all_records.sort(
                key=lambda r: (
                    r.get('entry_date', '0000-00-00'),
                    r.get('entry_time', '00:00')
                ),
                reverse=True
            )
            total_count = len(self.all_records)
            self.total_pages = max(1, (total_count + self.page_size - 1) // self.page_size)
            self.current_page = min(self.current_page, self.total_pages - 1)
        self.refresh_table()

    def load_all_records(self):
        self.all_records = self.firebase_db.get_records(limit=999999)
        # Sort by entry_date and entry_time descending
        self.all_records.sort(
            key=lambda r: (
                r.get('entry_date', '0000-00-00'),
                r.get('entry_time', '00:00')
            ),
            reverse=True
        )
        total_count = len(self.all_records)
        self.total_pages = max(1, (total_count + self.page_size - 1) // self.page_size)
        self.current_page = min(self.current_page, self.total_pages - 1)

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

    def nav_add_record(self):
        if self.navigate_to:
            self.navigate_to("add_record", security_id=self.user_id)

    def delete_record(self, record):
        confirm = messagebox.askyesno("Delete Record", "Are you sure you want to delete this record?")
        if confirm:
            try:
                record_id = record.get('record_id')
                if not record_id:
                    self.play_warning_sound()
                    messagebox.showerror("Error", "Record ID not found.")
                    return

                # Store record details before deletion for logging
                record_details = {
                    "vehicle_plate": record.get("vehicle_plate"),
                    "owner_identity": record.get("owner_identity"),
                    "owner_name": record.get("owner_name"),
                    "entry_date": record.get("entry_date"),
                    "entry_time": record.get("entry_time"),
                    "entry_reason": record.get("entry_reason")
                }

                if self.firebase_db.delete_record(record_id):
                    # Log the security action
                    self.firebase_db.add_security_action(
                        security_id=self.user_id,
                        action="Deleted record",
                        target_type="record",
                        target_id=record_id,
                        details=record_details
                    )
                    self.play_success_sound()
                    messagebox.showinfo("Success", "Record deleted successfully.")
                    # Refresh the records list
                    self.load_all_records()
                    self.refresh_table()
                else:
                    self.play_warning_sound()
                    messagebox.showerror("Error", "Failed to delete record.")
            except Exception as e:
                self.play_warning_sound()
                messagebox.showerror("Error", f"An error occurred while deleting the record: {e}")
