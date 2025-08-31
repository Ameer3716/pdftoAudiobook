import streamlit as st
import PyPDF2
import pyttsx3
from gtts import gTTS
import os
import tempfile
from PIL import Image
import pytesseract
import fitz  # PyMuPDF
from pydub import AudioSegment
from pydub.effects import normalize
import base64
import json
import re
from pathlib import Path
import io
import warnings
import subprocess
import requests
import numpy as np
import datetime
import asyncio
warnings.filterwarnings('ignore')

# Try to import edge-tts for better quality free TTS
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False

# Initialize session state
if 'chapters' not in st.session_state:
    st.session_state.chapters = []
if 'audio_files' not in st.session_state:
    st.session_state.audio_files = []
if 'voice_sample' not in st.session_state:
    st.session_state.voice_sample = None
if 'selected_chapters' not in st.session_state:
    st.session_state.selected_chapters = []

class FastVoiceCloner:
    """Simplified, faster voice cloning"""
    
    def __init__(self):
        self.sample_rate = 16000  # Lower sample rate for faster processing
        self.voice_characteristics = None
        
    def analyze_voice_sample(self, audio_path):
        """Quick voice analysis - minimal processing"""
        try:
            audio = AudioSegment.from_file(audio_path)
            audio = audio.set_channels(1)
            audio = audio.set_frame_rate(self.sample_rate)
            
            # Store basic characteristics only
            self.voice_characteristics = {
                'rate': audio.frame_rate,
                'dBFS': audio.dBFS,
            }
            return True
        except Exception as e:
            st.error(f"Error analyzing voice: {str(e)}")
            return False
    
    def apply_basic_voice_transfer(self, source_audio_path, output_path):
        """Fast, basic voice matching"""
        try:
            source = AudioSegment.from_file(source_audio_path)
            
            if self.voice_characteristics:
                # Only apply volume matching for speed
                target_dBFS = self.voice_characteristics.get('dBFS', source.dBFS)
                volume_change = target_dBFS - source.dBFS
                source = source + volume_change
            
            # Quick export without heavy processing
            source.export(output_path, format='mp3', bitrate="192k")
            return True
            
        except Exception as e:
            return False

