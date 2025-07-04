import customtkinter as ctk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
import datetime
from tkinter import messagebox
from firebase_config import firebase_db
from PIL import Image
import winsound  


class SecurityDashboard(ctk.CTkFrame):
    def __init__(self, master, user_id):
        super().__init__(master)
        self.user_id = user_id
        self.configure(fg_color="#f0f4ff")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Define week and month labels
        self.month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        today = datetime.date.today()
        self.current_year = today.year
        self.total_weeks = datetime.date(self.current_year, 12, 28).isocalendar()[1]
        self.current_week = today.isocalendar()[1]

        self.week_rects = []

        self.build_widgets()

    def build_widgets(self):
        # Main container
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)

        # Load icons for headers
        self.icon_diagram = ctk.CTkImage(Image.open("Pic/diagram.png"), size=(28, 28))
        self.icon_calendar = ctk.CTkImage(Image.open("Pic/calendar.png"), size=(28, 28))
        self.icon_car = ctk.CTkImage(Image.open("Pic/car.png"), size=(28, 28))
        self.icon_siren = ctk.CTkImage(Image.open("Pic/siren.png"), size=(22, 22))
        self.icon_no_entry = ctk.CTkImage(Image.open("Pic/no-entry.png"), size=(28, 28))

        # Header section
        header_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))

        # Welcome message
        ctk.CTkLabel(
            header_frame,
            text=f"Security Dashboard · {self.user_id}",
            font=ctk.CTkFont(family="Helvetica", size=22, weight="bold"),
            text_color="#2c3e50"
        ).pack(side="left")

        stats_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        stats_frame.pack(side="right")

        self.create_stat_card(stats_frame, "🚗 Today's Entries", str(self.get_today_entries()), "#4dabf7")
        # Get the current week number
        current_week_number = datetime.date.today().isocalendar()[1]
        self.create_stat_card(stats_frame, "📅 Current Week", f"Week {current_week_number}", "#20c997")

        # Main grid layout
        grid_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True)

        # Configure grid columns and rows
        grid_frame.grid_columnconfigure(0, weight=2, uniform="col")
        grid_frame.grid_columnconfigure(1, weight=1, uniform="col")
        grid_frame.grid_rowconfigure(0, weight=1, uniform="row")
        grid_frame.grid_rowconfigure(1, weight=1, uniform="row")

        # Weekly chart
        weekly_frame = self.create_chart_frame(grid_frame, "Weekly Entries Pattern", 0, 0, icon=self.icon_diagram)
        self.setup_weekly_chart(weekly_frame)

        # Monthly chart
        monthly_frame = self.create_chart_frame(grid_frame, "Monthly Trend Analysis", 1, 0, icon=self.icon_calendar)
        self.setup_monthly_chart(monthly_frame)

        # Right sidebar
        right_sidebar = ctk.CTkFrame(grid_frame, fg_color="transparent")
        right_sidebar.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=(10, 0))
        right_sidebar.grid_columnconfigure(0, weight=1)
        right_sidebar.grid_rowconfigure(0, weight=1)
        right_sidebar.grid_rowconfigure(1, weight=1)
        right_sidebar.grid_rowconfigure(2, weight=1)

        # Vehicle distribution
        pie_frame = self.create_chart_frame(right_sidebar, "Vehicle Distribution", 0, 0, icon=self.icon_car)
        pie_frame.grid(sticky="nsew")
        self.setup_pie_chart(pie_frame)

        # Alert section
        alert_frame = self.create_alert_frame(right_sidebar)
        alert_frame.grid(row=1, column=0, pady=(10, 0), sticky="nsew")

        # Blacklist frame
        blacklist_frame = self.create_blacklist_frame(right_sidebar)
        blacklist_frame.grid(row=2, column=0, pady=(10, 0), sticky="nsew")

    def create_stat_card(self, parent, title, value, color):
        frame = ctk.CTkFrame(parent,fg_color="white",
                             corner_radius=10,
                             border_width=1,
                             border_color="#dee2e6")
        frame.pack(side="left", padx=5)

        ctk.CTkLabel(frame, text=title,
                     font=ctk.CTkFont(size=12),
                     text_color="#495057").pack(padx=15, pady=(8, 0))
        ctk.CTkLabel(frame, text=value,
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=color).pack(padx=15, pady=(0, 8))

    def create_chart_frame(self, parent, title, row, col, icon=None):
        frame = ctk.CTkFrame(parent,
                             fg_color="white",
                             corner_radius=12,
                             border_width=1,
                             border_color="#dee2e6")
        frame.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)
        frame.grid_propagate(False)

        # Header with icon
        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(pady=12, padx=15, fill="x")
        if icon:
            ctk.CTkLabel(header, image=icon, text="", fg_color="transparent").pack(side="left", padx=(0, 8))
        ctk.CTkLabel(header, text=title, font=ctk.CTkFont(size=16, weight="bold"), text_color="#2c3e50").pack(side="left")
        return frame

    def get_week_range_label(self, year, week):
        start = datetime.date.fromisocalendar(year, week, 1)
        end = datetime.date.fromisocalendar(year, week, 7)
        return f"{start} to {end}"

    def setup_weekly_chart(self, parent):
        nav_frame = ctk.CTkFrame(parent, fg_color="transparent")
        nav_frame.pack(side="top", fill="x", pady=(10, 0), padx=20)
        nav_frame.grid_columnconfigure(0, weight=1)
        nav_frame.grid_columnconfigure(1, weight=2)
        nav_frame.grid_columnconfigure(2, weight=1)

        prev_btn = ctk.CTkButton(nav_frame, text="◀ Previous Week",
                                command=self.show_previous_week,
                                fg_color="#4dabf7",
                                hover_color="#228be6",
                                width=130,
                                height=32,
                                font=ctk.CTkFont(size=14, weight="bold"))
        prev_btn.grid(row=0, column=0, sticky="w", padx=5)

        week_range = self.get_week_range_label(self.current_year, self.current_week)
        self.week_label = ctk.CTkLabel(nav_frame, 
            text=week_range,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#2c3e50")
        self.week_label.grid(row=0, column=1, sticky="nsew")

        next_btn = ctk.CTkButton(nav_frame, text="Next Week ▶",
                                command=self.show_next_week,
                                fg_color="#4dabf7",
                                hover_color="#228be6",
                                width=130,
                                height=32,
                                font=ctk.CTkFont(size=14, weight="bold"))
        next_btn.grid(row=0, column=2, sticky="e", padx=5)

        # Chart setup
        self.week_bar_fig, self.week_bar_ax = plt.subplots(figsize=(5, 2.8))
        self.week_bar_canvas = FigureCanvasTkAgg(self.week_bar_fig, master=parent)
        self.week_bar_canvas.get_tk_widget().pack(side="top", fill="both", expand=True, padx=15, pady=(0, 15))
        self.week_bar_ax.set_facecolor("#f8f9fa")
        self.week_bar_fig.patch.set_facecolor('white')
        self.week_bar_fig.subplots_adjust(bottom=0.2)
        self.update_week_bar_chart()

    def update_week_bar_chart(self):
        self.week_bar_ax.clear()
        week_number = self.current_week
        year = self.current_year
        # Fetch data from Firestore
        week_data = self.fetch_weekly_data(year, week_number)
        self.week_data = {f"Week {self.current_week}": week_data}
        current_week_data = week_data
        gradient = np.linspace(0.8, 1.2, len(current_week_data))
        colors = plt.cm.Blues(gradient)
        self.week_bar_ax.grid(color='#f1f3f5', linestyle='--', zorder=1)
        bars = self.week_bar_ax.bar(
            current_week_data.keys(),
            [sum(day.values()) for day in current_week_data.values()],
            color=colors,
            edgecolor='white',
            linewidth=1.5,
            width=0.6,
            zorder=5
        )
        self.week_rects = bars
        self.week_bar_ax.tick_params(axis='x', colors="#495057", rotation=45)
        self.week_bar_ax.tick_params(axis='y', colors="#495057")
        self.week_bar_tooltip = self.week_bar_ax.annotate("", 
            xy=(0,0), 
            xytext=(0, -25),
            textcoords="offset points",
            ha="center", 
            va="top",
            bbox=dict(
                boxstyle="round,pad=0.5",
                fc="white",
                ec="#4dabf7",
                alpha=0.9,
                linewidth=1
            ),
            arrowprops=dict(
                arrowstyle="->",
                connectionstyle="arc3",
                color="#4dabf7"
            ),
            zorder=10
        )
        self.week_bar_tooltip.set_visible(False)
        self.week_bar_canvas.mpl_connect('motion_notify_event', self.on_week_bar_hover)
        self.week_bar_canvas.draw()

    def show_previous_week(self):
        if self.current_week > 1:
            self.current_week -= 1
            self.update_week_bar_chart()
            week_range = self.get_week_range_label(self.current_year, self.current_week)
            self.week_label.configure(text=week_range)

    def play_warning_sound(self):
        try:
            winsound.PlaySound("SystemHand", winsound.SND_ALIAS)
        except:
            pass

    def show_next_week(self):
        # Only allow navigation up to the current week of the current year
        today = datetime.date.today()
        current_year = today.year
        current_week = today.isocalendar()[1]
        if (self.current_year == current_year and self.current_week >= current_week) or (self.current_week >= self.total_weeks):
            self.play_warning_sound()
            messagebox.showwarning("Warning", "Cannot display data for future weeks.")
            return
        self.current_week += 1
        self.update_week_bar_chart()
        week_range = self.get_week_range_label(self.current_year, self.current_week)
        self.week_label.configure(text=week_range)

    def on_week_bar_hover(self, event):
        if event.inaxes == self.week_bar_ax:
            hit = False
            for rect, (day, values) in zip(self.week_rects,
                                       self.week_data[f"Week {self.current_week}"].items()):
                if rect.contains(event)[0]:
                    hit = True
                    total_entries = sum(values.values())
                    tooltip_text = f"{day}\n"
                    tooltip_text += f"Total: {total_entries}\n"
                    tooltip_text += f"Staff: {values['Staff']}\n"
                    tooltip_text += f"Student: {values['Student']}\n"
                    tooltip_text += f"Visitor: {values['Visitor']}"
                    
                    # Update tooltip
                    self.week_bar_tooltip.xy = (rect.get_x() + rect.get_width()/2, rect.get_height())
                    self.week_bar_tooltip.set_text(tooltip_text)
                    self.week_bar_tooltip.set_visible(True)
                    self.week_bar_canvas.draw_idle()
                    break
            if not hit:
                self.week_bar_tooltip.set_visible(False)
                self.week_bar_canvas.draw_idle()
        else:
            self.week_bar_tooltip.set_visible(False)
            self.week_bar_canvas.draw_idle()


    def setup_monthly_chart(self, parent):
        nav_frame = ctk.CTkFrame(parent, fg_color="transparent")
        nav_frame.pack(side="top", fill="x", pady=(10, 0), padx=20)
        nav_frame.grid_columnconfigure(0, weight=1)
        nav_frame.grid_columnconfigure(1, weight=2)
        nav_frame.grid_columnconfigure(2, weight=1)

        prev_btn = ctk.CTkButton(nav_frame, text="◀ Previous Year",
                                command=self.show_previous_year,
                                fg_color="#4dabf7",
                                hover_color="#228be6",
                                width=130,
                                height=32,
                                font=ctk.CTkFont(size=14, weight="bold"))
        prev_btn.grid(row=0, column=0, sticky="w", padx=5)

        self.year_label = ctk.CTkLabel(nav_frame, 
            text=f"Year {self.current_year}",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#2c3e50")
        self.year_label.grid(row=0, column=1, sticky="nsew")

        next_btn = ctk.CTkButton(nav_frame, text="Next Year ▶",
                                command=self.show_next_year,
                                fg_color="#4dabf7",
                                hover_color="#228be6",
                                width=130,
                                height=32,
                                font=ctk.CTkFont(size=14, weight="bold"))
        next_btn.grid(row=0, column=2, sticky="e", padx=5)

        # Chart setup
        self.month_line_graph_fig, self.month_line_graph_ax = plt.subplots(figsize=(5, 2.8))
        self.month_line_graph_canvas = FigureCanvasTkAgg(self.month_line_graph_fig, master=parent)
        self.month_line_graph_canvas.get_tk_widget().pack(side="top", fill="both", expand=True, padx=15, pady=(0, 15))
        self.month_line_graph_ax.set_facecolor("#f8f9fa")
        self.month_line_graph_fig.patch.set_facecolor('white')
        self.update_month_line_graph()

    def update_month_line_graph(self):
        self.month_line_graph_ax.clear()
        # Fetch data from Firestore
        current_year_data = self.fetch_monthly_data(self.current_year)
        months = list(current_year_data.keys())
        x = np.arange(len(months))

        self.staff_line, = self.month_line_graph_ax.plot(
            x, [m["Staff"] for m in current_year_data.values()],
            color="#4dabf7", lw=2.5, marker="o", markersize=8,
            markerfacecolor="white", markeredgewidth=2
        )
        self.student_line, = self.month_line_graph_ax.plot(
            x, [m["Student"] for m in current_year_data.values()],
            color="#20c997", lw=2.5, marker="s", markersize=8,
            markerfacecolor="white", markeredgewidth=2
        )
        self.visitor_line, = self.month_line_graph_ax.plot(
            x, [m["Visitor"] for m in current_year_data.values()],
            color="#ff922b", lw=2.5, marker="D", markersize=8,
            markerfacecolor="white", markeredgewidth=2
        )

        # Styling
        self.month_line_graph_ax.set_xticks(x)
        self.month_line_graph_ax.set_xticklabels(months, color="#495057")
        self.month_line_graph_ax.tick_params(axis='y', colors="#495057")
        self.month_line_graph_ax.grid(color='#f1f3f5', linestyle='--')
        self.month_line_graph_ax.legend()

        self.month_line_graph_canvas.draw()

        # Recreate tooltip and event binding after chart update
        if hasattr(self, 'month_line_tooltip'):
            del self.month_line_tooltip
        self.month_line_tooltip = self.month_line_graph_ax.annotate("", xy=(0,0), xytext=(20, -10), textcoords="offset points",
            ha="left", va="bottom", fontsize=10, color="#2c3e50",
            bbox=dict(boxstyle="round,pad=0.3", fc="#f8f9fa", ec="#20c997", lw=1), arrowprops=dict(arrowstyle="->", color="#20c997"))
        self.month_line_tooltip.set_visible(False)
        self.month_line_graph_fig.canvas.mpl_connect('motion_notify_event', self.on_month_line_hover)

    def show_previous_year(self):
        # Allow navigation to previous years, but not before 2024
        if self.current_year <= 2024:
            messagebox.showwarning("Warning", "No data available for years before 2024.")
            return
        self.current_year -= 1
        self.update_month_line_graph()
        self.year_label.configure(text=f"Year {self.current_year}")

    def show_next_year(self):
        current_year = datetime.date.today().year
        if self.current_year >= current_year:
            self.play_warning_sound()
            messagebox.showwarning("Warning", "Cannot display data for future years.")
            return
        self.current_year += 1
        self.update_month_line_graph()
        self.year_label.configure(text=f"Year {self.current_year}")

    def on_month_line_hover(self, event):
        if event.inaxes != self.month_line_graph_ax:
            self.month_line_tooltip.set_visible(False)
            self.month_line_graph_canvas.draw_idle()
            return
        lines = [self.staff_line, self.student_line, self.visitor_line]
        labels = ["Staff", "Student", "Visitor"]
        colors = ["#4dabf7", "#20c997", "#ff922b"]
        min_dist = float('inf')
        closest_info = None
        for line, label, color in zip(lines, labels, colors):
            xdata = line.get_xdata()
            ydata = line.get_ydata()
            distances = np.sqrt((xdata - event.xdata) ** 2 + (ydata - event.ydata) ** 2)
            idx = np.argmin(distances)
            dist = distances[idx]
            if dist < min_dist and dist < 0.3:
                min_dist = dist
                closest_info = {
                    'month': self.month_labels[idx],
                    'value': ydata[idx],
                    'category': label,
                    'x': xdata[idx],
                    'y': ydata[idx],
                    'color': color
                }
        if closest_info:
            self.month_line_tooltip.xy = (closest_info['x'], closest_info['y'])
            self.month_line_tooltip.set_text(f"{closest_info['month']}\n{closest_info['category']}: {closest_info['value']}")
            self.month_line_tooltip.set_bbox(dict(boxstyle="round,pad=0.3", fc="#f8f9fa", ec=closest_info['color'], lw=1))
            self.month_line_tooltip.arrow_patch.set_color(closest_info['color'])
            self.month_line_tooltip.set_visible(True)
        else:
            self.month_line_tooltip.set_visible(False)
        self.month_line_graph_canvas.draw_idle()

    def setup_pie_chart(self, parent):
        self.pie_fig, self.pie_ax = plt.subplots(figsize=(3.5, 2.5))
        self.pie_canvas = FigureCanvasTkAgg(self.pie_fig, master=parent)
        self.pie_canvas.get_tk_widget().pack(fill="both", expand=True, padx=15, pady=15)

        # Style adjustments
        self.pie_ax.set_facecolor("#f8f9fa")
        self.pie_fig.patch.set_facecolor('white')
        self.pie_fig.subplots_adjust(right=0.65)

        self.update_pie_chart()

    def update_pie_chart(self):
        self.pie_ax.clear()
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        records = firebase_db.get_records(limit=1000)
        staff_count = 0
        student_count = 0
        visitor_count = 0
        for rec in records:
            if rec.get("entry_date") == today_str:
                identity = rec.get("owner_identity", "Visitor").capitalize()
                if identity == "Staff":
                    staff_count += 1
                elif identity == "Student":
                    student_count += 1
                else:
                    visitor_count += 1

        labels = []
        sizes = []
        colors = []
        explode = []
        if staff_count > 0:
            labels.append("Staff")
            sizes.append(staff_count)
            colors.append("#4dabf7")
            explode.append(0.05)
        if student_count > 0:
            labels.append("Student")
            sizes.append(student_count)
            colors.append("#20c997")
            explode.append(0.05)
        if visitor_count > 0:
            labels.append("Visitor")
            sizes.append(visitor_count)
            colors.append("#ff922b")
            explode.append(0.05)

        if sum([staff_count, student_count, visitor_count]) == 0:
            self.pie_ax.text(0.5, 0.5, "No data for today", ha='center', va='center', fontsize=14, color='#adb5bd')
            self.pie_canvas.draw()
            return

        def absolute_value(val):
            total = sum(sizes)
            amount = int(round(val/100.*total))
            return f'{amount}'

        wedges, texts, autotexts = self.pie_ax.pie(
            sizes, labels=labels, colors=colors,
            autopct=absolute_value, startangle=90,
            explode=explode, shadow=True,
            wedgeprops={'linewidth': 1.5, 'edgecolor': 'white'}
        )

        # Styling
        for text in texts:
            text.set_color("#495057")
            text.set_fontsize(9)
        for autotext in autotexts:
            autotext.set_color("white")
            autotext.set_fontsize(9)

        self.pie_ax.legend(wedges, labels,
                          title="Vehicle Types",
                          loc="center left",
                          bbox_to_anchor=(1.1, 0.5),
                          frameon=False,
                          fontsize=9)

        self.pie_canvas.draw()

    def create_alert_frame(self, parent):
        frame = ctk.CTkFrame(parent,
                             fg_color="white",
                             corner_radius=12,
                             border_width=1,
                             border_color="#dee2e6")

        # Header with icon
        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(pady=12)
        ctk.CTkLabel(header, image=self.icon_siren, text="", fg_color="transparent").pack(side="left", padx=(0, 8))
        ctk.CTkLabel(header, text="Security Alerts", font=ctk.CTkFont(size=16, weight="bold"), text_color="#2c3e50").pack(side="left")

        # Create alert list container
        self.alert_list = ctk.CTkFrame(frame, fg_color="white")
        self.alert_list.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.alert_types = ["Critical", "Warning", "Information"]
        for i in range(len(self.alert_types)):
            self.alert_list.grid_rowconfigure(i, weight=1)
        self.alert_list.grid_columnconfigure(0, weight=1)

        # Create cards for each alert type
        self.create_alert_cards()

        return frame

    def create_alert_cards(self):
        # Clear old cards before rebuilding
        for widget in self.alert_list.winfo_children():
            widget.destroy()

        color_map = {
            "Critical": ("#ff6b6b", "❗"),
            "Warning": ("#ffd43b", "⚠️"),
            "Information": ("#20c997", "ℹ️")
        }

        for row, alert_type in enumerate(self.alert_types):
            bg_color, icon = color_map[alert_type]
            card = ctk.CTkFrame(self.alert_list, fg_color="white", border_width=2, border_color=bg_color, corner_radius=8)
            card.grid(row=row, column=0, pady=4, padx=8, sticky="ew")

            icon_label = ctk.CTkLabel(card, text=icon, font=ctk.CTkFont(size=18), text_color=bg_color)
            icon_label.pack(side="left", padx=(15, 8), pady=4)
            type_label = ctk.CTkLabel(card, text=alert_type, font=ctk.CTkFont(size=14, weight="bold"), text_color=bg_color)
            type_label.pack(side="left", padx=8, pady=4)

            # unseen count logic
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

            # Add hover effect
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

            # Add click event
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
                # Table header
                table_header = ctk.CTkFrame(scroll_frame, fg_color="#f1f3f5")
                table_header.pack(fill="x", padx=6, pady=(0, 4))
                ctk.CTkLabel(table_header, text="Message", font=ctk.CTkFont(size=14, weight="bold"), text_color="#2c3e50", anchor="w", width=500, justify="left").pack(side="left", fill="x", padx=(10, 5))
                ctk.CTkLabel(table_header, text="Date", font=ctk.CTkFont(size=14, weight="bold"), text_color="#2c3e50", anchor="center", width=140, justify="center").pack(side="left", padx=(0, 0))
                ctk.CTkLabel(table_header, text="Time", font=ctk.CTkFont(size=14, weight="bold"), text_color="#2c3e50", anchor="e", width=120, justify="right").pack(side="left", padx=(0, 10))
                alerts = firebase_db.get_alerts_with_ids(type.lower(), limit=100)
                # Mark all as seen for this user
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
                    self.create_alert_cards()
                ctk.CTkButton(popup, text="Close", command=close_and_refresh, fg_color=color, hover_color=self.adjust_color(color, 0.8)).pack(pady=(0, 12))

            card.bind("<Button-1>", lambda e, t=alert_type, i=icon, c=bg_color: show_alert_details(t, i, c))
            for child in card.winfo_children():
                child.bind("<Button-1>", lambda e, t=alert_type, i=icon, c=bg_color: show_alert_details(t, i, c))

    def adjust_color(self, hex_color, factor):
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

        new_rgb = [min(255, int(c * factor)) for c in rgb]

        return f'#{new_rgb[0]:02x}{new_rgb[1]:02x}{new_rgb[2]:02x}'

    def get_today_entries(self):
        # Get today's date in YYYY-MM-DD format
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        # Fetch records for today
        records = firebase_db.get_records(limit=1000)
        count = 0
        for rec in records:
            if rec.get("entry_date") == today_str:
                count += 1
        return count

    def create_blacklist_frame(self, parent):
        frame = ctk.CTkFrame(
            parent,
            fg_color="white",
            corner_radius=12,
            border_width=1,
            border_color="#dee2e6"
        )
        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(pady=(12, 0))
        ctk.CTkLabel(header, image=self.icon_no_entry, text="", fg_color="transparent").pack(side="left", padx=(0, 8))
        ctk.CTkLabel(header, text="Blacklist Vehicles", font=ctk.CTkFont(size=16, weight="bold"), text_color="black").pack(side="left")

        search_var = tk.StringVar()

        search_frame = ctk.CTkFrame(frame, fg_color="transparent")
        search_frame.pack(pady=(8, 4), padx=10)

        search_entry = ctk.CTkEntry(
            search_frame,
            textvariable=search_var,
            width=220,
            fg_color="#f1f3f5",
            border_color="#c92a2a",
            border_width=2,
            text_color="black"
        )
        search_entry.pack(fill="x")

        placeholder_label = tk.Label(
            search_frame,
            text="E.g. ABC1234",
            fg="black",
            bg="#f1f3f5",
            font=("Arial", 11, "italic")
        )
        placeholder_label.place(x=8, y=2)

        def update_placeholder(*args):
            if search_var.get():
                placeholder_label.place_forget()
            else:
                placeholder_label.place(x=8, y=2)

        search_entry.bind("<FocusIn>", lambda e: update_placeholder())
        search_entry.bind("<FocusOut>", lambda e: update_placeholder())
        search_var.trace_add("write", lambda *a: update_placeholder())

        update_placeholder()

        scroll_frame = ctk.CTkScrollableFrame(frame, fg_color="white", width=260, height=180)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        def refresh_blacklist_cards(filtered_list):
            for widget in scroll_frame.winfo_children():
                widget.destroy()
            if not filtered_list:
                ctk.CTkLabel(
                    scroll_frame,
                    text="No results found.",
                    font=ctk.CTkFont(size=13, weight="bold"),
                    text_color="#adb5bd"
                ).pack(pady=20)
            for item in filtered_list:
                card = ctk.CTkFrame(scroll_frame, fg_color="#f8f9fa", corner_radius=8)
                card.pack(fill="x", pady=4, padx=2)
                ctk.CTkLabel(
                    card,
                    text=f"🚗 {item['vehicle_plate']}",
                    font=ctk.CTkFont(size=14, weight="bold"),
                    text_color="#c92a2a"
                ).pack(side="left", padx=(10, 6), pady=8)
                ctk.CTkLabel(
                    card,
                    text=item['reason'],
                    font=ctk.CTkFont(size=13),
                    text_color="#495057"
                ).pack(side="left", padx=6, pady=8)

                def show_details(event=None, data=item):
                    popup = ctk.CTkToplevel(frame)
                    popup.title("Blacklist Vehicle Details")
                    popup.geometry("350x180")
                    popup.grab_set()
                    popup.configure(fg_color="#18191a")

                    # Centering the popup on the screen
                    popup.update_idletasks()
                    w = 350
                    h = 180
                    x = (popup.winfo_screenwidth() // 2) - (w // 2)
                    y = (popup.winfo_screenheight() // 2) - (h // 2)
                    popup.geometry(f"{w}x{h}+{x}+{y}")

                    content = ctk.CTkFrame(popup, fg_color="white", corner_radius=16)
                    content.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.88, relheight=0.82)

                    # Plate number
                    ctk.CTkLabel(
                        content,
                        text=f"🚗 {data['vehicle_plate']}",
                        font=ctk.CTkFont(size=22, weight="bold"),
                        text_color="#ff4444",  # Bright red
                        anchor="center"
                    ).pack(pady=(18, 6))

                    # Reason
                    ctk.CTkLabel(
                        content,
                        text=f"Reason: {data['reason']}",
                        font=ctk.CTkFont(size=15, weight="bold"),
                        text_color="black",
                        anchor="center"
                    ).pack(pady=(0, 18))

                    # Close button
                    ctk.CTkButton(
                        content,
                        text="Close",
                        fg_color="#3578e5",
                        hover_color="#2851a3",
                        text_color="white",
                        font=ctk.CTkFont(size=15, weight="bold"),
                        width=120,
                        height=36,
                        command=popup.destroy
                    ).pack(pady=(0, 8))

                card.bind("<Button-1>", show_details)
                for child in card.winfo_children():
                    child.bind("<Button-1>", show_details)

        def on_search(*args):
            query = search_var.get().strip().lower()
            if not query:
                filtered = self.blacklist_data
            else:
                filtered = [item for item in self.blacklist_data if query in item['vehicle_plate'].lower()]
            refresh_blacklist_cards(filtered)

        def update_blacklist_data():
            # Fetch blacklist data from Firebase
            self.blacklist_data = firebase_db.get_blacklist()
            # Update the display with the new data
            on_search()

        search_var.trace_add("write", on_search)
        
        # Initial data load
        update_blacklist_data()

        return frame

    def fetch_weekly_data(self, year, week):
        records = firebase_db.get_records(limit=500)
        week_days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        week_data = {day: {"Staff": 0, "Student": 0, "Visitor": 0} for day in week_days}
        for rec in records:
            entry_date = rec.get("entry_date")
            owner_identity = rec.get("owner_identity", "Visitor").capitalize()
            if entry_date:
                try:
                    dt = datetime.datetime.strptime(entry_date, "%Y-%m-%d").date()
                except ValueError:
                    continue  # Skip if date format is wrong
                entry_year, entry_week, entry_weekday = dt.isocalendar()
                if entry_year == year and entry_week == week:
                    day_name = week_days[dt.weekday()]
                    if owner_identity in week_data[day_name]:
                        week_data[day_name][owner_identity] += 1
                    else:
                        week_data[day_name]["Visitor"] += 1
        return week_data

    def fetch_monthly_data(self, year):
        records = firebase_db.get_records(limit=2000)
        month_labels = self.month_labels
        # Initialize data structure
        month_data = {month: {"Staff": 0, "Student": 0, "Visitor": 0} for month in month_labels}
        for rec in records:
            entry_date = rec.get("entry_date")
            owner_identity = rec.get("owner_identity", "Visitor").capitalize()
            if entry_date:
                try:
                    dt = datetime.datetime.strptime(entry_date, "%Y-%m-%d").date()
                except ValueError:
                    continue
                if dt.year == year:
                    month_idx = dt.month - 1
                    month_name = month_labels[month_idx]
                    if owner_identity in month_data[month_name]:
                        month_data[month_name][owner_identity] += 1
                    else:
                        month_data[month_name]["Visitor"] += 1
        return month_data


