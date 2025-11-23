import sys
import cv2
import psycopg2
import numpy as np
from datetime import datetime
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal, QTimer, QDateTime
from PyQt5.QtGui import QFontDatabase
from PyQt5.QtWidgets import (QWidget, QLineEdit, QMessageBox, QPushButton, 
                             QMainWindow, QStackedWidget, QDateTimeEdit, QTextEdit)
from Db_connection import get_db_connection

class OffenseData:
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.juv_id = None
        self.offense_info = {
            'offense_type': '',
            'case_no': '',
            'datetime': None,
            'location': '',
            'description': '',
            'complainant': '',
            'officer': ''
        }

class AddOffenseWindow(QMainWindow):
    def __init__(self, juv_id):
        super().__init__()
        uic.loadUi("ui/EnrollMainWindow.ui", self)  # Reuse the same main window
        self.load_fonts()
        
        # Initialize temporary data storage with juvenile ID
        self.offense_data = OffenseData()
        self.offense_data.juv_id = juv_id
        
        # Add the stacked widget
        self.stack_widget = QStackedWidget(self)
        uic.loadUi("ui/enroll-stack.ui", self.stack_widget)
        self.stack_widget.move(417, 0)

        # Add the sidebar widget
        self.sidebar_widget = QWidget(self)
        uic.loadUi("ui/enroll-sidebar.ui", self.sidebar_widget)
        self.sidebar_widget.move(0, 0)

        # Create offense pages
        self.offense_info = AddOffenseInfo(self.offense_data)
        self.offense_info.switch_to_review.connect(self.review_offense_page)
        
        self.review_offense = ReviewOffenseInfo2(self.offense_data)
        self.review_offense.switch_to_offense.connect(self.offense_page)
        self.review_offense.data_submitted.connect(self.save_to_database)

        # Add instances to the stacked widget
        self.stack_widget.addWidget(self.offense_info)
        self.stack_widget.addWidget(self.review_offense)

        # Set the initial page to offense information
        self.stack_widget.setCurrentWidget(self.offense_info)

    def offense_page(self):
        self.stack_widget.setCurrentWidget(self.offense_info)

    def review_offense_page(self):
        self.review_offense.populate_fields()
        self.stack_widget.setCurrentWidget(self.review_offense)

    def save_to_database(self):
        try:
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Insert into OFFENSE_INFORMATION
            cursor.execute("""
                INSERT INTO OFFENSE_INFORMATION 
                (OFFNS_TYPE, OFFNS_CASE_RECORD_NO, OFFNS_DATE_TIME, OFFNS_LOCATION, 
                OFFNS_DESCRIPTION, OFFNS_COMPLAINANT, OFFNS_BARANGAY_OFFICER_IN_CHARGE, JUV_ID)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                self.offense_data.offense_info['offense_type'],
                self.offense_data.offense_info['case_no'],
                self.offense_data.offense_info['datetime'],
                self.offense_data.offense_info['location'],
                self.offense_data.offense_info['description'],
                self.offense_data.offense_info['complainant'],
                self.offense_data.offense_info['officer'],
                self.offense_data.juv_id
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            # Show success message
            QMessageBox.information(self, "Success", "New offense record successfully added!")
            
            # Return to menu with filter for this juvenile
            self.return_to_menu()
            
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to save data: {str(e)}")
            print(f"Database error: {e}")

    def return_to_menu(self):
        from DashboardMenu import DbMenuWindow as RecordWindow
        self.main_window = RecordWindow()

        # Pass the juv_id to filter records
        if self.offense_data.juv_id:
            self.main_window.show_page("records", filter_juv_id=self.offense_data.juv_id)
        else:
            self.main_window.show_page("records")
        
        self.main_window.show()
        self.close()
        
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


class AddOffenseInfo(QWidget):
    switch_to_review = pyqtSignal()
    
    def __init__(self, offense_data, parent=None):
        super().__init__()
        uic.loadUi("ui/enroll-offenseinfo.ui", self)
        self.load_fonts()
        self.offense_data = offense_data

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
        
        if missing_fields:
            QMessageBox.warning(
                self,
                "Required Fields Missing",
                f"Please fill in the following required fields:\n\n" + "\n".join(f"• {field}" for field in missing_fields)
            )
            return
        
        # Save data
        self.offense_data.offense_info['offense_type'] = self.offensetype_line.text().strip() if self.offensetype_line else ''
        self.offense_data.offense_info['case_no'] = self.generate_case_number()
        self.offense_data.offense_info['location'] = self.location_line.text().strip() if self.location_line else ''
        self.offense_data.offense_info['complainant'] = self.complainant_line.text().strip() if self.complainant_line else ''
        self.offense_data.offense_info['officer'] = self.officer_line.text().strip() if self.officer_line else ''
        
        self.offense_data.offense_info['datetime'] = self.datetime_dt.dateTime().toPyDateTime() if self.datetime_dt else datetime.now()
        self.offense_data.offense_info['description'] = self.desc_text.toPlainText().strip() if self.desc_text else ''
        
        self.switch_to_review.emit()

    def generate_case_number(self):
        #Generate unique case number in format 10-0001
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get the latest case number
            cursor.execute("SELECT OFFNS_CASE_RECORD_NO FROM OFFENSE_INFORMATION ORDER BY OFFNS_ID DESC LIMIT 1")
            result = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if result:
                # Extract the number part and increment
                last_case = result[0]
                parts = last_case.split('-')
                if len(parts) == 2:
                    number = int(parts[1]) + 1
                    return f"10-{number:04d}"
            
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


class ReviewOffenseInfo2(QWidget):
    switch_to_offense = pyqtSignal()
    data_submitted = pyqtSignal()
    
    def __init__(self, offense_data, parent=None):
        super().__init__()
        uic.loadUi("ui/review-offenseinfo-2.ui", self)
        self.load_fonts()
        self.offense_data = offense_data

        # Get UI elements
        self.offensetype_line = self.findChild(QLineEdit, "offensetype_line")
        self.caseno_line = self.findChild(QLineEdit, "caseno_line")
        self.location_line = self.findChild(QLineEdit, "location_line")
        self.complainant_line = self.findChild(QLineEdit, "complainant_line")
        self.officer_line = self.findChild(QLineEdit, "officer_line")
        
        self.datetime_dt = self.findChild(QDateTimeEdit, "datetime_dt")
        self.desc_text = self.findChild(QTextEdit, "desc_text")

        # Buttons
        self.submit_btn = self.findChild(QPushButton, "submit_btn")
        if self.submit_btn:
            self.submit_btn.clicked.connect(self.submit_data)

        self.prev_btn = self.findChild(QPushButton, "prevbtn")
        if self.prev_btn:
            self.prev_btn.clicked.connect(self.go_to_offense)

    def populate_fields(self):
        if self.offensetype_line:
            self.offensetype_line.setText(self.offense_data.offense_info['offense_type'])
        if self.caseno_line:
            self.caseno_line.setText(self.offense_data.offense_info['case_no'])
            self.caseno_line.setReadOnly(True)  # Case number should not be edited
        if self.location_line:
            self.location_line.setText(self.offense_data.offense_info['location'])
        if self.complainant_line:
            self.complainant_line.setText(self.offense_data.offense_info['complainant'])
        if self.officer_line:
            self.officer_line.setText(self.offense_data.offense_info['officer'])
        
        if self.datetime_dt and self.offense_data.offense_info['datetime']:
            self.datetime_dt.setDateTime(QDateTime(self.offense_data.offense_info['datetime']))
        
        if self.desc_text:
            self.desc_text.setPlainText(self.offense_data.offense_info['description'])

    def submit_data(self):
        # Update data with any changes
        if self.offensetype_line:
            self.offense_data.offense_info['offense_type'] = self.offensetype_line.text().strip()
        
        if self.location_line:
            self.offense_data.offense_info['location'] = self.location_line.text().strip()
        if self.complainant_line:
            self.offense_data.offense_info['complainant'] = self.complainant_line.text().strip()
        if self.officer_line:
            self.offense_data.offense_info['officer'] = self.officer_line.text().strip()
        
        if self.datetime_dt:
            self.offense_data.offense_info['datetime'] = self.datetime_dt.dateTime().toPyDateTime()
        if self.desc_text:
            self.offense_data.offense_info['description'] = self.desc_text.toPlainText().strip()
        
        # Emit signal to save to database
        self.data_submitted.emit()

    def go_to_offense(self):
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