import streamlit as st
import os
from youtube import YouTubeSearcher
from gemini import KeyConceptExtractor
from stringextractor import StringExtractor
from hash_check import PDFDuplicateChecker
from video_storage import VideoStorage

def handle_pdf_upload(uploaded_file, concept_extractor, string_extractor):
    """Handles the processing of the uploaded PDF file."""
    temp_path = f"temp_{uploaded_file.name}"
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    try:
        with open(temp_path, "rb") as f:
            file_bytes = f.read()

        with PDFDuplicateChecker() as duplicate_checker:
            file_hash = duplicate_checker.compute_hash(file_bytes)

            if st.session_state.get('current_file_hash') == file_hash:
                return

            # Reset state for the new file
            st.session_state.current_file_hash = file_hash
            st.session_state.concepts = []
            st.session_state.video_results = None

            is_duplicate, existing_concepts = duplicate_checker.check_and_store_key_concepts(file_bytes, [])
            
            if is_duplicate and existing_concepts:
                st.info("This PDF has been processed before. Using stored key concepts.")
                st.session_state.concepts = existing_concepts
                
                with VideoStorage() as video_storage:
                    existing_videos = video_storage.get_videos_for_file(file_hash)
                if existing_videos:
                    st.info("Found and loaded previously saved YouTube videos for this document.")
                    st.session_state.video_results = existing_videos
            else:
                with st.spinner("Extracting key concepts from PDF..."):
                    concepts_text = concept_extractor.extract_from_pdf(temp_path)
                    extracted_concepts = string_extractor.extract_list_from_string(concepts_text)
                    if extracted_concepts:
                        duplicate_checker.store_key_concepts(file_bytes, extracted_concepts)
                        st.session_state.concepts = extracted_concepts
                        st.success("Concepts extracted!")

    except Exception as e:
        st.error(f"An error occurred during PDF processing: {e}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

def display_video_results(video_results):
    """Displays video results in a structured layout."""
    st.subheader("🎬 Study Resources")
    for concept, videos in video_results.items():
        st.markdown(f"**{concept}**")
        for video in videos:
            st.markdown(f"- [{video['title']}]({video['url']})")

    st.markdown("---")
    st.subheader("📺 Watch Videos")
    for concept, videos in video_results.items():
        st.markdown(f"### {concept}")
        if videos:
            video_cols = st.columns(len(videos))
            for i, video in enumerate(videos):
                with video_cols[i]:
                    st.video(video['url'])

def main():
    st.set_page_config(page_title="StudyBud", page_icon="📚", layout="wide")
    st.title("📚 StudyBud: Learn from PDFs with AI")
    st.markdown("Upload a PDF or enter text to extract key concepts and explore related YouTube videos")

    # Initialize session state variables
    for key, default_value in [
        ('concepts', []),
        ('current_file_hash', None),
        ('video_results', None),
        ('extractors_loaded', False)
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

    tab1, tab2 = st.tabs(["📄 Upload PDF", "✏️ Enter Text"])

    with tab1:
        uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])
        if uploaded_file:
            handle_pdf_upload(uploaded_file, concept_extractor, string_extractor)

    with tab2:
        user_text = st.text_area("Enter text to analyze", height=150)
        if user_text and st.button("Extract Concepts"):
            with st.spinner("Extracting key concepts from text..."):
                try:
                    concepts_text = concept_extractor.extract_from_text(user_text)
                    extracted_concepts = string_extractor.extract_list_from_string(concepts_text)
                    if extracted_concepts:
                        st.session_state.concepts = extracted_concepts
                        st.session_state.current_file_hash = None
                        st.session_state.video_results = None
                        st.success("Concepts extracted!")
                except Exception as e:
                    st.error(f"Error processing text: {e}")

    if st.session_state.concepts:
        st.subheader("📋 Key Concepts")
        num_columns = 4
        cols = st.columns(num_columns)
        
        for i, concept in enumerate(st.session_state.concepts[:]):
            with cols[i % num_columns]:
                if st.button(f"❌ {concept}", key=f"remove_{concept}_{i}", use_container_width=True):
                    st.session_state.concepts.remove(concept)
                    st.session_state.video_results = None  # Invalidate video results
                    st.experimental_rerun()

        if st.button("Find YouTube Videos"):
            if not st.session_state.video_results:
                with st.spinner("Searching YouTube for relevant videos..."):
                    video_results = youtube_searcher.search_multiple(st.session_state.concepts)
                    st.session_state.video_results = video_results
                    
                    if st.session_state.current_file_hash:
                        video_storage = VideoStorage()
                        video_storage.store_videos_for_file(
                            st.session_state.current_file_hash,
                            video_results,
                            filename=uploaded_file.name if 'uploaded_file' in locals() else None
                        )
                        video_storage.close()
    
    # Display videos if they exist in the session state
    if st.session_state.video_results:
        display_video_results(st.session_state.video_results)

if __name__ == "__main__":
    main()