class PDFToAudiobook:
    def __init__(self):
        self.tts_engine = None
        self.voice_cloner = FastVoiceCloner()
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        
    def extract_text_from_pdf(self, pdf_file):
        """Fast PDF text extraction - skip OCR by default"""
        chapters = []
        current_chapter = {"title": "Chapter 1", "content": ""}
        chapter_num = 1
        
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                
                # Simple chapter detection
                if re.search(r'Chapter\s+\d+|CHAPTER\s+\d+', text, re.IGNORECASE):
                    if current_chapter["content"].strip():
                        chapters.append(current_chapter)
                        chapter_num += 1
                        current_chapter = {
                            "title": f"Chapter {chapter_num}",
                            "content": ""
                        }
                
                current_chapter["content"] += text + "\n"
            
            if current_chapter["content"].strip():
                chapters.append(current_chapter)
        
        except Exception as e:
            st.error(f"Error extracting PDF: {str(e)}")
        
        return chapters if chapters else [{"title": "Full Book", "content": current_chapter["content"]}]
    
    async def generate_with_edge_tts_fast(self, text, output_path, voice="en-US-AriaNeural"):
        """Fast Edge TTS generation"""
        try:
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(output_path)
            return True
        except Exception as e:
            return False
    
    def generate_with_gtts_fast(self, text, output_path, lang='en'):
        """Fast gTTS generation"""
        try:
            tts = gTTS(text=text, lang=lang, slow=False)
            tts.save(output_path)
            return True
        except Exception as e:
            return False
    
    def generate_with_pyttsx3_fast(self, text, output_path, voice_settings=None):
        """Fast pyttsx3 generation"""
        try:
            if self.tts_engine is None:
                self.tts_engine = pyttsx3.init()
            
            # Use faster rate
            self.tts_engine.setProperty('rate', voice_settings.get('rate', 180) if voice_settings else 180)
            self.tts_engine.setProperty('volume', 0.9)
            
            self.tts_engine.save_to_file(text, output_path)
            self.tts_engine.runAndWait()
            return True
        except Exception as e:
            return False
    
    def process_chapters_fast(self, chapters, voice_sample_path, tts_method="gTTS", 
                             voice_settings=None, progress_callback=None, pdf_filename="audiobook"):
        """Fast chapter processing with minimal voice processing"""
        audio_files = []
        total_chapters = len(chapters)
        
        # Quick voice analysis if provided
        use_voice_cloning = False
        if voice_sample_path:
            use_voice_cloning = self.voice_cloner.analyze_voice_sample(voice_sample_path)
        
        for idx, chapter in enumerate(chapters):
            if progress_callback:
                progress_callback((idx + 1) / total_chapters, f"Processing {chapter['title']}...")
            
            # Basic text cleaning
            clean_text = self.clean_text_fast(chapter['content'])
            
            if not clean_text.strip():
                continue
            
            # Process smaller chunks for memory efficiency
            max_chunk_size = 5000  # Increased chunk size for speed
            text_chunks = self.split_text_fast(clean_text, max_chunk_size)
            
            # Generate audio for each chunk
            chunk_files = []
            for chunk_idx, chunk in enumerate(text_chunks):
                temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
                temp_audio.close()
                
                success = False
                
                # Generate TTS
                if tts_method == "Edge TTS" and EDGE_TTS_AVAILABLE:
                    voice = voice_settings.get('edge_voice', 'en-US-AriaNeural') if voice_settings else 'en-US-AriaNeural'
                    success = asyncio.run(self.generate_with_edge_tts_fast(chunk, temp_audio.name, voice))
                elif tts_method == "gTTS":
                    lang = voice_settings.get('language', 'en') if voice_settings else 'en'
                    success = self.generate_with_gtts_fast(chunk, temp_audio.name, lang)
                else:
                    success = self.generate_with_pyttsx3_fast(chunk, temp_audio.name, voice_settings)
                
                if success:
                    chunk_files.append(temp_audio.name)
            
            # Quick merge without complex processing
            if chunk_files:
                chapter_audio = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
                chapter_audio.close()
                
                if len(chunk_files) == 1:
                    # Single chunk - just copy
                    import shutil
                    shutil.copy(chunk_files[0], chapter_audio.name)
                    os.remove(chunk_files[0])
                else:
                    # Multiple chunks - simple concatenation
                    combined = AudioSegment.empty()
                    for chunk_file in chunk_files:
                        chunk_audio_seg = AudioSegment.from_file(chunk_file)
                        combined += chunk_audio_seg
                        os.remove(chunk_file)
                    combined.export(chapter_audio.name, format='mp3', bitrate="192k")
                
                # Optional: Apply basic voice matching
                if use_voice_cloning:
                    cloned_audio = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
                    cloned_audio.close()
                    
                    if self.voice_cloner.apply_basic_voice_transfer(chapter_audio.name, cloned_audio.name):
                        os.remove(chapter_audio.name)
                        chapter_audio.name = cloned_audio.name
                
                # Save to directory
                safe_chapter_title = re.sub(r'[^\w\s-]', '', chapter['title']).strip().replace(' ', '_')
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                saved_filename = f"{pdf_filename}_{safe_chapter_title}_{timestamp}.mp3"
                saved_path = os.path.join(self.script_dir, saved_filename)
                
                # Copy to saved location
                import shutil
                shutil.copy(chapter_audio.name, saved_path)
                
                audio_files.append({
                    'title': chapter['title'],
                    'path': chapter_audio.name,
                    'saved_path': saved_path
                })
                st.success(f"✅ Generated: {saved_filename}")
        
        return audio_files
    
    def clean_text_fast(self, text):
        """Fast text cleaning"""
        # Basic cleaning only
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s\.\,\!\?\-\']', '', text)
        return text.strip()
    
    def split_text_fast(self, text, max_chars=5000):
        """Fast text splitting"""
        if len(text) <= max_chars:
            return [text]
        
        chunks = []
        words = text.split()
        current_chunk = []
        current_length = 0
        
        for word in words:
            word_length = len(word) + 1
            if current_length + word_length > max_chars:
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_length = word_length
            else:
                current_chunk.append(word)
                current_length += word_length
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def merge_audio_files_fast(self, audio_files, output_path, pdf_filename="audiobook"):
        """Fast audio merging"""
        try:
            combined = AudioSegment.empty()
            
            for audio_file in audio_files:
                try:
                    audio = AudioSegment.from_file(audio_file['path'])
                    # Add small silence between chapters
                    if len(combined) > 0:
                        silence = AudioSegment.silent(duration=1000)
                        combined = combined + silence + audio
                    else:
                        combined = audio
                except Exception as e:
                    st.warning(f"Could not add {audio_file['title']}: {str(e)}")
            
            if len(combined) > 0:
                # Export with reasonable quality
                combined.export(output_path, format="mp3", bitrate="192k")
                
                # Save to directory
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                saved_filename = f"{pdf_filename}_complete_{timestamp}.mp3"
                saved_path = os.path.join(self.script_dir, saved_filename)
                combined.export(saved_path, format="mp3", bitrate="192k")
                st.success(f"✅ Complete audiobook saved: {saved_filename}")
                
                return True
            return False
        except Exception as e:
            st.error(f"Error merging: {str(e)}")
            return False

