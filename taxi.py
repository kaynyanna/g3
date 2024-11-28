import sqlite3
from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtWebEngineWidgets import QWebEngineView
import sys
import folium
import os


class LoginWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Taxi Booking Login")
        self.setGeometry(100, 100, 400, 200)

        # Create central widget and layout
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        layout = QtWidgets.QVBoxLayout(central_widget)

        # Create username and password fields
        self.username_input = QtWidgets.QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.password_input = QtWidgets.QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)

        # Create login button
        login_button = QtWidgets.QPushButton("Login")
        login_button.clicked.connect(self.something(self))

        # Add widgets to layout
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addWidget(login_button)

    def something(self):
        print("something is wrong")

    def handle_login(self):
        print("handle login called ")
        username = self.username_input.text()
        password = self.password_input.text()
        try:
            print("here 1")
            db = DatabaseHandler()
            cursor = db.cursor

            print("here 2")

        # Check credentials
            cursor.execute('''
                SELECT c.customer_id 
                FROM CustomerCredentials cc
                JOIN Customer c ON cc.customer_id = c.customer_id
                WHERE cc.username = ? AND cc.password = ?
            ''', (username, password,))

            result = cursor.fetchone()
            print(result)

            if result:
                print("result contains data")
                self.booking_window = BookingWindow(result[0])
                self.booking_window.show()
                self.close()
            elif not result:
                print("notning found")
            else:
                print("result is blank")
                QtWidgets.QMessageBox.warning(self, "Login Failed", "Invalid username or password")
        except Exception as e:
            print(sys.exc_info())
            raise e


class BookingWindow(QtWidgets.QMainWindow):
    def __init__(self, customer_id):
        super().__init__()
        self.customer_id = customer_id
        self.setWindowTitle("Book a Ride")
        self.setGeometry(100, 100, 600, 400)

        # Create central widget and layout
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        layout = QtWidgets.QVBoxLayout(central_widget)
        # Create welcome label
        welcome_label = QtWidgets.QLabel(f"Welcome! Book your ride below")
        welcome_label.setStyleSheet("font-size: 16px; margin: 10px;")
        welcome_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(welcome_label)
        # Create booking form
        form_layout = QtWidgets.QFormLayout()
        # Add a status label to show database connection
        self.db_status_label = QtWidgets.QLabel()
        try:
            db = DatabaseHandler()
            cursor = db.cursor
            cursor.execute("SELECT 1")  # Simple test query
            self.db_status_label.setText("Database Connected")
            self.db_status_label.setStyleSheet("color: green")
        except Exception as e:
            self.db_status_label.setText(f"Database Error: {str(e)}")
            self.db_status_label.setStyleSheet("color: red")
        form_layout.addRow("Database Status:", self.db_status_label)
        self.date_input = QtWidgets.QDateTimeEdit()
        self.date_input.setDateTime(QtCore.QDateTime.currentDateTime())
        self.location_input = QtWidgets.QLineEdit()

        form_layout.addRow("Date and Time:", self.date_input)
        form_layout.addRow("Pickup Location:", self.location_input)

        # Create book button
        book_button = QtWidgets.QPushButton("Book Ride")
        book_button.clicked.connect(self.handle_booking)

        # Add layouts and widgets
        layout.addLayout(form_layout)
        layout.addWidget(book_button)

    def handle_booking(self):
        date = self.date_input.dateTime().toString("yyyy-MM-dd hh:mm")
        location = self.location_input.text()

        if not location:
            QtWidgets.QMessageBox.warning(self, "Booking Error", "Please enter a pickup location")
            return

        # Basic price calculation (can be modified based on requirements)
        price = 20.00

        db = DatabaseHandler()
        cursor = db.cursor

        try:
            cursor.execute('''
                INSERT INTO Booking (booking_date, booking_price, booking_location)
                VALUES (?, ?, ?)
            ''', (date, price, location))

            db.conn.commit()
            QtWidgets.QMessageBox.information(self, "Success", "Ride booked successfully!")
            self.location_input.clear()

        except sqlite3.Error as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to book ride: {str(e)}")


