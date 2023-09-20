import os
import re
import requests
import PyPDF2
from bs4 import BeautifulSoup
from docx import Document
import io

# Define the GitHub repository and folder path
repo = 'saifullah0317/search-engine-documents'
folderpath = 'documents/'  # Remove 'tree/main' from the path

# Create the API URL to list the contents of the folder
api_url = f'https://api.github.com/repos/{repo}/contents/{folderpath}'

# Use the GitHub API to get the list of files in the folder
response = requests.get(api_url)
if response.status_code == 200:
    folder_contents = response.json()

    # Iterate through the files in the folder
    for item in folder_contents:
        if item['type'] == 'file':
            file_path = item['path']

            # Create the raw file URL
            raw_url = f'https://raw.githubusercontent.com/{repo}/main/{file_path}'

            # Use requests to get the content of the file
            file_response = requests.get(raw_url)

            if file_response.status_code == 200:
                file_content = file_response.content
                file_name = os.path.basename(file_path)

                # Check file extension to determine how to process
                if file_name.endswith('.pdf'):
                    # PDF file
                    pdf = PyPDF2.PdfReader(io.BytesIO(file_content))
                    text = ""
                    for page_num in range(len(pdf.pages)):
                        text += pdf.pages[page_num].extract_text()

                elif file_name.endswith('.docx'):
                    # DOCX file
                    doc = Document(io.BytesIO(file_content))
                    text = ""
                    for paragraph in doc.paragraphs:
                        text += paragraph.text + "\n"

                elif file_name.endswith('.html'):
                    # HTML file
                    soup = BeautifulSoup(file_content, 'html.parser')
                    text = soup.get_text()

                elif file_name.endswith('.txt'):
                    # Plain text file
                    text = file_content.decode('utf-8')

                else:
                    # Unsupported file type
                    text = "Unsupported file type: " + file_name

                # Now 'text' contains the text content of the file
                print(f"File Name: {file_name}")
                print(f"Content:")
                print(text)
                print("\n" + "=" * 80 + "\n")
            else:
                print(f'Failed to retrieve file content from GitHub: {file_path}')
else:
    print('Failed to list folder contents from GitHub.')

# Continue with any additional processing as needed
