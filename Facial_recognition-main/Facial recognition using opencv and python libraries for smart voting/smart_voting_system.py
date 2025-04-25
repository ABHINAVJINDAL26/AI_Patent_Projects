import sys
import os
import cv2
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                            QStackedWidget, QMessageBox, QFrame, QGridLayout)
from PyQt5.QtGui import QPixmap, QImage, QFont, QIcon
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QSize

from data_manager import DataManager
from face_recognition import FaceRecognition

# Global stylesheet
STYLESHEET = """
QWidget {
    font-family: 'Segoe UI', Arial;
    font-size: 12px;
}

QLabel {
    color: #333333;
}

QLineEdit {
    padding: 8px;
    border: 1px solid #cccccc;
    border-radius: 4px;
    background-color: #ffffff;
}

QPushButton {
    background-color: #2196F3;
    color: white;
    padding: 10px 15px;
    border: none;
    border-radius: 4px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #0b7dda;
}

QPushButton:pressed {
    background-color: #0a5999;
}

QFrame#card {
    background-color: white;
    border-radius: 8px;
    padding: 20px;
}

QLabel#heading {
    font-size: 24px;
    font-weight: bold;
    color: #2196F3;
    margin-bottom: 20px;
}

QLabel#subheading {
    font-size: 18px;
    color: #555555;
    margin-bottom: 10px;
}
"""