class DatabaseHandler:
    def __init__(self, db_name='taxibookingdb.db'):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.initialize_tables()

    def initialize_tables(self):
        """Initialize the required tables for the application."""
        # Create the Customer table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Customer (
                customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_fname TEXT NOT NULL,
                customer_lname TEXT NOT NULL,
                customer_phonenumber TEXT UNIQUE NOT NULL,
                customer_email TEXT UNIQUE NOT NULL
            )
        ''')

        # Create the Booking table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Booking (
                booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_date TEXT NOT NULL,
                booking_price REAL NOT NULL,
                booking_location TEXT NOT NULL,
                driver_id INTEGER,
                FOREIGN KEY (driver_id) REFERENCES Driver(driver_id)
            )
        ''')

        # Create the Driver table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Driver (
                driver_id INTEGER PRIMARY KEY AUTOINCREMENT,
                driver_name TEXT NOT NULL,
                driver_license_number TEXT UNIQUE NOT NULL,
                driver_phone_number TEXT UNIQUE NOT NULL
            )
        ''')

        self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS CustomerCredentials (
                    customer_id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    FOREIGN KEY (customer_id) REFERENCES Customer(customer_id)
                )
            ''')

        # Commit changes
        self.conn.commit()

    def create_customer(self, fname, lname, phone, email):
        """Insert a new customer into the Customer table."""
        try:
            self.cursor.execute('''
                INSERT INTO Customer (customer_fname, customer_lname, customer_phonenumber, customer_email)
                VALUES (?, ?, ?, ?)
            ''', (fname, lname, phone, email))
            self.conn.commit()
            return self.cursor.lastrowid  # Return the new customer's ID
        except sqlite3.IntegrityError as e:
            print("Error: ", e)
            return None

    def register_customer_credentials(self, customer_id, username, password):
        """Register a customer's credentials."""
        try:
            self.cursor.execute('''
                INSERT INTO CustomerCredentials (customer_id, username, password)
                VALUES (?, ?, ?)
            ''', (customer_id, username, password))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError as e:
            print("Error registering customer credentials:", e)
            return False

    def authenticate_customer(self, username, password):
        """Authenticate a customer using username and password."""
        self.cursor.execute('''
            SELECT customer_id FROM CustomerCredentials WHERE username = ? AND password = ?
        ''', (username, password,))
        result = self.cursor.fetchone()
        return result is not None

    def create_booking(self, booking_date, price, location, driver_id=None):
        """Insert a new booking into the Booking table."""
        self.cursor.execute('''
            INSERT INTO Booking (booking_date, booking_price, booking_location, driver_id)
            VALUES (?, ?, ?, ?)
        ''', (booking_date, price, location, driver_id))
        self.conn.commit()
        return self.cursor.lastrowid  # Return the new booking's ID

    def fetch_customers(self):
        """Retrieve all customers."""
        self.cursor.execute('SELECT * FROM Customer')
        return self.cursor.fetchall()

    def fetch_bookings(self):
        """Retrieve all bookings."""
        self.cursor.execute('SELECT * FROM Booking')
        return self.cursor.fetchall()

    def close(self):
        """Close the database connection."""
        self.conn.close()


