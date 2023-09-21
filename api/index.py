from flask import Flask, request, jsonify
import os
import re
import PyPDF2
from docx import Document
from bs4 import BeautifulSoup
import io
import requests
import math
from collections import Counter

app = Flask(__name__)

# Step 2: Gather Your Documents
def gather_documents():
    documents = []
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
                        continue  # Unsupported file type

                    documents.append({
                        'filename': file_name,
                        'content': text
                    })
                else:
                    print(f'Failed to retrieve file content from GitHub: {file_path}')
    else:
        print('Failed to list folder contents from GitHub.')

    return documents

documents = gather_documents()

# Calculate IDF (Inverse Document Frequency)
def calculate_idf(documents, keyword):
    total_documents = len(documents)
    documents_containing_keyword = sum(1 for doc in documents if keyword in doc['content'])
    
    if documents_containing_keyword == 0:
        return 0.0  # Avoid division by zero
    else:
        return math.log10(total_documents / documents_containing_keyword)

# Calculate TF (Term Frequency)
def calculate_tf(document, keyword):
    word_list = re.findall(r'\w+', document.lower())
    word_count = Counter(word_list)
    return word_count[keyword] / len(word_list)

# Step 3: Create a Query Function
def search(query):
    # Step 4: Implement Keyword Matching with TF-IDF Scoring
    results = []
    query_keywords = re.findall(r'\w+', query.lower())
    
    for document in documents:
        document_keywords = re.findall(r'\w+', document['content'].lower())
        matched_keywords = set(query_keywords).intersection(document_keywords)
        
        # Calculate TF-IDF score for the document
        tfidf_score = sum(calculate_tf(document['content'], keyword) * calculate_idf(documents, keyword) for keyword in matched_keywords)
        
        if tfidf_score > 0:  # Only include documents with a non-zero TF-IDF score
            results.append({
                'filename': document['filename'],
                'tfidf_score': tfidf_score
            })
    
    # Step 6: Display the Ranked Documents
    results.sort(key=lambda x: x['tfidf_score'], reverse=True)
    return results


@app.route('/')
def home():
    query = request.args.get('query', '')
    
    if not query:
        return jsonify({'message': 'Please provide a query.'})
    # print(documents)
    results = search(query)
    
    if results:
        return jsonify(results)
    else:
        return jsonify({'message': 'No results matched your query.'})

if __name__ == "__main__":
    app.run(debug=True, port=3000)
