import sys
import cv2
import psycopg2
import numpy as np
from datetime import datetime
from PyQt5 import uic, Qt
from PyQt5.QtCore import QEvent, pyqtSignal, Qt, QTimer, QDate, QDateTime
from PyQt5.QtGui import QFontDatabase, QImage, QPixmap
from PyQt5.QtWidgets import (QWidget, QApplication, QComboBox, QLineEdit, QMessageBox, QPushButton, QLabel,
                             QDialogButtonBox, QDialog, QStyle, QMainWindow, QStackedWidget, QListWidget, QHBoxLayout,
                             QListWidgetItem, QVBoxLayout, QDateEdit, QDateTimeEdit, QTextEdit)
from Db_connection import get_db_connection


class EnrollmentData:
    def __init__(self):
        self.reset()

    def reset(self):
        # Personal Information
        self.personal_info = {
            'lname': '',
            'fname': '',
            'mname': '',
            'suffix': '',
            'sex': '',
            'gender': '',
            'age': '',
            'dob': None,
            'birthplace': '',
            'citizenship': '',
            'state': '',
            'municipal': '',
            'brgy': '',
            'street': ''
        }

        # Parent/Guardian Information
        self.parent_info = {
            'fullname': '',
            'relationship': '',
            'sex': '',
            'dob': None,
            'age': '',
            'civil_status': '',
            'citizenship': '',
            'occupation': '',
            'email': '',
            'contact': '',
            'address': ''
        }

        # Offense Information
        self.offense_info = {
            'offense_type': '',
            'case_no': '',
            'datetime': None,
            'location': '',
            'description': '',
            'complainant': '',
            'officer': ''
        }

        # Facial Data
        self.facial_data = {
            'image': None,
            'embedding': None
        }
        
        # Store JUV_ID after enrollment
        self.juv_id = None

    def reset_facial_only(self):
        self.facial_data = {
            'image': None,
            'embedding': None
        }