class FullscreenMixin:
    def setup_fullscreen(self):
        # Add fullscreen button
        self.fullscreen_btn = QtWidgets.QPushButton("🔲")
        self.fullscreen_btn.setToolTip("Toggle Fullscreen")
        self.fullscreen_btn.clicked.connect(self.toggle_fullscreen)
        self.fullscreen_btn.setFixedSize(40, 40)
        self.fullscreen_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                font-size: 20px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.2);
                border-radius: 20px;
            }
        """)

        # Add shortcuts
        self.shortcut_f11 = QtGui.QShortcut(QtGui.QKeySequence('F11'), self)
        self.shortcut_f11.activated.connect(self.toggle_fullscreen)

        self.shortcut_alt_enter = QtGui.QShortcut(QtGui.QKeySequence('Alt+Return'), self)
        self.shortcut_alt_enter.activated.connect(self.toggle_fullscreen)

        # Enable maximize button
        self.setWindowFlags(
            QtCore.Qt.WindowType.Window |
            QtCore.Qt.WindowType.CustomizeWindowHint |
            QtCore.Qt.WindowType.WindowCloseButtonHint |
            QtCore.Qt.WindowType.WindowMinimizeButtonHint |
            QtCore.Qt.WindowType.WindowMaximizeButtonHint
        )

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()


class MainMenuWindow(QtWidgets.QMainWindow):
    def __init__(self, database):
        super().__init__()
        self.database = database  # Assign the passed database instance
        self.setWindowTitle("✨ Magical Taxi Service ✨")
        self.setWindowIcon(QtGui.QIcon(os.path.join('icons', 'taxi.png')))  # Set the window icon
        self.booking_window = None
        self.setup_ui()

    def setup_ui(self):
        # Main widget and layout
        main_widget = QtWidgets.QWidget()
        self.setCentralWidget(main_widget)
        layout = QtWidgets.QVBoxLayout(main_widget)

        # Title with magical taxi logo
        title_layout = QtWidgets.QVBoxLayout()

        logo_label = QtWidgets.QLabel("🚖")
        logo_label.setStyleSheet("font-size: 72px;")
        logo_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        title = QtWidgets.QLabel("Magical Taxi Service")
        title.setStyleSheet("""
            font-size: 36px;
            color: #FF69B4;
            font-weight: bold;
            margin-bottom: 20px;
        """)
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        title_layout.addWidget(logo_label)
        title_layout.addWidget(title)
        layout.addLayout(title_layout)

        # Create buttons
        login_btn = QtWidgets.QPushButton("👤 Login")
        book_btn = QtWidgets.QPushButton("🚖 Book a Ride")
        create_account_btn = QtWidgets.QPushButton("✨ Create Account")
        exit_btn = QtWidgets.QPushButton("❌ Exit")  # Exit button

        # Connect buttons to their functions
        login_btn.clicked.connect(self.show_login)
        book_btn.clicked.connect(self.show_booking)
        create_account_btn.clicked.connect(self.show_create_account)
        exit_btn.clicked.connect(QtWidgets.QApplication.quit)

        # Add buttons to layout
        layout.addWidget(login_btn)
        layout.addWidget(book_btn)
        layout.addWidget(create_account_btn)
        layout.addWidget(exit_btn)

        view_customers_btn = QtWidgets.QPushButton("View All Customers")
        view_customers_btn.clicked.connect(self.view_customers)
        layout.addWidget(view_customers_btn)

        self.setFixedSize(400, 300)

        # Quick code entry
        self.code_input = QtWidgets.QLineEdit()
        self.code_input.setPlaceholderText("Enter quick access code...")
        self.code_input.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.code_input.textChanged.connect(self.check_code)
        layout.addWidget(self.code_input)

        # Style the window
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #FFF0F5, stop: 0.5 #FFE1FF, stop: 1 #E6E6FA
                );
            }
            QPushButton {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #FF69B4, stop: 1 #DA70D6
                );
                color: white;
                border: none;
                padding: 15px;
                border-radius: 15px;
                font-size: 16px;
                min-width: 250px;
                margin: 10px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #FF1493, stop: 1 #C71585
                );
            }
            QLineEdit {
                padding: 12px;
                border: 2px solid #FF69B4;
                border-radius: 10px;
                font-size: 14px;
                margin: 10px;
                background: white;
            }
            QLineEdit:focus {
                border-color: #FF1493;
                background: #FFF5F9;
            }
        """)

        # Set fixed size for the window
        self.setFixedSize(400, 600)

    def check_code(self):
        if self.code_input.text().lower() == "group3":
            self.show_booking()

    def show_booking(self):
        if not self.booking_window:
            self.booking_window = MagicalBookingWindow(main_menu=self)
        self.booking_window.show()
        self.hide()

    def show_create_account(self):
        self.create_account_window = CreateAccountWindow(database=self.database)  # Pass the database instance
        self.create_account_window.show()
        self.hide()

    def view_customers(self):
        """Display all customers from the database."""
        customers = self.database.fetch_customers()
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle("All Customers")
        msg.setText("\n".join([f"{c[1]} {c[2]} ({c[3]}, {c[4]})" for c in customers]))
        msg.exec()

    def show_login(self):
        self.login_window = LoginWindow(database=self.database)
        self.login_window.show()
        self.hide()  # Hide instead of close


