import sys
import psycopg2
from PyQt5 import uic, Qt
from PyQt5.QtCore import QEvent, pyqtSignal, Qt, QDate
from PyQt5.QtGui import QFontDatabase
from PyQt5.QtWidgets import (QWidget, QApplication, QComboBox, QLineEdit, QMessageBox, QPushButton, QLabel,
                             QDialogButtonBox, QDialog, QStyle, QMainWindow, QStackedWidget, QListWidget, QHBoxLayout,
                             QListWidgetItem, QTableWidget, QDateEdit)
from Db_connection import get_db_connection
import LoggedUser
from LoginMain import LogIn

class DbMenuWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("ui/DashboardMenuWindow.ui", self)
        self.load_fonts()

        self.stacked_widget = QStackedWidget(self)
        uic.loadUi("ui/dbmenu-stack.ui", self.stacked_widget)
        self.stacked_widget.move(0, 0)

        #pyqt signals
        self.dbmenu = DashboardMenu()
        self.dbmenu.switch_to_records.connect(self.records_page)
        self.dbmenu.switch_to_settings.connect(self.settings_page)

        self.records = DashboardRecords()
        self.records.switch_to_dbmenu.connect(self.dbmenu_page)
        self.records.switch_to_specificfile.connect(self.case_personalpage)

        self.settings = Settings()
        self.settings.switch_to_editsettings.connect(self.editsettings_page)
        self.settings.back_to_menu.connect(self.dbmenu_page)

        self.editsettings = EditSettings()
        self.editsettings.switch_to_settings.connect(self.settings_page)

        self.case_personalinfo = CasePersonalInfo()
        self.case_personalinfo.switch_to_parentinfo.connect(self.case_parentpage)
        self.case_personalinfo.close_page.connect(self.records_page)

        self.case_parentinfo = CaseParentInfo()
        self.case_parentinfo.switch_to_offense.connect(self.case_offensepage)
        self.case_parentinfo.switch_to_personal.connect(self.case_personalpage)
        self.case_parentinfo.close_page.connect(self.records_page)

        self.case_offenseinfo = CaseOffenseInfo()
        self.case_offenseinfo.switch_to_history.connect(self.case_historypage)
        self.case_offenseinfo.switch_to_parent.connect(self.case_parentpage)
        self.case_offenseinfo.close_page.connect(self.records_page)

        self.case_crimehistory = CaseCriminalHistory()
        self.case_crimehistory.switch_to_offense.connect(self.case_offensepage)
        self.case_crimehistory.close_page.connect(self.records_page)

        #add instances to the stacked widget
        self.stacked_widget.addWidget(self.dbmenu)
        self.stacked_widget.addWidget(self.records)
        self.stacked_widget.addWidget(self.settings)
        self.stacked_widget.addWidget(self.editsettings)
        self.stacked_widget.addWidget(self.case_personalinfo)
        self.stacked_widget.addWidget(self.case_parentinfo)
        self.stacked_widget.addWidget(self.case_offenseinfo)
        self.stacked_widget.addWidget(self.case_crimehistory)

        #set the initial page to dashboard menu
        self.stacked_widget.setCurrentWidget(self.dbmenu)

    def records_page(self):
        self.stacked_widget.setCurrentWidget(self.records)

    def dbmenu_page(self):
        self.stacked_widget.setCurrentWidget(self.dbmenu)

    def settings_page(self):
        # Load user data before showing settings page
        self.settings.load_user_data()
        self.stacked_widget.setCurrentWidget(self.settings)

    def editsettings_page(self):
        # Load user data before showing edit settings page
        self.editsettings.load_user_data()
        self.stacked_widget.setCurrentWidget(self.editsettings)

    def case_personalpage(self):
        self.stacked_widget.setCurrentWidget(self.case_personalinfo)

    def case_parentpage(self):
        self.stacked_widget.setCurrentWidget(self.case_parentinfo)

    def case_offensepage(self):
        self.stacked_widget.setCurrentWidget(self.case_offenseinfo)

    def case_historypage(self):
        self.stacked_widget.setCurrentWidget(self.case_crimehistory)

    #helper method to show the record page after user submits or enroll a new profile
    def show_page(self, page_name: str):
        pages = {
            "menu": self.dbmenu,
            "records": self.records,
        }

        if page_name in pages:
            self.stacked_widget.setCurrentWidget(pages[page_name])

    def load_fonts(self):
        # Poppins
        if QFontDatabase.addApplicationFont("assets/fonts/Poppins-Regular.ttf") != -1:
            print("Poppins font loaded successfully.")
        else:
            print("Failed to load Poppins font.")

        # Helvetica
        if QFontDatabase.addApplicationFont("assets/fonts/Helvetica.ttf") != -1:
            print("Helvetica font loaded successfully.")
        else:
            print("Failed to load Helvetica font.")

        # Inter
        if QFontDatabase.addApplicationFont("assets/fonts/Inter-XtraBold.ttf") != -1:
            print("Inter font loaded successfully.")
        else:
            print("Failed to load Inter font.")

