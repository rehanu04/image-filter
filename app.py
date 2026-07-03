import streamlit as st
from PIL import Image, ImageOps, ImageFilter, ImageEnhance
import segno
import io
import base64

# Set up Streamlit page config
st.set_page_config(
    page_title="Studio & QR Engine",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium styling using CSS injection
st.markdown("""
    <style>
        /* Modern font and text gradient */
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Outfit', sans-serif;
        }
        
        .main-title {
            font-size: 2.8rem;
            font-weight: 700;
            background: linear-gradient(135deg, #FF4B4B 0%, #8A2387 50%, #E94057 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
            text-align: center;
        }
        
        .subtitle {
            font-size: 1.1rem;
            color: #88888b;
            text-align: center;
            margin-bottom: 2rem;
        }
        
        /* Premium Card style */
        .info-card {
            background-color: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
        }
        
        /* Hover micro-animations for download buttons */
        div.stDownloadButton > button {
            background: linear-gradient(135deg, #FF4B4B 0%, #E94057 100%) !important;
            color: white !important;
            border-radius: 8px !important;
            border: none !important;
            font-weight: 600 !important;
            padding: 10px 24px !important;
            transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
            width: 100% !important;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
        }
        
        div.stDownloadButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 7px 14px rgba(233, 64, 87, 0.4) !important;
            background: linear-gradient(135deg, #FF6B6B 0%, #F27121 100%) !important;
        }

        /* Success & info message formatting */
        .custom-warning {
            background-color: rgba(255, 165, 0, 0.1);
            border: 1px solid orange;
            padding: 15px;
            border-radius: 8px;
            color: #FFA500;
            margin-bottom: 15px;
        }
    </style>
""", unsafe_allow_html=True)

# Helper function to resize callbacks maintaining aspect ratio
def update_width(orig_w, orig_h):
    if st.session_state.get('maintain_aspect', True):
        ratio = orig_h / orig_w
        st.session_state.resize_height = max(1, int(st.session_state.resize_width * ratio))

def update_height(orig_w, orig_h):
    if st.session_state.get('maintain_aspect', True):
        ratio = orig_w / orig_h
        st.session_state.resize_width = max(1, int(st.session_state.resize_height * ratio))

# Header Layout
st.markdown("<div class='main-title'>🎨 Image Studio & Universal QR Engine</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Refined workspace combining advanced image manipulation and dynamic QR code matrix generation.</div>", unsafe_allow_html=True)

# 1. WORKSPACE NAVIGATION
st.sidebar.markdown("### 🗺️ Navigation")
app_mode = st.sidebar.radio(
    "Choose Workspace Mode:",
    ["🎨 Advanced Image Studio", "🔮 Universal QR Engine"]
)

# ----------------------------------------------------
# MODE A: ADVANCED IMAGE STUDIO
# ----------------------------------------------------
if app_mode == "🎨 Advanced Image Studio":
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚙️ Studio Control Panel")
    
    # File Uploader
    uploaded_file = st.file_uploader(
        "Upload image to populate the studio canvas:", 
        type=["png", "jpg", "jpeg"]
    )
    
    if uploaded_file is not None:
        try:
            # Load original image
            original_image = Image.open(uploaded_file)
            original_width, original_height = original_image.size
            
            # Keep track of file in session state to handle resets on new uploads
            file_key = f"img_{uploaded_file.name}_{uploaded_file.size}"
            if st.session_state.get("current_image_key") != file_key:
                st.session_state.current_image_key = file_key
                st.session_state.resize_width = original_width
                st.session_state.resize_height = original_height
                st.session_state.crop_left = 0
                st.session_state.crop_right = original_width
                st.session_state.crop_top = 0
                st.session_state.crop_bottom = original_height
            
            # Layout Sidebar Controls
            st.sidebar.markdown("#### 🎨 Filters Panel")
            selected_filter = st.sidebar.selectbox(
                "Select Visual Filter Effect:",
                [
                    "Original", 
                    "Black & White", 
                    "Sepia Tone", 
                    "Gaussian Blur", 
                    "Contour Sketch",
                    "Vibrant Saturation", 
                    "Retro Negative", 
                    "Emboss Art"
                ]
            )
            
            # Interactive Filter Sub-Sliders
            blur_radius = 5
            saturation_factor = 2.0
            if selected_filter == "Gaussian Blur":
                blur_radius = st.sidebar.slider("Blur Radius (px)", 1, 30, 5)
            elif selected_filter == "Vibrant Saturation":
                saturation_factor = st.sidebar.slider("Saturation Factor", 0.0, 5.0, 2.0, 0.1)
            
            # Direct Manipulation Tools in Expanders
            st.sidebar.markdown("#### 🛠️ Canvas Tools")
            
            with st.sidebar.expander("✂️ Crop Settings", expanded=False):
                st.write(f"Dimensions: {original_width}x{original_height} px")
                crop_x = st.slider(
                    "Horizontal Crop Boundary (px)", 
                    0, original_width, 
                    (st.session_state.crop_left, st.session_state.crop_right)
                )
                crop_y = st.slider(
                    "Vertical Crop Boundary (px)", 
                    0, original_height, 
                    (st.session_state.crop_top, st.session_state.crop_bottom)
                )
                left, right = crop_x
                top, bottom = crop_y
                
                # Safeguards against zero sizes
                if right <= left: right = left + 1
                if bottom <= top: bottom = top + 1
                
                st.session_state.crop_left, st.session_state.crop_right = left, right
                st.session_state.crop_top, st.session_state.crop_bottom = top, bottom
                st.info(f"Cropped Area: {right - left}x{bottom - top} px")

            with st.sidebar.expander("📐 Resize Settings", expanded=False):
                st.checkbox("Maintain Aspect Ratio", key="maintain_aspect", value=True)
                
                st.number_input(
                    "Width (px)", 
                    key="resize_width", 
                    min_value=1, 
                    on_change=update_width, 
                    args=(original_width, original_height)
                )
                st.number_input(
                    "Height (px)", 
                    key="resize_height", 
                    min_value=1, 
                    on_change=update_height, 
                    args=(original_width, original_height)
                )
                
                # Current values from session_state
                resize_w = st.session_state.resize_width
                resize_h = st.session_state.resize_height

            with st.sidebar.expander("💾 Compression Engine", expanded=True):
                quality = st.slider("JPEG Compression Quality", 1, 100, 85)

            # Heavy Processing: Convolution, Slicing, and Resizing shielded in try-except
            try:
                # 1. Apply Crop Slicing
                img_stage = original_image.crop((left, top, right, bottom))
                
                # 2. Apply Resize Configuration
                img_stage = img_stage.resize((resize_w, resize_h), Image.Resampling.LANCZOS)
                
                # 3. Apply Filter Convolution/Transformation
                if selected_filter == "Black & White":
                    processed_image = ImageOps.grayscale(img_stage)
                elif selected_filter == "Sepia Tone":
                    gray = ImageOps.grayscale(img_stage.convert("RGB"))
                    processed_image = ImageOps.colorize(gray, "#704214", "#C0B283")
                elif selected_filter == "Gaussian Blur":
                    processed_image = img_stage.filter(ImageFilter.GaussianBlur(radius=blur_radius))
                elif selected_filter == "Contour Sketch":
                    processed_image = img_stage.filter(ImageFilter.CONTOUR)
                elif selected_filter == "Vibrant Saturation":
                    enhancer = ImageEnhance.Color(img_stage.convert("RGB"))
                    processed_image = enhancer.enhance(saturation_factor)
                elif selected_filter == "Retro Negative":
                    processed_image = ImageOps.invert(img_stage.convert("RGB"))
                elif selected_filter == "Emboss Art":
                    processed_image = img_stage.filter(ImageFilter.EMBOSS)
                else:
                    processed_image = img_stage

            except Exception as processing_error:
                st.markdown(
                    f"<div class='custom-warning'>⚠️ <b>Convolution Engine Error:</b> "
                    f"An error occurred while compiling image transformations. <br/>"
                    f"<i>Details: {str(processing_error)}</i></div>", 
                    unsafe_allow_html=True
                )
                processed_image = original_image

            # Calculate metrics
            original_size_kb = len(uploaded_file.getvalue()) / 1024.0
            
            # Compress image to temporary stream
            comp_buffer = io.BytesIO()
            try:
                # Save JPEG with specified quality
                temp_rgb = processed_image.convert("RGB")
                temp_rgb.save(comp_buffer, format="JPEG", quality=quality)
                mime_type = "image/jpeg"
                file_ext = "jpg"
            except Exception:
                # Fallback to lossless PNG if conversion fails
                comp_buffer = io.BytesIO()
                processed_image.save(comp_buffer, format="PNG")
                mime_type = "image/png"
                file_ext = "png"
                
            compressed_bytes = comp_buffer.getvalue()
            compressed_size_kb = len(compressed_bytes) / 1024.0
            saving = ((original_size_kb - compressed_size_kb) / original_size_kb) * 100
            
            # Dynamic metrics board layout
            st.markdown("### 📊 Live Compression Metrics")
            m_col1, m_col2, m_col3 = st.columns(3)
            with m_col1:
                st.metric("Original Size", f"{original_size_kb:.2f} KB")
            with m_col2:
                st.metric(
                    "Optimized Output Size", 
                    f"{compressed_size_kb:.2f} KB", 
                    delta=f"{compressed_size_kb - original_size_kb:.2f} KB", 
                    delta_color="inverse"
                )
            with m_col3:
                st.metric(
                    "Data Reduction Percentage", 
                    f"{saving:.1f}%" if saving >= 0 else "0.0% (Increased Size)"
                )
            
            # Main Canvas Comparison Columns
            st.markdown("---")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📸 Original Upload Canvas")
                st.image(original_image, use_container_width=True)
                st.caption(f"Original Dimensions: {original_width}x{original_height} px")
                
            with col2:
                st.markdown(f"#### ✨ Processed Results ({selected_filter})")
                st.image(processed_image, use_container_width=True)
                st.caption(f"Output Dimensions: {processed_image.width}x{processed_image.height} px")
            
            # Export Action block
            st.markdown("---")
            st.download_button(
                label=f"📥 Download Optimized Image ({file_ext.upper()})",
                data=compressed_bytes,
                file_name=f"studio_export.{file_ext}",
                mime=mime_type
            )
            
        except Exception as e:
            st.error(f"❌ Could not decode uploaded file. Ensure it is a valid image. Details: {e}")
            
    else:
        st.info("💡 Standby: Please upload a photo file from your device to activate the image studio canvas.")

# ----------------------------------------------------
# MODE B: UNIVERSAL QR ENGINE
# ----------------------------------------------------
elif app_mode == "🔮 Universal QR Engine":
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🎨 QR Style Customizer")
    
    # Color Pickers
    qr_dark_color = st.sidebar.color_picker("QR Line Color (Dark Blocks)", "#000000")
    qr_light_color = st.sidebar.color_picker("QR Background Canvas Color", "#FFFFFF")
    
    st.markdown("### 🧭 QR Target Pipelines")
    st.write("Convert paragraphs, redirection URLs, or binary image files into high-capacity QR Code matrices.")
    
    # Split into 3 tabbed segments
    tab1, tab2, tab3 = st.tabs(["✍️ Text to QR", "🔗 Link to QR", "🖼️ Image to QR Pipeline"])
    
    payload = ""
    run_generation = False
    
    with tab1:
        text_input = st.text_area(
            "Enter raw paragraphs / content:", 
            placeholder="Type anything here... When scanned, this text will display directly on the device scanner."
        )
        if text_input:
            payload = text_input
            run_generation = True
            
    with tab2:
        url_input = st.text_input(
            "Enter website destination URL:",
            placeholder="example.com"
        )
        if url_input:
            # Auto-prepend absolute routing address if missing
            temp_url = url_input.strip()
            if not (temp_url.startswith("http://") or temp_url.startswith("https://")):
                temp_url = "https://" + temp_url
            payload = temp_url
            run_generation = True
            
    with tab3:
        st.markdown("#### Convert Image to QR Code")
        st.caption("QR codes have a standard physical capacity limit of 2,953 bytes (Version 40). To encode an image, it must be downscaled to a tiny micro-resolution and converted into a Base64 URI string.")
        
        qr_uploaded_file = st.file_uploader(
            "Upload image asset to convert:", 
            type=["png", "jpg", "jpeg"],
            key="qr_uploader"
        )
        
        if qr_uploaded_file is not None:
            col_q1, col_q2 = st.columns(2)
            with col_q1:
                qr_resolution = st.selectbox(
                    "Target Resolution Grid (px):", 
                    [16, 24, 32, 40, 48], 
                    index=2,
                    help="Smaller resolutions ensure it fits under the QR data capacity limit."
                )
            with col_q2:
                qr_quality = st.slider(
                    "Thumb Quality Factor:", 
                    1, 100, 30,
                    help="Lower values compress JPEG data size to prevent QR buffer overflow."
                )
            
            try:
                # Open image
                raw_qr_img = Image.open(qr_uploaded_file)
                st.write(f"Original Resolution: {raw_qr_img.width}x{raw_qr_img.height} px")
                
                # Perform downscaling
                thumb_img = raw_qr_img.resize((qr_resolution, qr_resolution), Image.Resampling.LANCZOS)
                
                # Convert RGBA/Transparency to RGB on White Background for JPEG compression
                if thumb_img.mode in ("RGBA", "LA") or (thumb_img.mode == "P" and "transparency" in thumb_img.info):
                    bg_canvas = Image.new("RGB", thumb_img.size, (255, 255, 255))
                    bg_canvas.paste(thumb_img, mask=thumb_img.split()[3] if thumb_img.mode == "RGBA" else None)
                    thumb_img = bg_canvas
                else:
                    thumb_img = thumb_img.convert("RGB")
                
                # Save to in-memory JPEG bytes
                qr_img_bytes = io.BytesIO()
                thumb_img.save(qr_img_bytes, format="JPEG", quality=qr_quality)
                raw_bytes = qr_img_bytes.getvalue()
                
                # Convert to Base64 Data URI
                b64_str = base64.b64encode(raw_bytes).decode("utf-8")
                payload = f"data:image/jpeg;base64,{b64_str}"
                run_generation = True
                
                st.markdown(f"**Payload Footprint**: `{len(payload)}` characters of Base64 encoded data.")
                
                # Show thumbnail preview
                st.image(thumb_img, caption="Encoded Micro-Thumbnail Preview", width=120)
                
            except Exception as prep_error:
                st.markdown(
                    f"<div class='custom-warning'>⚠️ <b>Base64 Encoding Error:</b> "
                    f"Could not convert input file to Base64 format. <br/>"
                    f"<i>Details: {str(prep_error)}</i></div>", 
                    unsafe_allow_html=True
                )
                run_generation = False
                
    if run_generation and payload:
        st.markdown("---")
        st.markdown("### 🔮 Compiled Output Canvas")
        
        # Heavy QR code rendering operation shielded inside try-except block
        try:
            # Generate QR Matrix with Segno
            qr_code = segno.make(payload)
            
            # Save QR matrix to buffer using custom line and canvas color picker parameters
            qr_bytes_buffer = io.BytesIO()
            qr_code.save(
                qr_bytes_buffer, 
                kind="png", 
                scale=8, 
                dark=qr_dark_color, 
                light=qr_light_color
            )
            qr_output_png = qr_bytes_buffer.getvalue()
            
            # Display generated QR Code
            st.image(qr_output_png, caption="Generated QR Code Matrix", width=350)
            
            # Download engine
            st.download_button(
                label="📥 Download Compiled QR Code (PNG)",
                data=qr_output_png,
                file_name="qr_studio_export.png",
                mime="image/png"
            )
            
        except segno.DataOverflowError as overflow_err:
            st.markdown(
                f"<div class='custom-warning'>⚠️ <b>QR Matrix Overflow Error:</b> "
                f"The generated data block contains <b>{len(payload)}</b> characters, which exceeds "
                f"the version 40 QR capacity limit (max 2,953 bytes / 4,296 alphanumeric characters). <br/><br/>"
                f"<b>Solution:</b> If converting an image, please select a smaller target grid (e.g. 16x16 or 24x24 px) "
                f"or decrease the compression quality factor to make the file fit inside the QR code frame.</div>", 
                unsafe_allow_html=True
            )
            
        except Exception as matrix_error:
            st.markdown(
                f"<div class='custom-warning'>⚠️ <b>Matrix Rendering Engine Failure:</b> "
                f"Failed to compile target data into QR matrix. <br/>"
                f"<i>Details: {str(matrix_error)}</i></div>", 
                unsafe_allow_html=True
            )
            
    else:
        if not run_generation:
            st.info("💡 Standby: Please configure one of the pipelines above to activate the compilation canvas.")
