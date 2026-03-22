import streamlit as st
import pickle
import numpy as np
import os
import time
import sys

# Suppress warnings
import warnings
warnings.filterwarnings('ignore')

# Check if running on Streamlit Cloud (no camera support)
is_streamlit_cloud = os.environ.get('STREAMLIT_SERVER_HEADLESS', '').lower() == 'true'

# Page configuration
st.set_page_config(page_title="Sign Language Detector", layout="wide", initial_sidebar_state="collapsed")

# Show deployment warning
if is_streamlit_cloud:
    st.error("""
    ⚠️ **This app requires a local installation with camera access**
    
    Streamlit Cloud doesn't support webcam access (it's a headless server).
    
    **To use this app:**
    1. Clone the repository to your computer
    2. Install dependencies: `pip install -r requirements.txt`
    3. Run locally: `streamlit run app.py`
    4. Access at: http://localhost:8501
    
    This will give you full access to your camera for real-time sign language detection.
    """)
    st.stop()

# Import CV2 for local deployment
try:
    import cv2
    import mediapipe as mp
except ImportError as e:
    st.error(f"""
    ❌ **Import Error: {str(e)}**
    
    Please install required packages:
    ```bash
    pip install -r requirements.txt
    ```
    """)
    st.stop()

# Title Section
st.title("🤟 Real-Time Sign Language Detector")

# Global keyboard event listener
st.markdown("""
<script>
document.addEventListener('keydown', function(e) {
    const key = e.key.toLowerCase();
    
    const buttonMap = {
        'w': 'Start Detection',   // W = Start/Stop
        's': 'Add Letter',         // S = Add letter
        'b': 'Delete',             // B = Delete
        'v': 'Add Space',          // V = Space
        'c': 'Clear All',          // C = Clear
        'q': 'Stop Detection'      // Q = Stop
    };
    
    if(buttonMap[key]) {
        e.preventDefault();
        
        // Find and click the button
        const buttons = document.querySelectorAll('button');
        for(let btn of buttons) {
            const btnText = (btn.innerText || btn.textContent || '').trim();
            if(btnText === buttonMap[key]) {
                btn.click();
                console.log('🎹 Key ' + key.toUpperCase() + ' → ' + buttonMap[key]);
                break;
            }
        }
    }
}, true); // Capture phase for reliability
</script>
""", unsafe_allow_html=True)

# Load model with error handling
@st.cache_resource
def load_model():
    try:
        model_path = './model.p'
        if not os.path.exists(model_path):
            st.error(f"Model file not found at {model_path}")
            return None
        
        # Try loading with joblib first (better for sklearn models)
        try:
            import joblib
            model_dict = joblib.load(model_path)
            return model_dict.get('model', model_dict) if isinstance(model_dict, dict) else model_dict
        except:
            # Fallback to pickle
            with open(model_path, 'rb') as f:
                model_dict = pickle.load(f, encoding='latin1')
            return model_dict.get('model', model_dict) if isinstance(model_dict, dict) else model_dict
    except Exception as e:
        st.error(f"Error loading model: {str(e)}")
        return None

# Initialize MediaPipe
@st.cache_resource
def initialize_mediapipe():
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        static_image_mode=False, 
        max_num_hands=2,
        min_detection_confidence=0.3,
        min_tracking_confidence=0.3
    )
    return hands, mp_hands

model = load_model()
if model is None:
    st.error("Failed to load model. Please check model.p file.")
    st.stop()

hands, mp_hands = initialize_mediapipe()

# Labels dictionary
labels_dict = {i: chr(65 + i) for i in range(26)}

# Session state initialization
if "stored_letters" not in st.session_state:
    st.session_state.stored_letters = []
if "detection_running" not in st.session_state:
    st.session_state.detection_running = False
if "current_letter" not in st.session_state:
    st.session_state.current_letter = ""

# Callback functions for buttons (no rerun - smooth operation)
def toggle_detection():
    st.session_state.detection_running = not st.session_state.detection_running

def add_letter_action():
    st.session_state.action_add_letter = True

def delete_letter_action():
    st.session_state.action_delete = True

def add_space_action():
    st.session_state.action_space = True

def clear_all_action():
    st.session_state.action_clear = True

def stop_detection_action():
    st.session_state.action_stop = True

# Session state for keyboard actions
if "action_add_letter" not in st.session_state:
    st.session_state.action_add_letter = False
if "action_delete" not in st.session_state:
    st.session_state.action_delete = False
if "action_space" not in st.session_state:
    st.session_state.action_space = False
if "action_clear" not in st.session_state:
    st.session_state.action_clear = False
if "action_stop" not in st.session_state:
    st.session_state.action_stop = False

# Control buttons with callbacks (no rerun)
col_hidden1, col_hidden2, col_hidden3, col_hidden4, col_hidden5, col_hidden6 = st.columns(6)

with col_hidden1:
    st.button("Start Detection", key="start", on_click=toggle_detection)
with col_hidden2:
    st.button("Add Letter", key="add", on_click=add_letter_action)
with col_hidden3:
    st.button("Delete", key="delete", on_click=delete_letter_action)
with col_hidden4:
    st.button("Add Space", key="space", on_click=add_space_action)
with col_hidden5:
    st.button("Clear All", key="clear", on_click=clear_all_action)
