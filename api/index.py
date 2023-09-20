from flask import Flask,request, jsonify
import os
import re
import PyPDF2
# import docx
from docx import Document
from bs4 import BeautifulSoup
import io
import requests

app = Flask(__name__)

@app.route('/')
def home():
    filenames=[]
    document_index = extractText(filenames)
    queries = request.args.getlist('query')
    results=search(queries,document_index)
    try:
        resp=[]
        for filename,count in results.items():
            resp.append({
                "filename":filename,
                "termFrequency":count
            })
        for filename in filenames:
            for query in queries:
                if query in filename:
                    resp.append({
                        "filename":filename
                    })
        if resp:
            return jsonify(resp)
        else:
            return jsonify({"message":"no reuslt matched !"})
    except Exception as err:
        return jsonify({"error":err})

# Step 2: Gather Documents, text extraction and indexing
def extractText(filenames):
    index={}
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
                    filenames.append(file_name)
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
                        continue
                    words=re.findall(r"\w+", text.lower())
                    for word in words:
                        if word not in index:
                            index[word]=[]
                        index[word].append(file_name)
                else:
                    print(f'Failed to retrieve file content from GitHub: {file_path}')
                    return
        return index
    else:
        print('Failed to list folder contents from GitHub.')
        return

# Step 6: Build a Search Function
def search(queries, index):
    # query_words = re.findall(r"\w+", query.lower())
    matching_documents = {}
    for word in queries:
        if word in index:
            for filename in index[word]:
                if filename not in matching_documents:
                    matching_documents[filename] = 0
                matching_documents[filename] += 1
    return matching_documents

if __name__=="__main__":
    app.run(debug=True,port=3000)