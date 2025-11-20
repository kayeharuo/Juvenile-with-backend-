import sys
import cv2
import psycopg2
import numpy as np
from datetime import datetime
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal, QTimer, QDateTime, Qt
from PyQt5.QtGui import QFontDatabase, QPixmap
from PyQt5.QtWidgets import (QWidget, QLineEdit, QMessageBox, QPushButton, 
                             QMainWindow, QStackedWidget, QDateTimeEdit, QTextEdit,
                             QLabel, QTableWidget, QTableWidgetItem)
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
        self.review_offense.switch_to_history.connect(self.criminal_history_page)
        
        self.criminal_history = CriminalHistoryPage(self.offense_data)
        self.criminal_history.switch_to_review.connect(self.review_offense_page)
        # No need to connect data_submitted since it's handled internally now

        # Add instances to the stacked widget
        self.stack_widget.addWidget(self.offense_info)
        self.stack_widget.addWidget(self.review_offense)
        self.stack_widget.addWidget(self.criminal_history)

        # Set the initial page to offense information
        self.stack_widget.setCurrentWidget(self.offense_info)

    def offense_page(self):
        self.stack_widget.setCurrentWidget(self.offense_info)

    def review_offense_page(self):
        self.review_offense.populate_fields()
        self.stack_widget.setCurrentWidget(self.review_offense)
    
    def criminal_history_page(self):
        self.criminal_history.load_criminal_history()
        self.stack_widget.setCurrentWidget(self.criminal_history)

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
    switch_to_history = pyqtSignal()
    
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
            self.submit_btn.clicked.connect(self.go_to_history)

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

    def go_to_history(self):
        # Update data with any changes before going to history
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
        
        # Emit signal to go to history page
        self.switch_to_history.emit()

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


