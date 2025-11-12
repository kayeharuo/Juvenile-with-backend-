import sys
import psycopg2
from psycopg2 import errors
from PyQt5 import uic, Qt
from PyQt5.QtCore import QEvent, QDate
from PyQt5.QtGui import QFontDatabase
from PyQt5.QtWidgets import (QWidget, QApplication, QComboBox, QLineEdit, QMessageBox, QPushButton, QLabel,
                             QDialogButtonBox, QDialog, QStyle, QDateEdit)
from PyQt5.QtWidgets import *
from Db_connection import get_db_connection
import LoggedUser


class LogIn(QWidget):
    
    def __init__(self):
        super().__init__()
        uic.loadUi("ui/gradient-db.ui", self)
        self.load_fonts()

        #initialize widgets but no display
        self.login_account_widget = None
        self.forgot_password_widget = None
        self.create_account_widget = None

        #add logo
        self.loginlogo_widget = QWidget(self)
        uic.loadUi("ui/login-logo.ui", self.loginlogo_widget)
        self.loginlogo_widget.move(655, 245)

        #login
        self.show_login_account()

    def show_login_account(self):
        #hide forgot password widget
        if self.forgot_password_widget:
            self.forgot_password_widget.hide()

        #hide create account widget
        if self.create_account_widget:
            self.create_account_widget.hide()

        #show login account widget
        if not self.login_account_widget:
            self.login_account_widget = QWidget(self)
            uic.loadUi("ui/login-account.ui", self.login_account_widget)

            #hash password when logging in
            passw_line = self.login_account_widget.findChild(QLineEdit, "pw_line")
            if passw_line:
                passw_line.setEchoMode(QLineEdit.Password)

            #forgot password button
            forgot_pw_btn = self.login_account_widget.findChild(QPushButton, "forgotpw_btn")
            if forgot_pw_btn:
                forgot_pw_btn.clicked.connect(self.show_forgot_password)

            #create account button
            create_account_btn = self.login_account_widget.findChild(QPushButton, "createacc_btn")
            if create_account_btn:
                create_account_btn.clicked.connect(self.show_create_account)

            #login button
            login_btn = self.login_account_widget.findChild(QPushButton, "login_btn")
            if login_btn:
                login_btn.clicked.connect(self.handle_login)

        self.login_account_widget.move(500, 310)
        self.login_account_widget.show()
        self.login_account_widget.raise_()

        if self.loginlogo_widget:
            self.loginlogo_widget.raise_()

    def handle_login(self):
        un_line = self.login_account_widget.findChild(QLineEdit, "un_line")
        pw_line = self.login_account_widget.findChild(QLineEdit, "pw_line")

        if not un_line or not pw_line:
            QMessageBox.warning(self, "Error", "Unable to find login fields.")
            return

        username = un_line.text().strip()
        password = pw_line.text().strip()

        if not username:
            QMessageBox.warning(self, "Input Error", "Please enter your username.")
            return
        
        if not password:
            QMessageBox.warning(self, "Input Error", "Please enter your password.")
            return

        #authenticate user
        user_data = self.authenticate_user(username, password)
        if user_data:
            # Store the logged-in user_id in class variable
            LoggedUser.current_logged_in_user_id = user_data['user_id']
            print(f"LOGGED IN: User ID = {LoggedUser.current_logged_in_user_id}, Username = {user_data['username']}")
            
            self.open_menu_window()
        else:
            QMessageBox.warning(
                self, 
                "Login Failed", 
                "Invalid username or password.\n\nPlease try again."
            )
            #clear password field for security
            pw_line.clear()

    def authenticate_user(self, username, password):
        conn = get_db_connection()
        if not conn:
            QMessageBox.critical(self, "Database Error", "Failed to connect to the database.")
            return None

        try:
            cur = conn.cursor()
            query = """
                SELECT USER_ID, USER_USERNAME, USER_ROLE, ADMIN_ID 
                FROM USERS 
                WHERE USER_USERNAME = %s 
                AND USER_PASSWORD = crypt(%s, USER_PASSWORD)
            """
            cur.execute(query, (username, password))
            user = cur.fetchone()
            cur.close()

            if user:
                user_data = {
                    'user_id': user[0],
                    'username': user[1],
                    'role': user[2],
                    'admin_id': user[3]
                }
                return user_data
            else:
                return None

        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred during login:\n{e}")
            return None
        finally:
            if conn:
                conn.close()

    def open_menu_window(self):
        #Open the MenuWindow after successful login
        try:
            from MenuWindow import SystemMenu
            self.menu_window = SystemMenu()
            self.menu_window.show()
            
            self.close()
            
        except ImportError as e:
            QMessageBox.critical(
                self, 
                "Error", 
                f"Failed to load MenuWindow:\n{e}\n\nMake sure MenuWindow.py exists in the same directory."
            )
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Error", 
                f"An error occurred while opening the menu:\n{e}"
            )

    def show_forgot_password(self):
        #hide login account widget
        if self.login_account_widget:
            self.login_account_widget.hide()

        #hide create account widget
        if self.create_account_widget:
            self.create_account_widget.hide()

        #show forgot password widget
        if not self.forgot_password_widget:
            self.forgot_password_widget = ForgotPassword(self)

        self.forgot_password_widget.move(500, 310)
        self.forgot_password_widget.show()
        self.forgot_password_widget.raise_()

        if self.loginlogo_widget:
            self.loginlogo_widget.raise_()

    def show_create_account(self):
        #hide login account widget
        if self.login_account_widget:
            self.login_account_widget.hide()

        #hide forgot password widget
        if self.forgot_password_widget:
            self.forgot_password_widget.hide()

        #Destroy old create account widget and create a fresh one
        if self.create_account_widget:
            self.create_account_widget.deleteLater()
            self.create_account_widget = None

        #show create account widget
        if not self.create_account_widget:
            self.create_account_widget = CreateAccount(self)

        self.create_account_widget.move(500, 310)
        self.create_account_widget.show()
        self.create_account_widget.raise_()

        if self.loginlogo_widget:
            self.loginlogo_widget.raise_()

    def load_fonts(self):
        #Poppins
        if QFontDatabase.addApplicationFont("assets/fonts/Poppins-Regular.ttf") != -1:
            print("Poppins font loaded successfully.")
        else:
            print("Failed to load Poppins font.")

        #Helvetica
        if QFontDatabase.addApplicationFont("assets/fonts/Helvetica.ttf") != -1:
            print("Helvetica font loaded successfully.")
        else:
            print("Failed to load Helvetica font.")

        #Inter
        if QFontDatabase.addApplicationFont("assets/fonts/Inter-XtraBold.ttf") != -1:
            print("Inter font loaded successfully.")
        else:
            print("Failed to load Inter font.")

