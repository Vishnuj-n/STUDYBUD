import streamlit as st
import os
from youtube import YouTubeSearcher
from gemini import KeyConceptExtractor
from stringextractor import StringExtractor
from hash_check import PDFDuplicateChecker
from video_storage import VideoStorage

def handle_pdf_upload(uploaded_file, concept_extractor, string_extractor):
    """Handles the processing of the uploaded PDF file."""
    import time
    temp_path = f"temp_{uploaded_file.name}"
    
    # Progress tracking - placeholder for visual progress
    progress_placeholder = st.empty()
    progress_bar = progress_placeholder.progress(0, text="📖 Reading PDF file...")
    
    try:
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        time.sleep(0.3)
        progress_bar = progress_placeholder.progress(20, text="📖 Reading PDF file... ✓")
        time.sleep(0.3)
        progress_bar = progress_placeholder.progress(30, text="🔢 Computing file hash...")
        time.sleep(0.3)

        with open(temp_path, "rb") as f:
            file_bytes = f.read()

        with PDFDuplicateChecker() as duplicate_checker:
            file_hash = duplicate_checker.compute_hash(file_bytes)
            progress_bar = progress_placeholder.progress(40, text="🔢 Computing file hash... ✓")
            time.sleep(0.3)
            progress_bar = progress_placeholder.progress(50, text="🔍 Checking for duplicates...")
            time.sleep(0.3)

            if st.session_state.get('current_file_hash') == file_hash:
                progress_placeholder.empty()
                return

            # Reset state for the new file
            st.session_state.current_file_hash = file_hash
            st.session_state.concepts = []
            st.session_state.video_results = None
            st.session_state.num_videos_to_show = 4 # Reset video count

            is_duplicate, existing_concepts = duplicate_checker.check_and_store_key_concepts(file_bytes, [])
            
            if is_duplicate and existing_concepts:
                progress_bar = progress_placeholder.progress(70, text="💾 Loading cached concepts...")
                time.sleep(0.3)
                st.info("This PDF has been processed before. Using stored key concepts.")
                st.session_state.concepts = existing_concepts
                
                existing_videos = get_cached_videos(file_hash)
                if existing_videos:
                    st.info("Found and loaded previously saved YouTube videos for this document.")
                    st.session_state.video_results = existing_videos
                progress_bar = progress_placeholder.progress(100, text="✅ Complete!")
                time.sleep(0.5)
                progress_placeholder.empty()
            else:
                progress_bar = progress_placeholder.progress(60, text="🤖 Extracting key concepts...")
                time.sleep(0.3)
                concepts_text = concept_extractor.extract_from_pdf(temp_path)
                extracted_concepts = string_extractor.extract_list_from_string(concepts_text)
                if extracted_concepts:
                    progress_bar = progress_placeholder.progress(85, text="💾 Storing concepts...")
                    time.sleep(0.3)
                    duplicate_checker.store_key_concepts(file_bytes, extracted_concepts)
                    st.session_state.concepts = extracted_concepts
                    progress_bar = progress_placeholder.progress(100, text="✅ Complete!")
                    time.sleep(0.5)
                    progress_placeholder.empty()
                    st.success("Concepts extracted!")

    except Exception as e:
        progress_placeholder.empty()
        st.error(f"An error occurred during PDF processing: {e}")
    finally:
        progress_placeholder.empty()
        if os.path.exists(temp_path):
            os.remove(temp_path)

@st.cache_data
def get_cached_videos(file_hash):
    """Wrapper to cache database calls for videos."""
    with VideoStorage() as vs:
        return vs.get_videos_for_file(file_hash)

