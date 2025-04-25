import os
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

# Create images directory if it doesn't exist
if not os.path.exists('static/images'):
    os.makedirs('static/images')

# Function to create a colored image with text
def create_image(filename, text, width=640, height=360, bg_color=(53, 106, 195), text_color=(255, 255, 255)):
    # Create a colored background image
    img = np.zeros((height, width, 3), dtype=np.uint8)
    img[:] = bg_color[::-1]  # BGR format for OpenCV
    
    # Convert to PIL Image for text
    pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_img)
    
    # Add text
    try:
        font = ImageFont.truetype("arial.ttf", 36)
    except IOError:
        font = ImageFont.load_default()
    
    # Calculate text position to center it
    text_width, text_height = draw.textsize(text, font=font) if hasattr(draw, 'textsize') else (width//2, height//2)
    position = ((width - text_width) // 2, (height - text_height) // 2)
    
    # Draw text
    draw.text(position, text, font=font, fill=text_color)
    
    # Save image
    pil_img.save(f'static/images/{filename}')
    print(f"Created image: static/images/{filename}")

# Create images for the application
images = [
    ('voting_banner.jpg', 'AI Smart Voting System', (41, 128, 185)),
    ('secure_auth.jpg', 'Secure Authentication', (46, 204, 113)),
    ('facial_recognition.jpg', 'AI Facial Recognition', (155, 89, 182)),
    ('transparent_voting.jpg', 'Transparent Voting', (211, 84, 0)),
    ('secure_voting.jpg', 'Secure Voting Process', (52, 152, 219)),
    ('registration.jpg', 'Voter Registration', (230, 126, 34)),
    ('voter_id.jpg', 'Voter ID Verification', (26, 188, 156)),
    ('ai_face_recognition.jpg', 'AI Face Recognition', (142, 68, 173)),
    ('secure_voting_ai.jpg', 'AI-Powered Security', (41, 128, 185)),
    ('vote_matters.jpg', 'Your Vote Matters', (39, 174, 96)),
    ('bjp.jpg', 'BJP', (255, 153, 51)),
    ('congress.jpg', 'Congress', (0, 120, 215)),
    ('aap.jpg', 'AAP', (0, 166, 107)),
    ('nota.jpg', 'NOTA', (136, 136, 136)),
    ('ai_voting.jpg', 'AI-Powered Voting', (52, 152, 219)),
    ('one_vote.jpg', 'One Person, One Vote', (211, 84, 0))
]

# Generate all images
for filename, text, bg_color in images:
    create_image(filename, text, bg_color=bg_color)

print("All images generated successfully!")
