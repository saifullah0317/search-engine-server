from flask import Flask,request, jsonify
import os
import re
import PyPDF2
import docx
from bs4 import BeautifulSoup

app = Flask(__name__)

@app.route('/')
def home():
    query = request.args.getlist('query')[0]
    # search_directory = './api\static'
    search_directory = os.path.abspath('./static')
    documents,filenames = collect_documents(search_directory,query)
    document_index = index_documents(documents)
    results=search(query,document_index)
    try:
        resp=[]
        # if filenames:
        for filename in filenames:
            resp.append({
                "filename":filename
            })
        # elif results:
        for doc_path,count in results.items():
            resp.append({
                "filename":os.path.basename(doc_path),
                "termFrequency":count
            })
        if resp:
            return jsonify(resp)
        else:
            return jsonify({"message":"no reuslt matched !"})
    except Exception as err:
        return jsonify({"error":err})

# Step 2: Gather Documents
def collect_documents(directory,query):
    documents = []
    filenames = []
    static_folder=os.path.abspath(directory)
    for root, _, files in os.walk(static_folder):
        for filename in files:
            file_path = os.path.join(root, filename)
            if any(file_path.endswith(ext) for ext in (".pdf", ".docx", ".html", ".txt")):
                documents.append(file_path)
            if query.lower()==filename.lower():
                filenames.append(filename)
    return documents,filenames

# Step 5: Read and Index Documents
def extract_text_from_pdf(pdf_path):
    text = ""
    with open(pdf_path, "rb") as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        for page_num in range(len(pdf_reader.pages)):  
            page = pdf_reader.pages[page_num]
            text += page.extract_text()
    return text

def extract_text_from_docx(docx_path):
    text = ""
    if os.path.exists(docx_path):  # Check if the file exists
        doc = docx.Document(docx_path)
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
    return text

def extract_text_from_html(html_path):
    with open(html_path, "r", encoding="utf-8") as html_file:
        soup = BeautifulSoup(html_file, "html.parser")
        text = soup.get_text()
    return text

def extract_text_from_txt(txt_path):
    with open(txt_path, "r", encoding="utf-8") as txt_file:
        text = txt_file.read()
    return text

def index_documents(documents):
    index = {}
    for doc_path in documents:
        if doc_path.endswith(".pdf"):
            content = extract_text_from_pdf(doc_path)
        elif doc_path.endswith(".docx"):
            content = extract_text_from_docx(doc_path)
        elif doc_path.endswith(".html"):
            content = extract_text_from_html(doc_path)
        elif doc_path.endswith(".txt"):
            content = extract_text_from_txt(doc_path)
        else:
            content = ""  # Handle unsupported file types here

        words = re.findall(r"\w+", content.lower())  # Tokenize words
        for word in words:
            if word not in index:
                index[word] = []
            index[word].append(doc_path)
    return index

# Step 6: Build a Search Function
def search(query, index):
    query_words = re.findall(r"\w+", query.lower())
    matching_documents = {}
    for word in query_words:
        if word in index:
            for doc_path in index[word]:
                if doc_path not in matching_documents:
                    matching_documents[doc_path] = 0
                matching_documents[doc_path] += 1
    return matching_documents

if __name__=="__main__":
    app.run(debug=True,port=3000)