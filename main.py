# main.py (Final Consolidated Version)

# Standard Python Imports
import os
import shutil
import datetime
import sqlite3 as sq
from fpdf import FPDF
import pandas as pd
import xlsxwriter

# Kivy/KivyMD Imports
from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivy.uix.screenmanager import Screen, SlideTransition
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.list import IRightBodyTouch, ThreeLineAvatarIconListItem
from kivymd.uix.behaviors import TouchBehavior
from kivymd.toast import toast
from kivy.utils import platform

# Kivy widgets used in various popups
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.textinput import TextInput  # Explicitly importing TextInput
from datetime import date

# --- Configuration ---
# Prevent Permission Denied error on some Android versions
os.environ['KIVY_NO_ENV_CONFIG'] = '1'
Window.size = (360, 600)


# ---------------------


# --- Screens (for class definition consistency) ---
class Homescreen(Screen):
    pass


class Memoscreen(Screen):
    pass


class Billscreen(Screen):
    pass


class Content(MDBoxLayout):
    pass


class ListItemWithCheckbox(ThreeLineAvatarIconListItem):
    pass


class RightCheckbox(MDCheckbox, IRightBodyTouch):
    pass


# --- Main App Class ---
class JTCApp(MDApp):
    dialog = None
    db_name = "jtc.db"  # Standardized DB Name

    # -------------------------
    # Build / lifecycle
    # -------------------------
    def build(self):
        self.screen = Builder.load_file('main.kv')
        return self.screen

    def on_start(self):
        # Determine the correct DB path and connect
        self.db_path = os.path.join(self.user_data_dir, self.db_name)

        # Request necessary permissions (especially for Android)
        self.request_android_permissions()

        try:
            # 1. Ensure the directory exists
            if not os.path.exists(self.user_data_dir):
                os.makedirs(self.user_data_dir)

            # 2. Check if the DB exists (to ensure we use the correct path)
            if not os.path.exists(self.db_path):
                print(f"Database not found at {self.db_path}. Creating new one.")
                self._initialize_database()

            # 3. Populate list from DB
            co = sq.connect(self.db_path, timeout=10.0)
            cur = co.cursor()
            infos = cur.execute("SELECT * FROM trip_info").fetchall()

            list_one = self.root.get_screen('home').ids.list_one
            for info in infos:
                item = ListItemWithCheckbox(
                    text=f"{info[0]} - {info[1]}",
                    secondary_text=f"{info[3]} - {info[4]}",
                    tertiary_text=f"Date: {info[8]}"
                )
                list_one.add_widget(item)

            co.close()

            # Enable toolbar actions
            self.root.get_screen('home').ids.tool_bar.right_action_items.disabled = False

        except Exception as e:
            print(f"Error during on_start/DB initialization: {e}")
            toast(f"Startup Error: {e}")

    # -------------------------
    # Database Initialization (New Helper)
    # -------------------------
    def _initialize_database(self):
        """Creates the database file and necessary tables."""
        try:
            co = sq.connect(self.db_path, timeout=10.0)
            cur = co.cursor()
            self._ensure_trip_tables_exist(cur)
            self.ensure_bill_info_columns(cur)
            co.commit()
            co.close()
            print("Database and tables initialized successfully.")
        except Exception as e:
            print(f"Failed to initialize DB: {e}")

    # -------------------------
    # Platform / Permission Helpers
    # -------------------------
    def request_android_permissions(self):
        """Request external storage permission for Android to allow file saving."""
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])

    def get_downloads_folder(self):
        """Returns the appropriate directory for saving files (Memo/Bill/Backup)."""
        if platform == 'android':
            # Android: use shared download folder, appending a sub-folder
            from android.storage import primary_external_storage_path
            path = os.path.join(primary_external_storage_path(), 'Download', 'JTC_Files')
        else:
            # Desktop/Windows: Use home directory
            path = os.path.join(os.path.expanduser('~'), 'JTC_Files')

        os.makedirs(path, exist_ok=True)
        return path

    # -------------------------
    # Small helpers (Database and UI logic)
    # -------------------------
    @staticmethod
    def _ensure_trip_tables_exist(cur):
        """Create trip_info and trip_per if they don't exist."""
        cur.execute("""
            CREATE TABLE IF NOT EXISTS trip_info(
                trip_id INTEGER PRIMARY KEY AUTOINCREMENT,
                truck_no TEXT NOT NULL,
                m_s TEXT NOT NULL,
                from_trip TEXT NOT NULL,
                to_trip TEXT NOT NULL,
                advance TEXT NOT NULL,
                balance TEXT NOT NULL,
                fraight TEXT NOT NULL,
                date TEXT NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS trip_per(
                trip_id INTEGER PRIMARY KEY AUTOINCREMENT,
                truck_no TEXT NOT NULL,
                m_s TEXT NOT NULL,
                from_trip TEXT NOT NULL,
                to_trip TEXT NOT NULL,
                advance TEXT NOT NULL,
                balance TEXT NOT NULL,
                fraight TEXT NOT NULL,
                date TEXT NOT NULL
            )
        """)

    @staticmethod
    def ensure_bill_info_columns(cur):
        """Ensure bill_info table exists and has required columns (adds missing columns)."""
        cur.execute("""
            CREATE TABLE IF NOT EXISTS bill_info (
                bill_id INTEGER PRIMARY KEY AUTOINCREMENT,
                trip_id INTEGER,
                memo_number TEXT
            )
        """)
        cur.execute("PRAGMA table_info(bill_info)")
        existing = {row[1] for row in cur.fetchall()}
        required = {
            "truck_no": "TEXT", "m_s": "TEXT", "from_trip": "TEXT", "to_trip": "TEXT",
            "advance": "TEXT", "balance": "TEXT", "fraight": "TEXT", "consignor": "TEXT",
            "consignee": "TEXT", "description_of_goods": "TEXT", "no_of_articles": "TEXT",
            "weight": "TEXT", "bill_date": "TEXT", "remark": "TEXT", "additional_charge": "TEXT",
            "date": "TEXT"
        }
        for col, col_type in required.items():
            if col not in existing:
                cur.execute(f"ALTER TABLE bill_info ADD COLUMN {col} {col_type}")

    @staticmethod
    def to_float(val):
        try:
            # Handle comma separators in input (e.g. 1,000)
            return float(str(val).replace(',', ''))
        except Exception:
            return 0.0

    @staticmethod
    def _clear_all_selections(list_widget):
        """Uncheck all checkboxes in the list widget (children expected to be ListItemWithCheckbox)."""
        for w in list(list_widget.children):
            try:
                if hasattr(w, 'ids') and 'cb' in w.ids:
                    w.ids.cb.active = False
            except Exception:
                pass

    # -------------------------
    # Dialog to add new trip
    # -------------------------
    def show_confirmation_dialog(self):
        """Pop up the MDDialog (uses Content() custom widget from main.kv)."""
        if not self.dialog:
            self.dialog = MDDialog(
                title="Please enter details:",
                type="custom",
                content_cls=Content(),
                buttons=[
                    MDFlatButton(
                        text="CANCEL",
                        theme_text_color="Custom",
                        text_color=self.theme_cls.primary_color,
                        on_release=self.dialog_close,
                    ),
                    MDFlatButton(
                        text="OK",
                        theme_text_color="Custom",
                        text_color=self.theme_cls.primary_color,
                        on_release=self.dialog_ok,
                    ),
                ],
            )
        self.dialog.open()

    def dialog_close(self, *args):
        # Clear fields in the dialog content and close
        try:
            for i in range(1, 8):
                self.dialog.content_cls.ids[f"Trip_details{i}"].text = ""
        except Exception:
            pass
        self.dialog.dismiss(force=True)

    def dialog_ok(self, *args):
        # Validate dialog fields and insert into DB and UI
        fields = []
        try:
            for i in range(1, 8):
                fields.append(self.dialog.content_cls.ids[f"Trip_details{i}"])
        except Exception:
            toast("Dialog not properly configured in KV.")
            return

        for field in fields:
            if not field.text.strip():
                toast("Please fill all fields before continuing.")
                field.error = True
                return

        today = date.today().strftime('%d/%m/%Y')
        co = sq.connect(self.db_path, timeout=10.0)
        cur = co.cursor()
        # Ensure tables exist
        self._ensure_trip_tables_exist(cur)

        values = [field.text.strip() for field in fields]
        cur.execute("""INSERT INTO trip_info(truck_no,m_s,from_trip,to_trip,advance,balance,fraight,date)
                        VALUES(?,?,?,?,?,?,?,?)""", (*values, today))
        cur.execute("""INSERT INTO trip_per(truck_no,m_s,from_trip,to_trip,advance,balance,fraight,date)
                        VALUES(?,?,?,?,?,?,?,?)""", (*values, today))
        co.commit()

        # Clear input fields
        for field in fields:
            field.text = ""

        # Update UI with latest inserted
        infos = cur.execute("SELECT * FROM trip_info ORDER BY trip_id DESC LIMIT 1").fetchall()
        for info in infos:
            item = ListItemWithCheckbox(
                text=f"{info[0]} - {info[1]}",
                secondary_text=f"{info[3]} - {info[4]}",
                tertiary_text=f"Date: {info[8]}"
            )
            try:
                self.root.get_screen('home').ids.list_one.add_widget(item, index=len(
                    self.root.get_screen('home').ids.list_one.children))  # Add to top
            except Exception:
                pass

        cur.close()
        co.close()
        self.dialog.dismiss(force=True)

    # -------------------------
    # Delete selected trips
    # -------------------------
    def del_det(self, *args):
        list_container = self.root.get_screen('home').ids.list_one
        widgets_to_delete = []
        trip_ids_to_delete = []

        for w in list(list_container.children):
            if isinstance(w, ListItemWithCheckbox) and getattr(w, 'ids', None) and w.ids.cb.active:
                widgets_to_delete.append(w)
                # Extract trip_id from the list item text (e.g., "123 - TruckName")
                try:
                    trip_id = w.text.split('-')[0].strip()
                    trip_ids_to_delete.append(trip_id)
                except Exception:
                    print(f"Could not parse trip ID from list item text: {w.text}")

        if not widgets_to_delete:
            toast("No items selected for deletion.")
            return

        try:
            co = sq.connect(self.db_path, timeout=10.0)
            cur = co.cursor()
            for trip_id in trip_ids_to_delete:
                cur.execute("DELETE FROM trip_info WHERE trip_id=?", (trip_id,))
                # Also delete from trip_per and bill_info for integrity
                cur.execute("DELETE FROM trip_per WHERE trip_id=?", (trip_id,))
                cur.execute("DELETE FROM bill_info WHERE trip_id=?", (trip_id,))
            co.commit()
            co.close()

            # Update UI
            for w in widgets_to_delete:
                list_container.remove_widget(w)

            toast("Selected trips and associated data deleted.")
        except Exception as e:
            toast(f"Deletion failed: {e}")

    # -------------------------
    # Screen transitions
    # -------------------------
    def change_screen_Trn_left(self, screen_name):
        self.root.transition = SlideTransition(direction="left")
        self.root.current = screen_name

    def change_screen_Trn_right(self, screen_name):
        self.root.transition = SlideTransition(direction="right")
        self.root.current = screen_name

    # -------------------------
    # Generate Memo
    # -------------------------
    def Generate_Memo(self):
        memo_generated = False
        generated_bills = []

        # Get the list of trip widgets
        trip_list_widget = self.root.get_screen('home').ids.list_one.children
        list_widget = self.root.get_screen('home').ids.list_one

        # Check if at least one checkbox is selected
        any_checked = any(
            isinstance(item, ListItemWithCheckbox) and getattr(item, 'ids', None) and item.ids.cb.active for item in
            trip_list_widget)

        if not any_checked:
            toast("Please select at least one trip to generate memo.")
            return

            # PDF generator for memo

        def generate_memo_pdf(bill_no, trip_date, ms, truck_no, trip_to, trip_fra, trip_adv, trip_bal):
            try:
                pdf = FPDF('P', 'mm', 'Letter')
                pdf.add_page()

                # Replace 'Logo_JTC.png' with a placeholder path or ensure file exists in project root
                logo_path = os.path.join(os.getcwd(), 'Logo_JTC.png')
                if os.path.exists(logo_path):
                    pdf.image(logo_path, x=15, y=10, w=65)

                pdf.set_xy(85, 15)
                pdf.set_font('helvetica', 'B', 20)
                pdf.cell(0, 10, "JITENDRA TRANSPORT CO.", ln=True, align='L')

                pdf.set_font('helvetica', '', 11)
                pdf.set_x(85)
                pdf.cell(0, 6, "Office: A1, 102, Pawanputra Residency,", ln=True, align='L')
                pdf.set_x(85)
                pdf.cell(0, 6, "Kalher, Bhiwandi, Thane (421302)", ln=True, align='L')
                pdf.set_x(85)
                pdf.cell(0, 6, "Ph: 9960153368 / 8208287625 / 8788215464", ln=True, align='L')

                pdf.set_draw_color(0, 51, 102)
                pdf.set_line_width(0.8)
                pdf.line(10, 50, 205, 50)
                pdf.ln(15)

                pdf.set_font('helvetica', '', 12)
                pdf.cell(0, 10, f"Memo No: {bill_no}", ln=False, align='L')
                pdf.cell(0, 10, f"Date: {trip_date}", ln=True, align='R')
                pdf.ln(5)

                pdf.set_font('helvetica', '', 12)
                pdf.cell(0, 8, "To,", ln=True)
                pdf.cell(0, 8, f"M/S: {ms}", ln=True)
                pdf.cell(0, 8, "PAN No: BEAPS2082B", ln=True)
                pdf.ln(5)
                pdf.cell(0, 8, "Dear Sir,", ln=True)
                pdf.ln(5)

                # helper to write mixed bold parts
                def write_mixed_line(p, parts):
                    for text, style in parts:
                        p.set_font('helvetica', style, 12)
                        p.write(8, text)
                    p.ln(10)

                write_mixed_line(pdf, [
                    ("We are sending Truck No. ", ''), (truck_no, 'B'),
                    (" for ", ''), (trip_to, 'B'),
                    (" at the rate of Rs. ", ''), (str(trip_fra), 'B'),
                    (" per M.T. Guaranteed fixed M. Ton. Advance Rs. ", ''), (str(trip_adv), 'B'),
                    (", Balance Rs. ", ''), (str(trip_bal), 'B'),
                    (" at Mumbai one party delivery balance at godown.", '')
                ])

                pdf.ln(5)
                pdf.set_font('helvetica', '', 12)
                pdf.multi_cell(0, 8,
                               "Please arrange to load the truck and check all the necessary papers before loading the goods.")
                pdf.ln(5)
                pdf.multi_cell(0, 8,
                               "Kindly insure your goods; otherwise, we are not responsible for accidents, theft, looting, etc.")
                pdf.ln(10)

                pdf.cell(0, 10, "Thanking you,", ln=True)
                pdf.ln(15)
                pdf.cell(0, 10, "Yours faithfully,", ln=True, align='R')
                pdf.cell(0, 10, "For JITENDRA TRANSPORT CO.", ln=True, align='R')

                # Save memo in 'generated_memos'
                save_dir = self.get_downloads_folder()
                filename = os.path.join(save_dir, f"Memo_{bill_no}.pdf")
                pdf.output(filename)

                return filename

            except Exception as e:
                print("Error generating memo PDF:", e)
                return None

        # iterate selections and generate PDFs
        for w in list(list_widget.children):
            if isinstance(w, ListItemWithCheckbox):
                try:
                    cb = w.ids.cb
                except Exception:
                    continue
                if cb.active:
                    memo_generated = True
                    trip_id = w.text.split('-')[0].strip()

                    try:
                        co = sq.connect(self.db_path, timeout=10.0)
                        cur = co.cursor()
                        get_info = cur.execute("SELECT * FROM trip_info WHERE trip_id = ?", (trip_id,)).fetchall()
                        co.close()

                        for x in get_info:
                            bill_no = x[0]
                            truck_no = x[1]
                            ms = x[2]
                            # trip_from = x[3] # Unused here
                            trip_to = x[4]
                            trip_adv = x[5]
                            trip_bal = x[6]
                            trip_fra = x[7]
                            trip_date = x[8]

                            filename = generate_memo_pdf(bill_no, trip_date, ms, truck_no, trip_to, trip_fra, trip_adv,
                                                         trip_bal)
                            if filename:
                                generated_bills.append(bill_no)

                    except Exception as e:
                        toast(f"Database error on memo generation: {e}")
                        break

        # Show popup if any memo generated
        if memo_generated and generated_bills:
            bill_text = ", ".join(str(b) for b in generated_bills)
            message = f'Memo No(s): [b]{bill_text}[/b] has been generated successfully!'

            box = BoxLayout(orientation='vertical', padding=20, spacing=20)

            # Define rounded bg widget
            bg = Widget()
            with bg.canvas.before:
                Color(0.15, 0.15, 0.15, 0.95)
                bg.rect = RoundedRectangle(radius=[20], pos=bg.pos, size=bg.size)
            bg.bind(pos=lambda _, val: setattr(bg.rect, 'pos', val))
            bg.bind(size=lambda _, val: setattr(bg.rect, 'size', val))

            label = Label(text=message, markup=True, halign='center', valign='middle', color=(1, 1, 1, 1),
                          font_size='18sp')
            label.bind(size=lambda s, _: setattr(s, 'text_size', s.size))

            btn_layout = AnchorLayout(anchor_x='center', anchor_y='bottom')
            ok_button = Button(text="OK", size_hint=(0.3, 0.4), background_color=(0, 0.5, 1, 1), font_size='16sp')
            btn_layout.add_widget(ok_button)

            box.add_widget(label)
            box.add_widget(btn_layout)

            popup = Popup(title="✅ Memo Generated", content=box, size_hint=(0.6, 0.4), separator_color=(0, 0.5, 1, 1),
                          auto_dismiss=False)

            def close_popup(instance):
                # Uncheck all checkboxes
                self._clear_all_selections(list_widget)
                popup.dismiss()

            ok_button.bind(on_press=close_popup)
            popup.open()
        elif memo_generated and not generated_bills:
            toast("Memo generation failed for all selected trips.")

    # -------------------------
    # Generate Bill (single selection + collects extra details)
    # -------------------------
    def Generate_Bill(self):
        trip_list_widget = self.root.get_screen('home').ids.list_one
        trip_list = list(trip_list_widget.children)
        checked_items = [item for item in trip_list if getattr(item, 'ids', None) and item.ids.cb.active]

        if len(checked_items) == 0:
            toast("Please select one trip to generate bill.")
            return
        if len(checked_items) > 1:
            toast("Please select only one trip at a time.")
            return

        selected_item = checked_items[0]
        trip_id = selected_item.text.split('-')[0].strip()

        # fetch trip info to ensure it exists
        try:
            co = sq.connect(self.db_path, timeout=10.0)
            cur = co.cursor()
            trip_info = cur.execute("SELECT * FROM trip_info WHERE trip_id=?", (trip_id,)).fetchone()
            co.close()
        except Exception as e:
            toast(f"Database error: {e}")
            return

        if not trip_info:
            toast("Trip not found in database.")
            return

        # Build popup for collecting extra bill details
        fields = ["Consignor", "Consignee", "Description of Goods", "No of Articles", "Weight", "Remark",
                  "Additional Charge"]
        inputs = {}
        layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        scroll = ScrollView(size_hint=(1, 1))
        inner_layout = BoxLayout(orientation='vertical', spacing=8, size_hint_y=None)
        inner_layout.bind(minimum_height=inner_layout.setter('height'))

        for field in fields:
            box = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), spacing=dp(8))
            lbl = Label(text=field, size_hint_x=0.4, halign='right', valign='middle')
            lbl.bind(size=lbl.setter('text_size'))
            ti = TextInput(multiline=False, size_hint_x=0.6)
            if field == "Additional Charge":
                ti.input_filter = 'float'
            inputs[field] = ti
            box.add_widget(lbl)
            box.add_widget(ti)
            inner_layout.add_widget(box)

        scroll.add_widget(inner_layout)
        layout.add_widget(scroll)

        btn_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(60), spacing=dp(10),
                            padding=(0, dp(10)))
        submit_btn = Button(text="Submit")
        cancel_btn = Button(text="Cancel")
        btn_box.add_widget(submit_btn)
        btn_box.add_widget(cancel_btn)
        layout.add_widget(btn_box)

        popup = Popup(title="Enter Bill Details", content=layout, size_hint=(0.85, 0.8))

        # generate_pdf_bill: fetch bill_info and create the PDF
        def generate_pdf_bill(memo_number):
            try:
                co = sq.connect(self.db_path, timeout=10.0)
                co.row_factory = sq.Row
                cur = co.cursor()
                bill = cur.execute("SELECT * FROM bill_info WHERE memo_number=?", (memo_number,)).fetchone()
                co.close()
            except Exception as e:
                toast(f"DB fetch error: {e}")
                return

            if not bill:
                toast("Bill data not found for PDF generation.")
                return

            def safe_get(key):
                return bill[key] if key in bill.keys() and bill[key] is not None else ""

            memo = safe_get("memo_number")
            truck_no = safe_get("truck_no")
            ms = safe_get("m_s")
            from_trip = safe_get("from_trip")
            to_trip = safe_get("to_trip")
            advance = safe_get("advance")
            balance = safe_get("balance")
            fraight = safe_get("fraight")
            consignor = safe_get("consignor")
            consignee = safe_get("consignee")
            description = safe_get("description_of_goods")
            no_of_articles = safe_get("no_of_articles")
            weight = safe_get("weight")
            bill_date = safe_get("bill_date")
            remark = safe_get("remark")
            additional_charge = safe_get("additional_charge")
            trip_date = safe_get("date")

            # Build PDF (same layout as original)
            pdf = FPDF('P', 'mm', 'A4')
            pdf.add_page()

            logo_path = os.path.join(os.getcwd(), 'Logo_JTC.png')
            if os.path.exists(logo_path):
                pdf.image(logo_path, x=15, y=10, w=65)

            pdf.set_xy(85, 15)
            pdf.set_font('helvetica', 'B', 20)
            pdf.cell(0, 10, "JITENDRA TRANSPORT CO.", ln=True, align='L')
            pdf.set_font('helvetica', '', 11)
            pdf.set_x(85)
            pdf.cell(0, 6, "Office: A1, 102, Pawanputra Residency,", ln=True, align='L')
            pdf.set_x(85)
            pdf.cell(0, 6, "Kalher, Bhiwandi, Thane (421302)", ln=True, align='L')
            pdf.set_x(85)
            pdf.cell(0, 6, "Ph: 9960153368 / 8208287625 / 8788215464", ln=True, align='L')

            pdf.set_draw_color(0, 51, 102)
            pdf.set_line_width(0.8)
            pdf.line(10, 50, 205, 50)
            pdf.ln(15)

            pdf.set_font('helvetica', '', 11)
            pdf.cell(100, 6, f"Transporter Name: {ms}", border=0)
            pdf.cell(0, 6, f"Bill No: {memo}", align='R', ln=True)
            pdf.cell(100, 6, f"From: {from_trip}    To: {to_trip}", border=0)
            pdf.cell(0, 6, f"Bill Date: {bill_date}", align='R', ln=True)
            pdf.cell(100, 6, f"Load Date: {trip_date}", border=0)
            pdf.cell(0, 6, f"Truck No: {truck_no}", align='R', ln=True)
            pdf.ln(15)

            pdf.set_font('helvetica', 'B', 12)
            pdf.cell(0, 8, "Consignment Details", ln=True, align='C')
            pdf.set_font('helvetica', '', 11)
            pdf.ln(4)

            col_widths = [35, 35, 45, 20, 20, 25]
            headers = ["Consignor", "Consignee", "Description", "Articles", "Weight", "Rate"]
            pdf.set_fill_color(200, 220, 255)
            for i, header in enumerate(headers):
                pdf.cell(col_widths[i], 8, header, border=1, fill=True, align='C')
            pdf.ln()

            pdf.cell(col_widths[0], 8, consignor, border=1, align='C')
            pdf.cell(col_widths[1], 8, consignee, border=1, align='C')
            pdf.cell(col_widths[2], 8, description, border=1, align='C')
            pdf.cell(col_widths[3], 8, str(no_of_articles), border=1, align='C')
            pdf.cell(col_widths[4], 8, str(weight), border=1, align='C')
            pdf.cell(col_widths[5], 8, str(fraight), border=1, align='C')
            pdf.ln(10)

            pdf.set_font('helvetica', 'B', 12)
            pdf.cell(0, 10, "Charges Summary", ln=True, align='C')
            pdf.set_font('helvetica', '', 11)
            pdf.ln(3)

            advance_val = self.to_float(advance)
            balance_val = self.to_float(balance)
            additional_val = self.to_float(additional_charge)
            total_val = advance_val + balance_val + additional_val

            charges = [("Advance", f"{advance_val:,.2f}"), ("Balance", f"{balance_val:,.2f}")]
            if additional_val > 0:
                charges.append(("Additional Charges", f"{additional_val:,.2f}"))
            charges.append(("Total", f"{total_val:,.2f}"))

            table_width = 90
            page_width = 210
            x_start = (page_width - table_width) / 2
            label_width = 55
            value_width = 35

            for label, value in charges[:-1]:
                pdf.set_x(x_start)
                pdf.cell(label_width, 8, label, align='L')
                pdf.cell(8, 8, "Rs.", align='L')
                pdf.cell(value_width - 8, 8, value, align='R')
                pdf.ln(7)

            pdf.set_x(x_start)
            pdf.set_font('helvetica', 'B', 11)
            pdf.cell(label_width, 8, "Total", align='L')
            pdf.cell(8, 8, "Rs.", align='L')
            pdf.cell(value_width - 8, 8, f"{total_val:,.2f}", align='R')
            pdf.ln(15)

            if remark:
                pdf.set_font('helvetica', 'B', 11)
                pdf.cell(0, 6, "Remark:", ln=True)
                pdf.set_font('helvetica', '', 11)
                pdf.multi_cell(0, 6, remark)
                pdf.ln(4)

            pdf.set_font('helvetica', 'B', 12)
            pdf.cell(0, 8, "For JITENDRA TRANSPORT CO.", ln=True, align='R')
            pdf.ln(10)
            pdf.set_font('helvetica', '', 11)
            pdf.cell(0, 8, "(Authorised Signatory)", ln=True, align='R')
            pdf.ln(10)
            pdf.set_font('helvetica', 'I', 10)
            pdf.set_text_color(120, 120, 120)
            pdf.cell(0, 6, "This is a computer-generated bill. No signature required.", ln=True, align='C')

            save_dir = self.get_downloads_folder()
            filename = os.path.join(save_dir, f"Bill_{memo_number}.pdf")
            pdf.output(filename)

            # confirmation popup
            def close_ok(_):
                popup_ok.dismiss()
                self._clear_all_selections(trip_list_widget)

            # OK button inside AnchorLayout to center it
            ok_btn = Button(
                text="OK",
                size_hint=(None, None),
                size=(dp(100), dp(40))
            )
            ok_layout = AnchorLayout(anchor_x='center', anchor_y='center', size_hint_y=None, height=dp(60))
            ok_layout.add_widget(ok_btn)
            ok_btn.bind(on_release=close_ok)

            # Label that wraps text and adjusts height dynamically
            message = Label(
                text=f"Bill {memo_number} generated successfully!",
                halign='center',
                valign='middle',
                text_size=(dp(300), None)
            )
            message.bind(texture_size=lambda instance, value: setattr(instance, 'height', value[1]))

            # Spacer widgets for top and bottom spacing
            top_spacer = Widget(size_hint_y=None, height=dp(25))
            bottom_spacer = Widget(size_hint_y=None, height=dp(20))

            # Vertical layout
            box = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
            box.add_widget(top_spacer)
            box.add_widget(message)
            box.add_widget(bottom_spacer)
            box.add_widget(ok_layout)

            popup_ok = Popup(
                title="Success",
                content=box,
                size_hint=(None, None),
                size=(dp(350), dp(240)),
                auto_dismiss=False
            )
            popup_ok.open()

        # submit handler for the bill popup
        def submit_details(_instance):
            bill_data = {field: inputs[field].text.strip() for field in fields}
            required = ["Consignor", "Consignee", "Description of Goods", "No of Articles", "Weight"]
            for field in required:
                if not bill_data[field]:
                    toast(f"Please enter {field}.")
                    return

            # Generate a unique memo number
            memo_number = f"M-{trip_id}-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
            bill_date = datetime.date.today().strftime('%d/%m/%Y')

            try:
                co = sq.connect(self.db_path, timeout=10.0)
                cur = co.cursor()
                self.ensure_bill_info_columns(cur)

                trip_info_row = cur.execute("""
                    SELECT truck_no, m_s, from_trip, to_trip, advance, balance, fraight, date
                    FROM trip_info WHERE trip_id = ?
                """, (trip_id,)).fetchone()

                if not trip_info_row:
                    toast("Trip details not found.")
                    co.close()
                    return

                truck_no, m_s, from_trip, to_trip, advance, balance, fraight, trip_date = trip_info_row

                cur.execute("""
                    INSERT INTO bill_info (
                        trip_id, memo_number, truck_no, m_s, from_trip, to_trip,
                        advance, balance, fraight, consignor, consignee,
                        description_of_goods, no_of_articles, weight,
                        bill_date, remark, additional_charge, date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    int(trip_id), memo_number, truck_no, m_s, from_trip, to_trip,
                    advance, balance, fraight,
                    bill_data["Consignor"], bill_data["Consignee"],
                    bill_data["Description of Goods"], bill_data["No of Articles"],
                    bill_data["Weight"], bill_date,
                    bill_data.get("Remark", ""), bill_data.get("Additional Charge", "0"), trip_date
                ))

                co.commit()
                co.close()

                popup.dismiss()
                toast("Bill details saved successfully!")
                generate_pdf_bill(memo_number)
            except Exception as e:
                toast(f"Failed to save bill data: {e}")
                try:
                    popup.dismiss()
                except Exception:
                    pass

        submit_btn.bind(on_release=submit_details)
        cancel_btn.bind(on_release=lambda _: popup.dismiss())
        popup.open()

    # -------------------------
    # Database Backup/Export (Restored and Corrected)
    # -------------------------
    def backup_database_excel(self, *args):
        """Exports all database tables (trip_info, etc.) to a single Excel file."""
        from kivymd.toast import toast

        # Helper for UI feedback
        def show_result(success, message):
            # Attempt to reset the icon if it's set to loading ('sync')
            try:
                # Find the 'cloud-upload-outline' button index (assuming it's the second button, index 1)
                self.root.get_screen('home').ids.tool_bar.right_action_items[1][0] = "cloud-upload-outline"
            except Exception:
                pass

            if success:
                toast(f"✅ Backup saved: {message}", duration=5)
            else:
                toast(f"🛑 Backup failed: {message}", duration=5)

        try:
            # Show loading spinner (assuming the second button is the backup button)
            try:
                self.root.get_screen('home').ids.tool_bar.right_action_items[1][0] = "sync"
            except Exception:
                pass

            db_path = self.db_path

            if not os.path.exists(db_path):
                show_result(False, "Database file does not exist.")
                return False, "Database file does not exist"

            # Flush WAL
            try:
                co = sq.connect(db_path)
                co.execute("PRAGMA wal_checkpoint(FULL);")
                co.commit()
                co.close()
            except Exception as e:
                print("DB flush failed:", e)

            # Backup folder
            backup_dir = self.get_downloads_folder()
            os.makedirs(backup_dir, exist_ok=True)

            # Backup filename
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_dir, f"jtc_backup_{timestamp}.xlsx")

            # Connect DB and get all table names
            co = sq.connect(db_path)
            cur = co.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cur.fetchall()]

            # Create Excel writer
            with pd.ExcelWriter(backup_file, engine='xlsxwriter') as writer:
                for table in tables:
                    if table.startswith('sqlite_'):
                        continue

                    df = pd.read_sql_query(f"SELECT * FROM {table}", co)
                    sheet_name = table if len(table) <= 31 else table[:31]
                    df.to_excel(writer, sheet_name=sheet_name, index=False)

            co.close()
            show_result(True, os.path.basename(backup_file))
            return True, backup_file

        except Exception as e:
            error_message = f"Error: {str(e)}"
            print(f"EXCEL BACKUP ERROR: {error_message}")
            show_result(False, error_message)
            return False, error_message

    # -------------------------
    # Additional UI helpers (used by MDDialog in main.kv)
    # -------------------------
    def on_ok_pressed(self, instance):
        # This function is used by the MDDialog buttons (CANCEL/OK) via on_release
        # in the KV file, but the primary logic is in dialog_ok/dialog_close.
        # This function looks like it was intended for validation *before* calling dialog_ok.

        # We will keep the original logic for visual feedback (error state) but still rely on dialog_ok for DB commit.
        try:
            content = instance.parent.parent.content
        except Exception:
            return

        fields = []
        try:
            for i in range(1, 8):
                fields.append(content.ids[f"Trip_details{i}"])
        except Exception:
            try:
                content.ids.error_label.text = "Dialog fields not found."
            except Exception:
                pass
            return

        all_filled = True
        for field in fields:
            if not field.text.strip():
                field.error = True
                all_filled = False
            else:
                field.error = False

        if not all_filled:
            try:
                content.ids.error_label.text = "Please fill all fields before proceeding."
            except Exception:
                pass
            return

        try:
            content.ids.error_label.text = ""
        except Exception:
            pass

        # If all fields are filled, it will fall through and call dialog_ok via the button definition.

    def auto_update_freight(self):
        # Keeps Trip_details7 as sum of Trip_details5 and Trip_details6 in the MDDialog
        try:
            adv_text = self.dialog.content_cls.ids.Trip_details5.text.strip()
            bal_text = self.dialog.content_cls.ids.Trip_details6.text.strip()

            adv = self.to_float(adv_text)
            bal = self.to_float(bal_text)

            # Calculate total freight
            total_freight = adv + bal

            # Update the freight text field (Trip_details7)
            self.dialog.content_cls.ids.Trip_details7.text = str(total_freight)

        except AttributeError:
            # Handle case where dialog or content is not yet initialized
            pass
        except Exception as e:
            # Catch any other unexpected error during calculation
            print(f"Error updating freight: {e}")
            pass


# --- Run App ---
if __name__ == '__main__':
    JTCApp().run()