class DashboardMenu(QWidget):
    switch_to_records = pyqtSignal()
    switch_to_settings = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__()
        uic.loadUi("ui/dbmenu-gradientbg.ui", self)
        self.load_fonts()

        #add record action widget
        self.records_action_widget = QWidget(self)
        uic.loadUi("ui/dbmenu-records.ui", self.records_action_widget)
        self.records_action_widget.move(173, 290)

        #records proceed button
        self.records_btn = self.records_action_widget.findChild(QPushButton, "proceed_btn")
        if self.records_btn:
            self.records_btn.clicked.connect(self.go_to_records)

        #add settings action widget
        self.settings_action_widget = QWidget(self)
        uic.loadUi("ui/dbmenu-settings.ui", self.settings_action_widget)
        self.settings_action_widget.move(549, 290)

        # settings proceed button
        self.settings_btn = self.settings_action_widget.findChild(QPushButton, "proceed_btn")
        if self.settings_btn:
            self.settings_btn.clicked.connect(self.go_to_settings)

        #add logout action widget
        self.logout_action_widget = QWidget(self)
        uic.loadUi("ui/dbmenu-logout.ui", self.logout_action_widget)
        self.logout_action_widget.move(926, 290)
        logout_btn = self.logout_action_widget.findChild(QPushButton, "proceed_btn")
        if logout_btn:
            logout_btn.clicked.connect(self.handle_logout)

        #back to system menu button
        self.backsystemmenu_btn = self.findChild(QPushButton, "back_btn")
        if self.backsystemmenu_btn:
            self.backsystemmenu_btn.clicked.connect(self.go_systemmenu)

    #go back to system menu window
    def go_systemmenu(self):
        from MenuWindow import SystemMenu as SystemMenuWindow
        self.main_window = SystemMenuWindow()

        self.main_window.show()
        self.window().close()

    def go_to_records(self):
        self.switch_to_records.emit()

    def go_to_settings(self):
        self.switch_to_settings.emit()

    def handle_logout(self):
        #show confirmation dialog
        reply = QMessageBox.question(
            self,
            'Logout Confirmation',
            'Are you sure you want to logout?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            #clear the logged-in user ID
            LoggedUser.current_logged_in_user_id = None
            print("User logged out.")
            
            #create and show login window
            self.login_window = LogIn()
            self.login_window.show()
            
            #close the current dashboard window
            self.window().close()

    def load_fonts(self):
        # Poppins
        if QFontDatabase.addApplicationFont("assets/fonts/Poppins-Regular.ttf") != -1:
            print("Poppins font loaded successfully.")
        else:
            print("Failed to load Poppins font.")

        # Helvetica
        if QFontDatabase.addApplicationFont("assets/fonts/Helvetica.ttf") != -1:
            print("Helvetica font loaded successfully.")
        else:
            print("Failed to load Helvetica font.")

        # Inter
        if QFontDatabase.addApplicationFont("assets/fonts/Inter-XtraBold.ttf") != -1:
            print("Inter font loaded successfully.")
        else:
            print("Failed to load Inter font.")


#settings
class Settings(QWidget):
    switch_to_editsettings = pyqtSignal()
    back_to_menu = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__()
        uic.loadUi("ui/settings-placeholder.ui", self)
        self.load_fonts()

        #add sidebar logo
        self.sidebar_widget = QWidget(self)
        uic.loadUi("ui/enroll-sidebar.ui", self.sidebar_widget)
        self.sidebar_widget.move(0, 0)

        #add the settings ui
        self.settings_widget = QWidget(self)
        uic.loadUi("ui/settings.ui", self.settings_widget)
        self.settings_widget.move(417, 0)

        # Find the fields
        self.fullname_line = self.settings_widget.findChild(QLineEdit, "fullname_line")
        self.dob_date = self.settings_widget.findChild(QDateEdit, "dob_date")
        self.address_line = self.settings_widget.findChild(QLineEdit, "address_line")
        self.role_line = self.settings_widget.findChild(QLineEdit, "role_line")
        self.un_line = self.settings_widget.findChild(QLineEdit, "un_line")
        self.pw_line = self.settings_widget.findChild(QLineEdit, "pw_line")

        # Make all fields read-only
        if self.fullname_line:
            self.fullname_line.setReadOnly(True)
        if self.dob_date:
            self.dob_date.setReadOnly(True)
        if self.address_line:
            self.address_line.setReadOnly(True)
        if self.role_line:
            self.role_line.setReadOnly(True)
        if self.un_line:
            self.un_line.setReadOnly(True)
        if self.pw_line:
            self.pw_line.setReadOnly(True)
            self.pw_line.setEchoMode(QLineEdit.Password)

        #edit info button in settings ui
        self.edit_btn = self.settings_widget.findChild(QPushButton, "edit_btn")
        if self.edit_btn:
            self.edit_btn.clicked.connect(self.edit_account_info)

        # back to menu button in settings ui
        self.backmenu_btn = self.settings_widget.findChild(QPushButton, "btm_btn")
        if self.backmenu_btn:
            self.backmenu_btn.clicked.connect(self.back_dashboardmenu)

    def load_user_data(self):
        if LoggedUser.current_logged_in_user_id is None:
            QMessageBox.warning(self, "Error", "No user logged in.")
            return

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Query to get user data from both tables using user_id
            query = """
                SELECT 
                    ba.admin_fname, 
                    ba.admin_lname, 
                    ba.admin_mname, 
                    ba.admin_dob, 
                    ba.admin_address,
                    u.user_role,
                    u.user_username
                FROM users u
                JOIN barangay_admin ba ON u.admin_id = ba.admin_id
                WHERE u.user_id = %s
            """
            cursor.execute(query, (LoggedUser.current_logged_in_user_id,))
            result = cursor.fetchone()

            if result:
                fname, lname, mname, dob, address, role, username = result
                
                # Format full name
                middle_initial = f"{mname[0]}." if mname else ""
                fullname = f"{fname} {middle_initial} {lname}".strip()
                
                # Prefill fields
                if self.fullname_line:
                    self.fullname_line.setText(fullname)
                
                if self.dob_date and dob:
                    qdate = QDate(dob.year, dob.month, dob.day)
                    self.dob_date.setDate(qdate)
                
                if self.address_line:
                    self.address_line.setText(address)
                
                if self.role_line:
                    self.role_line.setText(role)
                
                if self.un_line:
                    self.un_line.setText(username)
                
                # Show masked password
                if self.pw_line:
                    self.pw_line.setText("password")
            else:
                QMessageBox.warning(self, "Error", "User data not found.")

            cursor.close()
            conn.close()

        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Error loading user data: {str(e)}")

    def edit_account_info(self):
        self.switch_to_editsettings.emit()

    def back_dashboardmenu(self):
        self.back_to_menu.emit()

    def load_fonts(self):
        # Poppins
        if QFontDatabase.addApplicationFont("assets/fonts/Poppins-Regular.ttf") != -1:
            print("Poppins font loaded successfully.")
        else:
            print("Failed to load Poppins font.")

        # Helvetica
        if QFontDatabase.addApplicationFont("assets/fonts/Helvetica.ttf") != -1:
            print("Helvetica font loaded successfully.")
        else:
            print("Failed to load Helvetica font.")

        # Inter
        if QFontDatabase.addApplicationFont("assets/fonts/Inter-XtraBold.ttf") != -1:
            print("Inter font loaded successfully.")
        else:
            print("Failed to load Inter font.")

class EditSettings(QWidget):
    switch_to_settings = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__()
        uic.loadUi("ui/settings-placeholder.ui", self)
        self.load_fonts()

        # add sidebar logo
        self.sidebar_widget = QWidget(self)
        uic.loadUi("ui/enroll-sidebar.ui", self.sidebar_widget)
        self.sidebar_widget.move(0, 0)

        # add the settings ui
        self.edit_widget = QWidget(self)
        uic.loadUi("ui/settings-editinfo.ui", self.edit_widget)
        self.edit_widget.move(417, 0)

        # Find the fields
        self.fullname_line = self.edit_widget.findChild(QLineEdit, "fullname_line")
        self.dob_date = self.edit_widget.findChild(QDateEdit, "dob_date")
        self.address_line = self.edit_widget.findChild(QLineEdit, "address_line")
        self.role_line = self.edit_widget.findChild(QLineEdit, "role_line")
        self.un_line = self.edit_widget.findChild(QLineEdit, "un_line")
        self.cpw_line = self.edit_widget.findChild(QLineEdit, "cpw_line")  # Current password
        self.npw_line = self.edit_widget.findChild(QLineEdit, "npw_line")  # New password

        # Make role field read-only (typically users shouldn't change their own role)
        if self.role_line:
            self.role_line.setReadOnly(True)

        # Set password fields to password mode (masked with dots)
        if self.cpw_line:
            self.cpw_line.setEchoMode(QLineEdit.Password)
        if self.npw_line:
            self.npw_line.setEchoMode(QLineEdit.Password)

        # edit info button
        self.back_btn = self.edit_widget.findChild(QPushButton, "back_btn")
        if self.back_btn:
            self.back_btn.clicked.connect(self.back_settings)

        # save info button
        self.save_btn = self.edit_widget.findChild(QPushButton, "save_btn")
        if self.save_btn:
            self.save_btn.clicked.connect(self.save_changes)

    def load_user_data(self):
        if LoggedUser.current_logged_in_user_id is None:
            QMessageBox.warning(self, "Error", "No user logged in.")
            return

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Query to get user data from both tables using user_id
            query = """
                SELECT 
                    ba.admin_fname, 
                    ba.admin_lname, 
                    ba.admin_mname, 
                    ba.admin_dob, 
                    ba.admin_address,
                    u.user_role,
                    u.user_username
                FROM users u
                JOIN barangay_admin ba ON u.admin_id = ba.admin_id
                WHERE u.user_id = %s
            """
            cursor.execute(query, (LoggedUser.current_logged_in_user_id,))
            result = cursor.fetchone()

            if result:
                fname, lname, mname, dob, address, role, username = result
                
                # Format full name
                middle_initial = f"{mname[0]}." if mname else ""
                fullname = f"{fname} {middle_initial} {lname}".strip()
                
                # Prefill fields
                if self.fullname_line:
                    self.fullname_line.setText(fullname)
                
                if self.dob_date and dob:
                    qdate = QDate(dob.year, dob.month, dob.day)
                    self.dob_date.setDate(qdate)
                
                if self.address_line:
                    self.address_line.setText(address)
                
                if self.role_line:
                    self.role_line.setText(role)
                
                if self.un_line:
                    self.un_line.setText(username)
                
                # Clear password fields
                if self.cpw_line:
                    self.cpw_line.clear()
                if self.npw_line:
                    self.npw_line.clear()
            else:
                QMessageBox.warning(self, "Error", "User data not found.")

            cursor.close()
            conn.close()

        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Error loading user data: {str(e)}")

    def save_changes(self):
        if LoggedUser.current_logged_in_user_id is None:
            QMessageBox.warning(self, "Error", "No user logged in.")
            return

        # Get field values
        fullname = self.fullname_line.text().strip() if self.fullname_line else ""
        dob = self.dob_date.date() if self.dob_date else None
        address = self.address_line.text().strip() if self.address_line else ""
        username = self.un_line.text().strip() if self.un_line else ""
        current_password = self.cpw_line.text() if self.cpw_line else ""
        new_password = self.npw_line.text() if self.npw_line else ""

        # Validate required fields
        if not fullname or not address or not username:
            QMessageBox.warning(self, "Validation Error", "Please fill in all required fields.")
            return

        # Parse full name
        name_parts = fullname.split()
        if len(name_parts) < 2:
            QMessageBox.warning(self, "Validation Error", "Please enter full name (First Middle Last or First Last).")
            return

        fname = name_parts[0]
        lname = name_parts[-1]
        mname = name_parts[1] if len(name_parts) > 2 else None
        # Remove period from middle name if present
        if mname and mname.endswith('.'):
            mname = mname[:-1]

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Get the admin_id for the current user
            cursor.execute("SELECT admin_id FROM users WHERE user_id = %s", 
                         (LoggedUser.current_logged_in_user_id,))
            admin_result = cursor.fetchone()
            
            if not admin_result:
                QMessageBox.warning(self, "Error", "User not found.")
                cursor.close()
                conn.close()
                return
            
            admin_id = admin_result[0]

            # If password fields are filled, verify current password and update
            update_password = False
            if current_password or new_password:
                if not current_password or not new_password:
                    QMessageBox.warning(self, "Validation Error", "Please enter both current and new password.")
                    cursor.close()
                    conn.close()
                    return

                # Verify current password using PostgreSQL's crypt function
                verify_query = """
                    SELECT user_password = crypt(%s, user_password) AS password_match
                    FROM users 
                    WHERE user_id = %s
                """
                cursor.execute(verify_query, (current_password, LoggedUser.current_logged_in_user_id))
                result = cursor.fetchone()
                
                if not result or not result[0]:
                    QMessageBox.warning(self, "Authentication Error", "Current password is incorrect.")
                    cursor.close()
                    conn.close()
                    return
                
                update_password = True

            # Update barangay_admin table
            update_admin_query = """
                UPDATE barangay_admin 
                SET admin_fname = %s, 
                    admin_lname = %s, 
                    admin_mname = %s, 
                    admin_dob = %s, 
                    admin_address = %s
                WHERE admin_id = %s
            """
            dob_value = dob.toPyDate() if dob else None
            cursor.execute(update_admin_query, 
                         (fname, lname, mname, dob_value, address, admin_id))

            # Update users table
            if update_password:
                # Use PostgreSQL's crypt function to hash the new password
                update_user_query = """
                    UPDATE users 
                    SET user_username = %s, 
                        user_password = crypt(%s, gen_salt('bf', 12))
                    WHERE user_id = %s
                """
                cursor.execute(update_user_query, 
                             (username, new_password, LoggedUser.current_logged_in_user_id))
            else:
                update_user_query = """
                    UPDATE users 
                    SET user_username = %s
                    WHERE user_id = %s
                """
                cursor.execute(update_user_query, 
                             (username, LoggedUser.current_logged_in_user_id))

            conn.commit()
            cursor.close()
            conn.close()

            # Show success message
            self.show_dialog()

            # Navigate back to settings view page
            self.switch_to_settings.emit()

        except psycopg2.IntegrityError as e:
            QMessageBox.warning(self, "Database Error", "Username already exists. Please choose a different username.")
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Error updating user data: {str(e)}")

    def back_settings(self):
        self.switch_to_settings.emit()

    def show_dialog(self):
        # show a success dialog
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setWindowTitle("Success")
        msg_box.setText("Information successfully updated.")
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()

    def load_fonts(self):
        # Poppins
        if QFontDatabase.addApplicationFont("assets/fonts/Poppins-Regular.ttf") != -1:
            print("Poppins font loaded successfully.")
        else:
            print("Failed to load Poppins font.")

        # Helvetica
        if QFontDatabase.addApplicationFont("assets/fonts/Helvetica.ttf") != -1:
            print("Helvetica font loaded successfully.")
        else:
            print("Failed to load Helvetica font.")

        # Inter
        if QFontDatabase.addApplicationFont("assets/fonts/Inter-XtraBold.ttf") != -1:
            print("Inter font loaded successfully.")
        else:
            print("Failed to load Inter font.")

#record list
class DashboardRecords(QWidget):
    switch_to_dbmenu = pyqtSignal()
    switch_to_specificfile = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__()
        uic.loadUi("ui/record-gradientbg.ui", self)
        self.load_fonts()

        #add the record widget (without the list widget)
        self.record_widget = QWidget(self)
        uic.loadUi("ui/record-list.ui", self.record_widget)
        self.record_widget.move(242, 121)

        #add logo
        self.loginlogo_widget = QWidget(self)
        uic.loadUi("ui/login-logo.ui", self.loginlogo_widget)
        self.loginlogo_widget.move(648, 80)
        self.loginlogo_widget.raise_()

        #find the list widget
        self.list_widget = self.record_widget.findChild(QListWidget, "listWidget")

        #add sample data only
        self.add_record("Alonte, Angela Marie", "10-0001", "September 10, 2021")
        self.add_record("Bautista, Herbert", "10-0002", "September 11, 2021")

        #back to menu button
        self.backmenu_btn = self.record_widget.findChild(QPushButton, "back_btn")
        if self.backmenu_btn:
            self.backmenu_btn.clicked.connect(self.go_to_dbmenu)

    #back to dashboard menu
    def go_to_dbmenu(self):
        self.switch_to_dbmenu.emit()

    #add record or row data to the list widget
    def add_record(self, name, case_no, date):
        #row container
        row_widget = QWidget()
        layout = QHBoxLayout(row_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        #column 1: Name
        name_btn = QPushButton(name)
        name_btn.setStyleSheet("text-align: left; padding-left: 20px;")

        #column 2: case number
        case_btn = QPushButton(case_no)
        case_btn.setStyleSheet("text-align: right; padding-right: 30px")

        #column 3: date
        date_btn = QPushButton(date)
        date_btn.setStyleSheet("text-align: right; padding-right: 20px;")

        layout.addWidget(name_btn, 3)
        layout.addWidget(case_btn, 2)
        layout.addWidget(date_btn, 2)

        #stylesheet
        row_widget.setStyleSheet("""
            QWidget {
                background-color: none;
                border: none;
                font-family: 'Poppins';
                font-size: 9pt;
                border-radius: 15px;
                padding-top: 15px;
                padding-bottom: 17px;
                padding-left: 12px;
                padding-right: 15px;
                color: #383838;
            }
            QWidget:hover{
                background-color: #3E2780;
                color: white;
            }
        """)

        #add to the list widget
        item = QListWidgetItem()
        item.setSizeHint(row_widget.sizeHint())
        self.list_widget.addItem(item)
        self.list_widget.setItemWidget(item, row_widget)

        # connect click event to navigate
        for btn in (name_btn, case_btn, date_btn):
            btn.clicked.connect(lambda _, case=case_no: self.open_record(case))

    def open_record(self, case_no):
        print(f"Opening record {case_no}")
        self.switch_to_specificfile.emit()

    def load_fonts(self):
        # Poppins
        if QFontDatabase.addApplicationFont("assets/fonts/Poppins-Regular.ttf") != -1:
            print("Poppins font loaded successfully.")
        else:
            print("Failed to load Poppins font.")

        # Helvetica
        if QFontDatabase.addApplicationFont("assets/fonts/Helvetica.ttf") != -1:
            print("Helvetica font loaded successfully.")
        else:
            print("Failed to load Helvetica font.")

        # Inter
        if QFontDatabase.addApplicationFont("assets/fonts/Poppins-Regular.ttf") != -1:
            print("Inter font loaded successfully.")
        else:
            print("Failed to load Inter font.")

#from here, this is when user clicks on a specific case record
class CasePersonalInfo(QWidget):
    switch_to_parentinfo = pyqtSignal()
    close_page = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__()
        uic.loadUi("ui/casefile-placeholder.ui", self)
        self.load_fonts()
        self.raise_()

        #add the sidebar logo
        self.sidebar_widget = QWidget(self)
        uic.loadUi("ui/enroll-sidebar.ui", self.sidebar_widget)
        self.sidebar_widget.move(0, 0)

        #add the personal info widget
        self.personal_widget = QWidget(self)
        uic.loadUi("ui/casefile-personalinfo.ui", self.personal_widget)
        self.personal_widget.move(417, 0)

        # next button
        self.next_btn = self.personal_widget.findChild(QPushButton, "next_button")
        if self.next_btn:
            self.next_btn.clicked.connect(self.go_to_parentinfo)

        # close button
        self.close_btn = self.personal_widget.findChild(QPushButton, "close_btn")
        if self.close_btn:
            self.close_btn.clicked.connect(self.go_to_recordlist)

    def go_to_parentinfo(self):
        self.switch_to_parentinfo.emit()

    def go_to_recordlist(self):
        self.close_page.emit()

    def load_fonts(self):
        # Poppins
        if QFontDatabase.addApplicationFont("assets/fonts/Poppins-Regular.ttf") != -1:
            print("Poppins font loaded successfully.")
        else:
            print("Failed to load Poppins font.")

        # Helvetica
        if QFontDatabase.addApplicationFont("assets/fonts/Helvetica.ttf") != -1:
            print("Helvetica font loaded successfully.")
        else:
            print("Failed to load Helvetica font.")

        # Inter
        if QFontDatabase.addApplicationFont("assets/fonts/Inter-XtraBold.ttf") != -1:
            print("Inter font loaded successfully.")
        else:
            print("Failed to load Inter font.")


class CaseParentInfo(QWidget):
    switch_to_offense = pyqtSignal()
    switch_to_personal = pyqtSignal()
    close_page = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__()
        uic.loadUi("ui/casefile-placeholder.ui", self)
        self.load_fonts()
        self.raise_()

        #add the sidebar logo
        self.sidebar_widget = QWidget(self)
        uic.loadUi("ui/enroll-sidebar.ui", self.sidebar_widget)
        self.sidebar_widget.move(0, 0)

        #add the offense info widget
        self.parent_widget = QWidget(self)
        uic.loadUi("ui/casefile-parentinfo.ui", self.parent_widget)
        self.parent_widget.move(417, 0)

        # next button
        self.next_btn = self.parent_widget.findChild(QPushButton, "next_button")
        if self.next_btn:
            self.next_btn.clicked.connect(self.go_to_offenseinfo)

        # previous button
        self.prev_btn = self.parent_widget.findChild(QPushButton, "prev_btn")
        if self.prev_btn:
            self.prev_btn.clicked.connect(self.go_to_personal)

        # close button
        self.close_btn = self.parent_widget.findChild(QPushButton, "close_btn")
        if self.close_btn:
            self.close_btn.clicked.connect(self.go_to_recordlist)

    def go_to_offenseinfo(self):
        self.switch_to_offense.emit()

    def go_to_personal(self):
        self.switch_to_personal.emit()

    def go_to_recordlist(self):
        self.close_page.emit()

    def load_fonts(self):
        # Poppins
        if QFontDatabase.addApplicationFont("assets/fonts/Poppins-Regular.ttf") != -1:
            print("Poppins font loaded successfully.")
        else:
            print("Failed to load Poppins font.")

        # Helvetica
        if QFontDatabase.addApplicationFont("assets/fonts/Helvetica.ttf") != -1:
            print("Helvetica font loaded successfully.")
        else:
            print("Failed to load Helvetica font.")

        # Inter
        if QFontDatabase.addApplicationFont("assets/fonts/Inter-XtraBold.ttf") != -1:
            print("Inter font loaded successfully.")
        else:
            print("Failed to load Inter font.")


class CaseOffenseInfo(QWidget):
    switch_to_history = pyqtSignal()
    switch_to_parent = pyqtSignal()
    close_page = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__()
        uic.loadUi("ui/casefile-placeholder.ui", self)
        self.load_fonts()
        self.raise_()

        #add the sidebar logo
        self.sidebar_widget = QWidget(self)
        uic.loadUi("ui/enroll-sidebar.ui", self.sidebar_widget)
        self.sidebar_widget.move(0, 0)

        #add the offense info widget
        self.offense_widget = QWidget(self)
        uic.loadUi("ui/casefile-offenseinfo.ui", self.offense_widget)
        self.offense_widget.move(417, 0)

        # next button
        self.next_btn = self.offense_widget.findChild(QPushButton, "next_button")
        if self.next_btn:
            self.next_btn.clicked.connect(self.go_to_history)

        # previous button
        self.prev_btn = self.offense_widget.findChild(QPushButton, "prev_btn")
        if self.prev_btn:
            self.prev_btn.clicked.connect(self.go_to_parent)

        # close button
        self.close_btn = self.offense_widget.findChild(QPushButton, "close_btn")
        if self.close_btn:
            self.close_btn.clicked.connect(self.go_to_recordlist)

    def go_to_history(self):
        self.switch_to_history.emit()

    def go_to_parent(self):
        self.switch_to_parent.emit()

    def go_to_recordlist(self):
        self.close_page.emit()

    def load_fonts(self):
        # Poppins
        if QFontDatabase.addApplicationFont("assets/fonts/Poppins-Regular.ttf") != -1:
            print("Poppins font loaded successfully.")
        else:
            print("Failed to load Poppins font.")

        # Helvetica
        if QFontDatabase.addApplicationFont("assets/fonts/Helvetica.ttf") != -1:
            print("Helvetica font loaded successfully.")
        else:
            print("Failed to load Helvetica font.")

        # Inter
        if QFontDatabase.addApplicationFont("assets/fonts/Inter-XtraBold.ttf") != -1:
            print("Inter font loaded successfully.")
        else:
            print("Failed to load Inter font.")

class CaseCriminalHistory(QWidget):
    switch_to_offense = pyqtSignal()
    close_page = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__()
        uic.loadUi("ui/casefile-placeholder.ui", self)
        self.load_fonts()
        self.raise_()

        #add the sidebar logo
        self.sidebar_widget = QWidget(self)
        uic.loadUi("ui/enroll-sidebar.ui", self.sidebar_widget)
        self.sidebar_widget.move(0, 0)

        #add the criminal history widget
        self.history_widget = QWidget(self)
        uic.loadUi("ui/casefile-criminalhistory.ui", self.history_widget)
        self.history_widget.move(417, 0)

        #criminal history record table
        self.history_table = self.history_widget.findChild(QTableWidget, "history_table")
        if self.history_table:
            self.history_table.setColumnWidth(0, 201)
            self.history_table.setColumnWidth(1, 262)
            self.history_table.setColumnWidth(2, 361)
            self.history_table.verticalHeader().setVisible(False)
            self.history_table.resizeRowsToContents()

        # previous button
        self.prev_btn = self.history_widget.findChild(QPushButton, "prev_btn")
        if self.prev_btn:
            self.prev_btn.clicked.connect(self.go_to_offense)

        # close button
        self.close_btn = self.history_widget.findChild(QPushButton, "close_btn")
        if self.close_btn:
            self.close_btn.clicked.connect(self.go_to_recordlist)

    def go_to_offense(self):
        self.switch_to_offense.emit()

    def go_to_recordlist(self):
        self.close_page.emit()

    def load_fonts(self):
        # Poppins
        if QFontDatabase.addApplicationFont("assets/fonts/Poppins-Regular.ttf") != -1:
            print("Poppins font loaded successfully.")
        else:
            print("Failed to load Poppins font.")

        # Helvetica
        if QFontDatabase.addApplicationFont("assets/fonts/Helvetica.ttf") != -1:
            print("Helvetica font loaded successfully.")
        else:
            print("Failed to load Helvetica font.")

        # Inter
        if QFontDatabase.addApplicationFont("assets/fonts/Inter-XtraBold.ttf") != -1:
            print("Inter font loaded successfully.")
        else:
            print("Failed to load Inter font.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = DbMenuWindow()
    ui.show()
    app.exec_()