class CreateAccount(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.create_account_widget = None
        self.create_account_2_widget = None
        
        #Temporary storage for barangay admin data (instead of inserting to DB)
        self.temp_admin_data = {
            'fname': None,
            'lname': None,
            'mname': None,
            'dob': None,
            'address': None
        }
        
        self.show_create_account_page1()

    def show_create_account_page1(self):
        #hide second page
        if self.create_account_2_widget:
            self.create_account_2_widget.hide()

        #show create account widget
        if not self.create_account_widget:
            self.create_account_widget = QWidget(self)
            uic.loadUi("ui/create-account.ui", self.create_account_widget)

            #next button
            next_btn = self.create_account_widget.findChild(QPushButton, "next_btn")
            if next_btn:
                next_btn.clicked.connect(self.handle_next_button)

            #back to login button
            back_btn = self.create_account_widget.findChild(QPushButton, "backtologin_btn")
            if back_btn:
                back_btn.clicked.connect(self.back_to_login)

        self.create_account_widget.move(0, 0)
        self.create_account_widget.show()
        self.create_account_widget.raise_()

    def handle_next_button(self):
        fn_line = self.create_account_widget.findChild(QLineEdit, "fn_line")
        mn_line = self.create_account_widget.findChild(QLineEdit, "mn_line")
        ln_line = self.create_account_widget.findChild(QLineEdit, "ln_line")
        dob = self.create_account_widget.findChild(QDateEdit, "dob")
        address_line = self.create_account_widget.findChild(QLineEdit, "address_line")

        if not all([fn_line, mn_line, ln_line, dob, address_line]):
            QMessageBox.warning(self, "Error", "Unable to find form fields.")
            return

        #Validate and store data temporarily (don't insert to DB yet)
        fname = fn_line.text().strip()
        lname = ln_line.text().strip()
        mname = mn_line.text().strip()
        dob_date = dob.date()
        address = address_line.text().strip()
        
        #Validation
        if not fname:
            QMessageBox.warning(self, "Input Error", "First name field cannot be empty.")
            return
        if not lname:
            QMessageBox.warning(self, "Input Error", "Last name field cannot be empty.")
            return
        if not address:
            QMessageBox.warning(self, "Input Error", "Address field cannot be empty.")
            return
        if not dob_date or not isinstance(dob_date, QDate) or not dob_date.isValid():
            QMessageBox.warning(self, "Input Error", "Please select a valid date of birth.")
            return
        
        #Store data temporarily
        self.temp_admin_data['fname'] = fname
        self.temp_admin_data['lname'] = lname
        self.temp_admin_data['mname'] = mname if mname else None
        self.temp_admin_data['dob'] = dob_date.toString("yyyy-MM-dd")
        self.temp_admin_data['address'] = address
        
        #Move to next page
        self.show_create_account_page2()

    def show_create_account_page2(self):
        #hide first page
        if self.create_account_widget:
            self.create_account_widget.hide()

        #show create account 2 widget
        if not self.create_account_2_widget:
            self.create_account_2_widget = QWidget(self)
            uic.loadUi("ui/create-account-2.ui", self.create_account_2_widget)


            #submit button
            submit_btn = self.create_account_2_widget.findChild(QPushButton, "submit_btn")
            if submit_btn:
                submit_btn.clicked.connect(self.create_account_verification)

            #back to previous page button
            back_to_prev_btn = self.create_account_2_widget.findChild(QPushButton, "back_btn")
            if back_to_prev_btn:
                back_to_prev_btn.clicked.connect(self.back_to_page1)

        self.create_account_2_widget.move(0, 0)
        self.create_account_2_widget.show()
        self.create_account_2_widget.raise_()

    def back_to_page1(self):
        #Just clear temporary data and go back (no DB operation needed)
        reply = QMessageBox.question(
            self, 
            'Confirm', 
            "Going back will discard the information entered on this page. Continue?",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.show_create_account_page1()

    def create_account_verification(self):
        #Validate fields before showing verification dialog
        role_dropdown = self.create_account_2_widget.findChild(QComboBox, "role_dropdown")
        un_line = self.create_account_2_widget.findChild(QLineEdit, "un_line")
        pw_line = self.create_account_2_widget.findChild(QLineEdit, "pw_line")

        if not role_dropdown or not un_line or not pw_line:
            QMessageBox.warning(self, "Error", "Unable to find form fields.")
            return

        role = role_dropdown.currentText().strip()
        username = un_line.text().strip()
        password = pw_line.text().strip()

        if not role:
            QMessageBox.warning(self, "Input Error", "Please select a role.")
            return
        if not username:
            QMessageBox.warning(self, "Input Error", "Please enter a username.")
            return
        if not password:
            QMessageBox.warning(self, "Input Error", "Please enter a password.")
            return
        
        if len(password) <= 6:
            QMessageBox.warning(
                self, 
                "Weak Password", 
                "Password must be more than 6 characters long.\n\n"
                "Please create a stronger password."
            )
            return

        #Show verification dialog
        verify = CAVerifyKey(self)
        result = verify.exec_()
        
        if result == QDialog.Accepted:
            #Successfully created account, go back to login
            self.back_to_login()

    def back_to_login(self):
        if self.parent_window:
            self.parent_window.show_login_account()

    def db_insert_admin_and_user(self, role, username, password):
        conn = get_db_connection()

        if not conn:
            QMessageBox.critical(self, "Database Error", "Failed to connect to the database.")
            return False

        try:
            cur = conn.cursor()
            
            #Insert into BARANGAY_ADMIN table
            admin_query = """
                INSERT INTO BARANGAY_ADMIN (ADMIN_FNAME, ADMIN_LNAME, ADMIN_MNAME, ADMIN_DOB, ADMIN_ADDRESS)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING ADMIN_ID
            """
            cur.execute(admin_query, (
                self.temp_admin_data['fname'],
                self.temp_admin_data['lname'],
                self.temp_admin_data['mname'],
                self.temp_admin_data['dob'],
                self.temp_admin_data['address']
            ))
            admin_id = cur.fetchone()[0]
            
            #Insert into USERS table using the admin_id
            user_query = """
                INSERT INTO USERS (USER_ROLE, USER_USERNAME, USER_PASSWORD, ADMIN_ID)
                VALUES (%s, %s, crypt(%s, gen_salt('bf', 12)), %s)
            """
            cur.execute(user_query, (role, username, password, admin_id))
            
            #Commit both inserts
            conn.commit()
            cur.close()

            QMessageBox.information(self, "Success", "Account successfully created!")
            
            #Clear temporary data after successful insertion
            self.temp_admin_data = {
                'fname': None,
                'lname': None,
                'mname': None,
                'dob': None,
                'address': None
            }
            
            return True

        except errors.UniqueViolation as e:
            conn.rollback()
            QMessageBox.warning(self, "Duplicate Entry", "This username already exists. Please choose another one.")
        except errors.NotNullViolation as e:
            conn.rollback()
            QMessageBox.warning(self, "Missing Field", f"A required field is missing: {e.diag.column_name}")
        except errors.CheckViolation:
            conn.rollback()
            QMessageBox.warning(self, "Invalid Role", "User role must be 'Admin', 'admin', or 'ADMIN'.")
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "Database Error", f"An unexpected error occurred:\n{e}")
        finally:
            if conn:
                conn.close()
        
        return False


class ForgotPassword(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi("ui/login-resetpw.ui", self)

        #hash pw fields
        newpw_line = self.findChild(QLineEdit, "newpw_line")
        confirmpw_line = self.findChild(QLineEdit, "confirmpw_line")

        if newpw_line:
            newpw_line.setEchoMode(QLineEdit.Password)
        if confirmpw_line:
            confirmpw_line.setEchoMode(QLineEdit.Password)

        back_btn = self.findChild(QPushButton, "backtologin_btn")
        if back_btn:
            back_btn.clicked.connect(self.back_to_login)

        cont_btn = self.findChild(QPushButton, "resetpw_btn")
        if cont_btn:
            cont_btn.clicked.connect(self.verification)

    def back_to_login(self):
        if self.parent():
            self.parent().show_login_account()

    def verification(self):
        #Validate fields before showing verification dialog
        un_line = self.findChild(QLineEdit, "un_line")
        newpw_line = self.findChild(QLineEdit, "newpw_line")
        confirmpw_line = self.findChild(QLineEdit, "confirmpw_line")

        if not un_line or not newpw_line or not confirmpw_line:
            QMessageBox.warning(self, "Error", "Unable to find form fields.")
            return

        username = un_line.text().strip()
        newpass = newpw_line.text().strip()
        confirmpass = confirmpw_line.text().strip()

        if not username:
            QMessageBox.warning(self, "Input Error", "Please enter a username.")
            return
        if not newpass:
            QMessageBox.warning(self, "Input Error", "Please enter a new password.")
            return
        if not confirmpass:
            QMessageBox.warning(self, "Input Error", "Please confirm your password.")
            return

        #Show verification dialog
        verify = VerifyKey(self)
        result = verify.exec_()
        
        if result == QDialog.Accepted:
            #Verification successful, go back to login
            self.back_to_login()

    def db_reset_password(self, username, newpass, confirmpass):
        #Validate inputs
        if not username.strip():
            QMessageBox.warning(self, "Input Error", "Username field cannot be empty.")
            return False
        if not newpass.strip():
            QMessageBox.warning(self, "Input Error", "New password field cannot be empty.")
            return False
        if not confirmpass.strip():
            QMessageBox.warning(self, "Input Error", "Confirm password field cannot be empty.")
            return False
        
        #Check if passwords match
        if newpass != confirmpass:
            QMessageBox.warning(self, "Password Mismatch", "New password and confirm password do not match.")
            return False
        
        #Check password length (optional - add your own requirements)
        if len(newpass) < 6:
            QMessageBox.warning(self, "Weak Password", "Password must be at least 6 characters long.")
            return False

        conn = get_db_connection()
        if not conn:
            QMessageBox.critical(self, "Database Error", "Failed to connect to the database.")
            return False

        try:
            cur = conn.cursor()
            
            #Check if username exists
            check_query = "SELECT USER_ID FROM USERS WHERE USER_USERNAME = %s"
            cur.execute(check_query, (username,))
            user = cur.fetchone()
            
            if not user:
                QMessageBox.warning(self, "User Not Found", f"Username '{username}' does not exist.")
                cur.close()
                return False
            
            #Update password with bcrypt hashing
            update_query = """
                UPDATE USERS 
                SET USER_PASSWORD = crypt(%s, gen_salt('bf', 12))
                WHERE USER_USERNAME = %s
            """
            cur.execute(update_query, (newpass, username))
            conn.commit()
            cur.close()

            QMessageBox.information(self, "Success", "Password has been reset successfully!")
            return True

        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "Database Error", f"An unexpected error occurred:\n{e}")
            return False
        finally:
            if conn:
                conn.close()

class VerifyKey(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi("ui/login-verify.ui", self)
        self.setModal(True)

        self.setWindowTitle("Verification Notice")
        style = QApplication.style()
        warning_icon = style.standardIcon(QStyle.SP_MessageBoxWarning)
        self.setWindowIcon(warning_icon)

        #widgets
        self.key_line = self.findChild(QLineEdit, "key_line")
        self.button_box = self.findChild(QDialogButtonBox, "buttonBox")

        #Disconnect default connections and connect to custom handler
        if self.button_box:
            try:
                self.button_box.accepted.disconnect()
                self.button_box.rejected.disconnect()
            except:
                pass  
            
            #Connect to our custom methods
            self.button_box.accepted.connect(self.verify_auth_key)
            self.button_box.rejected.connect(self.reject)

    def verify_auth_key(self):
        # Verify the authorization key before accepting the dialog
        input_key = self.key_line.text().strip() if self.key_line else ""

        if not input_key:
            QMessageBox.warning(self, "Input Error", "Please enter an authorization key.")
            return  

        conn = get_db_connection()
        if not conn:
            QMessageBox.critical(self, "Database Error", "Failed to connect to the database.")
            return  

        try:
            cur = conn.cursor()
            query = "SELECT 1 FROM AUTHORIZATION_KEY WHERE AUTH_KEY = crypt(%s, AUTH_KEY)"
            cur.execute(query, (input_key,))
            result = cur.fetchone()
            cur.close()  # Close cursor HERE after checking key
            conn.close()  # Close connection HERE

            if result:
                # Key is valid - proceed with password reset
                parent = self.parent()
                if parent and isinstance(parent, ForgotPassword):
                    un_line = parent.findChild(QLineEdit, "un_line")
                    newpw_line = parent.findChild(QLineEdit, "newpw_line")
                    confirmpw_line = parent.findChild(QLineEdit, "confirmpw_line")

                    username = un_line.text().strip() if un_line else None
                    newpass = newpw_line.text().strip() if newpw_line else None
                    confirmpass = confirmpw_line.text().strip() if confirmpw_line else None

                    if not username or not newpass or not confirmpass:
                        QMessageBox.warning(self, "Error", "Missing required fields.")
                        return  

                    # Reset password
                    success = parent.db_reset_password(username, newpass, confirmpass)
                    if success:
                        self.accept()  # Only accept/close if successful
                else:
                    QMessageBox.warning(self, "Error", "Parent form not found.")
            else:
                # Invalid key
                QMessageBox.warning(self, "Unauthorized", "Invalid authorization key. Please try again.")

        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"An unexpected error occurred:\n{e}")
            
        finally:
            if conn:
                conn.close()
                
class CAVerifyKey(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi("ui/create-account-verify.ui", self)
        self.setModal(True)

        #window setup
        self.setWindowTitle("Verification Notice")
        style = QApplication.style()
        info_icon = style.standardIcon(QStyle.SP_MessageBoxInformation)
        self.setWindowIcon(info_icon)

        #widgets
        self.key_line = self.findChild(QLineEdit, "key_line")
        self.button_box = self.findChild(QDialogButtonBox, "buttonBox")

        #connect ok/cancel
        if self.button_box:
            self.button_box.accepted.connect(self.verify_auth_key)
            self.button_box.rejected.connect(self.reject)

    def verify_auth_key(self):
        input_key = self.key_line.text().strip() if self.key_line else ""

        if not input_key:
            QMessageBox.warning(self, "Input Error", "Please enter an authorization key.")
            return

        conn = get_db_connection()
        if not conn:
            QMessageBox.critical(self, "Database Error", "Failed to connect to the database.")
            return

        try:
            cur = conn.cursor()
            query = "SELECT 1 FROM AUTHORIZATION_KEY WHERE AUTH_KEY = crypt(%s, AUTH_KEY)"
            cur.execute(query, (input_key,))
            result = cur.fetchone()
            cur.close()  
            conn.close()  

            if result:
                # Key is valid - now insert both admin and user data
                parent = self.parent()
                if parent and hasattr(parent, "create_account_2_widget") and parent.create_account_2_widget:
                    role_dropdown = parent.create_account_2_widget.findChild(QComboBox, "role_dropdown")
                    un_line = parent.create_account_2_widget.findChild(QLineEdit, "un_line")
                    pw_line = parent.create_account_2_widget.findChild(QLineEdit, "pw_line")

                    role = role_dropdown.currentText().strip() if role_dropdown else None
                    username = un_line.text().strip() if un_line else None
                    password = pw_line.text().strip() if pw_line else None

                    if not all([role, username, password]):
                        QMessageBox.warning(self, "Error", "Missing required fields.")
                        return
                    
                    success = parent.db_insert_admin_and_user(role, username, password)
                    if success:
                        self.accept()
                else:
                    QMessageBox.warning(self, "Error", "Parent form not found.")
            else:
                QMessageBox.warning(self, "Unauthorized", "Invalid authorization key. Please try again.")

        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"An unexpected error occurred:\n{e}")
        finally:
            if conn:
                conn.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = LogIn()
    ui.show()
    app.exec_()