class Enroll(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("ui/EnrollMainWindow.ui", self)
        self.load_fonts()

        # Initialize temporary data storage
        self.enrollment_data = EnrollmentData()

        # add the stacked widget
        self.stack_widget = QStackedWidget(self)
        uic.loadUi("ui/enroll-stack.ui", self.stack_widget)
        self.stack_widget.move(417, 0)

        # add the sidebar widget
        self.sidebar_widget = QWidget(self)
        uic.loadUi("ui/enroll-sidebar.ui", self.sidebar_widget)
        self.sidebar_widget.move(0, 0)

        self.personalinfo = PersonalInfo(self.enrollment_data)
        self.personalinfo.switch_to_parent.connect(self.parentinfo_page)

        self.parentinfo = ParentInfo(self.enrollment_data)
        self.parentinfo.switch_to_offense.connect(self.offenseinfo_page)

        self.offenseinfo = OffenseInfo(self.enrollment_data)
        self.offenseinfo.switch_to_bio.connect(self.biometrics_page)

        self.biometrics = BioInfo()
        self.biometrics.switch_to_facescan.connect(self.facescan_page)

        self.review1 = ReviewPersonalInfo(self.enrollment_data)
        self.review1.switch_to_review2.connect(self.review_page2)
        self.review1.switch_to_personalinfo.connect(self.restart_enrollment)

        self.review2 = ReviewParentInfo(self.enrollment_data)
        self.review2.switch_to_review3.connect(self.review_page3)
        self.review2.switch_to_review1.connect(self.review_page1)
        self.review2.switch_to_personalinfo.connect(self.restart_enrollment)

        self.review3 = ReviewOffenseInfo(self.enrollment_data)
        self.review3.switch_to_review4.connect(self.review_page4)
        self.review3.switch_to_review2.connect(self.review_page2)
        self.review3.switch_to_personalinfo.connect(self.restart_enrollment)

        self.review4 = ReviewBioInfo(self.enrollment_data)
        self.review4.switch_to_review3.connect(self.review_page3)
        self.review4.switch_to_personalinfo.connect(self.restart_enrollment)
        self.review4.data_submitted.connect(self.save_to_database)
        self.review4.close_enrollwindow.connect(self.open_dashboardmenu)

        # add instances to the stacked widget
        self.stack_widget.addWidget(self.personalinfo)
        self.stack_widget.addWidget(self.parentinfo)
        self.stack_widget.addWidget(self.offenseinfo)
        self.stack_widget.addWidget(self.biometrics)
        self.stack_widget.addWidget(self.review1)
        self.stack_widget.addWidget(self.review2)
        self.stack_widget.addWidget(self.review3)
        self.stack_widget.addWidget(self.review4)

        # set the initial page to personal information
        self.stack_widget.setCurrentWidget(self.personalinfo)

    def personalinfo_page(self):
        self.stack_widget.setCurrentWidget(self.personalinfo)

    def parentinfo_page(self):
        self.stack_widget.setCurrentWidget(self.parentinfo)

    def offenseinfo_page(self):
        self.stack_widget.setCurrentWidget(self.offenseinfo)

    def biometrics_page(self):
        self.stack_widget.setCurrentWidget(self.biometrics)

    def facescan_page(self):
        self.facescan = FaceScan(self, self.enrollment_data)
        self.facescan.scan_completed.connect(self.review_page1)
        self.facescan.exec_()

    def review_page1(self):
        self.review1.populate_fields()
        self.stack_widget.setCurrentWidget(self.review1)
        if hasattr(self, 'facescan'):
            self.facescan.close()

    def review_page2(self):
        self.review2.populate_fields()
        self.stack_widget.setCurrentWidget(self.review2)

    def review_page3(self):
        self.review3.populate_fields()
        self.stack_widget.setCurrentWidget(self.review3)

    def review_page4(self):
        self.review4.populate_fields()
        self.stack_widget.setCurrentWidget(self.review4)

    def open_dashboardmenu(self):
        from DashboardMenu import DbMenuWindow as RecordWindow
        self.main_window = RecordWindow()

        # Pass the juv_id to filter records
        if hasattr(self.enrollment_data, 'juv_id') and self.enrollment_data.juv_id:
            self.main_window.show_page("records", filter_juv_id=self.enrollment_data.juv_id)
        else:
            self.main_window.show_page("records")
        
        self.main_window.show()
        self.close()

    def restart_enrollment(self):
        self.enrollment_data.reset_facial_only()
        self.stack_widget.setCurrentWidget(self.personalinfo)

    def save_to_database(self):
        try:

            conn = get_db_connection()
            cursor = conn.cursor()

            # Insert into JUVENILE_PROFILE
            cursor.execute("""
                INSERT INTO JUVENILE_PROFILE 
                (JUV_LNAME, JUV_FNAME, JUV_MNAME, JUV_SUFFIX, JUV_SEX, JUV_GENDER, 
                JUV_AGE, JUV_DOB, JUV_PLACE_OF_BIRTH, JUV_CITIZENSHIP, 
                JUV_STATE_PROVINCE, JUV_MUNICIPALITY, JUV_BARANGAY, JUV_STREET)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING JUV_ID
            """, (
                self.enrollment_data.personal_info['lname'],
                self.enrollment_data.personal_info['fname'],
                self.enrollment_data.personal_info['mname'],
                self.enrollment_data.personal_info['suffix'],
                self.enrollment_data.personal_info['sex'],
                self.enrollment_data.personal_info['gender'],
                int(self.enrollment_data.personal_info['age']) if self.enrollment_data.personal_info['age'] else None,
                self.enrollment_data.personal_info['dob'],
                self.enrollment_data.personal_info['birthplace'],
                self.enrollment_data.personal_info['citizenship'],
                self.enrollment_data.personal_info['state'],
                self.enrollment_data.personal_info['municipal'],
                self.enrollment_data.personal_info['brgy'],
                self.enrollment_data.personal_info['street']
            ))

            juv_id = cursor.fetchone()[0]
            
            # Store juv_id in enrollment_data for later use
            self.enrollment_data.juv_id = juv_id

            # Insert into JUVENILE_GUARDIAN_PROFILE
            cursor.execute("""
                INSERT INTO JUVENILE_GUARDIAN_PROFILE 
                (GRDN_FULL_NAME, GRDN_JUV_RELATIONSHIP, GRDN_SEX, GRDN_DOB, GRDN_AGE, 
                GRDN_CIVIL_STATUS, GRDN_CITIZENSHIP, GRDN_OCCUPATION, GRDN_EMAIL_ADDRESS, 
                GRDN_CONTACT_NO, GRDN_RESIDENTIAL_ADDRESS, JUV_ID)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                self.enrollment_data.parent_info['fullname'],
                self.enrollment_data.parent_info['relationship'],
                self.enrollment_data.parent_info['sex'],
                self.enrollment_data.parent_info['dob'],
                int(self.enrollment_data.parent_info['age']) if self.enrollment_data.parent_info['age'] else None,
                self.enrollment_data.parent_info['civil_status'],
                self.enrollment_data.parent_info['citizenship'],
                self.enrollment_data.parent_info['occupation'],
                self.enrollment_data.parent_info['email'],
                self.enrollment_data.parent_info['contact'],
                self.enrollment_data.parent_info['address'],
                juv_id
            ))

            # Insert into OFFENSE_INFORMATION
            cursor.execute("""
                INSERT INTO OFFENSE_INFORMATION 
                (OFFNS_TYPE, OFFNS_CASE_RECORD_NO, OFFNS_DATE_TIME, OFFNS_LOCATION, 
                OFFNS_DESCRIPTION, OFFNS_COMPLAINANT, OFFNS_BARANGAY_OFFICER_IN_CHARGE, JUV_ID)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                self.enrollment_data.offense_info['offense_type'],
                self.enrollment_data.offense_info['case_no'],
                self.enrollment_data.offense_info['datetime'],
                self.enrollment_data.offense_info['location'],
                self.enrollment_data.offense_info['description'],
                self.enrollment_data.offense_info['complainant'],
                self.enrollment_data.offense_info['officer'],
                juv_id
            ))

            # Insert into FACIAL_DATA
            cursor.execute("""
                INSERT INTO FACIAL_DATA 
                (FACE_IMAGE, EMBEDDING, JUV_ID)
                VALUES (%s, %s, %s)
            """, (
                psycopg2.Binary(self.enrollment_data.facial_data['image']),
                self.enrollment_data.facial_data['embedding'],
                juv_id
            ))

            conn.commit()
            cursor.close()
            conn.close()

            # Show success message
            QMessageBox.information(self, "Success", "Record successfully saved to database!")

            # Note: Don't reset here - we need juv_id for filtering

        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to save data: {str(e)}")
            print(f"Database error: {e}")

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