class CriminalHistoryPage(QWidget):
    switch_to_review = pyqtSignal()
    data_submitted = pyqtSignal()
    
    def __init__(self, offense_data, parent=None):
        super().__init__()
        # Load the criminal history UI directly instead of using placeholder
        uic.loadUi("ui/casefile-criminalhistory.ui", self)
        self.load_fonts()
        self.offense_data = offense_data

        # Find labels
        self.casenum_label = self.findChild(QLabel, "casenum_label")
        
        # Create image label for facial photo
        self.photo_label = QLabel(self)
        self.photo_label.setGeometry(775, 70, 150, 150)
        self.photo_label.setStyleSheet("""
            QLabel {
                border: 2px solid #3E2780;
                border-radius: 10px;
                background-color: #f0f0f0;
            }
        """)
        self.photo_label.setScaledContents(True)
        self.photo_label.setAlignment(Qt.AlignCenter)
        
        # Criminal history record table
        self.history_table = self.findChild(QTableWidget, "history_table")
        if self.history_table:
            self.history_table.setColumnWidth(0, 201)
            self.history_table.setColumnWidth(1, 262)
            self.history_table.setColumnWidth(2, 361)
            self.history_table.verticalHeader().setVisible(False)
            self.history_table.resizeRowsToContents()

        # Done button
        self.done_btn = self.findChild(QPushButton, "done_btn")
        if self.done_btn:
            self.done_btn.clicked.connect(self.submit_and_return)

        # Previous button
        self.prev_btn = self.findChild(QPushButton, "prev_btn")
        if self.prev_btn:
            self.prev_btn.clicked.connect(self.go_to_review)

        # Close button (hide it for add offense flow)
        self.close_btn = self.findChild(QPushButton, "close_btn")
        if self.close_btn:
            self.close_btn.setVisible(False)

    def load_criminal_history(self):
        """Load criminal history from database for the juvenile"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Get juvenile information and face image
            cursor.execute("""
                SELECT 
                    jp.juv_fname,
                    jp.juv_mname,
                    jp.juv_lname,
                    jp.juv_suffix,
                    jp.juv_id,
                    fd.face_image
                FROM juvenile_profile jp
                LEFT JOIN facial_data fd ON jp.juv_id = fd.juv_id
                WHERE jp.juv_id = %s
            """, (self.offense_data.juv_id,))

            result = cursor.fetchone()
            if not result:
                cursor.close()
                conn.close()
                QMessageBox.warning(self, "Error", "Juvenile record not found.")
                return
                
            fname, mname, lname, suffix, juv_id, face_image = result
            
            # Display facial image (removed name display)
            if face_image and self.photo_label:
                pixmap = QPixmap()
                pixmap.loadFromData(face_image)
                self.photo_label.setPixmap(pixmap)
            elif self.photo_label:
                self.photo_label.setText("No Photo")
            
            # Update case number label with new offense case number
            if self.casenum_label:
                self.casenum_label.setText(f"Case No. {self.offense_data.offense_info['case_no']}")
            
            # Get all offenses for this juvenile (excluding the current one being added)
            cursor.execute("""
                SELECT 
                    oi.offns_case_record_no,
                    oi.offns_date_time,
                    oi.offns_type
                FROM offense_information oi
                WHERE oi.juv_id = %s
                ORDER BY oi.offns_date_time DESC
            """, (juv_id,))

            offenses = cursor.fetchall()
            cursor.close()
            conn.close()

            # Populate table with existing offenses
            if self.history_table:
                # Add 1 for the new offense about to be added
                total_rows = len(offenses) + 1
                self.history_table.setRowCount(total_rows)
                
                # Add the new offense as the first row (highlighted)
                self.history_table.setItem(0, 0, QTableWidgetItem(self.offense_data.offense_info['case_no']))
                
                date_str = self.offense_data.offense_info['datetime'].strftime("%B %d, %Y") if self.offense_data.offense_info['datetime'] else "N/A"
                self.history_table.setItem(0, 1, QTableWidgetItem(date_str))
                
                self.history_table.setItem(0, 2, QTableWidgetItem(self.offense_data.offense_info['offense_type']))
                
                # Style the new offense row to highlight it
                from PyQt5.QtGui import QColor, QFont
                for col in range(3):
                    item = self.history_table.item(0, col)
                    if item:
                        item.setBackground(QColor(62, 39, 128, 50))  # Light purple background
                        font = QFont()
                        font.setBold(True)
                        item.setFont(font)
                
                # Add existing offenses
                for row, offense in enumerate(offenses, start=1):
                    offense_case_no, offense_date, offense_type = offense
                    
                    # Case Number
                    self.history_table.setItem(row, 0, QTableWidgetItem(offense_case_no or "N/A"))
                    
                    # Date
                    date_str = offense_date.strftime("%B %d, %Y") if offense_date else "N/A"
                    self.history_table.setItem(row, 1, QTableWidgetItem(date_str))
                    
                    # Offense Type
                    self.history_table.setItem(row, 2, QTableWidgetItem(offense_type or "N/A"))

        except Exception as e:
            print(f"Error loading criminal history: {e}")
            QMessageBox.critical(self, "Database Error", f"Failed to load criminal history: {str(e)}")

    def submit_and_return(self):
        """Submit the new offense record and return to dashboard"""
        # First save to database
        self.save_to_database()
        
    def save_to_database(self):
        """Save the offense data to the database"""
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
            
            # Return to dashboard menu
            self.return_to_menu()
            
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to save data: {str(e)}")
            print(f"Database error: {e}")
    
    def return_to_menu(self):
        """Return to the dashboard menu"""
        from DashboardMenu import DbMenuWindow as RecordWindow
        
        # Get the parent window and close it
        parent_window = self.window()
        
        # Create and show the dashboard
        self.main_window = RecordWindow()
        self.main_window.show_page("records")
        self.main_window.show()
        
        # Close the AddOffense window
        parent_window.close()

    def go_to_review(self):
        self.switch_to_review.emit()

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