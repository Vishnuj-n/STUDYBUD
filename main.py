import streamlit as st
import os
from youtube import YouTubeSearcher
from gemini import KeyConceptExtractor
from stringextractor import StringExtractor
from hash_check import PDFDuplicateChecker
from video_storage import VideoStorage

def main():
    st.set_page_config(page_title="StudyBud", page_icon="📚", layout="wide")
    st.title("📚 StudyBud: Learn from PDFs with AI")
    st.markdown("Upload a PDF or enter text to extract key concepts and explore related YouTube videos")

    if 'concepts' not in st.session_state:
        st.session_state.concepts = []
    if 'concepts_text' not in st.session_state:
        st.session_state.concepts_text = ""
    if 'current_file_hash' not in st.session_state:
        st.session_state.current_file_hash = None

    @st.cache_resource
    def load_extractors():
        try:
            return KeyConceptExtractor(), StringExtractor(), YouTubeSearcher()
        except ValueError as e:
            st.error(f"Error initializing: {e}")
            return None, None, None

    concept_extractor, string_extractor, youtube_searcher = load_extractors()
    if not concept_extractor:
        return

    tab1, tab2 = st.tabs(["📄 Upload PDF", "✏️ Enter Text"])

    with tab1:
        uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])
        if uploaded_file:
            temp_path = f"temp_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Get the file bytes for hash checking
            with open(temp_path, "rb") as f:
                file_bytes = f.read()
            
            # Initialize the duplicate checker
            duplicate_checker = PDFDuplicateChecker()
            
            # Compute hash for later video link storage
            file_hash = duplicate_checker.compute_hash(file_bytes)
            st.session_state.current_file_hash = file_hash
            
            # Check if the file is a duplicate
            is_duplicate, existing_concepts = duplicate_checker.check_and_store_key_concepts(file_bytes, [])
            
            # Initialize VideoStorage to check for existing videos
            video_storage = VideoStorage()
            existing_videos = None
            
            if is_duplicate and existing_concepts:
                st.info("This PDF has been processed before. Using stored key concepts.")
                st.session_state.concepts = existing_concepts
                st.session_state.concepts_text = ", ".join(existing_concepts)
                st.success("Concepts retrieved!")
                
                # Check if we have stored videos for this PDF
                existing_videos = video_storage.get_links(file_hash)
                if existing_videos:
                    st.info("Found previously saved YouTube videos for this document.")
            else:
                with st.spinner("Extracting key concepts from PDF..."):
                    try:
                        concepts_text = concept_extractor.extract_from_pdf(temp_path)
                        extracted_concepts = string_extractor.extract_list_from_string(concepts_text)
                        if extracted_concepts:
                            # Store the key concepts in the database
                            duplicate_checker.store_key_concepts(file_bytes, extracted_concepts)
                            
                            st.session_state.concepts = extracted_concepts
                            st.session_state.concepts_text = concepts_text
                            st.success("Concepts extracted!")
                    except Exception as e:
                        st.error(f"Error processing PDF: {e}")
            
            duplicate_checker.close()
            video_storage.close()
            # Clean up the temporary file
            os.remove(temp_path)

    with tab2:
        user_text = st.text_area("Enter text to analyze", height=150)
        if user_text and st.button("Extract Concepts"):
            with st.spinner("Extracting key concepts from text..."):
                try:
                    concepts_text = concept_extractor.extract_from_text(user_text)
                    extracted_concepts = string_extractor.extract_list_from_string(concepts_text)
                    if extracted_concepts:
                        st.session_state.concepts = extracted_concepts
                        st.session_state.concepts_text = concepts_text
                        st.success("Concepts extracted!")
                        # For text input, we don't have a file hash
                        st.session_state.current_file_hash = None
                except Exception as e:
                    st.error(f"Error processing text: {e}")

    concepts = st.session_state.concepts
    if concepts:
        st.subheader("📋 Key Concepts")

        # Define a fixed number of columns for a grid layout
        num_columns = 4
        cols = st.columns(num_columns)
        
        # Create a copy to iterate over, as we might modify the list
        concepts_to_display = concepts[:]
        
        for i, concept in enumerate(concepts_to_display):
            # Distribute concepts into columns
            with cols[i % num_columns]:
                # use_container_width makes the button fill the column
                if st.button(f"❌ {concept}", key=f"remove_{concept}_{i}", use_container_width=True):
                    # Remove the concept from the original list in session_state
                    st.session_state.concepts.remove(concept)
                    st.experimental_rerun()

        if st.button("Find YouTube Videos"):
            with st.spinner("Searching YouTube for relevant videos..."):
                video_results = youtube_searcher.search_multiple(st.session_state.concepts)
                
                # Store video results if we have a file hash
                if st.session_state.current_file_hash:
                    video_storage = VideoStorage()
                    # Convert video_results to a format suitable for storage
                    all_urls = []
                    for concept, videos in video_results.items():
                        for video in videos:
                            all_urls.append(video['url'])
                    
                    video_storage.store_links(st.session_state.current_file_hash, all_urls)
                    video_storage.close()

                st.subheader("🎬 Study Resources")
                for concept, videos in video_results.items():
                    st.markdown(f"**{concept}**")
                    for video in videos:
                        st.markdown(f"- [{video['title']}]({video['url']})")

                st.markdown("---")
                st.subheader("📺 Watch Videos")
                for concept, videos in video_results.items():
                    st.markdown(f"### {concept}")
                    video_cols = st.columns(len(videos))
                    for i, video in enumerate(videos):
                        with video_cols[i]:
                            st.video(video['url'])

if __name__ == "__main__":
    main()
