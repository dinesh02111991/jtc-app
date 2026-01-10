# main.py (Final Consolidated Version - Updated for Android Build)

# Standard Python Imports
import os
import shutil
import datetime
import sqlite3 as sq
from fpdf import FPDF
# [REMOVED PANDAS]: Removed 'import pandas as pd' to fix build error.
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
from kivy.utils import platform  # Essential for platform-specific code

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

        # [CRITICAL FIX]: Request necessary permissions first
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
    # Platform / Permission Helpers (UPDATED FOR CORRECT INTEGRATION)
    # -------------------------
    def request_android_permissions(self):
        """Request external storage permission for Android to allow file saving."""
        if platform == 'android':
            try:
                # Import necessary Android classes via Pyjnius
                from android.permissions import request_permissions, Permission

                # Request the permissions
                request_permissions([
                    Permission.READ_EXTERNAL_STORAGE,
                    Permission.WRITE_EXTERNAL_STORAGE
                ])

            except ImportError:
                # Handle case where android module is not available (e.g., desktop testing)
                print("Warning: android.permissions module not found. Ignoring permission request.")
            except Exception as e:
                print(f"Could not request Android permissions: {e}")

    def get_downloads_folder(self):
        """Returns the appropriate directory for saving files (Memo/Bill/Backup)."""

        # Define the app's dedicated sub-folder name
        SUB_FOLDER = 'JTC_Files'

        if platform == 'android':
            # Android: Use shared external storage (e.g., /sdcard/Download/JTC_Files)
            try:
                # CRITICAL: Use primary_external_storage_path() to get the base of external storage
                from android.storage import primary_external_storage_path
                # Construct the path: External_Storage_Root/Download/JTC_Files
                base_path = primary_external_storage_path()
                # Use "Download" folder within external storage
                path = os.path.join(base_path, 'Download', SUB_FOLDER)
            except ImportError:
                # Fallback for older P4A or Kivy versions (saves to app's private data)
                path = os.path.join(self.user_data_dir, SUB_FOLDER)
                toast("Using private app data folder for saving.")

        else:
            # Desktop (Windows, Linux, macOS): Target the user's Downloads folder
            # 1. Get the Home directory (~/user)
            home_dir = os.path.expanduser('~')

            # 2. Construct the path: Home_Directory/Downloads/JTC_Files
            # This is the standard path on Windows and Linux/macOS
            path = os.path.join(home_dir, 'Downloads', SUB_FOLDER)

        # Ensure the directory exists before returning the path
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
    # Generate Memo (No change needed - uses FPDF directly)
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
        # ... (Your existing Generate_Bill function body, unchanged)
        # This function does not use pandas, so it is safe.
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
                    toast(f"Please fill the required field: {field}")
                    return

            # Check if all fields for bill_info exist (re-run ensure_bill_info_columns if needed)
            co = sq.connect(self.db_path, timeout=10.0)
            cur = co.cursor()
            self.ensure_bill_info_columns(cur)

            # Fetch a list of column names dynamically to build the INSERT statement
            cur.execute("PRAGMA table_info(bill_info)")
            column_names = [col[1] for col in cur.fetchall()]

            # Use data from trip_info for standard fields
            trip_data = {
                "truck_no": trip_info[1], "m_s": trip_info[2], "from_trip": trip_info[3],
                "to_trip": trip_info[4], "advance": trip_info[5], "balance": trip_info[6],
                "fraight": trip_info[7], "date": trip_info[8], "trip_id": trip_info[0]
            }

            # Map inputs to database column names
            bill_mapping = {
                "Consignor": "consignor", "Consignee": "consignee",
                "Description of Goods": "description_of_goods", "No of Articles": "no_of_articles",
                "Weight": "weight", "Remark": "remark", "Additional Charge": "additional_charge"
            }

            # Combine all data for insertion
            insert_data = {}
            for col in column_names:
                if col in trip_data:
                    insert_data[col] = trip_data[col]
                elif col in [v for k, v in bill_mapping.items()]:
                    # Map input data to the column name
                    input_key = next(k for k, v in bill_mapping.items() if v == col)
                    insert_data[col] = bill_data[input_key]
                elif col == "bill_date":
                    insert_data[col] = date.today().strftime('%d/%m/%Y')
                elif col == "memo_number":
                    # Generate simple memo number (Bill_ID is auto-incremented)
                    insert_data[col] = f"{trip_info[0]}_{date.today().strftime('%Y%m%d')}"
                else:
                    insert_data[col] = None  # Default any missing column

            # Build SQL statement
            cols = [c for c in column_names if c not in ('bill_id')]
            placeholders = ', '.join(['?'] * len(cols))
            col_names = ', '.join(cols)
            values_to_insert = [insert_data[col] for col in cols]

            try:
                # Use INSERT OR REPLACE to potentially update existing bill data if you re-run
                cur.execute(f"""
                    INSERT INTO bill_info ({col_names})
                    VALUES ({placeholders})
                """, tuple(values_to_insert))

                co.commit()
                popup.dismiss()
                memo_number = insert_data.get('memo_number')
                generate_pdf_bill(memo_number)
            except Exception as e:
                toast(f"Failed to save bill data: {e}")
                co.rollback()
            finally:
                co.close()

        cancel_btn.bind(on_release=popup.dismiss)
        submit_btn.bind(on_release=submit_details)
        popup.open()

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




    # -------------------------
    # Backup Function (REWRITTEN WITHOUT PANDAS)
    # -------------------------
    def backup_database_excel(self):
        # 1. Fetch ALL data from trip_info
        try:
            co = sq.connect(self.db_path, timeout=10.0)
            cur = co.cursor()

            # Get data and column headers
            cur.execute("SELECT * FROM trip_info")
            data = cur.fetchall()
            # Get column names for headers (needed for both Excel and PDF)
            headers = [description[0] for description in cur.description]

            co.close()
        except Exception as e:
            toast(f"Database read error for backup: {e}")
            return

        if not data:
            toast("No data found to backup.")
            return

        save_dir = self.get_downloads_folder()
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        # --- EXCEL EXPORT (Using xlsxwriter) ---
        excel_filename = os.path.join(save_dir, f"Backup_Trips_Excel_{timestamp}.xlsx")

        try:
            workbook = xlsxwriter.Workbook(excel_filename)
            worksheet = workbook.add_worksheet()

            # Write Header Row
            for col_num, header in enumerate(headers):
                worksheet.write(0, col_num, header)

            # Write Data Rows
            for row_num, row_data in enumerate(data):
                for col_num, item in enumerate(row_data):
                    worksheet.write(row_num + 1, col_num, item)

            workbook.close()
            excel_success = True
        except Exception as e:
            toast(f"Excel export failed: {e}")
            excel_success = False

        # --- PDF EXPORT (Using FPDF) ---
        pdf_filename = os.path.join(save_dir, f"Backup_Trips_PDF_{timestamp}.pdf")

        try:
            pdf = FPDF('L', 'mm', 'A4')  # Landscape orientation for more columns
            pdf.add_page()
            pdf.set_font("Arial", size=8)

            # Determine column widths dynamically (A4 Landscape = 297mm width)
            page_width = 280
            col_count = len(headers)
            col_width = page_width / col_count
            row_height = 5

            # Write Header Row (with shading)
            pdf.set_fill_color(200, 220, 255)
            for header in headers:
                pdf.cell(col_width, row_height, header, border=1, fill=True, align='C')
            pdf.ln(row_height)

            # Write Data Rows
            pdf.set_font("Arial", size=7)
            for row_data in data:
                for item in row_data:
                    # MultiCell used to handle long text wrapping, though it's less tidy
                    # Using cell for fixed layout:
                    pdf.cell(col_width, row_height, str(item), border=1, align='L', ln=0)
                pdf.ln(row_height)

            pdf.output(pdf_filename)
            pdf_success = True
        except Exception as e:
            toast(f"PDF export failed: {e}")
            pdf_success = False



        # --- Final Feedback ---
        success_messages = []
        if excel_success:
            success_messages.append(f"Excel backup saved to:\n{excel_filename}")
        if pdf_success:
            success_messages.append(f"PDF backup saved to:\n{pdf_filename}")

        if success_messages:
            msg = "\n\n".join(success_messages)
            toast(f"Backup Successful!\nFiles saved in JTC_Files folder.")

            # Show a more detailed pop-up if needed, but toast is quicker
        else:
            toast("Backup failed for both Excel and PDF.")


# ---------------------

if __name__ == '__main__':
    JTCApp().run()