class MagicalBookingWindow(QtWidgets.QMainWindow):
    def __init__(self, main_menu):
        super().__init__()
        self.main_menu = main_menu
        self.setWindowTitle("✨ Book Your Magical Ride ✨")
        self.setup_ui()

    def setup_ui(self):
        # Main widget and layout
        main_widget = QtWidgets.QWidget()
        self.setCentralWidget(main_widget)
        layout = QtWidgets.QVBoxLayout(main_widget)

        # Create tab widget
        tabs = QtWidgets.QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #FF69B4;
                border-radius: 10px;
                background: white;
            }
            QTabBar::tab {
                background: #FFE1FF;
                padding: 10px 15px;
                margin: 2px;
                border-radius: 5px;
            }
            QTabBar::tab:selected {
                background: #FF69B4;
                color: white;
            }
        """)

        # Add tabs
        tabs.addTab(self.create_location_tab(), "📍 Location")
        tabs.addTab(self.create_payment_tab(), "💳 Payment")
        tabs.addTab(self.create_preferences_tab(), "⚙️ Preferences")

        layout.addWidget(tabs)

        # Add Book Ride button at the bottom
        book_btn = QtWidgets.QPushButton("✨ Book Your Magical Ride ✨")
        book_btn.clicked.connect(self.confirm_booking)
        book_btn.setStyleSheet("""
            QPushButton {
                background: #FF69B4;
                color: white;
                padding: 15px;
                border-radius: 10px;
                font-size: 16px;
                font-weight: bold;
                margin: 10px;
            }
            QPushButton:hover {
                background: #FF1493;
            }
        """)
        layout.addWidget(book_btn)

    def create_location_tab(self):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)

        # Map view
        self.map_view = QWebEngineView()
        self.map = folium.Map(
            location=[10.6918, -61.2225],  # Trinidad coordinates
            zoom_start=10,
            tiles="OpenStreetMap"
        )

        # Add common locations
        self.common_locations = {
            "Port of Spain": [10.6596, -61.5086],
            "San Fernando": [10.2744, -61.4724],
            "Arima": [10.6374, -61.2829],
            "Chaguanas": [10.5170, -61.4109],
            "Piarco Airport": [10.5954, -61.3372],
            "Maracas Beach": [10.7502, -61.4419],
            "UWI St. Augustine": [10.6381, -61.4021]
        }

        for name, coords in self.common_locations.items():
            folium.Marker(coords, popup=name).add_to(self.map)

        # Save and display map
        temp_file = 'temp_map.html'
        self.map.save(temp_file)
        with open(temp_file, 'r') as f:
            html = f.read()
        self.map_view.setHtml(html)
        self.map_view.setMinimumHeight(400)
        layout.addWidget(self.map_view)

        # Location selection
        location_form = QtWidgets.QFormLayout()
        self.pickup_combo = QtWidgets.QComboBox()
        self.dropoff_combo = QtWidgets.QComboBox()

        locations = ["Select location..."] + list(self.common_locations.keys())
        self.pickup_combo.addItems(locations)
        self.dropoff_combo.addItems(locations)

        location_form.addRow("Pickup Location:", self.pickup_combo)
        location_form.addRow("Dropoff Location:", self.dropoff_combo)
        layout.addLayout(location_form)

        return tab

    def create_payment_tab(self):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)

        # Payment method selection
        payment_group = QtWidgets.QGroupBox("Select Payment Method")
        payment_layout = QtWidgets.QVBoxLayout()

        self.card_radio = QtWidgets.QRadioButton("Pay with Card 💳")
        self.cash_radio = QtWidgets.QRadioButton("Pay with Cash 💵")

        payment_layout.addWidget(self.card_radio)
        payment_layout.addWidget(self.cash_radio)
        payment_group.setLayout(payment_layout)
        layout.addWidget(payment_group)

        # Card details (initially hidden)
        self.card_details = QtWidgets.QGroupBox("Card Details")
        card_layout = QtWidgets.QFormLayout()

        self.card_number = QtWidgets.QLineEdit()
        self.card_number.setPlaceholderText("Card Number")

        self.card_holder = QtWidgets.QLineEdit()
        self.card_holder.setPlaceholderText("Cardholder Name")

        self.card_expiry = QtWidgets.QLineEdit()
        self.card_expiry.setPlaceholderText("MM/YY")

        self.card_cvv = QtWidgets.QLineEdit()
        self.card_cvv.setPlaceholderText("CVV")
        self.card_cvv.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)

        card_layout.addRow("Card Number:", self.card_number)
        card_layout.addRow("Cardholder Name:", self.card_holder)
        card_layout.addRow("Expiry Date:", self.card_expiry)
        card_layout.addRow("CVV:", self.card_cvv)

        self.card_details.setLayout(card_layout)
        self.card_details.hide()

        layout.addWidget(self.card_details)
        self.card_radio.toggled.connect(self.card_details.setVisible)

        return tab

    def create_preferences_tab(self):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)

        # Personal Information
        personal_group = QtWidgets.QGroupBox("Personal Details")
        personal_layout = QtWidgets.QFormLayout()

        self.name_input = QtWidgets.QLineEdit()
        self.name_input.setPlaceholderText("Your full name")

        self.phone_input = QtWidgets.QLineEdit()
        self.phone_input.setPlaceholderText("Your phone number")

        personal_layout.addRow("Full Name:", self.name_input)
        personal_layout.addRow("Phone Number:", self.phone_input)
        personal_group.setLayout(personal_layout)
        layout.addWidget(personal_group)

        # Ride Preferences
        pref_group = QtWidgets.QGroupBox("Ride Preferences")
        pref_layout = QtWidgets.QVBoxLayout()

        self.chat_check = QtWidgets.QCheckBox("I'm open to chatting with the driver")
        self.music_check = QtWidgets.QCheckBox("I'd like music during the ride")

        self.music_genre = QtWidgets.QComboBox()
        self.music_genre.addItems([
            "Select music genre...",
            "Pop", "Rock", "Jazz", "Classical",
            "Hip Hop", "R&B", "Soca", "Calypso"
        ])
        self.music_genre.hide()

        self.music_check.toggled.connect(self.music_genre.setVisible)

        pref_layout.addWidget(self.chat_check)
        pref_layout.addWidget(self.music_check)
        pref_layout.addWidget(self.music_genre)
        pref_group.setLayout(pref_layout)
        layout.addWidget(pref_group)

        return tab

    def confirm_booking(self):
        # Validate all required fields
        if not self.validate_booking():
            return

        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Icon.Information)
        msg.setText("✨ Booking Confirmed! ✨")
        msg.setInformativeText("Your magical ride is on the way!")
        msg.setWindowTitle("Booking Success")
        msg.exec()

        # Return to main menu
        self.main_menu.show()
        self.hide()

    def validate_booking(self):
        # Validate location selection
        if self.pickup_combo.currentText() == "Select location..." or \
                self.dropoff_combo.currentText() == "Select location...":
            self.show_error("Please select both pickup and dropoff locations")
            return False

        # Validate payment method
        if not (self.card_radio.isChecked() or self.cash_radio.isChecked()):
            self.show_error("Please select a payment method")
            return False

        # Validate card details if card payment selected
        if self.card_radio.isChecked():
            if not all([
                self.card_number.text(),
                self.card_holder.text(),
                self.card_expiry.text(),
                self.card_cvv.text()
            ]):
                self.show_error("Please fill in all card details")
                return False

        # Validate personal information
        if not all([self.name_input.text(), self.phone_input.text()]):
            self.show_error("Please fill in your personal information")
            return False

        return True

    def show_error(self, message):
        QtWidgets.QMessageBox.warning(self, "Error", message)

    def closeEvent(self, event):
        """Override close event to show main menu when booking window is closed"""
        self.main_menu.show()
        self.hide()
        event.ignore()


class LoginWindow(QtWidgets.QMainWindow, FullscreenMixin):
    def __init__(self, database):
        super().__init__()
        self.database = database
        self.setup_fullscreen()
        self.setWindowTitle("✨ Magical Login ✨")
        self.setup_ui()

    def setup_ui(self):
        # Main widget and layout
        main_widget = QtWidgets.QWidget()
        self.setCentralWidget(main_widget)
        layout = QtWidgets.QVBoxLayout(main_widget)

        # Title
        title = QtWidgets.QLabel("Login to Your Account")
        title.setStyleSheet("""
            font-size: 24px;
            color: #FF69B4;
            font-weight: bold;
            margin: 20px;
        """)
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Login form
        form_group = QtWidgets.QGroupBox()
        form_layout = QtWidgets.QFormLayout()

        # Username
        self.username_input = QtWidgets.QLineEdit()
        self.username_input.setPlaceholderText("Enter username...")
        form_layout.addRow("Username 👤", self.username_input)

        # Password
        self.password_input = QtWidgets.QLineEdit()
        self.password_input.setPlaceholderText("Enter password...")
        self.password_input.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        form_layout.addRow("Password 🔑", self.password_input)

        form_group.setLayout(form_layout)
        layout.addWidget(form_group)

        # Login button
        login_btn = QtWidgets.QPushButton("Login ✨")
        login_btn.clicked.connect(self.handle_login)
        layout.addWidget(login_btn)

        # Back button
        back_btn = QtWidgets.QPushButton("← Back to Main Menu")
        back_btn.clicked.connect(self.back_to_main)
        layout.addWidget(back_btn)

        # Style the window
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #FFF0F5, stop: 0.5 #FFE1FF, stop: 1 #E6E6FA
                );
            }
            QGroupBox {
                background: rgba(255, 255, 255, 0.7);
                border: 2px solid #FF69B4;
                border-radius: 15px;
                margin: 10px;
                padding: 20px;
            }
            QPushButton {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #FF69B4, stop: 1 #DA70D6
                );
                color: white;
                border: none;
                padding: 15px;
                border-radius: 15px;
                font-size: 16px;
                min-width: 200px;
                margin: 10px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #FF1493, stop: 1 #C71585
                );
            }
            QLineEdit {
                padding: 12px;
                border: 2px solid #FF69B4;
                border-radius: 10px;
                font-size: 14px;
                margin: 5px;
                background: white;
            }
            QLabel {
                color: #8B008B;
                font-size: 14px;
            }
        """)

        # Set fixed size
        self.setFixedSize(400, 500)

    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not all([username, password]):
            QtWidgets.QMessageBox.warning(self, "Login Failed", "Please enter both username and password!")
            return

        if self.main_menu.database.authenticate_customer(username, password):
            QtWidgets.QMessageBox.information(self, "Success", "Login successful!")
            self.main_menu = MainMenuWindow()
            self.main_menu.show_booking()
            self.close()
        else:
            QtWidgets.QMessageBox.warning(self, "Login Failed", "Invalid username or password!")

    def open_booking_window(self):
        self.booking_window = MagicalBookingWindow()
        self.booking_window.show()
        self.close()

    def back_to_main(self):
        self.main_window = MainMenuWindow()
        self.main_window.show()
        self.close()


