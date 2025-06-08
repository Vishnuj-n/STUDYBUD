import streamlit as st
import os
from youtube import YouTubeSearcher
from gemini import KeyConceptExtractor
from stringextractor import StringExtractor


def main():
    st.set_page_config(page_title="StudyBud", page_icon="📚", layout="wide")
    
    # App header
    st.title("📚 StudyBud: Learn from PDFs with AI")
    st.markdown("Upload a PDF or enter text to extract key concepts and find relevant YouTube videos")
    
    # Initialize state for storing concepts between interactions
    if 'concepts' not in st.session_state:
        st.session_state.concepts = []
    if 'concepts_text' not in st.session_state:
        st.session_state.concepts_text = ""
    if 'pdf_processed' not in st.session_state:
        st.session_state.pdf_processed = False
        
    # Initialize extractors and searchers
    @st.cache_resource
    def load_extractors():
        try:
            concept_extractor = KeyConceptExtractor()
            string_extractor = StringExtractor()
            youtube_searcher = YouTubeSearcher()
            return concept_extractor, string_extractor, youtube_searcher
        except ValueError as e:
            st.error(f"Error initializing: {e}")
            st.info("Make sure your GEMINI_API_KEY environment variable is set.")
            return None, None, None
    
    concept_extractor, string_extractor, youtube_searcher = load_extractors()
    
    if not concept_extractor:
        return
    
    # Create tabs for different input methods
    tab1, tab2 = st.tabs(["📄 Upload PDF", "✏️ Enter Text"])
    
    concepts = st.session_state.concepts
    
    with tab1:
        uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])
        
        # Check if we need to process the PDF or if we can use stored concepts
        process_pdf = False
        
        # Reset button to clear existing concepts
        if st.session_state.pdf_processed and st.button("Reset and Upload New PDF"):
            st.session_state.pdf_processed = False
            st.session_state.concepts = []
            st.session_state.concepts_text = ""
            st.experimental_rerun()
        
        if uploaded_file and not st.session_state.pdf_processed:
            process_pdf = True
            # Save uploaded file temporarily
            temp_path = f"temp_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Process the PDF
            with st.spinner("Extracting key concepts from PDF..."):
                try:
                    concepts_text = concept_extractor.extract_from_pdf(temp_path)
                    st.success("Concepts extracted!")
                    
                    # Store concepts in session state
                    st.session_state.concepts_text = concepts_text
                    st.session_state.pdf_processed = True
                    
                    # Extract concepts list from text
                    extracted_concepts = string_extractor.extract_list_from_string(concepts_text)
                    if extracted_concepts:
                        st.session_state.concepts = extracted_concepts
                    
                    # Remove temporary file
                    os.remove(temp_path)
                except Exception as e:
                    st.error(f"Error processing PDF: {e}")
        
        # Display and allow editing of concepts if we've processed a PDF
        if st.session_state.pdf_processed:
            # Allow editing the raw concepts text
            edited_concepts_text = st.text_area(
                "Key points from PDF (edit as needed)", 
                value=st.session_state.concepts_text, 
                height=150
            )
            
            # Update if text was edited
            if edited_concepts_text != st.session_state.concepts_text:
                st.session_state.concepts_text = edited_concepts_text
                # Re-extract concepts from edited text
                new_concepts = string_extractor.extract_list_from_string(edited_concepts_text)
                if new_concepts:
                    st.session_state.concepts = new_concepts
                    st.success("Updated key concepts from your edits!")
                else:
                    st.warning("Couldn't extract concepts from your edits. Make sure to keep the list format.")
            
            # Manual editing of the concepts list
            st.subheader("Edit Key Concepts")
            st.markdown("You can add, remove, or edit concepts directly:")
            
            # Create an editable list of concepts
            updated_concepts = []
            concept_count = len(st.session_state.concepts)
            
            # Add option to specify how many concepts to edit
            new_concept_count = st.number_input(
                "Number of concepts", 
                min_value=1, 
                max_value=20, 
                value=max(concept_count, 1)
            )
            
            # Adjust the concept list if count changed
            if new_concept_count > concept_count:
                st.session_state.concepts.extend([""] * (new_concept_count - concept_count))
            
            # Create text inputs for each concept
            for i in range(new_concept_count):
                concept_value = ""
                if i < len(st.session_state.concepts):
                    concept_value = st.session_state.concepts[i]
                    
                updated_concept = st.text_input(f"Concept {i+1}", value=concept_value)
                if updated_concept:  # Only add non-empty concepts
                    updated_concepts.append(updated_concept)
            
            # Update button to confirm changes
            if st.button("Update Concepts"):
                if updated_concepts:
                    st.session_state.concepts = updated_concepts
                    st.success("Concepts updated successfully!")
                else:
                    st.error("Please enter at least one concept")
            
            # Update the working concepts list
            concepts = st.session_state.concepts
    
    with tab2:
        user_text = st.text_area("Enter text to analyze", height=150)
        
        if user_text and st.button("Extract Concepts"):
            with st.spinner("Extracting key concepts from text..."):
                try:
                    concepts_text = concept_extractor.extract_from_text(user_text)
                    st.success("Concepts extracted!")
                    st.text_area("Extracted concepts", concepts_text, height=150)
                    
                    # Extract concepts list from text and store in session state
                    extracted_concepts = string_extractor.extract_list_from_string(concepts_text)
                    if extracted_concepts:
                        st.session_state.concepts = extracted_concepts
                        st.session_state.concepts_text = concepts_text
                        # Set this so users can edit the concepts
                        st.session_state.pdf_processed = True
                        # Update the working concepts list
                        concepts = st.session_state.concepts
                except Exception as e:
                    st.error(f"Error processing text: {e}")
    
    # Display concepts and search YouTube if concepts were extracted
    if concepts:
        st.subheader("📋 Current Key Concepts")
        for i, concept in enumerate(concepts, 1):
            st.write(f"{i}. {concept}")
        
        # Search YouTube for videos related to concepts
        if st.button("Find YouTube Videos"):
            with st.spinner("Searching YouTube for relevant videos..."):
                video_results = youtube_searcher.search_multiple(concepts)
                
                # Display results in a clean layout with concepts and videos side by side
                st.subheader("🎬 Study Resources")
                
                # Create two columns: one for concepts, one for videos
                concept_col, video_col = st.columns(2)
                
                # Display concepts in the left column
                with concept_col:
                    st.markdown("### 📋 Key Concepts")
                    for i, concept in enumerate(concepts, 1):
                        st.markdown(f"**{i}. {concept}**")
                        # Add some vertical spacing between concepts
                        if i < len(concepts):
                            st.markdown("<br>", unsafe_allow_html=True)
                
                # Display videos in the right column
                with video_col:
                    st.markdown("### 🎞️ YouTube Videos")
                    for concept, videos in video_results.items():
                        st.markdown(f"**Videos for: {concept}**")
                        for video in videos:
                            st.markdown(f"- [{video['title']}]({video['url']})")
                        # Add some vertical spacing between concept videos
                        if concept != list(video_results.keys())[-1]:
                            st.markdown("<br>", unsafe_allow_html=True)
                
                # Display videos with embedded players below the list
                st.markdown("---")
                st.subheader("📺 Watch Videos")
                
                for concept, videos in video_results.items():
                    st.markdown(f"### {concept}")
                    video_players = st.columns(len(videos))
                    for i, video in enumerate(videos):
                        with video_players[i]:
                            st.video(video['url'])


if __name__ == "__main__":
    main()