def display_video_results(video_results):
    """Displays video results with a 'Load More' button."""
    st.subheader("🎬 Study Resources")
    for concept, videos in video_results.items():
        st.markdown(f"**{concept}**")
        for video in videos:
            st.markdown(f"- [{video['title']}]({video['url']})")

    st.markdown("---")
    st.subheader("📺 Watch Videos")

    # Flatten all videos to manage display count easily
    all_videos_flat = [(concept, video) for concept, videos in video_results.items() for video in videos]
    
    num_to_show = st.session_state.get('num_videos_to_show', 4)
    videos_to_display = all_videos_flat[:num_to_show]

    # Display videos grouped by concept
    displayed_videos_by_concept = {}
    for concept, video in videos_to_display:
        if concept not in displayed_videos_by_concept:
            displayed_videos_by_concept[concept] = []
        displayed_videos_by_concept[concept].append(video)

    for concept, videos in displayed_videos_by_concept.items():
        st.markdown(f"### {concept}")
        if videos:
            # Create columns with a max of 4 per row for better layout
            cols = st.columns(min(len(videos), 4))
            for i, video in enumerate(videos):
                with cols[i % 4]:
                    st.video(video['url'])
    
    # 'Load More' button logic
    if len(all_videos_flat) > num_to_show:
        if st.button("Load More Videos"):
            st.session_state.num_videos_to_show += 4
            st.rerun()

def main():
    st.set_page_config(page_title="StudyBud", page_icon="📚", layout="wide")
    st.title("📚 StudyBud: Learn from PDFs with AI")
    st.markdown("Upload a PDF to extract key concepts and explore related YouTube videos")

    # --- Sidebar Settings ---
    with st.sidebar:
        st.title("⚙️ Settings")
        if st.button("🔑 Check Gemini API Key", use_container_width=True):
            try:
                with st.spinner("Sending test message to Gemini..."):
                    extractor = KeyConceptExtractor()
                    response = extractor.client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents="Test message. Reply with 'OK' if you receive this."
                    )
                    if response and response.text:
                        st.success(f"✅ Gemini API key is valid!\nResponse: {response.text[:80]}")
                    else:
                        st.error("API key works but received empty response")
            except Exception as e:
                st.error(f"❌ API key check failed: {str(e)}")
        st.divider()

    # --- Gemini API Key Check (removed from main, now in sidebar) ---


    # Initialize session state variables
    for key, default_value in [
        ('concepts', []),
        ('current_file_hash', None),
        ('video_results', None),
        ('extractors_loaded', False),
        ('num_videos_to_show', 4)
    ]:
        if key not in st.session_state:
            st.session_state[key] = default_value

    # Initialize heavy objects once
    if not st.session_state.extractors_loaded:
        try:
            st.session_state.concept_extractor = KeyConceptExtractor()
            st.session_state.string_extractor = StringExtractor()
            st.session_state.youtube_searcher = YouTubeSearcher()
            st.session_state.extractors_loaded = True
        except Exception as e:
            st.error(f"Error initializing core components: {e}")
            st.session_state.extractors_loaded = False
    
    if not st.session_state.extractors_loaded:
        return

    concept_extractor = st.session_state.concept_extractor
    string_extractor = st.session_state.string_extractor
    youtube_searcher = st.session_state.youtube_searcher

    # --- Main App Layout ---
    uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])
    if uploaded_file:
        handle_pdf_upload(uploaded_file, concept_extractor, string_extractor)



    if st.session_state.concepts:
        st.subheader("📋 Key Concepts")
        num_columns = 4
        cols = st.columns(num_columns)
        
        for i, concept in enumerate(st.session_state.concepts[:]):
            with cols[i % num_columns]:
                if st.button(f"❌ {concept}", key=f"remove_{concept}_{i}", use_container_width=True):
                    st.session_state.concepts.remove(concept)
                    st.session_state.video_results = None  # Invalidate video results
                    st.session_state.num_videos_to_show = 4 # Reset
                    st.rerun()

        if st.button("Find YouTube Videos"):
            if not st.session_state.video_results:
                with st.spinner("Searching YouTube for relevant videos..."):
                    video_results = youtube_searcher.search_multiple(st.session_state.concepts)
                    st.session_state.video_results = video_results
                    
                    if st.session_state.current_file_hash:
                        with VideoStorage() as video_storage:
                            video_storage.store_videos_for_file(
                                st.session_state.current_file_hash,
                                video_results,
                                filename=uploaded_file.name if 'uploaded_file' in locals() else None
                            )
    
    # Display videos if they exist in the session state
    if st.session_state.video_results:
        display_video_results(st.session_state.video_results)

if __name__ == "__main__":
    main()