class PersonalInfo(QWidget):
    switch_to_parent = pyqtSignal()

    def __init__(self, enrollment_data, parent=None):
        super().__init__()
        uic.loadUi("ui/enroll-personalinfo.ui", self)
        self.load_fonts()
        self.enrollment_data = enrollment_data

        # Get UI elements
        self.lname_line = self.findChild(QLineEdit, "lname_line")
        self.fname_line = self.findChild(QLineEdit, "fname_line")
        self.mname_line = self.findChild(QLineEdit, "mname_line")
        self.suffix_line = self.findChild(QLineEdit, "suffix_line")
        self.age_line = self.findChild(QLineEdit, "age_line")
        self.birthplace_line = self.findChild(QLineEdit, "birthplace_line")
        self.citizenship_line = self.findChild(QLineEdit, "citizenship_line")
        self.state_line = self.findChild(QLineEdit, "state_line")
        self.municipal_line = self.findChild(QLineEdit, "municipal_line")
        self.brgy_line = self.findChild(QLineEdit, "brgy_line")
        self.st_line = self.findChild(QLineEdit, "st_line")

        self.sex_combo = self.findChild(QComboBox, "sex_combo")
        self.gender_combo = self.findChild(QComboBox, "gender_combo")
        self.dob_date = self.findChild(QDateEdit, "dob_date")

        # Next button
        self.next_btn = self.findChild(QPushButton, "nxt_btn")
        if self.next_btn:
            self.next_btn.clicked.connect(self.save_and_continue)

    def save_and_continue(self):
        # Validate required fields
        missing_fields = []

        if self.lname_line and not self.lname_line.text().strip():
            missing_fields.append('Last Name')
        if self.fname_line and not self.fname_line.text().strip():
            missing_fields.append('First Name')
        if self.sex_combo and (not self.sex_combo.currentText() or self.sex_combo.currentText() == "Select"):
            missing_fields.append('Sex')
        if self.dob_date and not self.dob_date.date():
            missing_fields.append('Date of Birth')
        if self.age_line and not self.age_line.text().strip():
            missing_fields.append('Age')
        if self.birthplace_line and not self.birthplace_line.text().strip():
            missing_fields.append('Place of Birth')
        if self.citizenship_line and not self.citizenship_line.text().strip():
            missing_fields.append('Citizenship')
        if self.state_line and not self.state_line.text().strip():
            missing_fields.append('State/Province')
        if self.municipal_line and not self.municipal_line.text().strip():
            missing_fields.append('Municipality')
        if self.brgy_line and not self.brgy_line.text().strip():
            missing_fields.append('Barangay')

        # Validate age is positive if provided
        if self.age_line and self.age_line.text().strip():
            try:
                age = int(self.age_line.text().strip())
                if age <= 0:
                    QMessageBox.warning(self, "Invalid Age", "Age must be a positive number.")
                    return
            except ValueError:
                QMessageBox.warning(self, "Invalid Age", "Please enter a valid number for age.")
                return

        if missing_fields:
            QMessageBox.warning(
                self,
                "Required Fields Missing",
                f"Please fill in the following required fields:\n\n" + "\n".join(
                    f"• {field}" for field in missing_fields)
            )
            return

        # Save data
        self.enrollment_data.personal_info['lname'] = self.lname_line.text().strip() if self.lname_line else ''
        self.enrollment_data.personal_info['fname'] = self.fname_line.text().strip() if self.fname_line else ''
        self.enrollment_data.personal_info['mname'] = self.mname_line.text().strip() if self.mname_line else ''
        self.enrollment_data.personal_info['suffix'] = self.suffix_line.text().strip() if self.suffix_line else ''
        self.enrollment_data.personal_info['age'] = self.age_line.text().strip() if self.age_line else ''
        self.enrollment_data.personal_info[
            'birthplace'] = self.birthplace_line.text().strip() if self.birthplace_line else ''
        self.enrollment_data.personal_info[
            'citizenship'] = self.citizenship_line.text().strip() if self.citizenship_line else ''
        self.enrollment_data.personal_info['state'] = self.state_line.text().strip() if self.state_line else ''
        self.enrollment_data.personal_info[
            'municipal'] = self.municipal_line.text().strip() if self.municipal_line else ''
        self.enrollment_data.personal_info['brgy'] = self.brgy_line.text().strip() if self.brgy_line else ''
        self.enrollment_data.personal_info['street'] = self.st_line.text().strip() if self.st_line else ''

        self.enrollment_data.personal_info['sex'] = self.sex_combo.currentText() if self.sex_combo else ''
        self.enrollment_data.personal_info['gender'] = self.gender_combo.currentText() if self.gender_combo else ''
        self.enrollment_data.personal_info['dob'] = self.dob_date.date().toPyDate() if self.dob_date else None

        self.switch_to_parent.emit()

        # Save data
        self.enrollment_data.personal_info['lname'] = self.lname_line.text().strip() if self.lname_line else ''
        self.enrollment_data.personal_info['fname'] = self.fname_line.text().strip() if self.fname_line else ''
        self.enrollment_data.personal_info['mname'] = self.mname_line.text().strip() if self.mname_line else ''
        self.enrollment_data.personal_info['suffix'] = self.suffix_line.text().strip() if self.suffix_line else ''
        self.enrollment_data.personal_info['age'] = self.age_line.text().strip() if self.age_line else ''
        self.enrollment_data.personal_info[
            'birthplace'] = self.birthplace_line.text().strip() if self.birthplace_line else ''
        self.enrollment_data.personal_info[
            'citizenship'] = self.citizenship_line.text().strip() if self.citizenship_line else ''
        self.enrollment_data.personal_info['state'] = self.state_line.text().strip() if self.state_line else ''
        self.enrollment_data.personal_info[
            'municipal'] = self.municipal_line.text().strip() if self.municipal_line else ''
        self.enrollment_data.personal_info['brgy'] = self.brgy_line.text().strip() if self.brgy_line else ''
        self.enrollment_data.personal_info['street'] = self.st_line.text().strip() if self.st_line else ''

        self.enrollment_data.personal_info['sex'] = self.sex_combo.currentText() if self.sex_combo else ''
        self.enrollment_data.personal_info['gender'] = self.gender_combo.currentText() if self.gender_combo else ''
        self.enrollment_data.personal_info['dob'] = self.dob_date.date().toPyDate() if self.dob_date else None

        self.switch_to_parent.emit()

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


