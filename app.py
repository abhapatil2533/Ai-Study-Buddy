import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
from PIL import Image

# Setup
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# UI Settings
st.set_page_config(page_title="AI Study Buddy", layout="wide")

st.title("🎓 AI Study Buddy")
st.write("Input your notes or textbook images to get explanations, quizzes, and flashcards.")

# Get available models
@st.cache_data
def get_available_models():
    try:
        models = genai.list_models()
        # Filter for models that support generateContent
        valid_models = []
        for model in models:
            if 'generateContent' in model.supported_generation_methods:
                # Clean up the model name for display
                display_name = model.name.replace('models/', '')
                valid_models.append({
                    'full_name': model.name,
                    'display_name': display_name
                })
        return valid_models
    except Exception as e:
        st.error(f"Error fetching models: {e}")
        return []

# Sidebar
with st.sidebar:
    st.header("Menu")
    choice = st.radio("Select Action:", 
                      ["Explain Concept", "Generate Quiz", "Make Flashcards"])
    
    # Model selection dropdown
    st.divider()
    st.subheader("Model Settings")
    available_models = get_available_models()
    
    if available_models:
        model_options = [m['display_name'] for m in available_models]
        selected_model = st.selectbox(
            "Choose AI Model:",
            model_options,
            index=0 if model_options else None
        )
    else:
        st.warning("No models found. Using default model name.")
        selected_model = "gemini-pro"  # fallback

# Input Section
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Input Section")
    text_input = st.text_area("Paste text here...", height=200)
    image_input = st.file_uploader("Upload image", type=['png', 'jpg', 'jpeg'])
    
    if image_input:
        img = Image.open(image_input)
        st.image(img, use_container_width=True)

# Main Logic
if st.button("Start Processing"):
    if not text_input and not image_input:
        st.error("Please provide text or an image first.")
    else:
        with st.spinner("Processing... (this may take 10-30 seconds)"):
            try:
                # Use the selected model
                if available_models:
                    # Find the full model name from selection
                    selected_full = next(
                        m['full_name'] for m in available_models 
                        if m['display_name'] == selected_model
                    )
                    model = genai.GenerativeModel(selected_full)
                else:
                    # Fallback to try common model names
                    model_names_to_try = [
                        'gemini-1.5-flash',
                        'gemini-1.5-pro',
                        'gemini-1.0-pro',
                        'gemini-pro'
                    ]
                    model = None
                    for model_name in model_names_to_try:
                        try:
                            model = genai.GenerativeModel(model_name)
                            st.sidebar.success(f"Using model: {model_name}")
                            break
                        except:
                            continue
                    
                    if model is None:
                        st.error("Could not find any working model. Please check your API key and permissions.")
                        st.stop()
                
                prompts = {
                    "Explain Concept": "Summarize this content into easy bullet points and explain complex terms simply.",
                    "Generate Quiz": "Create 5 multiple choice questions with answers based on this content.",
                    "Make Flashcards": "Create 5 Question & Answer pairs from this content."
                }
                
                final_input = [prompts[choice]]
                if text_input: 
                    # Truncate if too long
                    text = text_input[:10000] if len(text_input) > 10000 else text_input
                    final_input.append(text)
                if image_input: 
                    final_input.append(img)
                
                response = model.generate_content(final_input)
                
                with col2:
                    st.subheader("Result")
                    st.markdown(response.text)
                    
            except Exception as e:
                st.error(f"Error: {e}")
                st.info("Try selecting a different model from the sidebar dropdown.")