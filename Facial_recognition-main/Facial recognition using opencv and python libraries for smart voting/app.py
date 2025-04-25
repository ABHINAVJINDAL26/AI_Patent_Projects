import os
import cv2
import numpy as np
import pandas as pd
import pickle
import bcrypt
import logging
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, Response, jsonify, flash
from flask_bootstrap import Bootstrap
from werkzeug.security import generate_password_hash, check_password_hash
from sklearn.neighbors import KNeighborsClassifier
import time

# Set up logging
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'ai_smart_voting_system_secret_key'
Bootstrap(app)

# Add template context processor for current date
@app.context_processor
def inject_now():
    return {'now': datetime.now()}

# Ensure data directory exists
if not os.path.exists('data/'):
    os.makedirs('data/')

# Initialize data files
USERS_FILE = 'data/users.xlsx'
VOTERS_FILE = 'data/voters.xlsx'
VOTES_FILE = 'data/votes.xlsx'
FACES_DATA_FILE = 'data/faces_data.pkl'
NAMES_FILE = 'data/names.pkl'

# Initialize files if they don't exist
def initialize_files():
    # Initialize users file
    if not os.path.exists(USERS_FILE):
        users_df = pd.DataFrame(columns=['email', 'password', 'registration_date'])
        users_df.to_excel(USERS_FILE, index=False)
    
    # Initialize voters file
    if not os.path.exists(VOTERS_FILE):
        voters_df = pd.DataFrame(columns=['email', 'voter_id', 'aadhar_id', 'registration_date'])
        voters_df.to_excel(VOTERS_FILE, index=False)
    
    # Initialize votes file
    if not os.path.exists(VOTES_FILE):
        votes_df = pd.DataFrame(columns=['aadhar_id', 'party', 'date', 'time'])
        votes_df.to_excel(VOTES_FILE, index=False)

initialize_files()

# Global variables for face capture
camera = None
face_detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
captured_faces = []
is_capturing = False
frames_total = 30
capture_after_frame = 2
frame_count = 0

