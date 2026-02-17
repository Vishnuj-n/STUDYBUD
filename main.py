import streamlit as st
import os
from youtube import YouTubeSearcher
from gemini import KeyConceptExtractor
from stringextractor import StringExtractor
from hash_check import PDFDuplicateChecker
from video_storage import VideoStorage

def parse_and_validate_concepts(text: str, max_concepts: int = 50) -> tuple[list, str]:
    """
    Parse and validate concepts from comma-separated text.
    
    Args:
        text: Comma-separated concept string
        max_concepts: Maximum allowed number of concepts
        
    Returns:
        tuple: (concepts_list, error_message) - error_message is empty if valid
    """
    try:
        # Split by comma and clean up
        raw_concepts = text.split(',')
        concepts = [c.strip() for c in raw_concepts if c.strip()]
        
        # Validation checks
        if not concepts:
            return [], "❌ No concepts provided. Please enter at least one concept."
        
        if len(concepts) > max_concepts:
            return [], f"❌ Too many concepts ({len(concepts)}). Maximum allowed: {max_concepts}"
        
        # Validate each concept
        for i, concept in enumerate(concepts, 1):
            if len(concept) < 2:
                return [], f"❌ Concept #{i} is too short: '{concept}' (minimum 2 characters)"
            if len(concept) > 100:
                return [], f"❌ Concept #{i} is too long: '{concept}' (maximum 100 characters)"
        
        # Check for duplicates
        if len(concepts) != len(set(concepts)):
            return [], "❌ Duplicate concepts found. Please remove duplicates."
        
        return concepts, ""
    
    except Exception as e:
        return [], f"❌ Error parsing concepts: {str(e)}"

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
            st.session_state.num_videos_to_show = 4 # Reset video count

            is_duplicate, existing_concepts = duplicate_checker.check_and_store_key_concepts(file_bytes, [])
            
            if is_duplicate and existing_concepts:
                st.info("This PDF has been processed before. Using stored key concepts.")
                st.session_state.concepts = existing_concepts
                
                existing_videos = get_cached_videos(file_hash)
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

        # Bulk Edit Section
        with st.expander("✏️ Edit All Concepts (Bulk Edit)", expanded=False):
            st.markdown("**Edit concepts below (comma-separated):**")
            concepts_text = ", ".join(st.session_state.concepts)
            
            edited_concepts_text = st.text_area(
                "Concepts:",
                value=concepts_text,
                height=120,
                placeholder="e.g., Concept 1, Concept 2, Concept 3",
                label_visibility="collapsed"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("💾 Save Changes", use_container_width=True):
                    validated_concepts, error_msg = parse_and_validate_concepts(edited_concepts_text, max_concepts=50)
                    
                    if error_msg:
                        st.error(error_msg)
                    else:
                        st.session_state.concepts = validated_concepts
                        st.session_state.video_results = None  # Invalidate video results
                        st.session_state.num_videos_to_show = 4  # Reset
                        st.success(f"✅ Updated! {len(validated_concepts)} concepts saved.")
                        st.rerun()
            
            with col2:
                if st.button("🔄 Reset", use_container_width=True):
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
