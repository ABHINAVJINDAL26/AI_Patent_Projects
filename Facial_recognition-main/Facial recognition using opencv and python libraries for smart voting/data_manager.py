import os
import pandas as pd
import bcrypt
import pickle
import numpy as np
from datetime import datetime

class DataManager:
    def __init__(self):
        # Create necessary directories
        if not os.path.exists('data/'):
            os.makedirs('data/')
        
        # Initialize data files
        self.users_file = 'data/users.xlsx'
        self.voters_file = 'data/voters.xlsx'
        self.votes_file = 'data/votes.xlsx'
        self.faces_data_file = 'data/faces_data.pkl'
        self.names_file = 'data/names.pkl'
        
        # Create files if they don't exist
        self._initialize_files()
    
    def _initialize_files(self):
        # Initialize users file
        if not os.path.exists(self.users_file):
            users_df = pd.DataFrame(columns=['email', 'password', 'registration_date'])
            users_df.to_excel(self.users_file, index=False)
        
        # Initialize voters file
        if not os.path.exists(self.voters_file):
            voters_df = pd.DataFrame(columns=['email', 'voter_id', 'aadhar_id', 'registration_date'])
            voters_df.to_excel(self.voters_file, index=False)
        
        # Initialize votes file
        if not os.path.exists(self.votes_file):
            votes_df = pd.DataFrame(columns=['aadhar_id', 'party', 'date', 'time'])
            votes_df.to_excel(self.votes_file, index=False)
    
    def register_user(self, email, password):
        """Register a new user with email and password"""
        # Check if email already exists
        users_df = pd.read_excel(self.users_file)
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
        users_df.to_excel(self.users_file, index=False)
        
        return True, "User registered successfully"
    
    def verify_login(self, email, password):
        """Verify user login credentials"""
        users_df = pd.read_excel(self.users_file)
        
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
    
    def register_voter(self, email, voter_id, aadhar_id):
        """Register voter ID and Aadhar ID for a user"""
        voters_df = pd.read_excel(self.voters_file)
        
        # Check if Aadhar ID already exists
        if aadhar_id in voters_df['aadhar_id'].values:
            return False, "Aadhar ID already registered"
        
        # Check if Voter ID already exists
        if voter_id in voters_df['voter_id'].values:
            return False, "Voter ID already registered"
        
        # Add new voter
        new_voter = pd.DataFrame({
            'email': [email],
            'voter_id': [voter_id],
            'aadhar_id': [aadhar_id],
            'registration_date': [datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
        })
        
        voters_df = pd.concat([voters_df, new_voter], ignore_index=True)
        voters_df.to_excel(self.voters_file, index=False)
        
        return True, "Voter registered successfully"
    
    def save_face_data(self, aadhar_id, face_data):
        """Save facial recognition data"""
        # Load existing data if available
        faces_data = []
        names = []
        
        if os.path.exists(self.faces_data_file) and os.path.exists(self.names_file):
            with open(self.faces_data_file, 'rb') as f:
                faces_data = pickle.load(f)
            with open(self.names_file, 'rb') as f:
                names = pickle.load(f)
        
        # Add new face data
        faces_data = np.append(faces_data, face_data, axis=0) if len(faces_data) > 0 else face_data
        names = names + [aadhar_id] * len(face_data)
        
        # Save updated data
        with open(self.faces_data_file, 'wb') as f:
            pickle.dump(faces_data, f)
        with open(self.names_file, 'wb') as f:
            pickle.dump(names, f)
        
        return True, "Face data saved successfully"
    
    def record_vote(self, aadhar_id, party):
        """Record a vote"""
        votes_df = pd.read_excel(self.votes_file)
        
        # Check if already voted
        if aadhar_id in votes_df['aadhar_id'].values:
            return False, "You have already cast your vote"
        
        # Record vote
        now = datetime.now()
        new_vote = pd.DataFrame({
            'aadhar_id': [aadhar_id],
            'party': [party],
            'date': [now.strftime("%Y-%m-%d")],
            'time': [now.strftime("%H:%M:%S")]
        })
        
        votes_df = pd.concat([votes_df, new_vote], ignore_index=True)
        votes_df.to_excel(self.votes_file, index=False)
        
        return True, "Vote recorded successfully"
    
    def has_voted(self, aadhar_id):
        """Check if a voter has already cast their vote"""
        votes_df = pd.read_excel(self.votes_file)
        return aadhar_id in votes_df['aadhar_id'].values
    
    def get_voter_by_email(self, email):
        """Get voter details by email"""
        voters_df = pd.read_excel(self.voters_file)
        voter = voters_df[voters_df['email'] == email]
        if voter.empty:
            return None
        return voter.iloc[0].to_dict()
    
    def get_voter_by_aadhar(self, aadhar_id):
        """Get voter details by Aadhar ID"""
        voters_df = pd.read_excel(self.voters_file)
        voter = voters_df[voters_df['aadhar_id'] == aadhar_id]
        if voter.empty:
            return None
        return voter.iloc[0].to_dict()