with col_hidden6:
    st.button("Stop Detection", key="stop", on_click=stop_detection_action)

# Main Layout - Two column layout
col_video, col_info = st.columns([2, 1], gap="medium")

with col_video:
    st.subheader("📹 Live Detection")
    frame_display = st.empty()

with col_info:
    st.subheader("📋 Detected Text")
    text_display = st.empty()
    
    st.subheader("⚙️ Keyboard Shortcuts")
    st.write("**W:** Start Detection")
    st.write("**S:** Add Letter")
    st.write("**B:** Delete Letter")
    st.write("**V:** Add Space")
    st.write("**C:** Clear All")
    st.write("**Q:** Stop Detection")

# Display text and controls
text_content = ''.join(st.session_state.stored_letters)
with text_display.container():
    st.text_input("Detected Text:", value=text_content, disabled=True)

predicted_character = ""

# Real-time detection
if st.session_state.detection_running:
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        st.error("❌ Camera not accessible. Please enable camera access.")
        st.stop()
    
    # Set camera properties
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles
    
    frame_count = 0
    
    while st.session_state.detection_running:
        ret, frame = cap.read()
        
        if not ret or frame is None:
            st.error("Failed to capture frame")
            break
        
        frame_count += 1
        
        # Initialize for each frame
        data_aux = []
        x_ = []
        y_ = []
        predicted_character = ""
        
        H, W, C = frame.shape
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process with MediaPipe
        results = hands.process(frame_rgb)
        
        # Detection logic from inference_classifier.py
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Draw landmarks
                mp_drawing.draw_landmarks(
                    frame,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                    mp_drawing_styles.get_default_hand_landmarks_style(),
                    mp_drawing_styles.get_default_hand_connections_style()
                )
                
                # Collect x, y coordinates
                for i in range(len(hand_landmarks.landmark)):
                    x = hand_landmarks.landmark[i].x
                    y = hand_landmarks.landmark[i].y
                    x_.append(x)
                    y_.append(y)
                
                # Normalize coordinates
                for i in range(len(hand_landmarks.landmark)):
                    x = hand_landmarks.landmark[i].x
                    y = hand_landmarks.landmark[i].y
                    data_aux.append(x - min(x_))
                    data_aux.append(y - min(y_))
        
        # Make prediction if hand detected
        if data_aux:
            # Pad/truncate to fixed size
            fixed_size = 42
            if len(data_aux) < fixed_size:
                data_aux = data_aux + [0] * (fixed_size - len(data_aux))
            elif len(data_aux) > fixed_size:
                data_aux = data_aux[:fixed_size]
            
            # Calculate bounding box
            if x_ and y_:
                x1 = int(min(x_) * W) - 10
                y1 = int(min(y_) * H) - 10
                x2 = int(max(x_) * W) - 10
                y2 = int(max(y_) * H) - 10
                
                try:
                    # Predict
                    prediction = model.predict([np.asarray(data_aux)])
                    if isinstance(prediction[0], str):
                        predicted_character = prediction[0]
                    else:
                        predicted_character = labels_dict[int(prediction[0])]
                    
                    # Draw bounding box and label
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 0), 4)
                    cv2.putText(frame, predicted_character, (x1, y1 - 10),
                               cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 0, 0), 3, cv2.LINE_AA)
                    
                    # Store current letter for display
                    st.session_state.current_letter = predicted_character
                    
                    # Handle keyboard input immediately after prediction (like cv2.waitKey in original)
                    if st.session_state.action_add_letter:
                        # S key: Add detected character
                        st.session_state.stored_letters.append(predicted_character)
                        st.session_state.action_add_letter = False
                    
                except AttributeError:
                    pass
                except Exception as e:
                    pass
        
        # Handle other keyboard actions that don't require prediction
        if st.session_state.action_delete:
            # B key: Delete last letter
            if st.session_state.stored_letters:
                st.session_state.stored_letters.pop()
            st.session_state.action_delete = False
        
        if st.session_state.action_space:
            # V key: Add space
            st.session_state.stored_letters.append(' ')
            st.session_state.action_space = False
        
        if st.session_state.action_clear:
            # C key: Clear all
            st.session_state.stored_letters.clear()
            st.session_state.current_letter = ""
            st.session_state.detection_running = False
            st.session_state.action_clear = False
        
        if st.session_state.action_stop:
            # Q key: Stop detection
            st.session_state.detection_running = False
            st.session_state.action_stop = False
            break
        
        # Draw text box at bottom (matching original script)
        text_content = ''.join(st.session_state.stored_letters)
        cv2.rectangle(frame, (10, H - 60), (W - 10, H - 10), (255, 255, 255), -1)
        cv2.rectangle(frame, (10, H - 60), (W - 10, H - 10), (0, 0, 0), 2)
        cv2.putText(frame, text_content, (20, H - 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2, cv2.LINE_AA)
        
        # Convert RGB for display
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_display.image(frame_rgb, use_container_width=True)
        
        # Update text display in real-time
        text_content = ''.join(st.session_state.stored_letters)
        with text_display.container():
            st.text_input("Detected Text:", value=text_content, disabled=True, key=f"text_{frame_count}")
        
        # Control framerate
        time.sleep(0.03)
    
    cap.release()
    st.session_state.detection_running = False