# User Authentication functions
def register_user(email, password):
    """Register a new user with email and password"""
    try:
        # Check if email already exists
        users_df = pd.read_excel(USERS_FILE)
        if email in users_df['email'].values:
            return False, "Email already registered"
        
        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Add new user
        new_user = pd.DataFrame({
            'email': [email],
            'password': [hashed_password.decode('utf-8')],
            'registration_date': [datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
        })
        
        users_df = pd.concat([users_df, new_user], ignore_index=True)
        
        try:
            users_df.to_excel(USERS_FILE, index=False)
        except PermissionError:
            # If file is open in another application, save to a temporary file
            temp_file = f"data/users_temp_{int(time.time())}.xlsx"
            users_df.to_excel(temp_file, index=False)
            return True, "User registered successfully (saved to temporary file due to file access issues)"
        
        return True, "User registered successfully"
    except Exception as e:
        logging.error(f"Error in register_user: {e}")
        return False, f"An error occurred during user registration: {str(e)}"

def verify_login(email, password):
    """Verify user login credentials"""
    try:
        users_df = pd.read_excel(USERS_FILE)
        
        # Check if email exists
        user = users_df[users_df['email'] == email]
        if user.empty:
            return False, "Email not registered"
        
        # Verify password
        stored_password = user['password'].values[0].encode('utf-8')
        if bcrypt.checkpw(password.encode('utf-8'), stored_password):
            return True, "Login successful"
        else:
            return False, "Incorrect password"
    except Exception as e:
        logging.error(f"Error in verify_login: {e}")
        return False, f"An error occurred during login: {str(e)}"

def register_voter(email, voter_id, aadhar_id):
    """Register voter ID and Aadhar ID for a user"""
    # Validate Aadhar ID format
    if not is_valid_aadhar_id(aadhar_id):
        return False, "Invalid Aadhar ID format. It must be 12 digits."
    
    # Validate Voter ID format
    if not is_valid_voter_id(voter_id):
        return False, "Invalid Voter ID format. It must be 10 characters with both letters and numbers."
    
    # Standardize format (remove spaces)
    aadhar_id = aadhar_id.replace(" ", "")
    voter_id = voter_id.replace(" ", "").upper()
    
    try:
        voters_df = pd.read_excel(VOTERS_FILE)
        
        # Check if Aadhar ID already exists
        if aadhar_id in voters_df['aadhar_id'].values:
            return False, "Aadhar ID already registered. Each Aadhar ID can only be used once for voting."
        
        # Check if Voter ID already exists
        if voter_id in voters_df['voter_id'].values:
            return False, "Voter ID already registered. Each Voter ID can only be used once for voting."
        
        # Check if this person has already voted by checking the votes file
        try:
            votes_df = pd.read_excel(VOTES_FILE)
            if aadhar_id in votes_df['aadhar_id'].values:
                return False, "This Aadhar ID has already been used for voting. Each person can vote only once."
        except Exception as e:
            logging.error(f"Error reading votes file: {e}")
            # Continue even if votes file can't be read
        
        # Add new voter
        new_voter = pd.DataFrame({
            'email': [email],
            'voter_id': [voter_id],
            'aadhar_id': [aadhar_id],
            'registration_date': [datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
        })
        
        voters_df = pd.concat([voters_df, new_voter], ignore_index=True)
        
        try:
            voters_df.to_excel(VOTERS_FILE, index=False)
        except PermissionError:
            # If file is open in another application, save to a temporary file
            temp_file = f"data/voters_temp_{int(time.time())}.xlsx"
            voters_df.to_excel(temp_file, index=False)
            return True, f"Voter registered successfully (saved to temporary file due to file access issues)"
        
        return True, "Voter registered successfully"
    except Exception as e:
        logging.error(f"Error in register_voter: {e}")
        return False, f"An error occurred during voter registration: {str(e)}"

def get_voter_by_email(email):
    """Get voter details by email"""
    try:
        voters_df = pd.read_excel(VOTERS_FILE)
        voter = voters_df[voters_df['email'] == email]
        if voter.empty:
            return None
        return voter.iloc[0].to_dict()
    except Exception as e:
        logging.error(f"Error in get_voter_by_email: {e}")
        return None

def has_voted(aadhar_id):
    """Check if a voter has already cast their vote"""
    try:
        votes_df = pd.read_excel(VOTES_FILE)
        return aadhar_id in votes_df['aadhar_id'].values
    except Exception as e:
        logging.error(f"Error in has_voted: {e}")
        return False  # Assume not voted if there's an error reading the file

def record_vote(aadhar_id, party):
    """Record a vote"""
    try:
        # Sanitize inputs to prevent encoding issues
        aadhar_id_safe = str(aadhar_id).encode('utf-8', errors='replace').decode('utf-8')
        party_safe = str(party).encode('utf-8', errors='replace').decode('utf-8')
        
        votes_df = pd.read_excel(VOTES_FILE)
        
        # Check if already voted
        if aadhar_id_safe in votes_df['aadhar_id'].values:
            return False, "You have already cast your vote"
        
        # Record vote
        now = datetime.now()
        new_vote = pd.DataFrame({
            'aadhar_id': [aadhar_id_safe],
            'party': [party_safe],
            'date': [now.strftime("%Y-%m-%d")],
            'time': [now.strftime("%H:%M:%S")]
        })
        
        votes_df = pd.concat([votes_df, new_vote], ignore_index=True)
        
        try:
            votes_df.to_excel(VOTES_FILE, index=False)
        except PermissionError:
            # If file is open in another application, save to a temporary file
            temp_file = f"data/votes_temp_{int(time.time())}.xlsx"
            votes_df.to_excel(temp_file, index=False)
            return True, "Vote recorded successfully (saved to temporary file due to file access issues)"
        
        return True, "Vote recorded successfully"
    except Exception as e:
        error_msg = str(e).encode('utf-8', errors='replace').decode('utf-8')
        logging.error(f"Error in record_vote: {error_msg}")
        return False, f"An error occurred while recording your vote. Please try again."

# Face Recognition functions
def save_face_data(aadhar_id, voter_id, face_data):
    """Save facial recognition data"""
    # Check if this face already exists in the database
    face_exists, existing_id = check_face_exists(face_data)
    if face_exists:
        # Check if the existing face is associated with a different Aadhar ID
        if existing_id != aadhar_id:
            return False, f"This face appears to be already registered with a different Aadhar ID. Facial recognition detected a match with ID: {existing_id}. If you believe this is an error, please contact the election officials."
    
    # Load existing data if available
    faces_data = []
    names = []
    voter_ids = []
    
    if os.path.exists(FACES_DATA_FILE) and os.path.exists(NAMES_FILE):
        with open(FACES_DATA_FILE, 'rb') as f:
            faces_data = pickle.load(f)
        with open(NAMES_FILE, 'rb') as f:
            names = pickle.load(f)
        
        # Check if this Aadhar ID already has face data
        if aadhar_id in names:
            return False, "This Aadhar ID already has face data registered"
    
    # Add new face data
    faces_data = np.append(faces_data, face_data, axis=0) if len(faces_data) > 0 else face_data
    names = names + [aadhar_id] * len(face_data)
    voter_ids = voter_ids + [voter_id] * len(face_data)
    
    # Save updated data
    with open(FACES_DATA_FILE, 'wb') as f:
        pickle.dump(faces_data, f)
    with open(NAMES_FILE, 'wb') as f:
        pickle.dump(names, f)
    with open('data/voter_ids.pkl', 'wb') as f:
        pickle.dump(voter_ids, f)
    
    return True, "Face data saved successfully"

def train_model():
    """Train the face recognition model with the saved data"""
    if not os.path.exists(FACES_DATA_FILE) or not os.path.exists(NAMES_FILE):
        return None
    
    # Load the data
    with open(FACES_DATA_FILE, 'rb') as f:
        faces = pickle.load(f)
    
    with open(NAMES_FILE, 'rb') as f:
        names = pickle.load(f)
    
    # Train the model
    model = KNeighborsClassifier(n_neighbors=5)
    model.fit(faces, names)
    
    return model

def check_face_exists(face_data):
    """Check if a similar face already exists in the database
    Returns a tuple (exists, existing_id) where:
    - exists: boolean indicating if the face exists
    - existing_id: the Aadhar ID associated with the existing face if found
    """
    if not os.path.exists(FACES_DATA_FILE) or not os.path.exists(NAMES_FILE):
        return False, None
    
    try:
        # Load existing face data
        with open(FACES_DATA_FILE, 'rb') as f:
            faces = pickle.load(f)
        with open(NAMES_FILE, 'rb') as f:
            names = pickle.load(f)
        
        if len(faces) == 0:
            return False, None
        
        # Train a KNN model with existing data
        model = KNeighborsClassifier(n_neighbors=1)  # Use 1 neighbor for exact matching
        model.fit(faces, names)
        
        # For each face in the new face_data, check if it matches any existing face
        for face in face_data:
            face_reshaped = face.reshape(1, -1)
            # Get the distance to the nearest neighbor
            distances, indices = model.kneighbors(face_reshaped)
            
            # If the distance is below a threshold, consider it a match
            # Lower threshold = stricter matching, higher threshold = more lenient matching
            threshold = 2000  # This threshold may need tuning based on your data
            if distances[0][0] < threshold:
                nearest_idx = indices[0][0]
                return True, names[nearest_idx]
        
        return False, None
    except Exception as e:
        logging.error(f"Error in check_face_exists: {e}")
        return False, None

# Add validation functions for Aadhar ID and Voter ID
def is_valid_aadhar_id(aadhar_id):
    """Validate Aadhar ID format (12 digits)"""
    if not aadhar_id:
        return False
    # Remove spaces if any
    aadhar_id = aadhar_id.replace(" ", "")
    # Check if it's 12 digits
    return aadhar_id.isdigit() and len(aadhar_id) == 12

def is_valid_voter_id(voter_id):
    """Validate Voter ID format (EPIC number - 10 characters with letters and numbers)"""
    if not voter_id:
        return False
    # Remove spaces if any
    voter_id = voter_id.replace(" ", "")
    # Check if it's 10 characters with letters and numbers
    return len(voter_id) == 10 and voter_id.isalnum() and not voter_id.isdigit() and not voter_id.isalpha()

# Video streaming and face capture functions
def generate_frames():
    """Generate frames from the camera with face detection"""
    global camera, captured_faces, is_capturing, frame_count
    
    if camera is None:
        camera = cv2.VideoCapture(0)
    
    while True:
        success, frame = camera.read()
        if not success:
            break
        
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_detector.detectMultiScale(gray, 1.3, 5)
        
        # Draw rectangle around faces and capture if needed
        for (x, y, w, h) in faces:
            # Draw rectangle
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
            # Capture face if in capturing mode
            if is_capturing:
                crop_img = frame[y:y+h, x:x+w]
                resized_img = cv2.resize(crop_img, (50, 50))
                
                if len(captured_faces) <= frames_total and frame_count % capture_after_frame == 0:
                    captured_faces.append(resized_img)
                
                frame_count += 1
                
                # Display progress
                progress = len(captured_faces)
                cv2.putText(frame, f"Capturing: {progress}/{frames_total}", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 120, 255), 2)
                
                # Progress bar
                progress_percent = min(progress / frames_total, 1.0)
                bar_width = 200
                bar_height = 20
                filled_width = int(bar_width * progress_percent)
                
                cv2.rectangle(frame, (10, 40), (10 + bar_width, 40 + bar_height), (200, 200, 200), -1)
                cv2.rectangle(frame, (10, 40), (10 + filled_width, 40 + bar_height), (0, 255, 0), -1)
        
        # Convert to JPEG
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        
        # Yield the frame in bytes
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        success, message = verify_login(email, password)
        
        if success:
            session['email'] = email
            
            # Check if voter details exist
            voter = get_voter_by_email(email)
            if voter:
                session['aadhar_id'] = voter['aadhar_id']
                session['voter_id'] = voter['voter_id']
                return redirect(url_for('face_recognition'))
            else:
                return redirect(url_for('voter_registration'))
        else:
            flash(message, 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')
        
        success, message = register_user(email, password)
        
        if success:
            flash(message, 'success')
            session['email'] = email
            return redirect(url_for('voter_registration'))
        else:
            flash(message, 'danger')
    
    return render_template('register.html')

@app.route('/voter-registration', methods=['GET', 'POST'])
def voter_registration():
    if 'email' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        voter_id = request.form.get('voter_id')
        aadhar_id = request.form.get('aadhar_id')
        
        # Validate Aadhar ID format
        if not is_valid_aadhar_id(aadhar_id):
            flash('Invalid Aadhar ID format. It must be 12 digits.', 'danger')
            return render_template('voter_registration.html')
        
        # Validate Voter ID format
        if not is_valid_voter_id(voter_id):
            flash('Invalid Voter ID format. It must be 10 characters with both letters and numbers.', 'danger')
            return render_template('voter_registration.html')
        
        # Standardize format (remove spaces)
        aadhar_id = aadhar_id.replace(" ", "")
        voter_id = voter_id.replace(" ", "").upper()
        
        # Check if this Aadhar ID has already voted
        votes_df = pd.read_excel(VOTES_FILE)
        if aadhar_id in votes_df['aadhar_id'].values:
            flash('This Aadhar ID has already been used for voting. Each person can vote only once.', 'danger')
            return render_template('voter_registration.html')
        
        success, message = register_voter(session['email'], voter_id, aadhar_id)
        
        if success:
            flash(message, 'success')
            session['aadhar_id'] = aadhar_id
            session['voter_id'] = voter_id
            return redirect(url_for('face_capture'))
        else:
            flash(message, 'danger')
    
    return render_template('voter_registration.html')

@app.route('/face-capture')
def face_capture():
    if 'email' not in session or 'aadhar_id' not in session or 'voter_id' not in session:
        flash('Please complete your voter registration first', 'warning')
        return redirect(url_for('voter_registration'))
    
    # Check if already voted
    if has_voted(session['aadhar_id']):
        flash('You have already cast your vote', 'warning')
        return redirect(url_for('already_voted'))
    
    global captured_faces, is_capturing, frame_count
    captured_faces = []
    is_capturing = False
    frame_count = 0
    
    return render_template('face_capture.html')

@app.route('/start-capture', methods=['POST'])
def start_capture():
    global is_capturing, frame_count
    is_capturing = True
    frame_count = 0
    return jsonify({'status': 'success'})

@app.route('/check-capture-status')
def check_capture_status():
    global captured_faces, is_capturing
    
    if len(captured_faces) >= frames_total:
        is_capturing = False
        
        # Process captured faces
        faces_data = np.asarray(captured_faces)
        faces_data = faces_data.reshape((len(faces_data), -1))
        
        # Save face data with both aadhar_id and voter_id
        success, message = save_face_data(session['aadhar_id'], session['voter_id'], faces_data)
        
        if success:
            return jsonify({
                'status': 'complete',
                'message': 'Face capture complete'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': message
            })
    
    return jsonify({
        'status': 'in_progress',
        'progress': len(captured_faces),
        'total': frames_total
    })

@app.route('/face-recognition')
def face_recognition():
    if 'email' not in session or 'aadhar_id' not in session or 'voter_id' not in session:
        flash('Please complete your voter registration first', 'warning')
        return redirect(url_for('voter_registration'))
    
    # Check if already voted
    if has_voted(session['aadhar_id']):
        flash('You have already cast your vote', 'warning')
        return redirect(url_for('already_voted'))
    
    return render_template('face_recognition.html')

@app.route('/recognize-face', methods=['POST'])
def recognize_face():
    # Train the model
    model = train_model()
    if model is None:
        return jsonify({
            'status': 'error',
            'message': 'No face data available for recognition'
        })
    
    # Get the image from the request
    file = request.files.get('image')
    if not file:
        return jsonify({
            'status': 'error',
            'message': 'No image provided'
        })
    
    # Read and process the image
    img_array = np.frombuffer(file.read(), np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    
    # Detect face
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_detector.detectMultiScale(gray, 1.3, 5)
    
    if len(faces) == 0:
        return jsonify({
            'status': 'error',
            'message': 'No face detected in the image'
        })
    
    # Process the first detected face
    x, y, w, h = faces[0]
    crop_img = img[y:y+h, x:x+w]
    resized_img = cv2.resize(crop_img, (50, 50))
    flattened_img = resized_img.flatten().reshape(1, -1)
    
    # Load all face data to check for any matches
    try:
        with open(FACES_DATA_FILE, 'rb') as f:
            all_faces = pickle.load(f)
        with open(NAMES_FILE, 'rb') as f:
            all_names = pickle.load(f)
            
        # Create a KNN model with all faces
        all_faces_model = KNeighborsClassifier(n_neighbors=1)
        all_faces_model.fit(all_faces, all_names)
        
        # Find the closest match and its distance
        distances, indices = all_faces_model.kneighbors(flattened_img)
        closest_distance = distances[0][0]
        closest_match_idx = indices[0][0]
        closest_match_id = all_names[closest_match_idx]
        
        # Check if the face matches any registered face (not just the current Aadhar ID)
        threshold = 2000  # Same threshold as in check_face_exists
        if closest_distance < threshold:
            # If the face matches a different Aadhar ID than the current session
            if closest_match_id != session['aadhar_id']:
                return jsonify({
                    'status': 'error',
                    'message': f'This face appears to be registered with a different Aadhar ID: {closest_match_id}. Multiple voting attempts are not allowed.'
                })
            
            # If the face matches the current Aadhar ID
            # Check if this Aadhar ID has already voted
            if has_voted(session['aadhar_id']):
                return jsonify({
                    'status': 'error',
                    'message': 'You have already cast your vote with this Aadhar ID'
                })
            
            return jsonify({
                'status': 'success',
                'message': 'Face recognized successfully'
            })
        else:
            # No close match found - this could be a new face or poor quality image
            return jsonify({
                'status': 'error',
                'message': 'Face recognition failed. Your face does not match your registered profile. Please ensure proper lighting and positioning.'
            })
            
    except Exception as e:
        logging.error(f"Error in face recognition: {e}")
        # Fallback to the original prediction method if there's an error
        predicted_id = model.predict(flattened_img)[0]
        
        # Check if the predicted ID matches the session Aadhar ID
        if predicted_id == session['aadhar_id']:
            # Check if this Aadhar ID has already voted
            if has_voted(session['aadhar_id']):
                return jsonify({
                    'status': 'error',
                    'message': 'You have already cast your vote with this Aadhar ID'
                })
            
            return jsonify({
                'status': 'success',
                'message': 'Face recognized successfully'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Face recognition failed. The face does not match your registered Aadhar ID.'
            })

@app.route('/voting')
def voting():
    if 'email' not in session or 'aadhar_id' not in session or 'voter_id' not in session:
        flash('Please complete your voter registration and face verification first', 'warning')
        return redirect(url_for('voter_registration'))
    
    # Check if already voted
    if has_voted(session['aadhar_id']):
        flash('You have already cast your vote', 'warning')
        return redirect(url_for('already_voted'))
    
    # Define candidates for the election
    candidates = [
        ('BJP', 'Bharatiya Janata Party'),
        ('Congress', 'Indian National Congress'),
        ('AAP', 'Aam Aadmi Party'),
        ('NOTA', 'None of the Above')
    ]
    
    return render_template('voting.html', candidates=candidates)

@app.route('/cast-vote', methods=['POST'])
def cast_vote():
    try:
        if 'email' not in session or 'aadhar_id' not in session or 'voter_id' not in session:
            flash('Please complete your voter registration and face verification first', 'warning')
            return redirect(url_for('voter_registration'))
        
        # Double-check if already voted
        if has_voted(session.get('aadhar_id')):
            flash('You have already cast your vote', 'warning')
            return redirect(url_for('already_voted'))
        
        party = request.form.get('party')
        
        # Verify that the party is valid
        valid_parties = ['BJP', 'Congress', 'AAP', 'NOTA']
        if party not in valid_parties:
            flash('Invalid party selection', 'danger')
            return redirect(url_for('voting'))
        
        success, message = record_vote(session.get('aadhar_id'), party)
        
        if success:
            try:
                aadhar_id_safe = str(session.get('aadhar_id', 'unknown')).encode('utf-8', errors='replace').decode('utf-8')
                voter_id_safe = str(session.get('voter_id', 'unknown')).encode('utf-8', errors='replace').decode('utf-8')
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                logging.info(f"Vote recorded for Aadhar ID: {aadhar_id_safe}, Voter ID: {voter_id_safe}, Time: {current_time}")
            except Exception as e:
                error_msg = str(e).encode('utf-8', errors='replace').decode('utf-8')
                logging.error(f"Error logging vote: {error_msg}")
            
            flash(message, 'success')
            return redirect(url_for('thank_you'))
        else:
            flash(message, 'danger')
            return redirect(url_for('voting'))
    except Exception as e:
        error_msg = str(e).encode('utf-8', errors='replace').decode('utf-8')
        logging.error(f"Unexpected error in cast_vote: {error_msg}")
        flash("An unexpected error occurred. Please try again.", 'danger')
        return redirect(url_for('voting'))

@app.route('/thank-you')
def thank_you():
    if 'email' not in session:
        return redirect(url_for('login'))
    
    return render_template('thank_you.html')

@app.route('/already-voted')
def already_voted():
    return render_template('already_voted.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/video-feed')
def video_feed():
    """Video streaming route"""
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/stop-camera')
def stop_camera():
    """Stop the camera"""
    global camera
    if camera is not None:
        camera.release()
        camera = None
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(debug=True)
