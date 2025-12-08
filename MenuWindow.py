import sys
import cv2
import psycopg2
import numpy as np
from scipy.spatial.distance import cosine
from PyQt5 import uic, Qt
from PyQt5.QtCore import QEvent, pyqtSignal, QTimer, QThread, Qt
from PyQt5.QtGui import QFontDatabase, QImage, QPixmap, QPainter
from PyQt5.QtWidgets import (QWidget, QApplication, QComboBox, QLineEdit, QMessageBox, QPushButton, QLabel,
                             QDialogButtonBox, QDialog, QStyle, QMainWindow, QStackedWidget, QVBoxLayout)
from Db_connection import get_db_connection


class SystemMenu(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("ui/SystemMenuWindow.ui", self)
        self.load_fonts()

        self.gradient_bg = QWidget(self)
        uic.loadUi("ui/action-gradientbg.ui", self.gradient_bg)
        self.gradient_bg.move(0, 0)

        #add a stack widget
        self.stacked_widget = QStackedWidget(self)
        uic.loadUi("ui/action-stack.ui", self.stacked_widget)
        self.stacked_widget.move(0, 0)
        self.stacked_widget.hide()

        #add the dashboard action widget
        self.dbaction_widget = QWidget(self)
        uic.loadUi("ui/action-dashboard.ui", self.dbaction_widget)
        self.dbaction_widget.move(275, 290)

        # add the enroll action widget
        self.enrollaction_widget = QWidget(self)
        uic.loadUi("ui/action-enroll.ui", self.enrollaction_widget)
        self.enrollaction_widget.move(754, 290)

        # button to go to dashboard menu
        self.db_btn = self.dbaction_widget.findChild(QPushButton, "proceed_btn")
        if self.db_btn:
            self.db_btn.clicked.connect(self.go_dashboardmenu)

        # button to proceed to enroll profile
        self.enroll_btn = self.enrollaction_widget.findChild(QPushButton, "proceed_btn")
        if self.enroll_btn:
            self.enroll_btn.clicked.connect(self.go_enroll_facescan)

        # DON'T create facescan yet - create it only when needed
        self.facescan = None

    def go_dashboardmenu(self):
        from DashboardMenu import DbMenuWindow as DbMenuMainWindow
        self.main_window = DbMenuMainWindow()

        self.main_window.show()
        self.close()

    def handle_recognition(self, match_found, juv_id=None):
        if match_found and juv_id:
            # Match found - open offense enrollment for existing juvenile
            self.open_add_offense_window(juv_id)
        else:
            # No match - open full enrollment
            self.open_enrollwindow()

    def open_enrollwindow(self):
        from EnrollMain import Enroll as EnrollMainWindow
        self.main_window = EnrollMainWindow()

        self.main_window.show()
        self.close()

    def open_add_offense_window(self, juv_id):
        #Open the add offense window for existing juvenile
        from AddOffense import AddOffenseWindow
        self.main_window = AddOffenseWindow(juv_id)

        self.main_window.show()
        self.close()

    def go_enroll_facescan(self):
        self.gradient_bg.hide()
        self.dbaction_widget.hide()
        self.enrollaction_widget.hide()

        # Create and initialize face scan ONLY when button is clicked
        if self.facescan is None:
            self.facescan = FaceScan(self.stacked_widget)
            self.stacked_widget.addWidget(self.facescan)
            self.facescan.recognition_completed.connect(self.handle_recognition)
        
        # Start the camera
        self.facescan.start_camera()
        
        self.stacked_widget.show()
        self.stacked_widget.setCurrentWidget(self.facescan)

    #CORRECT LOCATION - closeEvent for SystemMenu class
    def closeEvent(self, event):
        if self.facescan is not None:
            self.facescan.stop_camera()
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


class FaceScan(QWidget):
    recognition_completed = pyqtSignal(bool, object)  # match_found, juv_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi("ui/action-facescan.ui", self)
        self.load_fonts()

        self.layout = QVBoxLayout(self)
        self.video_label = QLabel(self)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.video_label)

        self.face_label = self.findChild(QLabel, "face_label")
        
        # Find the existing status label from UI
        self.status_label = self.findChild(QLabel, "label")

        # Load face detector (Haar cascade for simplicity)
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

        # Initialize variables but DON'T start camera yet
        self.cap = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        
        self.face_detected = False

    def start_camera(self):
        if self.cap is not None and self.cap.isOpened():
            print("Camera already running")
            return  # Camera already running
        
        # Release any existing camera first
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        
        # Prioritize using webcam for face scan if plugged in
        camera_indices = [1, 2, 0]
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
            QMessageBox.warning(self, "Camera Error", "No working camera found. Check connections and permissions.")
            return

        # Set camera properties
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)

        # Start timer for video feed
        self.timer.start(30)
        
        if self.status_label:
            self.status_label.setText("Position your face at the center for face scan")

    def stop_camera(self):
        print("Stopping camera...")
        if self.timer.isActive():
            self.timer.stop()
        
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        
        print("Camera stopped and released")

    def update_frame(self):
        if self.cap is None or not self.cap.isOpened():
            return
            
        ret, frame = self.cap.read()
        if not ret or frame is None:
            print("Failed to read frame")
            return
        
        # Validate frame
        if frame.size == 0:
            print("Empty frame received")
            return
        
        #Ensure frame is contiguous in memory
        frame = np.ascontiguousarray(frame)

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
                break

        # Recognition logic
        if face_in_center:
            if not self.face_detected:
                self.face_detected = True
                # Perform recognition
                match_found, juv_id = self.recognize_face(frame)
                
                # IMPORTANT: Stop camera before emitting signal
                self.stop_camera()
                
                if match_found:
                    if self.status_label:
                        self.status_label.setText("Biometric match detected. Adding new offense to profile...")
                    QTimer.singleShot(2000, lambda: self.recognition_completed.emit(True, juv_id))
                else:
                    if self.status_label:
                        self.status_label.setText("No biometric match detected. Proceeding to enrollment...")
                    QTimer.singleShot(2000, lambda: self.recognition_completed.emit(False, None))
                return  # Stop processing after recognition
        else:
            if self.face_detected:
                self.face_detected = False
                if self.status_label:
                    self.status_label.setText("Position your face at the center for face scan")

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

    def recognize_face(self, frame):
        try:
            import face_recognition
            import numpy as np
            
            if self.status_label:
                self.status_label.setText("Processing face recognition...")
            
            # Validate frame
            if frame is None or frame.size == 0:
                print("Invalid frame for recognition")
                return False, None
            
            # Ensure frame is uint8
            if frame.dtype != np.uint8:
                frame = frame.astype(np.uint8)
            
            #Ensure frame is C-contiguous
            if not frame.flags['C_CONTIGUOUS']:
                frame = np.ascontiguousarray(frame)
            
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            #Ensure RGB frame is also C-contiguous
            if not rgb_frame.flags['C_CONTIGUOUS']:
                rgb_frame = np.ascontiguousarray(rgb_frame)
            
            # Double-check RGB frame
            if rgb_frame.dtype != np.uint8:
                rgb_frame = rgb_frame.astype(np.uint8)
            
            # Get face encodings
            face_encodings = face_recognition.face_encodings(rgb_frame)
            
            if len(face_encodings) == 0:
                print("No face detected during recognition")
                return False, None
            
            scanned_embedding = face_encodings[0]
            
            # Fetch all embeddings from database
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT JUV_ID, EMBEDDING FROM FACIAL_DATA")
            results = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            if not results:
                print("No facial data in database")
                return False, None
            
            # Compare embeddings
            threshold = 0.4  # face_recognition threshold
            best_match_id = None
            best_distance = float('inf')
            
            for juv_id, stored_embedding_str in results:
                try:
                    stored_embedding = np.array(eval(stored_embedding_str))
                    
                    # Calculate face distance
                    distance = face_recognition.face_distance([stored_embedding], scanned_embedding)[0]
                    
                    if distance < best_distance:
                        best_distance = distance
                        best_match_id = juv_id
                    
                    print(f"JUV_ID {juv_id}: Distance = {distance:.4f}")
                    
                except Exception as e:
                    print(f"Error comparing with JUV_ID {juv_id}: {e}")
                    continue
            
            if best_distance < threshold:
                print(f"Match found! JUV_ID: {best_match_id}, Distance: {best_distance:.4f}")
                return True, best_match_id
            else:
                print(f"No match found. Best distance: {best_distance:.4f}")
                return False, None
                
        except Exception as e:
            print(f"Error during face recognition: {e}")
            import traceback
            traceback.print_exc()
            return False, None

    def hideEvent(self, event):
        self.stop_camera()
        super().hideEvent(event)

    def closeEvent(self, event):
        self.stop_camera()
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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = SystemMenu()
    ui.show()
    app.exec_()