class CreateAccountWindow(QtWidgets.QMainWindow, FullscreenMixin):
    def __init__(self, database):
        super().__init__()
        self.database = database  # Pass the database handler
        self.setWindowTitle("✨ Create Account ✨")
        self.setup_ui()

    def setup_ui(self):
        main_widget = QtWidgets.QWidget()
        self.setCentralWidget(main_widget)
        layout = QtWidgets.QVBoxLayout(main_widget)

        self.fname_input = QtWidgets.QLineEdit()
        self.fname_input.setPlaceholderText("First Name")
        layout.addWidget(self.fname_input)

        self.lname_input = QtWidgets.QLineEdit()
        self.lname_input.setPlaceholderText("Last Name")
        layout.addWidget(self.lname_input)

        self.phone_input = QtWidgets.QLineEdit()
        self.phone_input.setPlaceholderText("Phone Number")
        layout.addWidget(self.phone_input)

        self.email_input = QtWidgets.QLineEdit()
        self.email_input.setPlaceholderText("Email")
        layout.addWidget(self.email_input)

        self.username_input = QtWidgets.QLineEdit()
        self.username_input.setPlaceholderText("Choose a Username")
        layout.addWidget(self.username_input)

        self.password_input = QtWidgets.QLineEdit()
        self.password_input.setPlaceholderText("Create a Password")
        self.password_input.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)  # Hide password input
        layout.addWidget(self.password_input)

        # Submit button
        submit_btn = QtWidgets.QPushButton("Create Account")
        submit_btn.clicked.connect(self.create_account)
        layout.addWidget(submit_btn)

        back_btn = QtWidgets.QPushButton("Back to Main Menu")
        back_btn.clicked.connect(self.back_to_main)
        layout.addWidget(back_btn)

        self.setFixedSize(400, 300)

    def create_account(self):
        fname = self.fname_input.text().strip()
        lname = self.lname_input.text().strip()
        phone = self.phone_input.text().strip()
        email = self.email_input.text().strip()
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not all([fname, lname, phone, email, username, password]):
            QtWidgets.QMessageBox.warning(self, "Input Error", "All fields are required!")
            return

        try:
            # Create customer
            customer_id = self.database.create_customer(fname, lname, phone, email)
            if customer_id:
                # Register customer credentials
                if self.database.register_customer_credentials(customer_id, username, password):
                    QtWidgets.QMessageBox.information(self, "Success", "Account created successfully!")
                    self.back_to_main()
                else:
                    QtWidgets.QMessageBox.warning(self, "Error", "Username already exists!")
            else:
                QtWidgets.QMessageBox.warning(self, "Error", "An error occurred while creating the account.")
        except sqlite3.IntegrityError as e:
            QtWidgets.QMessageBox.warning(self, "Database Error", f"Error: {str(e)}")

    def back_to_main(self):
        self.main_menu = MainMenuWindow()
        self.main_menu.show()
        self.close()

        customer_id = self.database.create_customer(fname, lname, phone, email)
        if customer_id:
            QtWidgets.QMessageBox.information(
                self, "Success", f"Account created successfully! Customer ID: {customer_id}"
            )
            self.back_to_main()
        else:
            QtWidgets.QMessageBox.warning(
                self, "Error", "An error occurred while creating the account. Email might already exist."
            )

    def back_to_main(self):
        self.main_menu = MainMenuWindow()
        self.main_menu.show()
        self.close()

        # Create stacked widget for multiple pages
        self.stacked_widget = QtWidgets.QStackedWidget()
        layout.addWidget(self.stacked_widget)

        # Create pages
        self.create_account_details_page()
        self.create_2fa_page()

        # Navigation buttons
        nav_layout = QtWidgets.QHBoxLayout()
        self.back_btn = QtWidgets.QPushButton("← Back")
        self.next_btn = QtWidgets.QPushButton("Next →")

        self.back_btn.clicked.connect(self.go_back)
        self.next_btn.clicked.connect(self.go_next)

        nav_layout.addWidget(self.back_btn)
        nav_layout.addWidget(self.next_btn)
        layout.addLayout(nav_layout)

        self.setFixedSize(450, 600)
        self.update_nav_buttons()

    def create_account_details_page(self):
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)

        title = QtWidgets.QLabel("Create Your Account")
        title.setStyleSheet("font-size: 24px; color: #FF69B4; font-weight: bold;")
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        form_group = QtWidgets.QGroupBox()
        form_layout = QtWidgets.QFormLayout()

        # Username
        self.username_input = QtWidgets.QLineEdit()
        self.username_input.setPlaceholderText("Choose a username...")
        layout.addWidget(self.username_input)

        # Email
        self.email_input = QtWidgets.QLineEdit()
        self.email_input.setPlaceholderText("Enter your email...")
        form_layout.addRow("Email 📧", self.email_input)

        # Phone
        self.phone_input = QtWidgets.QLineEdit()
        self.phone_input.setPlaceholderText("Enter phone number...")
        form_layout.addRow("Phone 📱", self.phone_input)

        # Password
        self.password_input = QtWidgets.QLineEdit()
        self.password_input.setPlaceholderText("Create password...")
        self.password_input.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_input)

        # Confirm Password
        self.confirm_password = QtWidgets.QLineEdit()
        self.confirm_password.setPlaceholderText("Confirm password...")
        self.confirm_password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        form_layout.addRow("Confirm Password 🔐", self.confirm_password)

        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        self.stacked_widget.addWidget(page)

    def create_2fa_page(self):
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)

        title = QtWidgets.QLabel("Two-Factor Authentication")
        title.setStyleSheet("font-size: 24px; color: #FF69B4; font-weight: bold;")
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        form_group = QtWidgets.QGroupBox()
        form_layout = QtWidgets.QVBoxLayout()

        # 2FA Method Selection
        method_label = QtWidgets.QLabel("Choose 2FA Method:")
        self.email_2fa = QtWidgets.QRadioButton("Email Authentication 📧")
        self.phone_2fa = QtWidgets.QRadioButton("SMS Authentication 📱")

        verify_btn = QtWidgets.QPushButton("Send Verification Code ✨")
        verify_btn.clicked.connect(self.send_verification)

        # Verification Code Input
        self.verification_input = QtWidgets.QLineEdit()
        self.verification_input.setPlaceholderText("Enter verification code...")

        # Create Account Button
        create_btn = QtWidgets.QPushButton("Create Account ✨")
        create_btn.clicked.connect(self.handle_create_account)

        form_layout.addWidget(method_label)
        form_layout.addWidget(self.email_2fa)
        form_layout.addWidget(self.phone_2fa)
        form_layout.addWidget(verify_btn)
        form_layout.addWidget(self.verification_input)
        form_layout.addWidget(create_btn)

        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        self.stacked_widget.addWidget(page)

    def go_back(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.stacked_widget.setCurrentIndex(self.current_page)
        else:
            self.main_window = MainMenuWindow()
            self.main_window.show()
            self.close()
        self.update_nav_buttons()

    def go_next(self):
        if self.validate_first_page():
            self.current_page += 1
            self.stacked_widget.setCurrentIndex(self.current_page)
            self.update_nav_buttons()

    def update_nav_buttons(self):
        self.back_btn.setText("← Main Menu" if self.current_page == 0 else "← Back")
        self.next_btn.setVisible(self.current_page == 0)

    def validate_first_page(self):
        if not all([self.username_input.text(), self.email_input.text(),
                    self.phone_input.text(), self.password_input.text(),
                    self.confirm_password.text()]):
            QtWidgets.QMessageBox.warning(self, "Error", "Please fill in all fields! ✨")
            return False

        if self.password_input.text() != self.confirm_password.text():
            QtWidgets.QMessageBox.warning(self, "Error", "Passwords do not match! ✨")
            return False

        return True

    def send_verification(self):
        if not (self.email_2fa.isChecked() or self.phone_2fa.isChecked()):
            QtWidgets.QMessageBox.warning(self, "Error", "Please select a 2FA method! ✨")
            return

        # Simulate sending verification code
        QtWidgets.QMessageBox.information(
            self,
            "Verification Sent",
            "Verification code has been sent! ✨"
        )

    def handle_create_account(self):
        if not self.verification_input.text():
            QtWidgets.QMessageBox.warning(self, "Error", "Please enter verification code! ✨")
            return

        # Here you would normally validate the verification code
        # and create the account in your database

        QtWidgets.QMessageBox.information(
            self,
            "Success",
            "Account created successfully! ✨"
        )
        self.main_window = MainMenuWindow()
        self.main_window.show()
        self.close()


def main():
    app = QtWidgets.QApplication(sys.argv)
    database = DatabaseHandler()  # Create a single instance of the database
    window = MainMenuWindow(database)  # Pass the database instance
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
