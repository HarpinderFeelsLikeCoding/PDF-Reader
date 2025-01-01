import os
import PyPDF2
import pyttsx3
from pdf2image import convert_from_path
import pytesseract

def extract_text_from_pdf(pdf_path):
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
        
        if text.strip():
            return text
        else:
            print("No text found in the PDF. Attempting OCR...")
            return extract_text_with_ocr(pdf_path)
    except Exception as e:
        print(f"Error extracting text: {e}")
        return ""

def extract_text_with_ocr(pdf_path):
    try:
        images = convert_from_path(pdf_path)
        text = ""
        for image in images:
            text += pytesseract.image_to_string(image)
        return text
    except Exception as e:
        print(f"Error during OCR: {e}")
        return ""

def text_to_mp3(text, output_audio_file, voice_id=0, rate=150, volume=0.9):
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', rate)
        engine.setProperty('volume', volume)
        voices = engine.getProperty('voices')
        if voice_id < len(voices):
            engine.setProperty('voice', voices[voice_id].id)
        else:
            print("Invalid voice ID. Using default voice.")

        # Process in chunks if text is long
        chunk_size = 1000
        chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
        for i, chunk in enumerate(chunks):
            print(f"Processing chunk {i + 1}/{len(chunks)}...")
            engine.say(chunk)

        # Save to file
        engine.save_to_file(text, output_audio_file)
        engine.runAndWait()
        print(f"Audio saved to {output_audio_file}")
    except Exception as e:
        print(f"Error during text-to-speech conversion: {e}")

def pdf_to_mp3(pdf_path, output_audio_file):
    if not os.path.exists(pdf_path):
        print(f"Error: File {pdf_path} not found.")
        return

    print("Extracting text from PDF...")
    text = extract_text_from_pdf(pdf_path)

    if not text.strip():
        print("No extractable text found. Exiting...")
        return

    print("Converting text to speech...")
    text_to_mp3(text, output_audio_file)

if __name__ == "__main__":
    pdf_path = r"Harpinder Singh's Resume.pdf" 
    output_audio_file = "/Users/harpindersingh/output.mp3"
    pdf_to_mp3(pdf_path, output_audio_file)
