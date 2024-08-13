from flask import Flask, request, redirect, url_for, render_template, flash
from flask_pymongo import PyMongo
import spacy
import os
from werkzeug.utils import secure_filename
import docx2txt

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'proj'  # Set a secret key for session management

# MongoDB configuration
app.config['MONGO_URI'] = 'mongodb+srv://admin:admin@cluster0.zhhc8.mongodb.net/yourdbname'  # Replace with your MongoDB URI
mongo = PyMongo(app)

# Load spaCy model
nlp = spacy.load('en_core_web_sm')

# Define allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_skills(text):
    # Define a list of known skills
    KNOWN_SKILLS = {
        "Python", "Machine Learning", "C++", "C", "OpenCV", "SQL", "Java",
        "JavaScript", "ReactJS", "NodeJS", "Firebase", "Git", "TensorFlow",
        "Arduino", "ROS", "Flutter", "Raspberry Pi", "Unreal Engine","Kubernetes", "Docker", "AWS", "Azure", "GCP", "Data Science", "Big Data",
        "Apache Kafka", "Pandas", "NumPy", "Scikit-Learn", "PyTorch", "Hadoop",
        "Natural Language Processing", "Computer Vision", "GraphQL", "FastAPI","keras","flask","deep learning","streamlit","django","angular js",
        "android development","android","ux","ui","zeplin","wireframe","php","Ruby on Rails","SQLite"
    }
    
    doc = nlp(text)
    extracted_skills = set()
    
    # Check named entities and noun phrases
    for ent in doc.ents:
        if ent.text in KNOWN_SKILLS:
            extracted_skills.add(ent.text)

    for np in doc.noun_chunks:
        if np.text in KNOWN_SKILLS:
            extracted_skills.add(np.text)

    return list(extracted_skills)

def extract_text_from_file(file_path):
    if file_path.endswith('.pdf'):
        import fitz  # PyMuPDF
        pdf_document = fitz.open(file_path)
        text = ""
        for page in pdf_document:
            text += page.get_text()
        pdf_document.close()
    elif file_path.endswith('.docx'):
        text = docx2txt.process(file_path)
    else:
        text = ""
    
    return text

@app.route('/', methods=['GET', 'POST'])
def index():
    suggested_projects = []
    
    if request.method == 'POST':
        if 'resume' in request.files:
            file = request.files['resume']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join('uploaded_resumes', filename)
                file.save(file_path)
                
                text = extract_text_from_file(file_path)
                skills = extract_skills(text)
                
                resume_data = {
                    'filename': filename,
                    'text': text,
                    'skills': skills
                }
                mongo.db.resumeFetchedData.insert_one(resume_data)
                
                flash('Resume uploaded successfully!')
        
        elif 'project_name' in request.form:
            project_name = request.form['project_name']
            project_description = request.form['project_description']
            project_skills = [skill.strip() for skill in request.form['project_skills'].split(',')]
            
            project_data = {
                'name': project_name,
                'description': project_description,
                'skills_required': project_skills
            }
            
            mongo.db.projects.insert_one(project_data)
            
            flash('Project data uploaded successfully!')

        resumes = mongo.db.resumeFetchedData.find()
        all_skills = set()
        for resume in resumes:
            all_skills.update(resume['skills'])
        
        projects = mongo.db.projects.find()
        for project in projects:
            if any(skill in all_skills for skill in project['skills_required']):
                suggested_projects.append(project)
        
    return render_template('index.html', suggested_projects=suggested_projects)

if __name__ == '__main__':
    app.run(port=8000, debug=True)
