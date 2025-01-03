import os
import PyPDF2
import pyttsx3
from pdf2image import convert_from_path
import pytesseract
from pathlib import Path

class PDFConverter:
    """
    A class to handle PDF to MP3 conversion with improved resource management
    and progress tracking.
    """
    def __init__(self):
        # Initialize text-to-speech engine with default settings
        self.engine = None
        self.chunk_size = 500  # Smaller chunks for better stability
        
    def initialize_engine(self):
        """
        Safely initialize the text-to-speech engine with error handling.
        """
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 150)  # Standard speaking rate
            self.engine.setProperty('volume', 0.9)  # Slightly reduced volume for clarity
            return True
        except Exception as e:
            print(f"Failed to initialize speech engine: {e}")
            return False

    def extract_text_from_pdf(self, pdf_path):
        """
        Extracts text from a PDF file, handling both text-based and image-based PDFs.
        Now includes better error handling and progress reporting.
        """
        print(f"Starting text extraction from: {pdf_path}")
        text = ""
        
        try:
            with open(pdf_path, 'rb') as file:
                # Create PDF reader object
                reader = PyPDF2.PdfReader(file)
                total_pages = len(reader.pages)
                print(f"Processing {total_pages} pages...")

                # Extract text from each page
                for page_num, page in enumerate(reader.pages, 1):
                    print(f"Extracting text from page {page_num}/{total_pages}")
                    page_text = page.extract_text()
                    text += page_text + "\n"

                if text.strip():
                    return text
                else:
                    print("No text found in PDF, attempting OCR...")
                    return self._extract_text_with_ocr(pdf_path)
                    
        except Exception as e:
            print(f"Error during text extraction: {e}")
            return ""

    def _extract_text_with_ocr(self, pdf_path):
        """
        Handles OCR processing for image-based PDFs with improved error handling.
        """
        try:
            # Convert PDF pages to images
            images = convert_from_path(pdf_path)
            text = ""
            total_images = len(images)
            
            print(f"Performing OCR on {total_images} pages...")
            for idx, image in enumerate(images, 1):
                print(f"Processing image {idx}/{total_images}")
                page_text = pytesseract.image_to_string(image)
                text += page_text + "\n"
            
            return text
            
        except Exception as e:
            print(f"OCR processing failed: {e}")
            return ""

    def text_to_speech(self, text, output_file):
        """
        Converts text to speech with improved chunking and resource management.
        """
        if not self.initialize_engine():
            return False

        try:
            # Create output directory if it doesn't exist
            output_path = Path(output_file).parent
            output_path.mkdir(parents=True, exist_ok=True)

            # Process text in smaller chunks for better stability
            chunks = self._create_text_chunks(text)
            total_chunks = len(chunks)
            print(f"Processing {total_chunks} chunks of text...")

            # Save directly to file instead of using engine.say()
            for idx, chunk in enumerate(chunks, 1):
                print(f"Processing chunk {idx}/{total_chunks}")
                self.engine.save_to_file(chunk, f"temp_chunk_{idx}.mp3")
                self.engine.runAndWait()

            # Combine audio files if multiple chunks were created
            if total_chunks > 1:
                self._combine_audio_files(total_chunks, output_file)
            else:
                os.rename("temp_chunk_1.mp3", output_file)

            return True

        except Exception as e:
            print(f"Text-to-speech conversion failed: {e}")
            return False
        finally:
            # Clean up resources
            if self.engine:
                self.engine.stop()
            self._cleanup_temp_files(total_chunks)

    def _create_text_chunks(self, text):
        """
        Breaks text into smaller, manageable chunks at sentence boundaries.
        """
        words = text.split()
        chunks = []
        current_chunk = []
        current_size = 0

        for word in words:
            current_size += len(word)
            current_chunk.append(word)

            # Check if we should start a new chunk
            if current_size >= self.chunk_size or word.endswith(('.', '!', '?')):
                chunks.append(' '.join(current_chunk))
                current_chunk = []
                current_size = 0

        # Add any remaining text as the final chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks

    def _cleanup_temp_files(self, chunk_count):
        """
        Removes temporary files created during processing.
        """
        for i in range(1, chunk_count + 1):
            temp_file = f"temp_chunk_{i}.mp3"
            if os.path.exists(temp_file):
                os.remove(temp_file)

    def convert_pdf_to_mp3(self, pdf_path, output_file):
        """
        Main conversion method with improved error handling and progress tracking.
        """
        if not os.path.exists(pdf_path):
            print(f"Error: PDF file not found at {pdf_path}")
            return False

        print(f"Starting conversion of {pdf_path} to {output_file}")
        
        # Extract text from PDF
        text = self.extract_text_from_pdf(pdf_path)
        if not text.strip():
            print("No text could be extracted from the PDF")
            return False

        # Convert text to speech
        print(f"Converting text to speech...")
        success = self.text_to_speech(text, output_file)
        
        if success:
            print(f"Conversion completed successfully. Audio saved to: {output_file}")
        else:
            print("Conversion failed")
        
        return success

def main():
    """
    Example usage of the PDFConverter class.
    """
    # Create converter instance
    converter = PDFConverter()
    
    # Set input and output paths
    pdf_path = "Harpinder Singh's Resume.pdf"
    output_file = "output.mp3"
    
    # Perform conversion
    converter.convert_pdf_to_mp3(pdf_path, output_file)

if __name__ == "__main__":
    main()
