from flask import Flask, request, jsonify
import cv2
import numpy as np
import pickle
import mediapipe as mp
import base64
import os
import logging

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'model.p')
model = None
mp_hands = None
hands = None


def load_model():
    """Load the trained classifier model with sklearn cross-version compatibility patch."""
    global model
    try:
        with open(MODEL_PATH, 'rb') as f:
            model_dict = pickle.load(f)
        model = model_dict['model']

        # ---------------------------------------------------------------
        # CRITICAL FIX: model.p was trained with scikit-learn 1.3.x.
        # Newer sklearn versions added `monotonic_cst` to DecisionTree,
        # which causes AttributeError in predict() / predict_proba().
        # We patch the missing attribute on every tree estimator so the
        # model works on any scikit-learn version without reinstalling.
        # ---------------------------------------------------------------
        patched = 0
        for estimator in model.estimators_:
            if not hasattr(estimator, 'monotonic_cst'):
                estimator.monotonic_cst = None
                patched += 1
        if patched:
            logger.info(f"Patched {patched} tree estimator(s) for sklearn compatibility")

        logger.info(
            f"Model loaded: {type(model).__name__}, "
            f"features={model.n_features_in_}, classes={list(model.classes_)}"
        )
        return True
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return False


def initialize_mediapipe():
    """Initialize MediaPipe hand detection."""
    global mp_hands, hands
    try:
        mp_hands = mp.solutions.hands
        # static_image_mode=False gives better accuracy for sequential frames
        # (same setting as the original inference_classifier.py)
        hands = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.3,
            min_tracking_confidence=0.3,
        )
        logger.info("MediaPipe Hands initialized")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize MediaPipe: {e}")
        return False


# Initialise on startup
if not load_model():
    logger.error("Could not load model on startup")
if not initialize_mediapipe():
    logger.error("Could not initialize MediaPipe on startup")


@app.route('/')
def index():
    """Serve the main HTML page."""
    html_path = os.path.join(os.path.dirname(__file__), 'index.html')
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            return f.read(), 200, {'Content-Type': 'text/html; charset=utf-8'}
    except FileNotFoundError:
        return "index.html not found", 404


@app.route('/process_frame', methods=['POST'])
def process_frame():
    """
    Receive a base64-encoded JPEG frame from the browser, run MediaPipe hand
    detection, extract the same 42-feature vector used during training
    (x - min_x, y - min_y for all 21 landmarks), and return the prediction.

    Feature extraction mirrors inference_classifier.py exactly:
      - iterate landmarks once to collect x_, y_
      - iterate again to build data_aux with (lm.x - min(x_), lm.y - min(y_))
      - pad / truncate to exactly 42 values
    """
    if model is None or hands is None:
        return jsonify({'error': 'Model or MediaPipe not ready'}), 500

    try:
        data = request.json
        if not data or 'image' not in data:
            return jsonify({'error': 'No image data received'}), 400

        image_data = data['image']

        # Strip the data-URL prefix ("data:image/jpeg;base64,...")
        if ',' in image_data:
            image_data = image_data.split(',')[1]

        # Decode to OpenCV frame
        image_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if frame is None:
            return jsonify({'error': 'Failed to decode image'}), 400

        H, W, _ = frame.shape
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)

        detected_letter = None
        landmarks_data = None

        if results.multi_hand_landmarks:
            # Use only the first detected hand (same as inference_classifier.py
            # when only one hand is visible)
            hand_landmarks = results.multi_hand_landmarks[0]

            # -----------------------------------------------------------
            # Feature extraction — identical to inference_classifier.py
            # -----------------------------------------------------------
            x_ = []
            y_ = []
            for lm in hand_landmarks.landmark:
                x_.append(lm.x)
                y_.append(lm.y)

            min_x = min(x_)
            min_y = min(y_)

            data_aux = []
            landmark_points = []
            for lm in hand_landmarks.landmark:
                data_aux.append(lm.x - min_x)
                data_aux.append(lm.y - min_y)
                landmark_points.append({'x': float(lm.x), 'y': float(lm.y)})

            # Pad / truncate to exactly 42 values (21 landmarks × 2 coords)
            fixed_size = 42
            if len(data_aux) < fixed_size:
                data_aux += [0.0] * (fixed_size - len(data_aux))
            else:
                data_aux = data_aux[:fixed_size]

            # Bounding box in normalised coords
            x_min, x_max = min(x_), max(x_)
            y_min, y_max = min(y_), max(y_)

            landmarks_data = {
                'points': landmark_points,
                'x_min': float(x_min),
                'x_max': float(x_max),
                'y_min': float(y_min),
                'y_max': float(y_max),
                'letter': '?',
            }

            # -----------------------------------------------------------
            # Prediction — identical logic to inference_classifier.py
            # -----------------------------------------------------------
            try:
                input_arr = np.asarray([data_aux])
                prediction = model.predict(input_arr)

                # Model classes are strings ('A'…'Z')
                predicted_character = str(prediction[0])

                try:
                    probabilities = model.predict_proba(input_arr)
                    conf_score = float(np.max(probabilities[0]))
                except Exception as proba_err:
                    logger.warning(f"predict_proba failed: {proba_err}")
                    conf_score = 0.75

                detected_letter = {
                    'letter': predicted_character,
                    'confidence': round(conf_score, 4),
                }
                landmarks_data['letter'] = predicted_character

            except Exception as pred_err:
                logger.error(f"Prediction error: {pred_err}")

        return jsonify({
            'status': 'success',
            'detected_letter': detected_letter,
            'landmarks': landmarks_data,
        })

    except Exception as e:
        logger.error(f"process_frame error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'model_loaded': model is not None,
        'mediapipe_ready': hands is not None,
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