class VideoWidget(QLabel):
    """Widget to display video feed"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(640, 480)
        self.setAlignment(Qt.AlignCenter)
        self.setText("Camera feed will appear here")
        self.setStyleSheet("border: 1px solid #cccccc; background-color: #f0f0f0;")
    
    def update_frame(self, frame):
        """Update the widget with a new frame"""
        if frame is not None:
            # Convert the frame to QImage
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame_rgb.shape
            bytes_per_line = ch * w
            q_img = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
            
            # Scale the image to fit the widget while maintaining aspect ratio
            pixmap = QPixmap.fromImage(q_img)
            self.setPixmap(pixmap.scaled(self.width(), self.height(), Qt.KeepAspectRatio))


class LoginPage(QWidget):
    """Login page widget"""
    def __init__(self, data_manager, switch_page_callback):
        super().__init__()
        self.data_manager = data_manager
        self.switch_page = switch_page_callback
        self.init_ui()
    
    def init_ui(self):
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)
        
        # Create a card frame
        card = QFrame()
        card.setObjectName("card")
        card.setMinimumWidth(400)
        card.setMaximumWidth(500)
        card_layout = QVBoxLayout()
        
        # Heading
        heading = QLabel("Smart Voting System")
        heading.setObjectName("heading")
        heading.setAlignment(Qt.AlignCenter)
        
        # Subheading
        subheading = QLabel("Login to your account")
        subheading.setObjectName("subheading")
        subheading.setAlignment(Qt.AlignCenter)
        
        # Email field
        email_label = QLabel("Email:")
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your email")
        
        # Password field
        password_label = QLabel("Password:")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.Password)
        
        # Login button
        login_btn = QPushButton("Login")
        login_btn.clicked.connect(self.login)
        
        # Register link
        register_layout = QHBoxLayout()
        register_label = QLabel("Don't have an account?")
        register_btn = QPushButton("Register")
        register_btn.clicked.connect(lambda: self.switch_page(1))  # Switch to register page
        register_layout.addWidget(register_label)
        register_layout.addWidget(register_btn)
        register_layout.setAlignment(Qt.AlignCenter)
        
        # Add widgets to card layout
        card_layout.addWidget(heading)
        card_layout.addWidget(subheading)
        card_layout.addWidget(email_label)
        card_layout.addWidget(self.email_input)
        card_layout.addWidget(password_label)
        card_layout.addWidget(self.password_input)
        card_layout.addWidget(login_btn)
        card_layout.addLayout(register_layout)
        
        # Set card layout
        card.setLayout(card_layout)
        
        # Add card to main layout
        main_layout.addWidget(card)
        
        # Set main layout
        self.setLayout(main_layout)
    
    def login(self):
        """Handle login button click"""
        email = self.email_input.text()
        password = self.password_input.text()
        
        # Validate inputs
        if not email or not password:
            QMessageBox.warning(self, "Login Failed", "Please enter both email and password")
            return
        
        # Verify login
        success, message = self.data_manager.verify_login(email, password)
        
        if success:
            # Check if voter details exist
            voter = self.data_manager.get_voter_by_email(email)
            if voter:
                # Go to face recognition page
                self.switch_page(3, {'email': email, 'aadhar_id': voter['aadhar_id']})
            else:
                # Go to voter registration page
                self.switch_page(2, {'email': email})
        else:
            QMessageBox.warning(self, "Login Failed", message)


class RegisterPage(QWidget):
    """Registration page widget"""
    def __init__(self, data_manager, switch_page_callback):
        super().__init__()
        self.data_manager = data_manager
        self.switch_page = switch_page_callback
        self.init_ui()
    
    def init_ui(self):
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)
        
        # Create a card frame
        card = QFrame()
        card.setObjectName("card")
        card.setMinimumWidth(400)
        card.setMaximumWidth(500)
        card_layout = QVBoxLayout()
        
        # Heading
        heading = QLabel("Smart Voting System")
        heading.setObjectName("heading")
        heading.setAlignment(Qt.AlignCenter)
        
        # Subheading
        subheading = QLabel("Create a new account")
        subheading.setObjectName("subheading")
        subheading.setAlignment(Qt.AlignCenter)
        
        # Email field
        email_label = QLabel("Email:")
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your email")
        
        # Password field
        password_label = QLabel("Password:")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.Password)
        
        # Confirm password field
        confirm_password_label = QLabel("Confirm Password:")
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("Confirm your password")
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        
        # Register button
        register_btn = QPushButton("Register")
        register_btn.clicked.connect(self.register)
        
        # Login link
        login_layout = QHBoxLayout()
        login_label = QLabel("Already have an account?")
        login_btn = QPushButton("Login")
        login_btn.clicked.connect(lambda: self.switch_page(0))  # Switch to login page
        login_layout.addWidget(login_label)
        login_layout.addWidget(login_btn)
        login_layout.setAlignment(Qt.AlignCenter)
        
        # Add widgets to card layout
        card_layout.addWidget(heading)
        card_layout.addWidget(subheading)
        card_layout.addWidget(email_label)
        card_layout.addWidget(self.email_input)
        card_layout.addWidget(password_label)
        card_layout.addWidget(self.password_input)
        card_layout.addWidget(confirm_password_label)
        card_layout.addWidget(self.confirm_password_input)
        card_layout.addWidget(register_btn)
        card_layout.addLayout(login_layout)
        
        # Set card layout
        card.setLayout(card_layout)
        
        # Add card to main layout
        main_layout.addWidget(card)
        
        # Set main layout
        self.setLayout(main_layout)
    
    def register(self):
        """Handle register button click"""
        email = self.email_input.text()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()
        
        # Validate inputs
        if not email or not password or not confirm_password:
            QMessageBox.warning(self, "Registration Failed", "Please fill all fields")
            return
        
        if password != confirm_password:
            QMessageBox.warning(self, "Registration Failed", "Passwords do not match")
            return
        
        # Register user
        success, message = self.data_manager.register_user(email, password)
        
        if success:
            QMessageBox.information(self, "Registration Successful", message)
            # Go to voter registration page
            self.switch_page(2, {'email': email})
        else:
            QMessageBox.warning(self, "Registration Failed", message)


class VoterRegistrationPage(QWidget):
    """Voter registration page widget"""
    def __init__(self, data_manager, face_recognition, switch_page_callback):
        super().__init__()
        self.data_manager = data_manager
        self.face_recognition = face_recognition
        self.switch_page = switch_page_callback
        self.user_data = {}
        self.init_ui()
    
    def init_ui(self):
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)
        
        # Create a card frame
        card = QFrame()
        card.setObjectName("card")
        card.setMinimumWidth(400)
        card.setMaximumWidth(500)
        card_layout = QVBoxLayout()
        
        # Heading
        heading = QLabel("Voter Registration")
        heading.setObjectName("heading")
        heading.setAlignment(Qt.AlignCenter)
        
        # Subheading
        subheading = QLabel("Enter your voter details")
        subheading.setObjectName("subheading")
        subheading.setAlignment(Qt.AlignCenter)
        
        # Voter ID field
        voter_id_label = QLabel("Voter ID:")
        self.voter_id_input = QLineEdit()
        self.voter_id_input.setPlaceholderText("Enter your voter ID")
        
        # Aadhar ID field
        aadhar_id_label = QLabel("Aadhar ID:")
        self.aadhar_id_input = QLineEdit()
        self.aadhar_id_input.setPlaceholderText("Enter your Aadhar ID")
        
        # Register button
        register_btn = QPushButton("Register & Proceed to Face Capture")
        register_btn.clicked.connect(self.register_voter)
        
        # Add widgets to card layout
        card_layout.addWidget(heading)
        card_layout.addWidget(subheading)
        card_layout.addWidget(voter_id_label)
        card_layout.addWidget(self.voter_id_input)
        card_layout.addWidget(aadhar_id_label)
        card_layout.addWidget(self.aadhar_id_input)
        card_layout.addWidget(register_btn)
        
        # Set card layout
        card.setLayout(card_layout)
        
        # Add card to main layout
        main_layout.addWidget(card)
        
        # Set main layout
        self.setLayout(main_layout)
    
    def set_user_data(self, data):
        """Set user data from previous page"""
        self.user_data = data
    
    def register_voter(self):
        """Handle register button click"""
        voter_id = self.voter_id_input.text()
        aadhar_id = self.aadhar_id_input.text()
        
        # Validate inputs
        if not voter_id or not aadhar_id:
            QMessageBox.warning(self, "Registration Failed", "Please fill all fields")
            return
        
        # Register voter
        success, message = self.data_manager.register_voter(self.user_data.get('email', ''), voter_id, aadhar_id)
        
        if success:
            QMessageBox.information(self, "Registration Successful", message)
            # Go to face capture page
            self.switch_page(3, {'email': self.user_data.get('email', ''), 'aadhar_id': aadhar_id})
        else:
            QMessageBox.warning(self, "Registration Failed", message)


class FaceCaptureRecognitionPage(QWidget):
    """Face capture and recognition page widget"""
    def __init__(self, data_manager, face_recognition, switch_page_callback):
        super().__init__()
        self.data_manager = data_manager
        self.face_recognition = face_recognition
        self.switch_page = switch_page_callback
        self.user_data = {}
        self.init_ui()
    
    def init_ui(self):
        # Main layout
        main_layout = QVBoxLayout()
        
        # Heading
        heading = QLabel("Face Recognition")
        heading.setObjectName("heading")
        heading.setAlignment(Qt.AlignCenter)
        
        # Video widget
        self.video_widget = VideoWidget()
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        
        # Capture button
        self.capture_btn = QPushButton("Capture Face")
        self.capture_btn.clicked.connect(self.capture_face)
        
        # Recognize button
        self.recognize_btn = QPushButton("Recognize Face")
        self.recognize_btn.clicked.connect(self.recognize_face)
        
        # Add buttons to layout
        buttons_layout.addWidget(self.capture_btn)
        buttons_layout.addWidget(self.recognize_btn)
        
        # Status label
        self.status_label = QLabel("Please capture or recognize your face")
        self.status_label.setAlignment(Qt.AlignCenter)
        
        # Add widgets to main layout
        main_layout.addWidget(heading)
        main_layout.addWidget(self.video_widget)
        main_layout.addLayout(buttons_layout)
        main_layout.addWidget(self.status_label)
        
        # Set main layout
        self.setLayout(main_layout)
    
    def set_user_data(self, data):
        """Set user data from previous page"""
        self.user_data = data
        
        # Check if user has already voted
        if 'aadhar_id' in self.user_data and self.data_manager.has_voted(self.user_data['aadhar_id']):
            QMessageBox.warning(self, "Already Voted", "You have already cast your vote")
            self.capture_btn.setEnabled(False)
            self.recognize_btn.setEnabled(False)
            self.status_label.setText("You have already cast your vote")
    
    def capture_face(self):
        """Handle capture button click"""
        self.status_label.setText("Capturing face... Please look at the camera")
        
        # Disable buttons during capture
        self.capture_btn.setEnabled(False)
        self.recognize_btn.setEnabled(False)
        
        # Capture face in a non-blocking way
        QApplication.processEvents()
        
        # Capture face
        face_data = self.face_recognition.capture_face(self.video_widget.update_frame)
        
        if face_data is not None:
            # Save face data
            success, message = self.data_manager.save_face_data(self.user_data.get('aadhar_id', ''), face_data)
            
            if success:
                self.status_label.setText("Face captured successfully")
                QMessageBox.information(self, "Face Capture", "Face captured successfully. You can now proceed to voting.")
                # Go to voting page
                self.switch_page(4, self.user_data)
            else:
                self.status_label.setText("Failed to save face data")
                QMessageBox.warning(self, "Face Capture Failed", message)
        else:
            self.status_label.setText("Face capture failed. Please try again.")
            QMessageBox.warning(self, "Face Capture Failed", "Failed to capture face. Please try again.")
        
        # Re-enable buttons
        self.capture_btn.setEnabled(True)
        self.recognize_btn.setEnabled(True)
    
    def recognize_face(self):
        """Handle recognize button click"""
        self.status_label.setText("Recognizing face... Please look at the camera")
        
        # Disable buttons during recognition
        self.capture_btn.setEnabled(False)
        self.recognize_btn.setEnabled(False)
        
        # Recognize face in a non-blocking way
        QApplication.processEvents()
        
        # Recognize face
        recognized_id = self.face_recognition.recognize_face(self.video_widget.update_frame)
        
        if recognized_id is not None:
            # Check if recognized ID matches user's Aadhar ID
            if recognized_id == self.user_data.get('aadhar_id', ''):
                self.status_label.setText("Face recognized successfully")
                QMessageBox.information(self, "Face Recognition", "Face recognized successfully. You can now proceed to voting.")
                # Go to voting page
                self.switch_page(4, self.user_data)
            else:
                self.status_label.setText("Face recognition failed. ID mismatch.")
                QMessageBox.warning(self, "Face Recognition Failed", "The recognized face does not match your Aadhar ID.")
        else:
            self.status_label.setText("Face recognition failed. Please try again.")
            QMessageBox.warning(self, "Face Recognition Failed", "Failed to recognize face. Please try again.")
        
        # Re-enable buttons
        self.capture_btn.setEnabled(True)
        self.recognize_btn.setEnabled(True)


class VotingPage(QWidget):
    """Voting page widget"""
    def __init__(self, data_manager, switch_page_callback):
        super().__init__()
        self.data_manager = data_manager
        self.switch_page = switch_page_callback
        self.user_data = {}
        self.init_ui()
    
    def init_ui(self):
        # Main layout
        main_layout = QVBoxLayout()
        
        # Heading
        heading = QLabel("Cast Your Vote")
        heading.setObjectName("heading")
        heading.setAlignment(Qt.AlignCenter)
        
        # Subheading
        subheading = QLabel("Select a party to vote for")
        subheading.setObjectName("subheading")
        subheading.setAlignment(Qt.AlignCenter)
        
        # Parties grid
        parties_grid = QGridLayout()
        
        # BJP button
        bjp_btn = QPushButton("BJP")
        bjp_btn.setMinimumHeight(100)
        bjp_btn.setStyleSheet("background-color: #FF9933; font-size: 16px;")
        bjp_btn.clicked.connect(lambda: self.cast_vote("BJP"))
        
        # Congress button
        congress_btn = QPushButton("Congress")
        congress_btn.setMinimumHeight(100)
        congress_btn.setStyleSheet("background-color: #0078D7; font-size: 16px;")
        congress_btn.clicked.connect(lambda: self.cast_vote("Congress"))
        
        # AAP button
        aap_btn = QPushButton("AAP")
        aap_btn.setMinimumHeight(100)
        aap_btn.setStyleSheet("background-color: #00A86B; font-size: 16px;")
        aap_btn.clicked.connect(lambda: self.cast_vote("AAP"))
        
        # NOTA button
        nota_btn = QPushButton("NOTA")
        nota_btn.setMinimumHeight(100)
        nota_btn.setStyleSheet("background-color: #888888; font-size: 16px;")
        nota_btn.clicked.connect(lambda: self.cast_vote("NOTA"))
        
        # Add buttons to grid
        parties_grid.addWidget(bjp_btn, 0, 0)
        parties_grid.addWidget(congress_btn, 0, 1)
        parties_grid.addWidget(aap_btn, 1, 0)
        parties_grid.addWidget(nota_btn, 1, 1)
        
        # Instructions
        instructions = QLabel("Click on a party to cast your vote. Your vote is confidential and secure.")
        instructions.setAlignment(Qt.AlignCenter)
        
        # Add widgets to main layout
        main_layout.addWidget(heading)
        main_layout.addWidget(subheading)
        main_layout.addLayout(parties_grid)
        main_layout.addWidget(instructions)
        
        # Set main layout
        self.setLayout(main_layout)
    
    def set_user_data(self, data):
        """Set user data from previous page"""
        self.user_data = data
        
        # Check if user has already voted
        if 'aadhar_id' in self.user_data and self.data_manager.has_voted(self.user_data['aadhar_id']):
            QMessageBox.warning(self, "Already Voted", "You have already cast your vote")
            # Go to thank you page
            self.switch_page(5, self.user_data)
    
    def cast_vote(self, party):
        """Handle vote button click"""
        # Confirm vote
        reply = QMessageBox.question(self, "Confirm Vote", 
                                    f"Are you sure you want to vote for {party}?",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # Record vote
            success, message = self.data_manager.record_vote(self.user_data.get('aadhar_id', ''), party)
            
            if success:
                QMessageBox.information(self, "Vote Recorded", message)
                # Go to thank you page
                self.switch_page(5, self.user_data)
            else:
                QMessageBox.warning(self, "Vote Failed", message)


class ThankYouPage(QWidget):
    """Thank you page widget"""
    def __init__(self, switch_page_callback):
        super().__init__()
        self.switch_page = switch_page_callback
        self.init_ui()
    
    def init_ui(self):
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)
        
        # Create a card frame
        card = QFrame()
        card.setObjectName("card")
        card.setMinimumWidth(400)
        card.setMaximumWidth(500)
        card_layout = QVBoxLayout()
        
        # Heading
        heading = QLabel("Thank You!")
        heading.setObjectName("heading")
        heading.setAlignment(Qt.AlignCenter)
        
        # Message
        message = QLabel("Your vote has been recorded successfully. Thank you for participating in the democratic process.")
        message.setWordWrap(True)
        message.setAlignment(Qt.AlignCenter)
        
        # Home button
        home_btn = QPushButton("Back to Home")
        home_btn.clicked.connect(lambda: self.switch_page(0))
        
        # Add widgets to card layout
        card_layout.addWidget(heading)
        card_layout.addWidget(message)
        card_layout.addWidget(home_btn)
        
        # Set card layout
        card.setLayout(card_layout)
        
        # Add card to main layout
        main_layout.addWidget(card)
        
        # Set main layout
        self.setLayout(main_layout)


class MainWindow(QMainWindow):
    """Main application window"""
    def __init__(self):
        super().__init__()
        self.data_manager = DataManager()
        self.face_recognition = FaceRecognition()
        self.init_ui()
    
    def init_ui(self):
        # Set window properties
        self.setWindowTitle("Smart Voting System")
        self.setMinimumSize(800, 600)
        
        # Set stylesheet
        self.setStyleSheet(STYLESHEET)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        
        # Create stacked widget for pages
        self.stacked_widget = QStackedWidget()
        
        # Create pages
        self.login_page = LoginPage(self.data_manager, self.switch_page)
        self.register_page = RegisterPage(self.data_manager, self.switch_page)
        self.voter_registration_page = VoterRegistrationPage(self.data_manager, self.face_recognition, self.switch_page)
        self.face_capture_recognition_page = FaceCaptureRecognitionPage(self.data_manager, self.face_recognition, self.switch_page)
        self.voting_page = VotingPage(self.data_manager, self.switch_page)
        self.thank_you_page = ThankYouPage(self.switch_page)
        
        # Add pages to stacked widget
        self.stacked_widget.addWidget(self.login_page)  # Index 0
        self.stacked_widget.addWidget(self.register_page)  # Index 1
        self.stacked_widget.addWidget(self.voter_registration_page)  # Index 2
        self.stacked_widget.addWidget(self.face_capture_recognition_page)  # Index 3
        self.stacked_widget.addWidget(self.voting_page)  # Index 4
        self.stacked_widget.addWidget(self.thank_you_page)  # Index 5
        
        # Add stacked widget to layout
        layout.addWidget(self.stacked_widget)
        
        # Show login page by default
        self.stacked_widget.setCurrentIndex(0)
    
    def switch_page(self, index, data=None):
        """Switch to a different page"""
        # Set user data if provided
        if data is not None:
            if index == 2:  # Voter registration page
                self.voter_registration_page.set_user_data(data)
            elif index == 3:  # Face capture/recognition page
                self.face_capture_recognition_page.set_user_data(data)
            elif index == 4:  # Voting page
                self.voting_page.set_user_data(data)
        
        # Switch to the page
        self.stacked_widget.setCurrentIndex(index)


if __name__ == "__main__":
    # Create data directory if it doesn't exist
    if not os.path.exists('data/'):
        os.makedirs('data/')
    
    # Create application
    app = QApplication(sys.argv)
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run application
    sys.exit(app.exec_())