class ParentInfo(QWidget):
    switch_to_offense = pyqtSignal()

    def __init__(self, enrollment_data, parent=None):
        super().__init__()
        uic.loadUi("ui/enroll-parentinfo.ui", self)
        self.load_fonts()
        self.enrollment_data = enrollment_data

        # Get UI elements
        self.fullname_line = self.findChild(QLineEdit, "fullname_line")
        self.rs_line = self.findChild(QLineEdit, "rs_line")
        self.age_line = self.findChild(QLineEdit, "age_line")
        self.civilsts_line = self.findChild(QLineEdit, "civilsts_line")
        self.citizenship_line = self.findChild(QLineEdit, "citizenship_line")
        self.occu_line = self.findChild(QLineEdit, "occu_line")
        self.email_line = self.findChild(QLineEdit, "email_line")
        self.contact_line = self.findChild(QLineEdit, "contact_line")
        self.address_line = self.findChild(QLineEdit, "address_line")

        self.sex_combo = self.findChild(QComboBox, "sex_combo")
        self.dob_date = self.findChild(QDateEdit, "dob_date")

        # Next button
        self.next_btn = self.findChild(QPushButton, "nxt_btn")
        if self.next_btn:
            self.next_btn.clicked.connect(self.save_and_continue)

    def save_and_continue(self):
        # Validate required fields
        missing_fields = []

        if self.fullname_line and not self.fullname_line.text().strip():
            missing_fields.append('Full Name')
        if self.rs_line and not self.rs_line.text().strip():
            missing_fields.append('Relationship to Juvenile')
        if self.sex_combo and (not self.sex_combo.currentText() or self.sex_combo.currentText() == "Select"):
            missing_fields.append('Sex')
        if self.contact_line and not self.contact_line.text().strip():
            missing_fields.append('Contact Number')
        if self.address_line and not self.address_line.text().strip():
            missing_fields.append('Residential Address')
        if self.citizenship_line and not self.citizenship_line.text().strip():
            missing_fields.append('Citizenship')

        if missing_fields:
            QMessageBox.warning(
                self,
                "Required Fields Missing",
                f"Please fill in the following required fields:\n\n" + "\n".join(
                    f"• {field}" for field in missing_fields)
            )
            return

        # Validate age if provided
        if self.age_line and self.age_line.text().strip():
            try:
                age = int(self.age_line.text().strip())
                if age <= 0:
                    QMessageBox.warning(self, "Invalid Age", "Age must be a positive number.")
                    return
            except ValueError:
                QMessageBox.warning(self, "Invalid Age", "Please enter a valid number for age.")
                return

        # Validate email format if provided
        if self.email_line and self.email_line.text().strip():
            email = self.email_line.text().strip()
            if '@' not in email or '.' not in email.split('@')[-1]:
                QMessageBox.warning(self, "Invalid Email", "Please enter a valid email address.")
                return
            
            from ValidationUtils import check_email_exists
            if check_email_exists(email):
                QMessageBox.warning(
                    self, 
                    "Duplicate Email", 
                    f"The email '{email}' is already registered in the system.\n\n"
                    "Please use a different email address."
                )
                return

        # Save data
        self.enrollment_data.parent_info['fullname'] = self.fullname_line.text().strip() if self.fullname_line else ''
        self.enrollment_data.parent_info['relationship'] = self.rs_line.text().strip() if self.rs_line else ''
        self.enrollment_data.parent_info['age'] = self.age_line.text().strip() if self.age_line else ''
        self.enrollment_data.parent_info[
            'civil_status'] = self.civilsts_line.text().strip() if self.civilsts_line else ''
        self.enrollment_data.parent_info[
            'citizenship'] = self.citizenship_line.text().strip() if self.citizenship_line else ''
        self.enrollment_data.parent_info['occupation'] = self.occu_line.text().strip() if self.occu_line else ''
        self.enrollment_data.parent_info['email'] = self.email_line.text().strip() if self.email_line else ''
        self.enrollment_data.parent_info['contact'] = self.contact_line.text().strip() if self.contact_line else ''
        self.enrollment_data.parent_info['address'] = self.address_line.text().strip() if self.address_line else ''

        self.enrollment_data.parent_info['sex'] = self.sex_combo.currentText() if self.sex_combo else ''
        self.enrollment_data.parent_info['dob'] = self.dob_date.date().toPyDate() if self.dob_date else None

        self.switch_to_offense.emit()

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


