import streamlit as st
import os
from youtube import YouTubeSearcher
from gemini import KeyConceptExtractor
from stringextractor import StringExtractor

def main():
    st.set_page_config(page_title="StudyBud", page_icon="📚", layout="wide")
    st.title("📚 StudyBud: Learn from PDFs with AI")
    st.markdown("Upload a PDF or enter text to extract key concepts and explore related YouTube videos")

    if 'concepts' not in st.session_state:
        st.session_state.concepts = []
    if 'concepts_text' not in st.session_state:
        st.session_state.concepts_text = ""

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
            with st.spinner("Extracting key concepts from PDF..."):
                try:
                    concepts_text = concept_extractor.extract_from_pdf(temp_path)
                    extracted_concepts = string_extractor.extract_list_from_string(concepts_text)
                    if extracted_concepts:
                        st.session_state.concepts = extracted_concepts
                        st.session_state.concepts_text = concepts_text
                        st.success("Concepts extracted!")
                    os.remove(temp_path)
                except Exception as e:
                    st.error(f"Error processing PDF: {e}")

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
                except Exception as e:
                    st.error(f"Error processing text: {e}")

    concepts = st.session_state.concepts
    if concepts:
        st.subheader("📋 Key Concepts")

        cols = st.columns(len(concepts))
        for i, concept in enumerate(concepts):
            with cols[i]:
                if st.button(f"❌ {concept}", key=f"remove_{i}"):
                    st.session_state.concepts.pop(i)
                    st.experimental_rerun()

        if st.button("Find YouTube Videos"):
            with st.spinner("Searching YouTube for relevant videos..."):
                video_results = youtube_searcher.search_multiple(st.session_state.concepts)

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
