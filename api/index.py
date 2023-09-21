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
cors = CORS(app)

def gather_documents():
    documents = []
    repo = 'saifullah0317/search-engine-documents'
    folderpath = 'documents/' 

    api_url = f'https://api.github.com/repos/{repo}/contents/{folderpath}'

    response = requests.get(api_url)
    if response.status_code == 200:
        folder_contents = response.json()

        for item in folder_contents:
            if item['type'] == 'file':
                file_path = item['path']

                raw_url = f'https://raw.githubusercontent.com/{repo}/main/{file_path}'

                file_response = requests.get(raw_url)

                if file_response.status_code == 200:
                    file_content = file_response.content
                    file_name = os.path.basename(file_path)

                    if file_name.endswith('.pdf'):
                        pdf = PyPDF2.PdfReader(io.BytesIO(file_content))
                        text = ""
                        for page_num in range(len(pdf.pages)):
                            text += pdf.pages[page_num].extract_text()

                    elif file_name.endswith('.docx'):
                        doc = Document(io.BytesIO(file_content))
                        text = ""
                        for paragraph in doc.paragraphs:
                            text += paragraph.text + "\n"

                    elif file_name.endswith('.html'):
                        soup = BeautifulSoup(file_content, 'html.parser')
                        text = soup.get_text()

                    elif file_name.endswith('.txt'):
                        text = file_content.decode('utf-8')

                    else:
                        continue  

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

def calculate_idf(documents, keyword):
    total_documents = len(documents)
    documents_containing_keyword = sum(1 for doc in documents if keyword in doc['content'])
    
    if documents_containing_keyword == 0:
        return 0.0  
    else:
        return math.log10(total_documents / documents_containing_keyword)

def calculate_tf(document, keyword):
    word_list = re.findall(r'\w+', document.lower())
    word_count = Counter(word_list)
    return word_count[keyword] / len(word_list)

def search(query):
    results = []
    query_keywords = re.findall(r'\w+', query.lower())
    
    for document in documents:
        document_keywords = re.findall(r'\w+', document['content'].lower())
        matched_keywords = set(query_keywords).intersection(document_keywords)
        
        tfidf_score = sum(calculate_tf(document['content'], keyword) * calculate_idf(documents, keyword) for keyword in matched_keywords)
        
        if tfidf_score > 0: 
            results.append({
                'filename': document['filename'],
                'tfidf_score': tfidf_score
            })
    
    results.sort(key=lambda x: x['tfidf_score'], reverse=True)
    return results


@app.route('/')
@cross_origin()
def home():
    query = request.args.get('query', '')
    
    if not query:
        return jsonify({'message': 'Please provide a query.'})
    results = search(query)
    
    if results:
        return jsonify(results)
    else:
        return jsonify({'message': 'No results matched your query.'})

if __name__ == "__main__":
    app.run(debug=True, port=3000)
