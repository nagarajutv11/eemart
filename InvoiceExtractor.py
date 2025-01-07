from pathlib import Path
import google.generativeai as genai
from PIL import Image
import PyPDF2


class InvoiceExtractor:
    def __init__(self, api_key):
        self.api_key = api_key
        genai.configure(api_key=api_key)
        self.text_model = genai.GenerativeModel('gemini-pro')
        self.vision_model = genai.GenerativeModel('gemini-1.5-flash')
        self.prompt = "Extract the line items from this Invoice. Need Only Name/Desc, MRP, Qty, Rate, Tax Rate only. Should be a valid CSV format. Here is the file\n";
    
    def _extract_pdf_text(self, pdf_path: str):
        try:
            text = ""
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"Error extracting text from PDF {pdf_path}: {str(e)}")
            return None
        
    def process_image_files(self, image_paths):
        try:
            print('Processing pdf file.')
            # Open and process all images
            images = [Image.open(path) for path in image_paths]
            
            # Combine prompt and images
            content = [self.prompt] + images
            
            # Generate content with multiple images
            response = self.vision_model.generate_content(
                content
            )
            return self.formatOutput(response.text)
        except Exception as e:
            print(f"Error analyzing multiple images: {str(e)}")
            return None

    def process_pdf_file(self, pdf_path):
        try:
            print('Processing pdf file.')
            pdf_text = self._extract_pdf_text(str(pdf_path))
            combined_prompt = f"{self.prompt}\n\nText to analyze:\n{pdf_text}"
            response = self.text_model.generate_content(combined_prompt)
            return self.formatOutput(response.text)
        except Exception as e:
            print(f"Error analyzing PDF file: {str(e)}")
            return None
        
    def formatOutput(self, data):
        # split by new line
        data = data.split('\n')
        # these are in csv format. Create each line as an array
        data = [line.split(',') for line in data]
        # remove starting lines that are not part of the csv
        data = [line for line in data if len(line) == 5]
        return data