def main():
    st.set_page_config(
        page_title="Fast PDF to Audiobook Converter",
        page_icon="🎙️",
        layout="wide"
    )
    
    st.title("🎙️ Fast PDF to Audiobook Converter")
    st.markdown("Convert PDFs to audiobooks quickly with optional voice matching")
    
    # Initialize converter
    converter = PDFToAudiobook()
    
    # Display save directory
    st.info(f"📁 Audiobooks will be saved to: **{converter.script_dir}**")
    
    # Sidebar settings
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # TTS Method selection
        tts_methods = ["gTTS (Google - Fast)", "pyttsx3 (Offline - Fastest)"]
        if EDGE_TTS_AVAILABLE:
            tts_methods.insert(0, "Edge TTS (Microsoft - Good Quality)")
        
        tts_method = st.selectbox("TTS Engine", tts_methods)
        
        voice_settings = {}
        
        if tts_method == "Edge TTS (Microsoft - Good Quality)" and EDGE_TTS_AVAILABLE:
            edge_voices = ["en-US-AriaNeural", "en-US-JennyNeural", "en-US-GuyNeural"]
            voice_settings['edge_voice'] = st.selectbox("Voice", edge_voices)
        elif tts_method == "gTTS (Google - Fast)":
            voice_settings['language'] = st.selectbox("Language", ['en', 'es', 'fr', 'de'])
        elif tts_method == "pyttsx3 (Offline - Fastest)":
            voice_settings['rate'] = st.slider("Speech Rate", 150, 250, 180)
        
        st.markdown("---")
        enable_voice_matching = st.checkbox("Enable Voice Matching", value=False)
        
        if not EDGE_TTS_AVAILABLE:
            st.markdown("---")
            st.info("Install Edge TTS for better quality:")
            st.code("pip install edge-tts")
    
    # Main content
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if enable_voice_matching:
            st.header("1️⃣ Upload Voice Sample (Optional)")
            voice_sample = st.file_uploader(
                "Upload voice sample for matching",
                type=["mp3", "wav"],
                help="10-30 second clear recording"
            )
            
            if voice_sample:
                st.success("✅ Voice sample uploaded!")
                st.audio(voice_sample)
                
                temp_voice = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
                temp_voice.write(voice_sample.read())
                temp_voice.close()
                st.session_state.voice_sample = temp_voice.name
        
        st.header(f"{'2️⃣' if enable_voice_matching else '1️⃣'} Upload PDF")
        pdf_file = st.file_uploader("Choose PDF file", type="pdf")
        
        if pdf_file:
            st.success(f"✅ PDF uploaded: {pdf_file.name}")
            pdf_filename = pdf_file.name.replace('.pdf', '')
            
            if st.button("📖 Extract Text", type="primary"):
                with st.spinner("Extracting text..."):
                    chapters = converter.extract_text_from_pdf(pdf_file)
                    st.session_state.chapters = chapters
                    st.session_state.selected_chapters = list(range(len(chapters)))
                    st.success(f"Found {len(chapters)} chapter(s)!")
    
    with col2:
        st.header(f"{'3️⃣' if enable_voice_matching else '2️⃣'} Generate Audiobook")
        
        if st.session_state.chapters:
            # Chapter selection
            st.subheader("Select Chapters")
            
            col_all, col_none = st.columns(2)
            with col_all:
                if st.button("Select All"):
                    st.session_state.selected_chapters = list(range(len(st.session_state.chapters)))
                    st.rerun()
            with col_none:
                if st.button("Clear All"):
                    st.session_state.selected_chapters = []
                    st.rerun()
            
            # Show chapters
            for idx, chapter in enumerate(st.session_state.chapters):
                is_selected = st.checkbox(
                    f"{chapter['title']} ({len(chapter['content'])} chars)",
                    value=idx in st.session_state.selected_chapters,
                    key=f"ch_{idx}"
                )
                
                if is_selected and idx not in st.session_state.selected_chapters:
                    st.session_state.selected_chapters.append(idx)
                elif not is_selected and idx in st.session_state.selected_chapters:
                    st.session_state.selected_chapters.remove(idx)
            
            if st.session_state.selected_chapters:
                selected_count = len(st.session_state.selected_chapters)
                
                if st.button(f"🎙️ Generate {selected_count} Chapter(s)", type="primary"):
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    selected_chapters_list = [st.session_state.chapters[i] 
                                             for i in sorted(st.session_state.selected_chapters)]
                    
                    with st.spinner(f"Generating audio for {selected_count} chapter(s)..."):
                        audio_files = converter.process_chapters_fast(
                            selected_chapters_list,
                            st.session_state.voice_sample if enable_voice_matching else None,
                            tts_method=tts_method.split()[0],
                            voice_settings=voice_settings,
                            progress_callback=lambda p, t: (progress_bar.progress(p), status_text.text(t)),
                            pdf_filename=pdf_filename
                        )
                        
                        st.session_state.audio_files = audio_files
                        
                        if audio_files:
                            st.balloons()
                            st.success(f"🎉 Generated {len(audio_files)} audio file(s)!")
                            
                            # Merge if multiple chapters
                            if len(audio_files) > 1:
                                output_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
                                output_path.close()
                                
                                if converter.merge_audio_files_fast(audio_files, output_path.name, pdf_filename):
                                    with open(output_path.name, 'rb') as f:
                                        audio_bytes = f.read()
                                    
                                    st.download_button(
                                        label="⬇️ Download Complete Audiobook",
                                        data=audio_bytes,
                                        file_name=f"{pdf_filename}_complete.mp3",
                                        mime="audio/mp3",
                                        type="primary"
                                    )
                                    
                                    st.audio(audio_bytes, format='audio/mp3')
                            else:
                                # Single chapter
                                audio_file = audio_files[0]
                                if os.path.exists(audio_file['path']):
                                    with open(audio_file['path'], 'rb') as f:
                                        audio_bytes = f.read()
                                    
                                    st.download_button(
                                        label=f"⬇️ Download {audio_file['title']}",
                                        data=audio_bytes,
                                        file_name=f"{pdf_filename}_{audio_file['title']}.mp3",
                                        mime="audio/mp3",
                                        type="primary"
                                    )
                                    
                                    st.audio(audio_bytes, format='audio/mp3')
    
    # Individual downloads
    if st.session_state.audio_files:
        st.header("📂 Individual Chapters")
        st.info(f"Files saved to: **{converter.script_dir}**")
        
        cols = st.columns(3)
        for idx, audio_file in enumerate(st.session_state.audio_files):
            with cols[idx % 3]:
                if os.path.exists(audio_file['path']):
                    with open(audio_file['path'], 'rb') as f:
                        st.download_button(
                            label=f"📥 {audio_file['title']}",
                            data=f.read(),
                            file_name=f"{audio_file['title']}.mp3",
                            mime="audio/mp3",
                            key=f"dl_{idx}"
                        )

if __name__ == "__main__":
    main()