class OffenseInfo(QWidget):
    switch_to_bio = pyqtSignal()

    def __init__(self, enrollment_data, parent=None):
        super().__init__()
        uic.loadUi("ui/enroll-offenseinfo.ui", self)
        self.load_fonts()
        self.enrollment_data = enrollment_data

        # Get UI elements
        self.offensetype_line = self.findChild(QLineEdit, "offensetype_line")
        self.caseno_line = self.findChild(QLineEdit, "caseno_line")
        self.location_line = self.findChild(QLineEdit, "location_line")
        self.complainant_line = self.findChild(QLineEdit, "complainant_line")
        self.officer_line = self.findChild(QLineEdit, "officer_line")

        self.datetime_dt = self.findChild(QDateTimeEdit, "datetime_dt")
        self.desc_text = self.findChild(QTextEdit, "desc_text")

        # Set default datetime to now
        if self.datetime_dt:
            self.datetime_dt.setDateTime(QDateTime.currentDateTime())

        # Next button
        self.next_btn = self.findChild(QPushButton, "nxt_btn")
        if self.next_btn:
            self.next_btn.clicked.connect(self.save_and_continue)

    def save_and_continue(self):
        # Validate required fields
        missing_fields = []

        if self.offensetype_line and not self.offensetype_line.text().strip():
            missing_fields.append('Offense Type')
        if self.location_line and not self.location_line.text().strip():
            missing_fields.append('Location')
        if self.complainant_line and not self.complainant_line.text().strip():
            missing_fields.append('Complainant')
        if self.officer_line and not self.officer_line.text().strip():
            missing_fields.append('Barangay Officer in Charge')
        if self.desc_text and not self.desc_text.toPlainText().strip():
            missing_fields.append('Description of Incident')

        if missing_fields:
            QMessageBox.warning(
                self,
                "Required Fields Missing",
                f"Please fill in the following required fields:\n\n" + "\n".join(
                    f"• {field}" for field in missing_fields)
            )
            return

        # Save data
        self.enrollment_data.offense_info[
            'offense_type'] = self.offensetype_line.text().strip() if self.offensetype_line else ''
        self.enrollment_data.offense_info['case_no'] = self.generate_case_number()
        self.enrollment_data.offense_info['location'] = self.location_line.text().strip() if self.location_line else ''
        self.enrollment_data.offense_info[
            'complainant'] = self.complainant_line.text().strip() if self.complainant_line else ''
        self.enrollment_data.offense_info['officer'] = self.officer_line.text().strip() if self.officer_line else ''

        self.enrollment_data.offense_info[
            'datetime'] = self.datetime_dt.dateTime().toPyDateTime() if self.datetime_dt else datetime.now()
        self.enrollment_data.offense_info[
            'description'] = self.desc_text.toPlainText().strip() if self.desc_text else ''

        self.switch_to_bio.emit()

    def generate_case_number(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get the latest case number
            cursor.execute("SELECT OFFNS_CASE_RECORD_NO FROM OFFENSE_INFORMATION ORDER BY OFFNS_ID DESC LIMIT 1")
            result = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if result:
                last_case = result[0]
                parts = last_case.split('-')
                if len(parts) == 2:
                    number = int(parts[1]) + 1
                    new_case_no = f"10-{number:04d}"
                    
                    from ValidationUtils import check_case_number_exists
                    while check_case_number_exists(new_case_no):
                        number += 1
                        new_case_no = f"10-{number:04d}"
                    return new_case_no
        
            # Default first case number
            return "10-0001"
            
        except Exception as e:
            print(f"Error generating case number: {e}")
            return "10-0001"
        
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


class BioInfo(QWidget):
    switch_to_facescan = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__()
        uic.loadUi("ui/enroll-biometrics.ui", self)
        self.load_fonts()

        # Start face scan button
        self.start_btn = self.findChild(QPushButton, "start_btn")
        if self.start_btn:
            self.start_btn.clicked.connect(self.go_to_facescan)

    def go_to_facescan(self):
        self.switch_to_facescan.emit()

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


class FaceScan(QDialog):
    scan_completed = pyqtSignal()

    def __init__(self, parent=None, enrollment_data=None):
        super().__init__(parent)
        uic.loadUi("ui/enroll-facescan.ui", self)
        self.load_fonts()
        self.enrollment_data = enrollment_data

        self.layout = QVBoxLayout(self)
        self.video_label = QLabel(self)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.video_label)

        self.face_label = self.findChild(QLabel, "face_label")

        # Find the existing status label from UI
        self.status_label = self.findChild(QLabel, "label")

        # Load face detector (Haar cascade for simplicity)
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

        # Prioritize using webcam for face scan if plugged in
        camera_indices = [1, 2, 0]
        self.cap = None
        for index in camera_indices:
            print(f"Trying camera index {index}...")
            cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
            if not cap.isOpened():
                cap = cv2.VideoCapture(index)
            if cap.isOpened():
                ret, test_frame = cap.read()
                if ret and test_frame is not None:
                    print(f"Camera index {index} is working. Using it.")
                    self.cap = cap
                    break
                else:
                    cap.release()
                    print(f"Camera index {index} opened but failed to read frame. Skipping.")
            else:
                print(f"Failed to open camera index {index}.")

        if self.cap is None:
            print("No working camera found. Check connections and permissions.")
            return

        # Set camera properties to avoid resolution/format mismatches
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)

        # Timer for video feed
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

        # Timer for auto-capture; starts when face is detected
        self.capture_timer = QTimer(self)
        self.capture_timer.setSingleShot(True)
        self.capture_timer.timeout.connect(self.capture_and_save)

        # Countdown timer for visual feedback (updates every second)
        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self.update_countdown)
        self.countdown_value = 0

        self.face_detected = False
        self.captured_frame = None

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        # Convert to grayscale for detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect faces
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        # Check if a face is in the center
        frame_center_x, frame_center_y = frame.shape[1] // 2, frame.shape[0] // 2
        tolerance = 0.2  # 20% tolerance
        face_in_center = False
        for (x, y, w, h) in faces:
            face_center_x = x + w // 2
            face_center_y = y + h // 2
            if (abs(face_center_x - frame_center_x) < tolerance * frame_center_x and
                    abs(face_center_y - frame_center_y) < tolerance * frame_center_y):
                face_in_center = True
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                break  # Only consider the first detected face

        # Update status and timer based on detection
        if face_in_center:
            if not self.face_detected:
                self.face_detected = True
                if self.status_label:
                    self.status_label.setText("Face detected! Scanning in 3 seconds...")
                self.countdown_value = 3
                self.countdown_timer.start(1000)  # Update every 1 second
                self.capture_timer.start(3000)
        else:
            if self.face_detected:
                self.face_detected = False
                if self.status_label:
                    self.status_label.setText("Position your face at the center for face scan")
                self.capture_timer.stop()
                self.countdown_timer.stop()

        # Store current frame
        self.captured_frame = frame.copy()

        # Crop to square, centered
        h, w, ch = frame.shape
        if w > h:
            start_x = (w - h) // 2
            cropped = frame[:, start_x:start_x + h]
        else:
            start_y = (h - w) // 2
            cropped = frame[start_y:start_y + w, :]

        cropped = cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB)
        h_c, w_c, ch_c = cropped.shape
        qt_image = QImage(cropped.data, w_c, h_c, ch_c * w_c, QImage.Format_RGB888)

        if self.face_label:
            self.face_label.setPixmap(QPixmap.fromImage(qt_image).scaled(
                self.face_label.width(), self.face_label.height()
            ))

    def update_countdown(self):
        if self.countdown_value > 0:
            if self.status_label:
                self.status_label.setText(f"Scanning in {self.countdown_value}...")
            self.countdown_value -= 1
        else:
            self.countdown_timer.stop()

    def capture_and_save(self):
        ret, frame = self.cap.read()
        if ret and self.enrollment_data:
            if self.status_label:
                self.status_label.setText("Processing face... Please wait.")

            # Generate embedding
            embedding = self.generate_embedding(frame)

            if embedding is None:
                QMessageBox.warning(self, "Face Detection Error",
                                    "Could not detect or encode face clearly. Please try again.")
                self.face_detected = False
                if self.status_label:
                    self.status_label.setText("Position your face at the center for face scan")
                return
            
            from ValidationUtils import check_embedding_similarity
            exists, juv_id = check_embedding_similarity(embedding, threshold=0.4)
            
            if exists:
                reply = QMessageBox.question(
                    self,
                    "Duplicate Face Detected",
                    f"This face appears to be already registered in the system (JUV_ID: {juv_id}).\n\n"
                    "Are you sure you want to continue enrolling this person again?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.No:
                    self.face_detected = False
                    if self.status_label:
                        self.status_label.setText("Position your face at the center for face scan")
                    return
            
            is_success, buffer = cv2.imencode(".jpg", frame)
            if is_success:
                image_bytes = buffer.tobytes()

                # Save to temporary storage
                self.enrollment_data.facial_data['image'] = image_bytes
                self.enrollment_data.facial_data['embedding'] = embedding

                print("Photo captured and saved to temporary storage.")
                print(f"Embedding generated successfully with {len(eval(embedding))} dimensions")
                self.scan_completed.emit()
                self.accept()
            else:
                print("Failed to encode frame.")
        else:
            print("Failed to capture frame.")

    def generate_embedding(self, frame):
        try:
            import face_recognition

            if self.status_label:
                self.status_label.setText("Processing face... Please wait.")

            # Validate frame FIRST
            if frame is None or frame.size == 0:
                print("Invalid frame: empty or None")
                return None
            
            # Ensure frame is in correct format (uint8)
            if frame.dtype != np.uint8:
                print(f"Converting frame from {frame.dtype} to uint8")
                frame = frame.astype(np.uint8)
            
            # Ensure frame has 3 channels (BGR)
            if len(frame.shape) != 3 or frame.shape[2] != 3:
                print(f"Invalid frame shape: {frame.shape}")
                return None

            # Convert BGR to RGB (OpenCV uses BGR, face_recognition needs RGB)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Double-check RGB frame
            if rgb_frame.dtype != np.uint8:
                rgb_frame = rgb_frame.astype(np.uint8)

            # Get face encodings (128-dimension vector)
            face_encodings = face_recognition.face_encodings(rgb_frame)

            if len(face_encodings) == 0:
                print("No face detected for embedding generation")
                return None

            # Get the first face encoding
            embedding = face_encodings[0]

            # Convert to string for database storage
            return str(embedding.tolist())

        except Exception as e:
            print(f"Error generating face embedding: {e}")
            import traceback
            traceback.print_exc()
            return None
        
    def closeEvent(self, event):
        if self.cap:
            self.cap.release()
        super().closeEvent(event)

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


class ReviewPersonalInfo(QWidget):
    switch_to_review2 = pyqtSignal()
    switch_to_personalinfo = pyqtSignal()

    def __init__(self, enrollment_data, parent=None):
        super().__init__()
        uic.loadUi("ui/review-personalinfo.ui", self)
        self.load_fonts()
        self.enrollment_data = enrollment_data

        # Get UI elements
        self.lname = self.findChild(QLineEdit, "lname")
        self.fname = self.findChild(QLineEdit, "fname")
        self.mname = self.findChild(QLineEdit, "mname")
        self.suffix = self.findChild(QLineEdit, "suffix")
        self.age = self.findChild(QLineEdit, "age")
        self.birthplace = self.findChild(QLineEdit, "birthplace")
        self.citizenship = self.findChild(QLineEdit, "citizenship")
        self.province = self.findChild(QLineEdit, "province")
        self.municipality = self.findChild(QLineEdit, "municipality")
        self.barangay = self.findChild(QLineEdit, "barangay")
        self.street = self.findChild(QLineEdit, "street")

        self.sexcombo = self.findChild(QComboBox, "sexcombo")
        self.gendercombo = self.findChild(QComboBox, "gendercombo")
        self.dobdate = self.findChild(QDateEdit, "dobdate")

        # Next button
        self.next_btn = self.findChild(QPushButton, "next_button")
        if self.next_btn:
            self.next_btn.clicked.connect(self.update_and_continue)

        # Cancel button
        self.cancel_btn = self.findChild(QPushButton, "cancel_btn")
        if self.cancel_btn:
            self.cancel_btn.clicked.connect(self.go_to_personalinfo)

    def populate_fields(self):
        if self.lname:
            self.lname.setText(self.enrollment_data.personal_info['lname'])
        if self.fname:
            self.fname.setText(self.enrollment_data.personal_info['fname'])
        if self.mname:
            self.mname.setText(self.enrollment_data.personal_info['mname'])
        if self.suffix:
            self.suffix.setText(self.enrollment_data.personal_info['suffix'])
        if self.age:
            self.age.setText(self.enrollment_data.personal_info['age'])
        if self.birthplace:
            self.birthplace.setText(self.enrollment_data.personal_info['birthplace'])
        if self.citizenship:
            self.citizenship.setText(self.enrollment_data.personal_info['citizenship'])
        if self.province:
            self.province.setText(self.enrollment_data.personal_info['state'])
        if self.municipality:
            self.municipality.setText(self.enrollment_data.personal_info['municipal'])
        if self.barangay:
            self.barangay.setText(self.enrollment_data.personal_info['brgy'])
        if self.street:
            self.street.setText(self.enrollment_data.personal_info['street'])

        if self.sexcombo and self.enrollment_data.personal_info['sex']:
            index = self.sexcombo.findText(self.enrollment_data.personal_info['sex'])
            if index >= 0:
                self.sexcombo.setCurrentIndex(index)

        if self.gendercombo and self.enrollment_data.personal_info['gender']:
            index = self.gendercombo.findText(self.enrollment_data.personal_info['gender'])
            if index >= 0:
                self.gendercombo.setCurrentIndex(index)

        if self.dobdate and self.enrollment_data.personal_info['dob']:
            self.dobdate.setDate(QDate(self.enrollment_data.personal_info['dob']))

    def update_and_continue(self):
        # Update temporary data with any changes and continue
        if self.lname:
            self.enrollment_data.personal_info['lname'] = self.lname.text()
        if self.fname:
            self.enrollment_data.personal_info['fname'] = self.fname.text()
        if self.mname:
            self.enrollment_data.personal_info['mname'] = self.mname.text()
        if self.suffix:
            self.enrollment_data.personal_info['suffix'] = self.suffix.text()
        if self.age:
            self.enrollment_data.personal_info['age'] = self.age.text()
        if self.birthplace:
            self.enrollment_data.personal_info['birthplace'] = self.birthplace.text()
        if self.citizenship:
            self.enrollment_data.personal_info['citizenship'] = self.citizenship.text()
        if self.province:
            self.enrollment_data.personal_info['state'] = self.province.text()
        if self.municipality:
            self.enrollment_data.personal_info['municipal'] = self.municipality.text()
        if self.barangay:
            self.enrollment_data.personal_info['brgy'] = self.barangay.text()
        if self.street:
            self.enrollment_data.personal_info['street'] = self.street.text()

        if self.sexcombo:
            self.enrollment_data.personal_info['sex'] = self.sexcombo.currentText()
        if self.gendercombo:
            self.enrollment_data.personal_info['gender'] = self.gendercombo.currentText()
        if self.dobdate:
            self.enrollment_data.personal_info['dob'] = self.dobdate.date().toPyDate()

        self.switch_to_review2.emit()

    def go_to_personalinfo(self):
        self.switch_to_personalinfo.emit()

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


class ReviewParentInfo(QWidget):
    switch_to_review3 = pyqtSignal()
    switch_to_review1 = pyqtSignal()
    switch_to_personalinfo = pyqtSignal()

    def __init__(self, enrollment_data, parent=None):
        super().__init__()
        uic.loadUi("ui/review-parentinfo.ui", self)
        self.load_fonts()
        self.enrollment_data = enrollment_data

        # Get UI elements
        self.fullname_line = self.findChild(QLineEdit, "fullname_line")
        self.rs_line = self.findChild(QLineEdit, "rs_line")
        self.age_line = self.findChild(QLineEdit, "age_line")
        self.civilsts_line = self.findChild(QLineEdit, "civilsts_line")
        self.citizenship_line = self.findChild(QLineEdit, "citizenship_line")
        self.occu_line = self.findChild(QLineEdit, "occu_line")
        self.email_line = self.findChild(QLineEdit, "email_line")
        self.contact_line = self.findChild(QLineEdit, "contact_line")
        self.address_line = self.findChild(QLineEdit, "address_line")

        self.sex_combo = self.findChild(QComboBox, "sex_combo")
        self.dob_date = self.findChild(QDateEdit, "dob_date")

        # Buttons
        self.next_btn = self.findChild(QPushButton, "next_button")
        if self.next_btn:
            self.next_btn.clicked.connect(self.update_and_continue)

        self.prev_btn = self.findChild(QPushButton, "previous_btn")
        if self.prev_btn:
            self.prev_btn.clicked.connect(self.go_to_review1)

        self.cancel_btn = self.findChild(QPushButton, "cancel_btn")
        if self.cancel_btn:
            self.cancel_btn.clicked.connect(self.go_to_personalinfo)

    def populate_fields(self):
        if self.fullname_line:
            self.fullname_line.setText(self.enrollment_data.parent_info['fullname'])
        if self.rs_line:
            self.rs_line.setText(self.enrollment_data.parent_info['relationship'])
        if self.age_line:
            self.age_line.setText(self.enrollment_data.parent_info['age'])
        if self.civilsts_line:
            self.civilsts_line.setText(self.enrollment_data.parent_info['civil_status'])
        if self.citizenship_line:
            self.citizenship_line.setText(self.enrollment_data.parent_info['citizenship'])
        if self.occu_line:
            self.occu_line.setText(self.enrollment_data.parent_info['occupation'])
        if self.email_line:
            self.email_line.setText(self.enrollment_data.parent_info['email'])
        if self.contact_line:
            self.contact_line.setText(self.enrollment_data.parent_info['contact'])
        if self.address_line:
            self.address_line.setText(self.enrollment_data.parent_info['address'])

        if self.sex_combo and self.enrollment_data.parent_info['sex']:
            index = self.sex_combo.findText(self.enrollment_data.parent_info['sex'])
            if index >= 0:
                self.sex_combo.setCurrentIndex(index)

        if self.dob_date and self.enrollment_data.parent_info['dob']:
            self.dob_date.setDate(QDate(self.enrollment_data.parent_info['dob']))

    def update_and_continue(self):
        if self.email_line:
            new_email = self.email_line.text().strip()
            old_email = self.enrollment_data.parent_info['email']
            
            # Only check if email changed and is not empty
            if new_email and new_email != old_email:
                # Validate format
                if '@' not in new_email or '.' not in new_email.split('@')[-1]:
                    QMessageBox.warning(self, "Invalid Email", "Please enter a valid email address.")
                    return
                
                # Check if exists
                from ValidationUtils import check_email_exists
                if check_email_exists(new_email):
                    QMessageBox.warning(
                        self, 
                        "Duplicate Email", 
                        f"The email '{new_email}' is already registered in the system.\n\n"
                        "Please use a different email address."
                    )
                    return
            
        if self.fullname_line:
            self.enrollment_data.parent_info['fullname'] = self.fullname_line.text()
        if self.rs_line:
            self.enrollment_data.parent_info['relationship'] = self.rs_line.text()
        if self.age_line:
            self.enrollment_data.parent_info['age'] = self.age_line.text()
        if self.civilsts_line:
            self.enrollment_data.parent_info['civil_status'] = self.civilsts_line.text()
        if self.citizenship_line:
            self.enrollment_data.parent_info['citizenship'] = self.citizenship_line.text()
        if self.occu_line:
            self.enrollment_data.parent_info['occupation'] = self.occu_line.text()
        if self.email_line:
            self.enrollment_data.parent_info['email'] = self.email_line.text()
        if self.contact_line:
            self.enrollment_data.parent_info['contact'] = self.contact_line.text()
        if self.address_line:
            self.enrollment_data.parent_info['address'] = self.address_line.text()

        if self.sex_combo:
            self.enrollment_data.parent_info['sex'] = self.sex_combo.currentText()
        if self.dob_date:
            self.enrollment_data.parent_info['dob'] = self.dob_date.date().toPyDate()

        self.switch_to_review3.emit()

    def go_to_review1(self):
        self.switch_to_review1.emit()

    def go_to_personalinfo(self):
        self.switch_to_personalinfo.emit()

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


class ReviewOffenseInfo(QWidget):
    switch_to_review4 = pyqtSignal()
    switch_to_review2 = pyqtSignal()
    switch_to_personalinfo = pyqtSignal()

    def __init__(self, enrollment_data, parent=None):
        super().__init__()
        uic.loadUi("ui/review-offenseinfo.ui", self)
        self.load_fonts()
        self.enrollment_data = enrollment_data

        # Get UI elements
        self.offensetype_line = self.findChild(QLineEdit, "offensetype_line")
        self.caseno_line = self.findChild(QLineEdit, "caseno_line")
        self.location_line = self.findChild(QLineEdit, "location_line")
        self.complainant_line = self.findChild(QLineEdit, "complainant_line")
        self.officer_line = self.findChild(QLineEdit, "officer_line")

        self.datetime_dt = self.findChild(QDateTimeEdit, "datetime_dt")
        self.desc_text = self.findChild(QTextEdit, "desc_text")

        # Buttons
        self.next_btn = self.findChild(QPushButton, "next_button")
        if self.next_btn:
            self.next_btn.clicked.connect(self.update_and_continue)

        self.prev_btn = self.findChild(QPushButton, "prevbtn")
        if self.prev_btn:
            self.prev_btn.clicked.connect(self.go_to_review2)

        self.cancel_btn = self.findChild(QPushButton, "cancelbtn")
        if self.cancel_btn:
            self.cancel_btn.clicked.connect(self.go_to_personalinfo)

    def populate_fields(self):
        if self.offensetype_line:
            self.offensetype_line.setText(self.enrollment_data.offense_info['offense_type'])
        if self.caseno_line:
            self.caseno_line.setText(self.enrollment_data.offense_info['case_no'])
            self.caseno_line.setReadOnly(True)  # Case number should not be edited
        if self.location_line:
            self.location_line.setText(self.enrollment_data.offense_info['location'])
        if self.complainant_line:
            self.complainant_line.setText(self.enrollment_data.offense_info['complainant'])
        if self.officer_line:
            self.officer_line.setText(self.enrollment_data.offense_info['officer'])

        if self.datetime_dt and self.enrollment_data.offense_info['datetime']:
            self.datetime_dt.setDateTime(QDateTime(self.enrollment_data.offense_info['datetime']))

        if self.desc_text:
            self.desc_text.setPlainText(self.enrollment_data.offense_info['description'])

    def update_and_continue(self):
        if self.offensetype_line:
            self.enrollment_data.offense_info['offense_type'] = self.offensetype_line.text()
        # Case number is not updated as it's auto-generated
        if self.location_line:
            self.enrollment_data.offense_info['location'] = self.location_line.text()
        if self.complainant_line:
            self.enrollment_data.offense_info['complainant'] = self.complainant_line.text()
        if self.officer_line:
            self.enrollment_data.offense_info['officer'] = self.officer_line.text()

        if self.datetime_dt:
            self.enrollment_data.offense_info['datetime'] = self.datetime_dt.dateTime().toPyDateTime()
        if self.desc_text:
            self.enrollment_data.offense_info['description'] = self.desc_text.toPlainText()

        self.switch_to_review4.emit()

    def go_to_review2(self):
        self.switch_to_review2.emit()

    def go_to_personalinfo(self):
        self.switch_to_personalinfo.emit()

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


class ReviewBioInfo(QWidget):
    switch_to_review3 = pyqtSignal()
    switch_to_personalinfo = pyqtSignal()
    data_submitted = pyqtSignal()
    close_enrollwindow = pyqtSignal()

    def __init__(self, enrollment_data, parent=None):
        super().__init__()
        uic.loadUi("ui/review-biometrics.ui", self)
        self.load_fonts()
        self.enrollment_data = enrollment_data

        # Get UI elements
        self.facescan_lbl = self.findChild(QLabel, "facescan_lbl")

        # Buttons
        self.submit_btn = self.findChild(QPushButton, "submit_btn")
        if self.submit_btn:
            self.submit_btn.clicked.connect(self.submit_data)

        self.prev_btn = self.findChild(QPushButton, "prevbtn")
        if self.prev_btn:
            self.prev_btn.clicked.connect(self.go_to_review3)

        self.cancel_btn = self.findChild(QPushButton, "cancelbtn")
        if self.cancel_btn:
            self.cancel_btn.clicked.connect(self.go_to_personalinfo)

    def populate_fields(self):
        if self.facescan_lbl and self.enrollment_data.facial_data['image']:
            # Convert bytes back to image and display
            nparr = np.frombuffer(self.enrollment_data.facial_data['image'], np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            # Convert to RGB for display
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            h, w, ch = img_rgb.shape
            bytes_per_line = ch * w
            qt_image = QImage(img_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)

            self.facescan_lbl.setPixmap(QPixmap.fromImage(qt_image).scaled(
                self.facescan_lbl.width(),
                self.facescan_lbl.height(),
                Qt.KeepAspectRatio
            ))

    def submit_data(self):
        self.data_submitted.emit()
        self.close_enrollwindow.emit()

    def go_to_review3(self):
        self.switch_to_review3.emit()

    def go_to_personalinfo(self):
        self.switch_to_personalinfo.emit()

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
    ui = Enroll()
    ui.show()

    app.exec_()
