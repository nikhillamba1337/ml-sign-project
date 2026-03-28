from flask import Flask, request, jsonify
import cv2
import numpy as np
import pickle
import mediapipe as mp
import base64
from io import BytesIO
import joblib
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
        # Try joblib first
        model = joblib.load(MODEL_PATH)
        if isinstance(model, dict) and 'model' in model:
            model = model['model']
        logger.info("Model loaded with joblib")
    except:
        # Fallback to pickle with latin1 encoding
        try:
            with open(MODEL_PATH, 'rb') as f:
                data = pickle.load(f, encoding='latin1')
                model = data if isinstance(data, object) else data.get('model', data)
            logger.info("Model loaded with pickle")
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
        hand_landmarks = None
        
        if results.multi_hand_landmarks and len(results.multi_hand_landmarks) > 0:
            landmarks = results.multi_hand_landmarks[0]
            
            # Extract and normalize landmarks
            data_aux = []
            for lm in landmarks.landmark:
                data_aux.append(lm.x)
                data_aux.append(lm.y)
            
            # Ensure we have exactly 42 features
            if len(data_aux) == 42:
                try:
                    # Prepare input
                    input_data = np.asarray([data_aux])
                    
                    # Predict
                    prediction = model.predict(input_data)
                    predicted_char = str(prediction[0])
                    
                    # Get confidence if available
                    try:
                        probabilities = model.predict_proba(input_data)
                        conf_score = float(np.max(probabilities[0]))
                    except:
                        conf_score = 0.75  # Default confidence for models without proba
                    
                    detected_letter = {
                        'letter': predicted_char,
                        'confidence': round(conf_score, 2)
                    }
                    
                    # Get bounding box
                    x_coords = [lm.x for lm in landmarks.landmark]
                    y_coords = [lm.y for lm in landmarks.landmark]
                    
                    x_min, x_max = min(x_coords), max(x_coords)
                    y_min, y_max = min(y_coords), max(y_coords)
                    
                    hand_landmarks = {
                        'x_min': float(x_min),
                        'x_max': float(x_max),
                        'y_min': float(y_min),
                        'y_max': float(y_max),
                        'letter': predicted_char
                    }
                except Exception as pred_error:
                    logger.error(f"Prediction error: {pred_error}")
        
        return jsonify({
            'status': 'success',
            'detected_letter': detected_letter,
            'hand_landmarks': hand_landmarks
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
