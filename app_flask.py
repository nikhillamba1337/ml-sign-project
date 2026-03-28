from flask import Flask, request, jsonify
import cv2
import numpy as np
import pickle
import mediapipe as mp
import base64
from io import BytesIO
import os
import logging

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load model
MODEL_PATH = 'model.p'
model = None
mp_hands = None
hands = None

def load_model():
    """Load the trained classifier model"""
    global model
    try:
        # Load model as dictionary
        with open(MODEL_PATH, 'rb') as f:
            model_dict = pickle.load(f)
            model = model_dict['model']
        logger.info("Model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return False
    return True

def initialize_mediapipe():
    """Initialize MediaPipe hand detection"""
    global mp_hands, hands
    try:
        mp_hands = mp.solutions.hands
        hands = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.3,
            min_tracking_confidence=0.3
        )
        logger.info("MediaPipe initialized")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize MediaPipe: {e}")
        return False

# Load model and MediaPipe on startup
if not load_model():
    logger.error("Could not load model on startup")
if not initialize_mediapipe():
    logger.error("Could not initialize MediaPipe on startup")

# Label mapping (A-Z)
labels_dict = {i: chr(65 + i) for i in range(26)}

@app.route('/')
def index():
    """Serve the main page from root directory"""
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "index.html not found", 404

@app.route('/process_frame', methods=['POST'])
def process_frame():
    """Process a single frame from the camera"""
    if model is None or hands is None:
        return jsonify({'error': 'Model not loaded'}), 500
    
    try:
        # Get image from request
        data = request.json
        image_data = data.get('image')
        
        # Decode base64 image
        image_bytes = base64.b64decode(image_data.split(',')[1])
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return jsonify({'error': 'Failed to decode image'}), 400
        
        # Flip and convert color space
        frame = cv2.flip(frame, 1)
        h, w, c = frame.shape
        
        # Process with MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)
        
        detected_letter = None
        landmarks_data = None
        
        if results.multi_hand_landmarks and len(results.multi_hand_landmarks) > 0:
            landmarks = results.multi_hand_landmarks[0]
            
            # Extract coordinates
            x_coords = []
            y_coords = []
            landmark_points = []  # Store for drawing
            
            for lm in landmarks.landmark:
                x_coords.append(lm.x)
                y_coords.append(lm.y)
                landmark_points.append({'x': float(lm.x), 'y': float(lm.y)})
            
            # Normalize landmarks by subtracting min values (same as training)
            min_x = min(x_coords)
            min_y = min(y_coords)
            
            data_aux = []
            for lm in landmarks.landmark:
                data_aux.append(lm.x - min_x)
                data_aux.append(lm.y - min_y)
            
            # Ensure we have exactly 42 features
            if len(data_aux) == 42:
                try:
                    # Prepare input (same as original inference_classifier.py)
                    input_data = np.asarray([data_aux])
                    
                    # Predict (same logic as inference_classifier)
                    prediction = model.predict(input_data)
                    if isinstance(prediction[0], str):
                        predicted_character = prediction[0]
                    else:
                        predicted_character = labels_dict[int(prediction[0])]
                    
                    # Get confidence if available
                    try:
                        probabilities = model.predict_proba(input_data)
                        conf_score = float(np.max(probabilities[0]))
                    except:
                        conf_score = 0.75
                    
                    detected_letter = {
                        'letter': predicted_character,
                        'confidence': round(conf_score, 2)
                    }
                    
                    # Bounding box coordinates
                    x_min, x_max = min(x_coords), max(x_coords)
                    y_min, y_max = min(y_coords), max(y_coords)
                    
                    landmarks_data = {
                        'points': landmark_points,
                        'x_min': float(x_min),
                        'x_max': float(x_max),
                        'y_min': float(y_min),
                        'y_max': float(y_max),
                        'letter': predicted_character
                    }
                except Exception as pred_error:
                    logger.error(f"Prediction error: {pred_error}")
        
        return jsonify({
            'status': 'success',
            'detected_letter': detected_letter,
            'landmarks': landmarks_data
        })
    
    except Exception as e:
        logger.error(f"Error processing frame: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'model_loaded': model is not None,
        'mediapipe_ready': hands is not None
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
