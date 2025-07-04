import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime, timedelta
from PIL import Image
import calendar
from firebase_config import firebase_db
from tkinter import ttk, messagebox
import pytz
import winsound


class AdminDashboard(ctk.CTkFrame):
    def __init__(self, master, user_id):
        super().__init__(master)
        self.user_id = user_id
        self.db = firebase_db
        self.last_warning_viewed_time = None
        self.entries_period = 'month'  
        self.entries_user_type = 'Student' 
        self.entries_date = datetime.now()
        self.configure(fg_color="#f0f4ff")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.perodua_logo_size = (80, 48)
        self.other_logo_size = (60, 60)
        self.perodua_img = ctk.CTkImage(light_image=Image.open("Pic/perodua.png"), size=self.perodua_logo_size)
        self.toyota_img = ctk.CTkImage(light_image=Image.open("Pic/toyota.png"), size=self.other_logo_size)
        self.honda_img = ctk.CTkImage(light_image=Image.open("Pic/honda.png"), size=self.other_logo_size)
        self.folder_icon = ctk.CTkImage(light_image=Image.open("Pic/folder.png"), size=(24, 24))
        self.parking_icon = ctk.CTkImage(light_image=Image.open("Pic/parking.png"), size=(24, 24))
        self.notification_icon = ctk.CTkImage(light_image=Image.open("Pic/siren.png"), size=(20, 20))
        self.car_icon = ctk.CTkImage(light_image=Image.open("Pic/car.png"), size=(24, 24))
        self.build_widgets()
        self.after(100, self.load_initial_data)

    def load_initial_data(self):
        # Load overview cards data
        self.after(0, self.update_overview_cards)
        # Load vehicle entries data and draw chart
        self.after(100, self._draw_entries_chart)
        # Load action log
        self.after(200, self.refresh_action_log)

    def update_overview_cards(self):
        try:
            # Fetch  data for entries today and this week
            staff_count = self._get_registered_vehicle_count('staff')
            student_count = self._get_registered_vehicle_count('student')
            entries_today = self._get_entries_today()
            entries_week = self._get_entries_this_week_sum_all()
            
            # Update the cards
            if hasattr(self, 'overview_frame'):
                for widget in self.overview_frame.winfo_children():
                    widget.destroy()
                
                for card_args in [
                    ("👔 Staff Vehicles", str(staff_count), "#4dabf7", None, None, None),
                    ("🎓 Student Vehicles", str(student_count), "#20c997", None, None, None),
                    ("🚦 Entries Today", str(entries_today), "#ff922b", None, None, None),
                    ("📅 This Week", str(entries_week), "#845ef7", None, None, None),
                ]:
                    self.create_stat_card(self.overview_frame, *card_args)
        except Exception as e:
            print(f"Error updating overview cards: {e}")

    def build_widgets(self):
        # Main container
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)

        header_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        header_frame.grid_columnconfigure(0, weight=1)
        header_frame.grid_columnconfigure(1, weight=0)

        # Title
        ctk.CTkLabel(
            header_frame,
            text=f"Admin Dashboard · {self.user_id}",
            font=ctk.CTkFont(family="Helvetica", size=22, weight="bold"),
            text_color="#2c3e50"
        ).grid(row=0, column=0, sticky="w", padx=(10, 0), pady=(8, 8))

        self.overview_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        self.overview_frame.grid(row=0, column=1, sticky="e", padx=(0, 10), pady=(0, 0))
        for card_args in [
            ("👔 Staff Vehicles", "...", "#4dabf7", None, None, None),
            ("🎓 Student Vehicles", "...", "#20c997", None, None, None),
            ("🚦 Entries Today", "...", "#ff922b", None, None, None),
            ("📅 This Week", "...", "#845ef7", None, None, None),
        ]:
            self.create_stat_card(self.overview_frame, *card_args)

        grid_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True)
        for i in range(3):
            grid_frame.grid_columnconfigure(i, weight=1, uniform="col")
            grid_frame.grid_rowconfigure(i, weight=1, uniform="row")

        # Vehicle Entries
        entries_frame = ctk.CTkFrame(grid_frame, fg_color="white", corner_radius=12, border_width=1, border_color="#dee2e6")
        entries_frame.grid(row=0, column=0, rowspan=2, columnspan=2, sticky="nsew", padx=5, pady=5)
        self.setup_vehicle_entries_frame(entries_frame)

        # Alerts & Notifications
        alerts_frame = ctk.CTkFrame(grid_frame, fg_color="white", corner_radius=12, border_width=1, border_color="#dee2e6")
        alerts_frame.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)
        self.setup_alerts_panel(alerts_frame)

        # Parking Lot Utilization
        parking_frame = ctk.CTkFrame(grid_frame, fg_color="white", corner_radius=12, border_width=1, border_color="#dee2e6")
        parking_frame.grid(row=1, column=2, rowspan=2, sticky="nsew", padx=5, pady=5)
        self.setup_parking_utilization(parking_frame)

        # Daily Car Type Entries
        car_type_frame = ctk.CTkFrame(grid_frame, fg_color="white", corner_radius=12, border_width=1, border_color="#dee2e6")
        car_type_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
        self.setup_vehicle_type_chart(car_type_frame)

        # Admin Action Log
        action_log_frame = ctk.CTkFrame(grid_frame, fg_color="white", corner_radius=12, border_width=1, border_color="#dee2e6")
        action_log_frame.grid(row=2, column=1, sticky="nsew", padx=5, pady=5)
        self.setup_action_log_panel(action_log_frame)

    # Overview cards
    def create_overview_cards(self, parent):
        card_frame = ctk.CTkFrame(parent, fg_color="transparent")
        card_frame.pack(fill="x")
        # Fetch data for entries today and this week
        staff_count = self._get_registered_vehicle_count('staff')
        student_count = self._get_registered_vehicle_count('student')
        entries_today = self._get_entries_today()
        entries_week = self._get_entries_this_week_sum_all()
        for card_args in [
            ("👔 Staff Vehicles", str(staff_count), "#4dabf7", None, None, None),
            ("🎓 Student Vehicles", str(student_count), "#20c997", None, None, None),
            ("🚦 Entries Today", str(entries_today), "#ff922b", None, None, None),
            ("📅 This Week", str(entries_week), "#845ef7", None, None, None),
        ]:
            self.create_stat_card(card_frame, *card_args)

    def create_stat_card(self, parent, title, value, color, trend=None, trend_color=None, icon_right=None):
        frame = ctk.CTkFrame(parent, fg_color="white", corner_radius=10, border_width=1, border_color="#dee2e6")
        frame.pack(side="left", padx=8, ipadx=8, pady=2)
        ctk.CTkLabel(frame, text=title, font=ctk.CTkFont(size=12), text_color="#495057").pack(padx=15, pady=(8, 0), anchor="w")
        value_row = ctk.CTkFrame(frame, fg_color="transparent")
        value_row.pack(padx=15, pady=(0, 8), fill="x")
        ctk.CTkLabel(value_row, text=value, font=ctk.CTkFont(size=18, weight="bold"), text_color=color).pack(side="left")
        if trend:
            ctk.CTkLabel(value_row, text=trend, font=ctk.CTkFont(size=12, weight="bold"), text_color=trend_color).pack(side="left", padx=(8,0))
        if icon_right:
            ctk.CTkLabel(value_row, text=icon_right, font=ctk.CTkFont(size=18), text_color="#ffd43b").pack(side="right")

    def _get_entries_today(self):
        # Get today date
        today = datetime.now().strftime('%Y-%m-%d')
        total = 0
        for user_type in ['staff', 'student', 'visitor']:
            records = self.db.get_records_by_period(user_type, datetime.now(), datetime.now())
            total += sum(1 for r in records if r.get('entry_date') == today)
        return total

    def _get_entries_this_week_sum_all(self):
        now = datetime.now()
        start_of_week = now - timedelta(days=now.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        total = 0
        for user_type in ['staff', 'student', 'visitor']:
            records = self.db.get_records_by_period(user_type, start_of_week, end_of_week)
            total += len(records)
        return total

    def _get_registered_vehicle_count(self, user_type):
        owners = self.db.search_owners('owner_identity', user_type)
        return len(owners)

    def setup_vehicle_entries_frame(self, parent):
        # --- Modern Top Row: Card Background ---
        control_card = ctk.CTkFrame(
            parent,
            fg_color="#eaf3fb",
            corner_radius=18,
            border_width=1,
            border_color="#b6d0ee"
        )
        control_card.pack(fill="x", pady=(18, 0), padx=24)
        control_card.grid_columnconfigure(0, weight=0)
        control_card.grid_columnconfigure(1, weight=0)
        control_card.grid_columnconfigure(2, weight=0)
        control_card.grid_columnconfigure(3, weight=1)
        control_card.grid_columnconfigure(4, weight=0)

        self.period_toggle = ctk.CTkSegmentedButton(
            control_card,
            values=["Month", "Year"],
            command=self._on_period_toggle,
            width=140, height=38, corner_radius=18,
            fg_color="#eafaf1"
        )
        self.period_toggle.set("Month")
        self.period_toggle.grid(row=0, column=0, padx=(18, 12), pady=12, sticky="w")

        nav_frame = ctk.CTkFrame(control_card, fg_color="transparent")
        nav_frame.grid(row=0, column=1, padx=(0, 0), pady=0, sticky="w")
        nav_btn_style = {
            "width": 38, "height": 38, "corner_radius": 19,
            "fg_color": "#3498f7", "hover_color": "#2176bd",
            "text_color": "#fff", "font": ctk.CTkFont(size=18, weight="bold")
        }
        self.prev_btn = ctk.CTkButton(nav_frame, text="◀", command=self._on_prev_period, **nav_btn_style)
        self.prev_btn.pack(side="left", padx=(0, 6))
        self.period_label = ctk.CTkLabel(
            nav_frame, text=self._get_period_label(),
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#2176bd",
            fg_color="#fff", corner_radius=12, padx=18, pady=6
        )
        self.period_label.pack(side="left", padx=2)
        self.next_btn = ctk.CTkButton(nav_frame, text="▶", command=self._on_next_period, **nav_btn_style)
        self.next_btn.pack(side="left", padx=(6, 0))

        self.user_type_combo = ctk.CTkComboBox(
            control_card, values=["Staff", "Student", "Visitor"],
            width=130, height=38, corner_radius=18,
            fg_color="#fff", button_color="#2176bd",
            border_color="#2176bd", text_color="#222",
            font=ctk.CTkFont(size=14), command=self._on_user_type_change
        )
        self.user_type_combo.set("Student")
        self.user_type_combo.grid(row=0, column=2, padx=(18, 12), pady=12, sticky="w")

        export_frame = ctk.CTkFrame(control_card, fg_color="transparent")
        export_frame.grid(row=0, column=4, padx=(0, 10), pady=0, sticky="e")
        ctk.CTkButton(
            export_frame, text="Export CSV", width=90, height=36,
            fg_color="#20c997", hover_color="#128f76",
            font=ctk.CTkFont(size=13, weight="bold"), corner_radius=10,
            text_color="#fff", command=self._export_csv
        ).pack(side="left", padx=4)

        self.entries_fig, self.entries_ax = plt.subplots(figsize=(5.5, 2.8))
        self.entries_canvas = FigureCanvasTkAgg(self.entries_fig, master=parent)
        self.entries_canvas.get_tk_widget().pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self._draw_entries_chart()

    def _get_period_label(self):
        if self.entries_period == 'month':
            return self.entries_date.strftime('%B %Y')
        else:
            return self.entries_date.strftime('%Y')

    def _on_period_toggle(self, value):
        self.entries_period = value.lower()
        self.period_label.configure(text=self._get_period_label())
        self._draw_entries_chart()

    def _on_prev_period(self):
        if self.entries_period == 'month':
            month = self.entries_date.month - 1 or 12
            year = self.entries_date.year - (1 if self.entries_date.month == 1 else 0)
            self.entries_date = self.entries_date.replace(year=year, month=month)
        else:
            self.entries_date = self.entries_date.replace(year=self.entries_date.year - 1)
        self.period_label.configure(text=self._get_period_label())
        self._draw_entries_chart()

    def _on_next_period(self):
        now = datetime.now()
        if self.entries_period == 'month':
            month = self.entries_date.month + 1 if self.entries_date.month < 12 else 1
            year = self.entries_date.year + (1 if self.entries_date.month == 12 else 0)
            # Prevent navigating to future month
            if (year > now.year) or (year == now.year and month > now.month):
                self._show_future_popup()
                return
            self.entries_date = self.entries_date.replace(year=year, month=month)
        else:
            year = self.entries_date.year + 1
            # Prevent navigating to future year
            if year > now.year:
                self._show_future_popup()
                return
            self.entries_date = self.entries_date.replace(year=year)
        self.period_label.configure(text=self._get_period_label())
        self._draw_entries_chart()

    def _on_user_type_change(self, value):
        self.entries_user_type = value
        self._draw_entries_chart()

    def _fetch_entries_data_from_firestore(self):
        user_type = self.entries_user_type.lower()
        if self.entries_period == 'month':
            year = self.entries_date.year
            month = self.entries_date.month
            days_in_month = calendar.monthrange(year, month)[1]
            start_date = datetime(year, month, 1)
            end_date = datetime(year, month, days_in_month)
            records = self.db.get_records_by_period(user_type, start_date, end_date)
            counts = [0] * days_in_month
            for r in records:
                entry_date = r.get('entry_date', '')
                try:
                    dt = datetime.strptime(entry_date, '%Y-%m-%d')
                    if dt.year == year and dt.month == month:
                        counts[dt.day - 1] += 1
                except Exception:
                    continue
            return counts
        else:
            year = self.entries_date.year
            start_date = datetime(year, 1, 1)
            end_date = datetime(year, 12, 31)
            records = self.db.get_records_by_period(user_type, start_date, end_date)
            counts = [0] * 12
            for r in records:
                entry_date = r.get('entry_date', '')
                try:
                    dt = datetime.strptime(entry_date, '%Y-%m-%d')
                    if dt.year == year:
                        counts[dt.month - 1] += 1
                except Exception:
                    continue
            return counts

    def _draw_entries_chart(self):
        if not hasattr(self, 'entries_ax'):
            return
            
        self.entries_ax.clear()

        try:
            entries = self._fetch_entries_data_from_firestore()
            if self.entries_period == 'month':
                days = [str(i+1) for i in range(len(entries))]
                bars = self.entries_ax.bar(days, entries, color="#4dabf7", zorder=3)
                self.entries_ax.set_xlabel("Day")
            else:
                months = [datetime(2000, m, 1).strftime('%b') for m in range(1, 13)]
                bars = self.entries_ax.bar(months, entries, color="#4dabf7", zorder=3)
                self.entries_ax.set_xlabel("Month")
            self.entries_ax.set_facecolor("#f8f9fa")
            self.entries_fig.patch.set_facecolor('white')
            self.entries_ax.set_ylabel("Entries")
            self.entries_ax.tick_params(axis='x', colors="#495057")
            self.entries_ax.tick_params(axis='y', colors="#495057")
            self.entries_ax.grid(color='#f1f3f5', linestyle='--', axis='y', zorder=1)
            self.entries_fig.tight_layout()
            self.entries_canvas.draw()

            if hasattr(self, '_tooltip_label') and self._tooltip_label:
                self._tooltip_label.destroy()
            self._tooltip_label = None
            def on_motion(event):
                vis = False
                if event.inaxes == self.entries_ax:
                    for bar, val in zip(bars, entries):
                        contains, _ = bar.contains(event)
                        if contains:
                            x = event.x
                            y = event.y + 20
                            if not self._tooltip_label:
                                self._tooltip_label = ctk.CTkLabel(self.entries_canvas.get_tk_widget(), text=f"{val} entries", font=ctk.CTkFont(size=13, weight="bold"), fg_color="#343a40", text_color="#fff")
                            self._tooltip_label.configure(text=f"{val} entries")
                            self._tooltip_label.place(x=x, y=y, anchor="n")
                            vis = True
                            break
                if not vis and self._tooltip_label:
                    self._tooltip_label.place_forget()
            self.entries_canvas.mpl_connect('motion_notify_event', on_motion)
        except Exception as e:
            print(f"Error drawing entries chart: {e}")

    def _export_csv(self):
        import csv
        from tkinter import filedialog, messagebox
        import os
        # Fetch the data for the current chart
        entries = self._fetch_entries_data_from_firestore()
        user_type = self.entries_user_type
        if self.entries_period == 'month':
            header = ['Day', 'Entries']
            rows = [[str(i+1), entries[i]] for i in range(len(entries))]
            default_name = self.entries_date.strftime(f'Entries_{user_type}_%B_%Y.csv')
        else:
            header = ['Month', 'Entries']
            months = [datetime(2000, m, 1).strftime('%b') for m in range(1, 13)]
            rows = [[months[i], entries[i]] for i in range(len(entries))]
            default_name = self.entries_date.strftime(f'Entries_{user_type}_%Y.csv')
        # Ask user where to save
        file_path = filedialog.asksaveasfilename(
            defaultextension='.csv',
            filetypes=[('CSV files', '*.csv')],
            initialfile=default_name,
            title='Save CSV File'
        )
        if not file_path:
            return
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([f'User Type: {user_type}'])
                writer.writerow(header)
                writer.writerows(rows)
            messagebox.showinfo('Export Successful', f'CSV file saved to:\n{os.path.abspath(file_path)}')
        except Exception as e:
            messagebox.showerror('Export Failed', f'Failed to export CSV:\n{e}')

    # Alerts & Recent Actions
    def setup_alerts_panel(self, parent):
        title_frame = ctk.CTkFrame(parent, fg_color="transparent")
        title_frame.pack(pady=(12, 0))
        ctk.CTkLabel(title_frame, image=self.notification_icon, text="", width=24, height=24).pack(side="left", padx=(0, 6))
        ctk.CTkLabel(title_frame, text="Alerts & Notifications", font=ctk.CTkFont(size=16, weight="bold"), text_color="#2c3e50").pack(side="left")
        alert_frame = ctk.CTkFrame(parent, fg_color="white", corner_radius=12)
        alert_frame.pack(fill="both", expand=True, padx=10, pady=(8, 10))

        self.alert_types = ["Critical", "Warning", "Information"]
        color_map = {"Critical": "#ff6b6b", "Warning": "#ffd43b", "Information": "#20c997"}
        icon_map = {"Critical": "❗", "Warning": "⚠️", "Information": "ℹ️"}

        for row, alert_type in enumerate(self.alert_types):
            bg_color, icon = color_map[alert_type], icon_map[alert_type]
            card = ctk.CTkFrame(alert_frame, fg_color="white", border_width=2, border_color=bg_color, corner_radius=8, height=50)
            card.pack(fill="x", pady=12, padx=8, ipady=0)
            card.pack_propagate(False)
            icon_label = ctk.CTkLabel(card, text=icon, font=ctk.CTkFont(size=18), text_color=bg_color)
            icon_label.pack(side="left", padx=(12, 6), pady=4)
            type_label = ctk.CTkLabel(card, text=alert_type, font=ctk.CTkFont(size=14, weight="bold"), text_color=bg_color)
            type_label.pack(side="left", padx=6, pady=4)

            # alert count logic
            alerts = firebase_db.get_alerts_with_ids(alert_type.lower(), limit=100)
            unseen_alerts = [a for a in alerts if self.user_id not in a.get("seen_by", [])]
            count = len(unseen_alerts)

            # Only show badge if there are unseen alerts
            if count > 0:
                badge_size = 24
                badge_frame = ctk.CTkFrame(card, width=badge_size, height=badge_size, corner_radius=badge_size//2, fg_color=bg_color)
                badge_frame.pack(side="right", padx=10)
                badge_frame.pack_propagate(False)
                badge_label = ctk.CTkLabel(badge_frame, text=str(count), font=ctk.CTkFont(size=12, weight="bold"), text_color="white")
                badge_label.place(relx=0.5, rely=0.5, anchor="center")

            def on_enter(e, c=card, cl=bg_color, icon_l=icon_label, type_l=type_label):
                c.configure(fg_color=cl)
                icon_l.configure(text_color="white")
                type_l.configure(text_color="white")
            def on_leave(e, c=card, cl=bg_color, icon_l=icon_label, type_l=type_label):
                c.configure(fg_color="white")
                icon_l.configure(text_color=cl)
                type_l.configure(text_color=cl)
            card.bind("<Enter>", on_enter)
            card.bind("<Leave>", on_leave)

            def show_alert_details(type=alert_type, icon=icon, color=bg_color):
                popup = ctk.CTkToplevel(self)
                popup.title(f"{type} Alerts")
                popup.geometry("800x500")
                popup.grab_set()
                popup.update_idletasks()
                w = 800
                h = 500
                x = (popup.winfo_screenwidth() // 2) - (w // 2)
                y = (popup.winfo_screenheight() // 2) - (h // 2)
                popup.geometry(f"{w}x{h}+{x}+{y}")
                header_frame = ctk.CTkFrame(popup, fg_color=color, corner_radius=0)
                header_frame.pack(fill="x", ipady=8)
                ctk.CTkLabel(header_frame, text=f"{icon} {type} Alerts", font=ctk.CTkFont(size=16, weight="bold"), text_color="white").pack(pady=(8, 8))
                scroll_frame = ctk.CTkScrollableFrame(popup, fg_color="white", width=700, height=140)
                scroll_frame.pack(padx=18, pady=(18, 18), fill="both", expand=True)

                table_header = ctk.CTkFrame(scroll_frame, fg_color="#f1f3f5")
                table_header.pack(fill="x", padx=6, pady=(0, 4))
                ctk.CTkLabel(table_header, text="Message", font=ctk.CTkFont(size=14, weight="bold"), text_color="#2c3e50", anchor="w", width=500, justify="left").pack(side="left", fill="x", padx=(10, 5))
                ctk.CTkLabel(table_header, text="Date", font=ctk.CTkFont(size=14, weight="bold"), text_color="#2c3e50", anchor="center", width=140, justify="center").pack(side="left", padx=(0, 0))
                ctk.CTkLabel(table_header, text="Time", font=ctk.CTkFont(size=14, weight="bold"), text_color="#2c3e50", anchor="e", width=120, justify="right").pack(side="left", padx=(0, 10))
                alerts = firebase_db.get_alerts_with_ids(type.lower(), limit=100)

                alert_ids = [alert.get("doc_id") for alert in alerts if alert.get("doc_id")]
                firebase_db.mark_alerts_as_seen(type.lower(), alert_ids, self.user_id)
                if not alerts:
                    ctk.CTkLabel(
                        scroll_frame,
                        text="No messages found.",
                        font=ctk.CTkFont(size=13, weight="bold"),
                        text_color="#adb5bd"
                    ).pack(pady=20)
                for alert in alerts:
                    message_text = alert.get("message", "")
                    date_text = alert.get("date", "")
                    time_text = alert.get("time", "")
                    row = ctk.CTkFrame(scroll_frame, fg_color="#f8f9fa")
                    row.pack(fill="x", padx=6, pady=2)
                    ctk.CTkLabel(row, text=message_text, font=ctk.CTkFont(size=13), text_color="#2c3e50", anchor="w", width=500, justify="left").pack(side="left", fill="x", padx=(10, 5))
                    ctk.CTkLabel(row, text=date_text, font=ctk.CTkFont(size=12), text_color="#888888", anchor="center", width=140, justify="center").pack(side="left", padx=(0, 0))
                    ctk.CTkLabel(row, text=time_text, font=ctk.CTkFont(size=12), text_color="#888888", anchor="e", width=120, justify="right").pack(side="left", padx=(0, 10))
                def close_and_refresh():
                    popup.destroy()

                    for widget in parent.winfo_children():
                        widget.destroy()
                    self.setup_alerts_panel(parent)
                ctk.CTkButton(popup, text="Close", command=close_and_refresh, fg_color=color, hover_color=color).pack(pady=(0, 12))

            card.bind("<Button-1>", lambda e, t=alert_type, i=icon, c=bg_color: show_alert_details(t, i, c))
            for child in card.winfo_children():
                child.bind("<Button-1>", lambda e, t=alert_type, i=icon, c=bg_color: show_alert_details(t, i, c))

    def setup_action_log_panel(self, parent):
        title_frame = ctk.CTkFrame(parent, fg_color="transparent")
        title_frame.pack(pady=(12, 0))
        ctk.CTkLabel(title_frame, image=self.folder_icon, text="", width=24, height=24).pack(side="left", padx=(0, 6))
        ctk.CTkLabel(title_frame, text="Action Log", font=ctk.CTkFont(size=16, weight="bold"), text_color="#2c3e50").pack(side="left")

        filter_frame = ctk.CTkFrame(parent, fg_color="white", corner_radius=10)
        filter_frame.pack(fill="x", padx=12, pady=(8, 4))

        self.action_search_var = ctk.StringVar()
        self.action_search_entry = ctk.CTkEntry(
            filter_frame,
            width=150,
            height=32,
            text_color="white",
            fg_color="black",
            textvariable=self.action_search_var
        )
        self.action_search_entry.pack(side="left", padx=8, pady=8)

        self._search_placeholder = "Search User ID..."
        def _set_placeholder():
            self.action_search_entry.delete(0, "end")
            self.action_search_entry.insert(0, self._search_placeholder)
            self.action_search_entry.configure(text_color="#cccccc")
        def _clear_placeholder(event=None):
            if self.action_search_entry.get() == self._search_placeholder:
                self.action_search_entry.delete(0, "end")
                self.action_search_entry.configure(text_color="white")
        def _restore_placeholder(event=None):
            if not self.action_search_entry.get():
                _set_placeholder()
        self.action_search_entry.bind("<FocusIn>", _clear_placeholder)
        self.action_search_entry.bind("<FocusOut>", _restore_placeholder)
        self.action_search_entry.bind("<KeyRelease>", self.refresh_action_log)

        _set_placeholder()

        self.user_filter = ctk.CTkComboBox(
            filter_frame,
            values=["All Actions", "Admin Actions", "Security Actions"],
            width=140,
            height=32,
            font=("Arial", 12),
            command=self.refresh_action_log
        )
        self.user_filter.set("All Actions")
        self.user_filter.pack(side="right", padx=8, pady=8)

        # Create table frame
        table_frame = ctk.CTkFrame(parent, fg_color="white", corner_radius=10)
        table_frame.pack(fill="both", expand=True, padx=12, pady=(4, 12))

        # Create Treeview for table
        style = ttk.Style()
        style.configure("ActionLog.Treeview",
                       background="#ffffff",
                       foreground="black",
                       rowheight=30,
                       fieldbackground="#ffffff",
                       font=("Arial", 12))
        style.configure("ActionLog.Treeview.Heading",
                       background="#f1f3f5",
                       foreground="black",
                       font=("Arial", 12, "bold"))
        style.map('ActionLog.Treeview', 
                 background=[('selected', '#1a73e8')],
                 foreground=[('selected', 'white')])
        
        columns = ("User Type", "User ID", "Action")
        self.action_tree = ttk.Treeview(table_frame, columns=columns, show="headings", 
                                      style="ActionLog.Treeview", height=6)

        self.action_tree.column("User Type", width=120, anchor="w")
        self.action_tree.column("User ID", width=120, anchor="w")
        self.action_tree.column("Action", width=260, anchor="w")
        
        for col in columns:
            self.action_tree.heading(col, text=col)

        self.action_tree.pack(fill="both", expand=True, padx=2, pady=2)

        self.action_tree.bind("<Double-1>", self.show_action_details)

        self.refresh_action_log()

    def refresh_action_log(self, event=None):
        try:
            # Clear existing items
            for item in self.action_tree.get_children():
                self.action_tree.delete(item)

            filter_value = self.user_filter.get()
            entry_val = self.action_search_entry.get() if hasattr(self, 'action_search_entry') else ''
            if hasattr(self, '_search_placeholder') and entry_val == self._search_placeholder:
                search_text = ''
            else:
                search_text = entry_val.strip().lower()
            
            # Fetch actions based on filter
            actions = []
            if filter_value in ["All Actions", "Admin Actions"]:
                admin_actions = self.db.get_admin_actions(limit=100)
                for action in admin_actions:
                    actions.append(("Admin", action))
            
            if filter_value in ["All Actions", "Security Actions"]:
                security_actions = self.db.get_security_actions(limit=100)
                for action in security_actions:
                    actions.append(("Security", action))

            # Filter by User ID
            if search_text:
                filtered = []
                for user_type, action in actions:
                    user_id = action.get('admin_id' if user_type == "Admin" else 'security_id', 'Unknown')
                    if search_text in str(user_id).lower():
                        filtered.append((user_type, action))
                actions = filtered

            actions.sort(key=lambda x: x[1].get('timestamp', datetime.min), reverse=True)

            actions = actions[:6]
            
            if not actions:
                self.action_tree.insert("", "end", values=("No actions", "", ""))
            else:
                for user_type, action in actions:
                    user_id = action.get('admin_id' if user_type == "Admin" else 'security_id', 'Unknown')
                    action_text = action.get('action', '')
                    
                    # Store the full action data in a tag for later retrieval
                    tag = f"action_{len(self.action_tree.get_children())}"
                    self.action_tree.insert("", "end", 
                                          values=(user_type, user_id, action_text),
                                          tags=(tag,))
                    # Store the action data for later use
                    self.action_tree.action_data = getattr(self.action_tree, 'action_data', {})
                    self.action_tree.action_data[tag] = action

        except Exception as e:
            print(f"Error loading actions: {e}")
            self.action_tree.insert("", "end", values=("Error loading actions", "", ""))

    def show_action_details(self, event):
        selection = self.action_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        tags = self.action_tree.item(item, "tags")
        if not tags:
            return
            
        action_data = self.action_tree.action_data.get(tags[0])
        if not action_data:
            return

        # Get user type from the tree item
        user_type = self.action_tree.item(item)['values'][0]

        # Create popup window
        popup = ctk.CTkToplevel(self)
        popup.title(f"{user_type} Action Details")
        popup.geometry("700x600")
        popup.grab_set()

        # Center the popup on the screen
        popup.update_idletasks()
        width = 700
        height = 600
        x = (popup.winfo_screenwidth() // 2) - (width // 2)
        y = (popup.winfo_screenheight() // 2) - (height // 2)
        popup.geometry(f"{width}x{height}+{x}+{y}")

        content_frame = ctk.CTkFrame(popup, fg_color="white")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        info_frame = ctk.CTkFrame(content_frame, fg_color="#f8f9fa")
        info_frame.pack(fill="x", pady=(0, 20), padx=10)

        header_color = "#1a73e8" if user_type == "Admin" else "#20c997"
        ctk.CTkLabel(info_frame, 
                    text=f"{user_type} Action Details",
                    font=ctk.CTkFont(size=18, weight="bold"),
                    text_color=header_color).pack(pady=(10, 15))
        
        # User info
        user_id = action_data.get('admin_id' if user_type == "Admin" else 'security_id', 'Unknown')
        ctk.CTkLabel(info_frame, 
                    text=f"{user_type} ID: {user_id}",
                    font=ctk.CTkFont(size=14),
                    text_color="black").pack(anchor="w", padx=15, pady=2)
        
        # Action info
        ctk.CTkLabel(info_frame,
                    text=f"Action: {action_data.get('action', 'Unknown')}",
                    font=ctk.CTkFont(size=14),
                    text_color="black").pack(anchor="w", padx=15, pady=2)

        timestamp = action_data.get('timestamp')
        if timestamp:
            local_tz = pytz.timezone('Asia/Kuala_Lumpur')
            if timestamp.tzinfo is None:
                timestamp = pytz.utc.localize(timestamp)
            local_time = timestamp.astimezone(local_tz)
            timestamp_str = local_time.strftime('%Y-%m-%d %H:%M:%S')
            ctk.CTkLabel(info_frame,
                        text=f"Time: {timestamp_str}",
                        font=ctk.CTkFont(size=14),
                        text_color="black").pack(anchor="w", padx=15, pady=2)

        target_type = action_data.get('target_type', 'Unknown')
        target_id = action_data.get('target_id', 'Unknown')
        ctk.CTkLabel(info_frame,
                    text=f"Target: {target_type} ({target_id})",
                    font=ctk.CTkFont(size=14),
                    text_color="black").pack(anchor="w", padx=15, pady=(2, 10))

        details = action_data.get('details', {})
        if isinstance(details, dict):
            changes_frame = ctk.CTkScrollableFrame(content_frame, fg_color="white")
            changes_frame.pack(fill="both", expand=True, padx=10)
            
            if 'before' in details and 'after' in details:
                ctk.CTkLabel(changes_frame,
                           text="Changes:",
                           font=ctk.CTkFont(size=16, weight="bold"),
                           text_color="black").pack(anchor="w", pady=(0, 10))

                for key in details['after']:
                    if key.lower() in [
                        'created at', 'updated at',
                        'exit updated at', 'exit updated by admin', 'exit updated by security']:
                        continue
                    before_val = details['before'].get(key, None)
                    after_val = details['after'][key]
                    if before_val in [None, '', 'N/A']:
                        before_val_display = 'N/A'
                    else:
                        before_val_display = before_val
                    if before_val_display != after_val:
                        change_frame = ctk.CTkFrame(changes_frame, fg_color="#f8f9fa")
                        change_frame.pack(fill="x", pady=5, padx=5)

                        ctk.CTkLabel(change_frame,
                                   text=f"{key}:",
                                   font=ctk.CTkFont(size=13, weight="bold"),
                                   text_color="black").pack(anchor="w", padx=10, pady=(5, 0))
                        # Old value (in red)
                        ctk.CTkLabel(change_frame,
                                   text=f"Old: {before_val_display}",
                                   font=ctk.CTkFont(size=12),
                                   text_color="#dc3545").pack(anchor="w", padx=20, pady=(0, 2))
                        # New value (in green)
                        ctk.CTkLabel(change_frame,
                                   text=f"New: {after_val}",
                               font=ctk.CTkFont(size=12),
                               text_color="#28a745").pack(anchor="w", padx=20, pady=(0, 5))
            else:
                for key, value in details.items():
                    if isinstance(value, dict) or key.lower() in ['created at', 'updated at']:
                        continue  # Skip nested dictionaries and timestamp fields
                    detail_frame = ctk.CTkFrame(changes_frame, fg_color="#f8f9fa")
                    detail_frame.pack(fill="x", pady=2)
                    ctk.CTkLabel(detail_frame,
                               text=f"{key}: {value}",
                               font=ctk.CTkFont(size=12),
                               text_color="black").pack(anchor="w", padx=10, pady=5)

        # Close button
        ctk.CTkButton(popup,
                     text="Close",
                     command=popup.destroy,
                     fg_color=header_color,
                     hover_color="#1557b0" if user_type == "Admin" else "#15b075",
                     height=32).pack(pady=20)

    # Vehicle Type Chart
    def get_daily_brand_counts(self):
        today = datetime.now().strftime('%Y-%m-%d')
        brand_plate_map = {}
        for user_type in ['staff', 'student', 'visitor']:
            records = self.db.get_records_by_period(user_type, datetime.now(), datetime.now())
            for r in records:
                if r.get('entry_date') == today:
                    brand = r.get('brand', 'Unknown')
                    plate = r.get('vehicle_plate')
                    if brand and plate:
                        if brand not in brand_plate_map:
                            brand_plate_map[brand] = set()
                        brand_plate_map[brand].add(plate)
        # Count unique plates per brand
        return {brand: len(plates) for brand, plates in brand_plate_map.items()}

    def setup_vehicle_type_chart(self, parent):
        title_frame = ctk.CTkFrame(parent, fg_color="transparent")
        title_frame.pack(pady=(12, 0))
        ctk.CTkLabel(title_frame, image=self.car_icon, text="", width=24, height=24).pack(side="left", padx=(0, 6))
        ctk.CTkLabel(title_frame, text="Daily Car Type Entries Amount", font=ctk.CTkFont(size=15, weight="bold"), text_color="#2c3e50").pack(side="left")

        brand_counts = self.get_daily_brand_counts()
        perodua_count = brand_counts.get("Perodua", 0)
        toyota_count = brand_counts.get("Toyota", 0)
        honda_count = brand_counts.get("Honda", 0)

        car_types = [
            ("Perodua", self.perodua_img, perodua_count, "#4dabf7"),
            ("Toyota", self.toyota_img, toyota_count, "#20c997"),
            ("Honda", self.honda_img, honda_count, "#ff922b"),
        ]

        cards_outer = ctk.CTkFrame(parent, fg_color="transparent")
        cards_outer.pack(fill="both", expand=True, padx=10, pady=10)
        cards_outer.grid_rowconfigure(0, weight=1)
        cards_outer.grid_rowconfigure(1, weight=1)
        cards_outer.grid_columnconfigure(0, weight=1)

        top_row = ctk.CTkFrame(cards_outer, fg_color="transparent")
        top_row.grid(row=0, column=0, pady=(0, 10))
        for name, img, count, color in car_types[:2]:
            card = ctk.CTkFrame(top_row, fg_color="white", border_width=2, border_color=color, corner_radius=10, width=220)
            card.pack(side="left", padx=30, ipadx=8, ipady=8, fill="y")
            if name == "Perodua":
                ctk.CTkLabel(card, image=img, text="", width=80, height=48).pack(side="left", padx=(18, 10), pady=10)
            else:
                ctk.CTkLabel(card, image=img, text="", width=60, height=60).pack(side="left", padx=(18, 10), pady=10)
            right_frame = ctk.CTkFrame(card, fg_color="transparent")
            right_frame.pack(side="left", padx=4, pady=10)
            ctk.CTkLabel(right_frame, text=name, font=ctk.CTkFont(size=13, weight="bold"), text_color="#2c3e50").pack(anchor="w")
            ctk.CTkLabel(right_frame, text=f"{count} entries", font=ctk.CTkFont(size=15, weight="bold"), text_color=color).pack(anchor="w")

        bottom_row = ctk.CTkFrame(cards_outer, fg_color="transparent")
        bottom_row.grid(row=1, column=0)
        name, img, count, color = car_types[2]
        card = ctk.CTkFrame(bottom_row, fg_color="white", border_width=2, border_color=color, corner_radius=10, width=220)
        card.pack(pady=2, ipadx=8, ipady=8)
        ctk.CTkLabel(card, image=img, text="", width=60, height=60).pack(side="left", padx=(18, 10), pady=10)
        right_frame = ctk.CTkFrame(card, fg_color="transparent")
        right_frame.pack(side="left", padx=4, pady=10)
        ctk.CTkLabel(right_frame, text=name, font=ctk.CTkFont(size=13, weight="bold"), text_color="#2c3e50").pack(anchor="w")
        ctk.CTkLabel(right_frame, text=f"{count} entries", font=ctk.CTkFont(size=15, weight="bold"), text_color=color).pack(anchor="w")

    # Parking Utilization
    def setup_parking_utilization(self, parent):
        title_frame = ctk.CTkFrame(parent, fg_color="transparent")
        title_frame.pack(pady=(18, 8))
        ctk.CTkLabel(title_frame, image=self.parking_icon, text="", width=24, height=24).pack(side="left", padx=(0, 6))
        ctk.CTkLabel(title_frame, text="Parking Lot Utilization", font=ctk.CTkFont(size=18, weight="bold"), text_color="#2c3e50").pack(side="left")
        lots = [
            ("Student Lot", 60, 100, "#4dabf7", "🎓"),
            ("Staff Lot", 35, 60, "#20c997", "👔"),
            ("Visitor Lot", 12, 40, "#ff922b", "🧑‍💼"),
        ]

        cards_frame = ctk.CTkFrame(parent, fg_color="transparent")
        cards_frame.pack(fill="both", expand=True, padx=18, pady=(0, 18))
        cards_frame.grid_rowconfigure((0,1,2), weight=1)
        cards_frame.grid_columnconfigure(0, weight=1)
        for i, (name, available, total, color, icon) in enumerate(lots):
            card = ctk.CTkFrame(cards_frame, fg_color="white", border_width=2, border_color=color, corner_radius=12)
            card.pack(fill="x", padx=12, pady=25)  # Increased vertical padding for more space between cards

            top_row = ctk.CTkFrame(card, fg_color="transparent")
            top_row.pack(fill="x", padx=12, pady=(10, 0))
            ctk.CTkLabel(top_row, text=icon, font=ctk.CTkFont(size=22), text_color=color).pack(side="left", padx=(0, 8))
            ctk.CTkLabel(top_row, text=name, font=ctk.CTkFont(size=14, weight="bold"), text_color=color).pack(side="left")

            ctk.CTkLabel(card, text=f"{available}/{total} available", font=ctk.CTkFont(size=13), text_color="#495057").pack(anchor="w", padx=16, pady=(2, 8))

            bar_frame = ctk.CTkFrame(card, fg_color="#f8f9fa", corner_radius=8)
            bar_frame.pack(fill="x", padx=16, pady=(0, 12))
            percent = available / total
            bar = ctk.CTkProgressBar(bar_frame, height=18, progress_color=color)
            bar.set(percent)
            bar.pack(fill="x", padx=0, pady=4)

    def _show_future_popup(self):
        self.play_warning_sound()
        messagebox.showwarning("Invalid Period", "Cannot display or navigate to a future month or year.")

    def play_warning_sound(self):
        try:
            winsound.PlaySound("SystemHand", winsound.SND_ALIAS)
        except:
            pass

