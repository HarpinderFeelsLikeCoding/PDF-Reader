import boto3
import fitz  # PyMuPDF
import os
from pathlib import Path
from botocore.exceptions import BotoCoreError, ClientError
from contextlib import closing
import time

class AWSPDFConverter:
    """
    Converts PDFs to MP3 files using AWS Polly for high-quality speech synthesis.
    Handles large documents by breaking them into manageable chunks and provides
    detailed progress tracking.
    """
    def __init__(self, aws_access_key_id, aws_secret_access_key, region_name='us-east-1'):
        # Initialize AWS services with your credentials
        self.polly_client = boto3.client(
            'polly',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name
        )
        
        # Default voice settings - Joanna is a natural-sounding neural voice
        self.voice_id = 'Joanna'
        self.output_format = 'mp3'
        
        # Create a directory for temporary files
        self.temp_dir = Path('temp_audio_files')
        self.temp_dir.mkdir(exist_ok=True)

    def extract_text_from_pdf(self, pdf_path):
        """
        Extracts text from PDF using PyMuPDF, which is faster and more reliable
        than PyPDF2. Handles complex layouts and different PDF formats.
        """
        print(f"Reading PDF: {pdf_path}")
        text_chunks = []
        
        try:
            # Open PDF document
            doc = fitz.open(pdf_path)
            
            # AWS Polly has a 3000 character limit per request
            # We'll use 2800 to leave some margin
            MAX_CHUNK_SIZE = 2800
            
            current_chunk = ""
            
            # Process each page
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                
                # Split text into sentences (rough approximation)
                sentences = text.replace('\n', ' ').split('. ')
                
                for sentence in sentences:
                    # Check if adding this sentence would exceed chunk size
                    if len(current_chunk) + len(sentence) < MAX_CHUNK_SIZE:
                        current_chunk += sentence + '. '
                    else:
                        # Store current chunk and start a new one
                        if current_chunk:
                            text_chunks.append(current_chunk.strip())
                        current_chunk = sentence + '. '
            
            # Add the last chunk if it exists
            if current_chunk:
                text_chunks.append(current_chunk.strip())
            
            print(f"Extracted {len(text_chunks)} text chunks")
            return text_chunks
            
        except Exception as e:
            print(f"Error extracting text from PDF: {str(e)}")
            raise

    def synthesize_speech(self, text, output_path):
        """
        Converts text to speech using AWS Polly's neural engine.
        Handles the API call and saves the audio stream to a file.
        """
        try:
            # Request speech synthesis
            response = self.polly_client.synthesize_speech(
                Engine='neural',  # Use neural engine for better quality
                OutputFormat=self.output_format,
                Text=text,
                VoiceId=self.voice_id
            )
            
            # Save the audio stream to a file
            if "AudioStream" in response:
                with closing(response["AudioStream"]) as stream:
                    with open(output_path, "wb") as file:
                        file.write(stream.read())
            
        except (BotoCoreError, ClientError) as error:
            print(f"Error synthesizing speech: {error}")
            raise

    def combine_audio_files(self, input_files, output_file):
        """
        Combines multiple audio chunks into a single MP3 file using ffmpeg.
        Now with more robust path handling and error checking.
        """
        try:
            # Convert output_file to absolute path
            output_file = os.path.abspath(output_file)
        
            # Create a file listing all audio chunks with absolute paths
            list_file = os.path.join(self.temp_dir, 'file_list.txt')
            print(f"Creating file list at: {list_file}")
        
            with open(list_file, 'w') as f:
                for file in input_files:
                    # Ensure we're using absolute paths
                    abs_path = os.path.abspath(file)
                    print(f"Adding file to list: {abs_path}")
                    f.write(f"file '{abs_path}'\n")
        
            # Construct and execute ffmpeg command
            ffmpeg_cmd = f'ffmpeg -f concat -safe 0 -i "{list_file}" -c copy "{output_file}"'
            print(f"Executing command: {ffmpeg_cmd}")
        
            # Execute ffmpeg command
            result = os.system(ffmpeg_cmd)
        
            if result != 0:
                raise Exception(f"ffmpeg command failed with exit code {result}")
            
            # Verify the output file was created
            if not os.path.exists(output_file):
                raise Exception(f"Output file was not created at {output_file}")
            
            print(f"Successfully created output file at: {output_file}")
        
            # Clean up temporary files
            os.remove(list_file)
            for file in input_files:
                if os.path.exists(file):
                    os.remove(file)
                
        except Exception as e:
            print(f"Error combining audio files: {str(e)}")
            raise

    def convert_pdf_to_speech(self, pdf_path, output_path):
        """
        Main conversion method with improved path handling and verification.
        """
        try:
            # Convert paths to absolute paths
            pdf_path = os.path.abspath(pdf_path)
            output_path = os.path.abspath(output_path)
            
            print(f"Starting conversion of {pdf_path}")
            print(f"Output will be saved to {output_path}")
            
            # Create output directory if it doesn't exist
            output_dir = os.path.dirname(output_path)
            os.makedirs(output_dir, exist_ok=True)
            
            # Extract text chunks from PDF
            text_chunks = self.extract_text_from_pdf(pdf_path)
            
            # Process each chunk
            temp_files = []
            for i, chunk in enumerate(text_chunks):
                print(f"Processing chunk {i+1}/{len(text_chunks)}")
                
                # Create temporary file for this chunk using absolute path
                temp_file = os.path.join(self.temp_dir, f"chunk_{i}.mp3")
                self.synthesize_speech(chunk, temp_file)
                temp_files.append(temp_file)
                
                # Small delay to avoid AWS rate limits
                time.sleep(0.5)
            
            # Combine all audio chunks into final file
            print("Combining audio chunks...")
            self.combine_audio_files(temp_files, output_path)
            
            print(f"Conversion complete! Audio saved to: {output_path}")
            
        except Exception as e:
            print(f"Error during conversion: {str(e)}")
            raise

def main():
    AWS_ACCESS_KEY_ID = 'meh'
    AWS_SECRET_ACCESS_KEY = 'meh again'
    
    # Create converter instancegit
    converter = AWSPDFConverter(
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )
    
    # Use absolute paths for input and output
    current_dir = os.path.dirname(os.path.abspath(__file__))
    input_pdf = os.path.join(current_dir, 'Annie Jacobsen - Operation Paperclip. The Secret Intelligence Program that Brought Nazi Scientists to America - 2014.pdf')
    output_mp3 = os.path.join(current_dir, 'output.mp3')
    
    # Convert PDF to speech
    converter.convert_pdf_to_speech(input_pdf, output_mp3)

if __name__ == "__main__":
    main()
