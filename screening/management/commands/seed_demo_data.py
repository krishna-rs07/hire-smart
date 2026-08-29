"""
Django management command to seed the database with realistic fictional demo data.

Creates:
- 1 demo recruiter account
- 8 demo jobs across different roles
- ~25 fictional candidates with realistic resumes
- PDF/DOCX resume files (generated from real content)
- AI screening results using the actual ML pipeline

Safe to run multiple times: uses deterministic lookups to avoid duplicates.
"""

import os
import logging
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.core.files import File
from django.conf import settings
from django.utils import timezone
from django.db import transaction

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Data definitions                                                            #
# --------------------------------------------------------------------------- #

RECRUITER_USERNAME = 'demo_recruiter'
RECRUITER_PASSWORD = 'Demo@12345'
RECRUITER_EMAIL = 'recruiter@hiresmart.demo'

# 8 Jobs: (title, company_name, description, required_skills, preferred_skills,
#          min_experience, education, location, employment_type)
JOBS_DATA = [
    {
        'title': 'Python Developer',
        'company': 'TechFlow Solutions Pvt Ltd',
        'description': """We are seeking a skilled Python Developer to join our backend engineering team.

Responsibilities:
- Design and develop scalable backend services using Python and Django
- Build REST APIs and integrate with databases (PostgreSQL, Redis)
- Write clean, maintainable, and well-tested code
- Collaborate with frontend and DevOps teams

Requirements:
- 3+ years of experience with Python
- Strong knowledge of Django or Flask web frameworks
- Experience with REST API development
- Familiarity with PostgreSQL and ORM
- Knowledge of Git and CI/CD pipelines

Preferred:
- Experience with FastAPI
- Knowledge of Docker and AWS
- Familiarity with Celery for async tasks
- Understanding of microservices architecture""",
        'required_skills': 'Python, Django, REST API, PostgreSQL, Git',
        'preferred_skills': 'FastAPI, Docker, AWS, Celery, Flask, Redis',
        'minimum_experience': 3,
        'education_requirement': 'B.Tech Computer Science',
        'location': 'Bangalore, Karnataka',
        'employment_type': 'full_time',
    },
    {
        'title': 'Machine Learning Engineer',
        'company': 'NeuralWorks AI',
        'description': """Join our ML team to build production-grade machine learning systems.

Responsibilities:
- Design, train, and deploy ML models
- Build data pipelines for training and inference
- Work with deep learning frameworks (TensorFlow, PyTorch)
- Monitor and improve model performance

Requirements:
- 4+ years experience in machine learning
- Strong Python programming skills
- Experience with TensorFlow or PyTorch
- Knowledge of scikit-learn and data preprocessing
- Understanding of SQL and data handling

Preferred:
- Experience with NLP or Computer Vision
- Knowledge of MLOps tools (MLflow, Kubeflow)
- Familiarity with cloud platforms (AWS, GCP)
- Experience with Spark or Hadoop""",
        'required_skills': 'Python, Machine Learning, TensorFlow, PyTorch, scikit-learn, SQL',
        'preferred_skills': 'NLP, Computer Vision, MLflow, AWS, Spark, Keras, Deep Learning',
        'minimum_experience': 4,
        'education_requirement': 'M.Tech or B.Tech',
        'location': 'Hyderabad, Telangana',
        'employment_type': 'full_time',
    },
    {
        'title': 'Data Analyst',
        'company': 'Insight Analytics Pvt Ltd',
        'description': """We are hiring a Data Analyst to turn data into actionable business insights.

Responsibilities:
- Analyze large datasets using SQL and Python
- Build dashboards and reports with Power BI / Tableau
- Perform statistical analysis and data visualization
- Communicate findings to stakeholders

Requirements:
- 2+ years of experience in data analysis
- Strong SQL skills
- Proficiency in Excel and data visualization tools
- Basic Python for data manipulation (pandas)
- Good communication skills

Preferred:
- Experience with Tableau or Power BI
- Knowledge of statistics
- Familiarity with Google Analytics
- Experience with ETL processes""",
        'required_skills': 'SQL, Excel, Python, pandas, Data Visualization',
        'preferred_skills': 'Tableau, Power BI, Statistics, Google Analytics, ETL, Reporting',
        'minimum_experience': 2,
        'education_requirement': 'B.Com or B.Tech',
        'location': 'Pune, Maharashtra',
        'employment_type': 'full_time',
    },
    {
        'title': 'Full Stack Developer',
        'company': 'CodeCraft Labs',
        'description': """Full Stack Developer needed to build end-to-end web applications.

Responsibilities:
- Develop frontend with React and backend with Node.js / Django
- Design RESTful APIs and database schemas
- Implement authentication and authorization
- Deploy and maintain applications

Requirements:
- 3+ years of full stack development
- Proficiency in JavaScript and React
- Backend experience with Node.js or Python/Django
- Knowledge of HTML, CSS, and RESTful APIs
- Experience with MongoDB or PostgreSQL

Preferred:
- Experience with TypeScript
- Knowledge of AWS or Azure
- Familiarity with Docker and Kubernetes
- Experience with GraphQL""",
        'required_skills': 'JavaScript, React, Node.js, HTML, CSS, REST API',
        'preferred_skills': 'TypeScript, Django, AWS, Docker, MongoDB, GraphQL, Python',
        'minimum_experience': 3,
        'education_requirement': 'B.Tech',
        'location': 'Chennai, Tamil Nadu',
        'employment_type': 'full_time',
    },
    {
        'title': 'Frontend Developer',
        'company': 'Pixel Perfect Studios',
        'description': """We need a Frontend Developer passionate about crafting beautiful UIs.

Responsibilities:
- Build responsive web interfaces with React / Vue
- Implement designs using HTML, CSS, and JavaScript
- Optimize applications for performance
- Collaborate with UX designers

Requirements:
- 2+ years of frontend development
- Strong HTML, CSS, and JavaScript
- Experience with React or Vue.js
- Knowledge of responsive design
- Familiarity with version control (Git)

Preferred:
- Experience with TypeScript
- Knowledge of SASS or Tailwind CSS
- Familiarity with Webpack or Vite
- Understanding of accessibility standards""",
        'required_skills': 'HTML, CSS, JavaScript, React, Responsive Design',
        'preferred_skills': 'Vue.js, TypeScript, SASS, Tailwind CSS, Webpack, Bootstrap',
        'minimum_experience': 2,
        'education_requirement': 'B.Tech or MCA',
        'location': 'Mumbai, Maharashtra',
        'employment_type': 'full_time',
    },
    {
        'title': 'Backend Developer',
        'company': 'ServerStack Technologies',
        'description': """Backend Developer to architect robust server-side systems.

Responsibilities:
- Design and implement APIs and microservices
- Optimize database queries and caching
- Write unit and integration tests
- Ensure system security and scalability

Requirements:
- 4+ years of backend development
- Strong Python or Java
- Experience with REST API design
- Knowledge of databases (PostgreSQL, MySQL)
- Understanding of authentication (JWT, OAuth)

Preferred:
- Experience with Django or Spring Boot
- Knowledge of Redis or RabbitMQ
- Familiarity with Docker and Kubernetes
- Experience with AWS or GCP""",
        'required_skills': 'Python, Java, REST API, PostgreSQL, MySQL, JWT',
        'preferred_skills': 'Django, Spring Boot, Redis, Docker, AWS, Kubernetes, OAuth',
        'minimum_experience': 4,
        'education_requirement': 'B.Tech',
        'location': 'Noida, Uttar Pradesh',
        'employment_type': 'full_time',
    },
    {
        'title': 'Data Scientist',
        'company': 'Quantix Research',
        'description': """Data Scientist to derive insights from complex datasets.

Responsibilities:
- Build predictive models and ML pipelines
- Perform exploratory data analysis
- Communicate results to business teams
- Deploy models to production

Requirements:
- 3+ years in data science
- Strong Python and SQL
- Experience with pandas, NumPy, scikit-learn
- Knowledge of statistics and probability
- Familiarity with data visualization

Preferred:
- Experience with deep learning (TensorFlow, PyTorch)
- Knowledge of NLP or time-series forecasting
- Familiarity with cloud ML services
- Experience with big data tools (Spark)""",
        'required_skills': 'Python, SQL, pandas, NumPy, scikit-learn, Statistics',
        'preferred_skills': 'TensorFlow, PyTorch, NLP, Spark, Deep Learning, Data Visualization',
        'minimum_experience': 3,
        'education_requirement': 'M.Tech or M.Sc',
        'location': 'Bangalore, Karnataka',
        'employment_type': 'full_time',
    },
    {
        'title': 'Java Developer',
        'company': 'Enterprise Soft Systems',
        'description': """Java Developer for enterprise application development.

Responsibilities:
- Develop enterprise applications using Java and Spring
- Build SOAP/REST web services
- Work with relational databases (Oracle, MySQL)
- Follow Agile development practices

Requirements:
- 3+ years of Java development
- Strong knowledge of Spring Framework
- Experience with Hibernate and JPA
- Knowledge of REST and SOAP APIs
- Familiarity with Maven or Gradle

Preferred:
- Experience with Microservices
- Knowledge of Spring Boot
- Familiarity with Docker and Jenkins
- Understanding of Kafka or RabbitMQ""",
        'required_skills': 'Java, Spring, Hibernate, REST API, MySQL, Maven',
        'preferred_skills': 'Spring Boot, Microservices, Docker, Jenkins, Kafka, SOAP, Oracle',
        'minimum_experience': 3,
        'education_requirement': 'B.Tech',
        'location': 'Gurgaon, Haryana',
        'employment_type': 'full_time',
    },
]

# Candidate data: (name, email, phone, location, education, skills_list,
#                  experience_years, resume_text, certs_list)
# Each resume_text is realistic and will be parsed by the actual pipeline.
CANDIDATES_DATA = [
    # ---- Excellent Python Developer matches ----
    {
        'name': 'Arjun Nair',
        'email': 'arjun.nair@email.com',
        'phone': '+91-9845012345',
        'location': 'Bangalore, Karnataka',
        'education': 'B.Tech Computer Science, NIT Karnataka (2018)',
        'experience': 5,
        'skills': ['Python', 'Django', 'REST API', 'PostgreSQL', 'Git', 'FastAPI', 'Docker', 'AWS'],
        'certs': ['AWS Certified Developer', 'Django Certified'],
        'text': """ARJUN NAIR
Email: arjun.nair@email.com | Phone: +91-9845012345 | Location: Bangalore, Karnataka

SUMMARY
Senior Python Developer with 5 years of experience building scalable backend systems.

EDUCATION
B.Tech in Computer Science, National Institute of Technology Karnataka, 2018

SKILLS
Python, Django, FastAPI, REST API, PostgreSQL, Redis, Git, Docker, AWS, Celery

EXPERIENCE
Software Engineer, TechVision Pvt Ltd (2020-Present)
- Developed REST APIs using Django and FastAPI serving 1M+ requests/day
- Built data pipelines with Celery and Redis
- Deployed applications on AWS using Docker

Python Developer, CodeBase Solutions (2018-2020)
- Built backend services with Django and PostgreSQL
- Implemented CI/CD pipelines with Git and Jenkins

PROJECTS
- Real-time chat application using Django Channels and WebSocket
- E-commerce backend with Stripe payment integration

CERTIFICATIONS
- AWS Certified Developer Associate
- Django for Professionals Certification

ACHIEVEMENTS
- Reduced API response time by 40% through caching optimization
- Led a team of 4 developers on a microservices migration""",
    },
    {
        'name': 'Priya Menon',
        'email': 'priya.menon@email.com',
        'phone': '+91-9876512345',
        'location': 'Bangalore, Karnataka',
        'education': 'M.Tech Computer Science, IISc Bangalore (2019)',
        'experience': 4,
        'skills': ['Python', 'Django', 'Flask', 'REST API', 'PostgreSQL', 'Git', 'AWS', 'Docker'],
        'certs': ['AWS Solutions Architect'],
        'text': """PRIYA MENON
Email: priya.menon@email.com | Phone: +91-9876512345 | Bangalore, Karnataka

PROFILE
Python backend developer with 4 years of experience in web development.

EDUCATION
M.Tech in Computer Science, Indian Institute of Science Bangalore, 2019
B.Tech in Computer Science, College of Engineering Trivandrum, 2017

SKILLS
Python, Django, Flask, REST API, PostgreSQL, Git, Docker, AWS, Redis

EXPERIENCE
Backend Developer, CloudNet Pvt Ltd (2019-Present)
- Designed REST APIs with Django and PostgreSQL
- Containerized services using Docker
- Automated deployments on AWS

Software Engineer Intern, DataSoft (2018-2019)
- Built Flask microservices for internal tools

PROJECTS
- Inventory management system using Django and PostgreSQL
- Notification service with Celery

CERTIFICATIONS
- AWS Solutions Architect Associate

ACHIEVEMENTS
- Improved deployment frequency by 3x using Docker-based CI/CD""",
    },
    # ---- Excellent ML Engineer matches ----
    {
        'name': 'Suresh Kumar',
        'email': 'suresh.kumar@email.com',
        'phone': '+91-9812012345',
        'location': 'Hyderabad, Telangana',
        'education': 'M.Tech Computer Science, IIT Hyderabad (2019)',
        'experience': 5,
        'skills': ['Python', 'Machine Learning', 'TensorFlow', 'PyTorch', 'scikit-learn', 'SQL', 'NLP', 'Deep Learning'],
        'certs': ['TensorFlow Developer Certificate', 'GCP ML Certification'],
        'text': """SURESH KUMAR
Email: suresh.kumar@email.com | Phone: +91-9812012345 | Hyderabad, Telangana

SUMMARY
Machine Learning Engineer with 5 years building production ML systems.

EDUCATION
M.Tech Computer Science, Indian Institute of Technology Hyderabad, 2019
B.Tech Electronics, NIT Warangal, 2017

SKILLS
Python, Machine Learning, Deep Learning, TensorFlow, PyTorch, scikit-learn, SQL, NLP, Keras, Spark

EXPERIENCE
ML Engineer, DeepAI Labs (2020-Present)
- Built NLP models for sentiment analysis using TensorFlow and PyTorch
- Deployed models on GCP with MLflow tracking
- Processed large datasets with Spark

Data Scientist, AnalyticsPro (2019-2020)
- Developed recommendation systems with scikit-learn
- Created SQL-based data pipelines

PROJECTS
- Question answering system using BERT transformers
- Real-time object detection with YOLOv8

CERTIFICATIONS
- TensorFlow Developer Certificate
- Google Cloud Professional ML Engineer

ACHIEVEMENTS
- Published 2 papers on NLP at international conferences
- Improved model accuracy by 15% through feature engineering""",
    },
    {
        'name': 'Kavya Reddy',
        'email': 'kavya.reddy@email.com',
        'phone': '+91-9949012345',
        'location': 'Hyderabad, Telangana',
        'education': 'B.Tech Computer Science, IIIT Hyderabad (2020)',
        'experience': 4,
        'skills': ['Python', 'Machine Learning', 'PyTorch', 'TensorFlow', 'scikit-learn', 'SQL', 'Computer Vision'],
        'certs': ['PyTorch Scholarship'],
        'text': """KAVYA REDDY
Email: kavya.reddy@email.com | Phone: +91-9949012345 | Hyderabad, Telangana

PROFILE
Machine Learning Engineer specializing in Computer Vision.

EDUCATION
B.Tech in Computer Science, International Institute of Information Technology Hyderabad, 2020

SKILLS
Python, Machine Learning, Computer Vision, PyTorch, TensorFlow, scikit-learn, SQL, OpenCV

EXPERIENCE
ML Engineer, VisionAI Pvt Ltd (2020-Present)
- Developed image classification models with PyTorch
- Built data augmentation pipelines with OpenCV
- Trained models on cloud GPU instances

Research Assistant, IIIT Hyderabad (2019-2020)
- Worked on segmentation models using TensorFlow

PROJECTS
- Facial recognition attendance system
- Medical image classification for X-ray diagnosis

CERTIFICATIONS
- PyTorch Deep Learning Scholarship

ACHIEVEMENTS
- Won 1st place in Kaggle computer vision competition""",
    },
    # ---- Excellent Data Analyst matches ----
    {
        'name': 'Rahul Sharma',
        'email': 'rahul.sharma@email.com',
        'phone': '+91-9822012345',
        'location': 'Pune, Maharashtra',
        'education': 'B.Com, University of Mumbai (2019)',
        'experience': 3,
        'skills': ['SQL', 'Excel', 'Python', 'pandas', 'Data Visualization', 'Tableau', 'Statistics'],
        'certs': ['Tableau Desktop Specialist'],
        'text': """RAHUL SHARMA
Email: rahul.sharma@email.com | Phone: +91-9822012345 | Pune, Maharashtra

SUMMARY
Data Analyst with 3 years of experience in business intelligence.

EDUCATION
Bachelor of Commerce, University of Mumbai, 2019

SKILLS
SQL, Excel, Python, pandas, Tableau, Data Visualization, Statistics, Reporting

EXPERIENCE
Data Analyst, BizMetrics Pvt Ltd (2020-Present)
- Built interactive dashboards in Tableau
- Wrote complex SQL queries for reporting
- Automated Excel reports with Python pandas

Junior Analyst, FinanceCorp (2019-2020)
- Created monthly KPI reports in Excel

PROJECTS
- Sales forecasting model using Python
- Customer segmentation dashboard in Tableau

CERTIFICATIONS
- Tableau Desktop Specialist

ACHIEVEMENTS
- Reduced reporting time by 60% through automation""",
    },
    {
        'name': 'Anita Desai',
        'email': 'anita.desai@email.com',
        'phone': '+91-9893012345',
        'location': 'Pune, Maharashtra',
        'education': 'M.Sc Statistics, Pune University (2018)',
        'experience': 4,
        'skills': ['SQL', 'Excel', 'Python', 'pandas', 'Power BI', 'Statistics', 'Data Visualization'],
        'certs': ['Microsoft Power BI Certified'],
        'text': """ANITA DESAI
Email: anita.desai@email.com | Phone: +91-9893012345 | Pune, Maharashtra

PROFILE
Data Analyst with strong statistical background.

EDUCATION
M.Sc in Statistics, Savitribai Phule Pune University, 2018
B.Sc in Mathematics, Fergusson College, 2016

SKILLS
SQL, Excel, Python, pandas, Power BI, Statistics, Data Visualization, ETL

EXPERIENCE
Senior Data Analyst, RetailInsights (2019-Present)
- Developed Power BI dashboards for executive reporting
- Performed A/B testing with statistical methods
- Built ETL pipelines using Python

Data Analyst, HealthData (2018-2019)
- Analyzed patient outcomes with SQL and Python

PROJECTS
- Churn prediction model in Python
- Inventory optimization dashboard in Power BI

CERTIFICATIONS
- Microsoft Power BI Data Analyst Associate

ACHIEVEMENTS
- Identified cost savings of 2 crores through analytics""",
    },
    # ---- Excellent Full Stack Developer matches ----
    {
        'name': 'Vikram Singh',
        'email': 'vikram.singh@email.com',
        'phone': '+91-9815012345',
        'location': 'Chennai, Tamil Nadu',
        'education': 'B.Tech Computer Science, Anna University (2018)',
        'experience': 5,
        'skills': ['JavaScript', 'React', 'Node.js', 'HTML', 'CSS', 'REST API', 'Python', 'Django', 'AWS'],
        'certs': ['AWS Certified Solutions Architect'],
        'text': """VIKRAM SINGH
Email: vikram.singh@email.com | Phone: +91-9815012345 | Chennai, Tamil Nadu

SUMMARY
Full Stack Developer with 5 years of end-to-end web development.

EDUCATION
B.Tech in Computer Science, Anna University, 2018

SKILLS
JavaScript, React, Node.js, HTML, CSS, REST API, Python, Django, MongoDB, AWS, Docker

EXPERIENCE
Full Stack Developer, WebWorks Pvt Ltd (2019-Present)
- Built React frontends with Node.js backends
- Designed REST APIs using Django and Express
- Deployed full stack apps on AWS with Docker

Frontend Developer, UICompany (2018-2019)
- Developed responsive UIs with React and CSS

PROJECTS
- Full-stack e-learning platform with React and Django
- Real-time collaboration tool with WebSocket

CERTIFICATIONS
- AWS Certified Solutions Architect

ACHIEVEMENTS
- Shipped 3 products from concept to production""",
    },
    {
        'name': 'Meera Iyer',
        'email': 'meera.iyer@email.com',
        'phone': '+91-9872012345',
        'location': 'Chennai, Tamil Nadu',
        'education': 'MCA, Chennai Mathematical Institute (2020)',
        'experience': 3,
        'skills': ['JavaScript', 'React', 'Node.js', 'HTML', 'CSS', 'REST API', 'MongoDB', 'TypeScript'],
        'certs': ['MongoDB Certified Developer'],
        'text': """MEERA IYER
Email: meera.iyer@email.com | Phone: +91-9872012345 | Chennai, Tamil Nadu

PROFILE
Full Stack Developer with React and Node.js expertise.

EDUCATION
Master of Computer Applications, Chennai Mathematical Institute, 2020
B.Sc Computer Science, Stella Maris College, 2017

SKILLS
JavaScript, React, Node.js, TypeScript, HTML, CSS, REST API, MongoDB, GraphQL

EXPERIENCE
Full Stack Developer, AppCraft (2020-Present)
- Developed React SPAs with TypeScript
- Built GraphQL APIs with Node.js and MongoDB
- Implemented responsive designs with CSS

Web Developer, StartupX (2019-2020)
- Created REST APIs with Express.js

PROJECTS
- Social media app with React and GraphQL
- Task management tool with Node.js

CERTIFICATIONS
- MongoDB Certified Developer

ACHIEVEMENTS
- Built UI component library adopted across 5 teams""",
    },
    # ---- Excellent Frontend Developer matches ----
    {
        'name': 'Sneha Patil',
        'email': 'sneha.patil@email.com',
        'phone': '+91-9827012345',
        'location': 'Mumbai, Maharashtra',
        'education': 'B.Tech Computer Science, VJTI Mumbai (2020)',
        'experience': 3,
        'skills': ['HTML', 'CSS', 'JavaScript', 'React', 'Responsive Design', 'TypeScript', 'SASS', 'Tailwind CSS'],
        'certs': ['Meta Frontend Developer Certificate'],
        'text': """SNEHA PATIL
Email: sneha.patil@email.com | Phone: +91-9827012345 | Mumbai, Maharashtra

SUMMARY
Frontend Developer focused on pixel-perfect, responsive UIs.

EDUCATION
B.Tech in Computer Science, Veermata Jijabai Technological Institute Mumbai, 2020

SKILLS
HTML, CSS, JavaScript, React, TypeScript, Responsive Design, SASS, Tailwind CSS, Bootstrap

EXPERIENCE
Frontend Developer, PixelCraft (2020-Present)
- Built responsive web apps with React and TypeScript
- Styled components with SASS and Tailwind CSS
- Optimized page load speed by 50%

UI Developer, WebStyle (2019-2020)
- Created HTML/CSS templates from designs

PROJECTS
- Design system with React and Tailwind
- Animated landing page with CSS transitions

CERTIFICATIONS
- Meta Frontend Developer Professional Certificate

ACHIEVEMENTS
- Lighthouse performance score improved to 98""",
    },
    {
        'name': 'Rohan Kulkarni',
        'email': 'rohan.kulkarni@email.com',
        'phone': '+91-9899012345',
        'location': 'Mumbai, Maharashtra',
        'education': 'MCA, Mumbai University (2019)',
        'experience': 2,
        'skills': ['HTML', 'CSS', 'JavaScript', 'React', 'Vue.js', 'Responsive Design', 'Git'],
        'certs': [],
        'text': """ROHAN KULKARNI
Email: rohan.kulkarni@email.com | Phone: +91-9899012345 | Mumbai, Maharashtra

PROFILE
Frontend Developer with React and Vue experience.

EDUCATION
Master of Computer Applications, Mumbai University, 2019

SKILLS
HTML, CSS, JavaScript, React, Vue.js, Responsive Design, Git, Webpack

EXPERIENCE
Frontend Developer, DesignHub (2019-Present)
- Developed SPAs with React and Vue.js
- Implemented responsive layouts with CSS Grid
- Used Webpack for bundling

Junior Developer, WebPlus (2018-2019)
- Built static websites with HTML and CSS

PROJECTS
- Portfolio site with Vue.js
- Component library with React

ACHIEVEMENTS
- Migrated legacy jQuery code to React""",
    },
    # ---- Excellent Backend Developer matches ----
    {
        'name': 'Aditya Joshi',
        'email': 'aditya.joshi@email.com',
        'phone': '+91-9817012345',
        'location': 'Noida, Uttar Pradesh',
        'education': 'B.Tech Computer Science, IIT Roorkee (2017)',
        'experience': 6,
        'skills': ['Python', 'Java', 'REST API', 'PostgreSQL', 'MySQL', 'JWT', 'Django', 'Redis'],
        'certs': ['Oracle Certified Professional'],
        'text': """ADITYA JOSHI
Email: aditya.joshi@email.com | Phone: +91-9817012345 | Noida, Uttar Pradesh

SUMMARY
Backend Developer with 6 years designing scalable APIs.

EDUCATION
B.Tech in Computer Science, Indian Institute of Technology Roorkee, 2017

SKILLS
Python, Java, Django, REST API, PostgreSQL, MySQL, JWT, Redis, OAuth, Docker

EXPERIENCE
Senior Backend Engineer, ServerPro (2019-Present)
- Built microservices with Django and Python
- Designed JWT authentication with OAuth2
- Optimized PostgreSQL queries reducing latency by 35%

Software Engineer, BackendWorks (2017-2019)
- Developed REST APIs with Java Spring
- Used Redis for caching

PROJECTS
- Payment gateway integration with JWT
- Rate limiter using Redis

CERTIFICATIONS
- Oracle Certified Professional Java SE

ACHIEVEMENTS
- Architected system handling 10M daily requests""",
    },
    {
        'name': 'Neha Gupta',
        'email': 'neha.gupta@email.com',
        'phone': '+91-9878012345',
        'location': 'Noida, Uttar Pradesh',
        'education': 'M.Tech Computer Science, DTU Delhi (2019)',
        'experience': 4,
        'skills': ['Java', 'Python', 'REST API', 'MySQL', 'PostgreSQL', 'Docker', 'AWS', 'Kubernetes'],
        'certs': ['AWS Certified SysOps'],
        'text': """NEHA GUPTA
Email: neha.gupta@email.com | Phone: +91-9878012345 | Noida, Uttar Pradesh

PROFILE
Backend Developer with cloud-native experience.

EDUCATION
M.Tech in Computer Science, Delhi Technological University, 2019

SKILLS
Java, Python, REST API, MySQL, PostgreSQL, Docker, AWS, Kubernetes, JWT

EXPERIENCE
Backend Developer, CloudStack (2019-Present)
- Built containerized microservices with Docker and Kubernetes
- Developed REST APIs with Python and Java
- Deployed on AWS EKS

Software Engineer, DataServe (2018-2019)
- Created database schemas in PostgreSQL

PROJECTS
- Event-driven order processing with Kafka
- Auth service with JWT and OAuth

CERTIFICATIONS
- AWS Certified SysOps Administrator

ACHIEVEMENTS
- Reduced infrastructure cost by 30% with Kubernetes""",
    },
    # ---- Excellent Data Scientist matches ----
    {
        'name': 'Karthik Raj',
        'email': 'karthik.raj@email.com',
        'phone': '+91-9847012345',
        'location': 'Bangalore, Karnataka',
        'education': 'M.Tech Data Science, IISc Bangalore (2020)',
        'experience': 4,
        'skills': ['Python', 'SQL', 'pandas', 'NumPy', 'scikit-learn', 'Statistics', 'TensorFlow', 'NLP'],
        'certs': ['TensorFlow Data Certificate'],
        'text': """KARTHIK RAJ
Email: karthik.raj@email.com | Phone: +91-9847012345 | Bangalore, Karnataka

SUMMARY
Data Scientist with 4 years in predictive modeling and NLP.

EDUCATION
M.Tech in Data Science, Indian Institute of Science Bangalore, 2020
B.Tech in Information Technology, PSG Tech Coimbatore, 2018

SKILLS
Python, SQL, pandas, NumPy, scikit-learn, Statistics, TensorFlow, PyTorch, NLP, Data Visualization

EXPERIENCE
Data Scientist, PredictAI (2020-Present)
- Built forecasting models with scikit-learn and TensorFlow
- Developed NLP pipelines for text classification
- Communicated insights to product teams

Analyst, DataMine (2018-2020)
- Performed EDA with pandas and NumPy

PROJECTS
- Demand forecasting for retail chain
- Sentiment analysis API using NLP

CERTIFICATIONS
- TensorFlow Data and Deployment Certificate

ACHIEVEMENTS
- Increased forecast accuracy by 22%""",
    },
    {
        'name': 'Lakshmi Nandan',
        'email': 'lakshmi.nandan@email.com',
        'phone': '+91-9901012345',
        'location': 'Bangalore, Karnataka',
        'education': 'M.Sc Data Science, BITS Pilani (2021)',
        'experience': 3,
        'skills': ['Python', 'SQL', 'pandas', 'NumPy', 'scikit-learn', 'Statistics', 'Deep Learning'],
        'certs': [],
        'text': """LAKSHMI NANDAN
Email: lakshmi.nandan@email.com | Phone: +91-9901012345 | Bangalore, Karnataka

PROFILE
Data Scientist focused on deep learning.

EDUCATION
M.Sc in Data Science, BITS Pilani, 2021
B.Tech in Electronics, NIT Calicut, 2019

SKILLS
Python, SQL, pandas, NumPy, scikit-learn, Statistics, Deep Learning, PyTorch

EXPERIENCE
Data Scientist, NeuralSoft (2021-Present)
- Trained deep learning models with PyTorch
- Built data pipelines with SQL and pandas
- Conducted A/B tests with statistical rigor

Intern, ML Labs (2020-2021)
- Researched time-series forecasting

PROJECTS
- Stock price predictor with LSTM
- Customer lifetime value model

ACHIEVEMENTS
- Presented research at company tech summit""",
    },
    # ---- Excellent Java Developer matches ----
    {
        'name': 'Manoj Verma',
        'email': 'manoj.verma@email.com',
        'phone': '+91-9819012345',
        'location': 'Gurgaon, Haryana',
        'education': 'B.Tech Computer Science, NIT Kurukshetra (2018)',
        'experience': 5,
        'skills': ['Java', 'Spring', 'Hibernate', 'REST API', 'MySQL', 'Maven', 'Spring Boot', 'Microservices'],
        'certs': ['Oracle Certified Java Professional'],
        'text': """MANOJ VERMA
Email: manoj.verma@email.com | Phone: +91-9819012345 | Gurgaon, Haryana

SUMMARY
Java Developer with 5 years in enterprise applications.

EDUCATION
B.Tech in Computer Science, National Institute of Technology Kurukshetra, 2018

SKILLS
Java, Spring, Spring Boot, Hibernate, REST API, MySQL, Maven, Microservices, Docker, JPA

EXPERIENCE
Senior Java Developer, EnterpriseSoft (2019-Present)
- Built microservices with Spring Boot and Hibernate
- Designed REST APIs with JPA and MySQL
- Containerized apps with Docker

Java Developer, CorpSystems (2018-2019)
- Developed SOAP web services with Spring

PROJECTS
- Order management microservice architecture
- Payment integration with Spring

CERTIFICATIONS
- Oracle Certified Professional Java SE 11

ACHIEVEMENTS
- Led migration from monolith to microservices""",
    },
    {
        'name': 'Pooja Bansal',
        'email': 'pooja.bansal@email.com',
        'phone': '+91-9879012345',
        'location': 'Gurgaon, Haryana',
        'education': 'MCA, NIT Trichy (2020)',
        'experience': 3,
        'skills': ['Java', 'Spring', 'Hibernate', 'REST API', 'Oracle', 'Maven', 'Jenkins', 'Docker'],
        'certs': ['Jenkins Certified'],
        'text': """POOJA BANSAL
Email: pooja.bansal@email.com | Phone: +91-9879012345 | Gurgaon, Haryana

PROFILE
Java Developer with DevOps exposure.

EDUCATION
Master of Computer Applications, National Institute of Technology Trichy, 2020

SKILLS
Java, Spring, Hibernate, REST API, Oracle, MySQL, Maven, Jenkins, Docker, Kafka

EXPERIENCE
Java Developer, SoftEdge (2020-Present)
- Developed enterprise apps with Spring and Hibernate
- Built CI/CD pipelines with Jenkins and Docker
- Used Kafka for event streaming

Software Engineer, TechHub (2019-2020)
- Created REST APIs with Java

PROJECTS
- Notification service with Kafka
- Batch processing with Spring Batch

CERTIFICATIONS
- Jenkins Certified Engineer

ACHIEVEMENTS
- Reduced deployment time from 2 hours to 15 minutes""",
    },
    # ---- Good but not perfect matches ----
    {
        'name': 'Deepak Yadav',
        'email': 'deepak.yadav@email.com',
        'phone': '+91-9828012345',
        'location': 'Bangalore, Karnataka',
        'education': 'B.Tech Computer Science, VTU Belgaum (2021)',
        'experience': 2,
        'skills': ['Python', 'Django', 'Git', 'HTML', 'CSS', 'JavaScript'],
        'certs': [],
        'text': """DEEPAK YADAV
Email: deepak.yadav@email.com | Phone: +91-9828012345 | Bangalore, Karnataka

PROFILE
Junior Python Developer with web development experience.

EDUCATION
B.Tech in Computer Science, Visvesvaraya Technological University, 2021

SKILLS
Python, Django, Git, HTML, CSS, JavaScript, REST API

EXPERIENCE
Software Developer, WebIndia (2021-Present)
- Built Django web applications
- Created REST APIs for mobile apps
- Used Git for version control

Intern, CodeLab (2020-2021)
- Learned Python and Django basics

PROJECTS
- Blog platform with Django
- To-do app with React

ACHIEVEMENTS
- Shipped first production app within 6 months""",
    },
    {
        'name': 'Saranya Krishnan',
        'email': 'saranya.krishnan@email.com',
        'phone': '+91-9888012345',
        'location': 'Chennai, Tamil Nadu',
        'education': 'B.E Computer Science, CEG Guindy (2020)',
        'experience': 3,
        'skills': ['Java', 'Spring', 'REST API', 'MySQL', 'HTML', 'CSS', 'JavaScript'],
        'certs': [],
        'text': """SARANYA KRISHNAN
Email: saranya.krishnan@email.com | Phone: +91-9888012345 | Chennai, Tamil Nadu

PROFILE
Java Developer with full stack exposure.

EDUCATION
B.E in Computer Science, College of Engineering Guindy, 2020

SKILLS
Java, Spring, REST API, MySQL, HTML, CSS, JavaScript, Git

EXPERIENCE
Software Engineer, AppWorks (2020-Present)
- Developed Java backend with Spring framework
- Built REST APIs consumed by frontend
- Created simple web UIs with HTML and CSS

Trainee, JavaCorp (2019-2020)
- Learned Spring and Hibernate

PROJECTS
- Library management system in Java
- Weather app with REST API

ACHIEVEMENTS
- Recognized as employee of the quarter""",
    },
    {
        'name': 'Tarun Malhotra',
        'email': 'tarun.malhotra@email.com',
        'phone': '+91-9812012346',
        'location': 'Delhi, NCR',
        'education': 'B.Tech Computer Science, IP University (2019)',
        'experience': 4,
        'skills': ['Python', 'Machine Learning', 'scikit-learn', 'SQL', 'pandas', 'NumPy'],
        'certs': [],
        'text': """TARUN MALHOTRA
Email: tarun.malhotra@email.com | Phone: +91-9812012346 | Delhi, NCR

PROFILE
ML Engineer with classical ML focus.

EDUCATION
B.Tech in Computer Science, Guru Gobind Singh Indraprastha University, 2019

SKILLS
Python, Machine Learning, scikit-learn, SQL, pandas, NumPy, Statistics

EXPERIENCE
ML Engineer, DataLogic (2019-Present)
- Built predictive models with scikit-learn
- Processed data with pandas and SQL
- Applied statistical methods for analysis

Intern, AIWorks (2018-2019)
- Trained regression models

PROJECTS
- Loan default prediction model
- Customer segmentation with clustering

ACHIEVEMENTS
- Deployed 5 models to production""",
    },
    # ---- Average matches ----
    {
        'name': 'Nikhil Thomas',
        'email': 'nikhil.thomas@email.com',
        'phone': '+91-9848012346',
        'location': 'Kochi, Kerala',
        'education': 'BCA, MG University (2021)',
        'experience': 2,
        'skills': ['JavaScript', 'HTML', 'CSS', 'React', 'Git'],
        'certs': [],
        'text': """NIKHIL THOMAS
Email: nikhil.thomas@email.com | Phone: +91-9848012346 | Kochi, Kerala

PROFILE
Frontend Developer with React basics.

EDUCATION
Bachelor of Computer Applications, Mahatma Gandhi University, 2021

SKILLS
JavaScript, HTML, CSS, React, Git

EXPERIENCE
Web Developer, SiteBuild (2021-Present)
- Built static websites with HTML and CSS
- Started learning React for components
- Used Git for collaboration

Freelancer (2020-2021)
- Created landing pages for small businesses

PROJECTS
- Personal portfolio with React
- Weather widget with JavaScript

ACHIEVEMENTS
- Completed 10 freelance projects""",
    },
    {
        'name': 'Varsha Rao',
        'email': 'varsha.rao@email.com',
        'phone': '+91-9888012346',
        'location': 'Bangalore, Karnataka',
        'education': 'B.Com, Bangalore University (2020)',
        'experience': 2,
        'skills': ['Excel', 'SQL', 'Python', 'Data Visualization'],
        'certs': [],
        'text': """VARSHA RAO
Email: varsha.rao@email.com | Phone: +91-9888012346 | Bangalore, Karnataka

PROFILE
Junior Data Analyst.

EDUCATION
Bachelor of Commerce, Bangalore University, 2020

SKILLS
Excel, SQL, Python, Data Visualization, pandas

EXPERIENCE
Analyst, ReportNow (2020-Present)
- Created Excel dashboards for sales teams
- Wrote basic SQL queries for data extraction
- Started learning Python for automation

Intern, DataCare (2019-2020)
- Maintained Excel trackers

PROJECTS
- Monthly sales report automation
- Inventory tracker in Excel

ACHIEVEMENTS
- Automated weekly report saving 4 hours""",
    },
    {
        'name': 'Arvind Pillai',
        'email': 'arvind.pillai@email.com',
        'phone': '+91-9901012346',
        'location': 'Trivandrum, Kerala',
        'education': 'M.Tech Computer Science, CET Trivandrum (2021)',
        'experience': 2,
        'skills': ['Python', 'Django', 'Machine Learning', 'SQL', 'Git'],
        'certs': [],
        'text': """ARVIND PILLAI
Email: arvind.pillai@email.com | Phone: +91-9901012346 | Trivandrum, Kerala

PROFILE
Software Engineer exploring ML.

EDUCATION
M.Tech in Computer Science, College of Engineering Trivandrum, 2021

SKILLS
Python, Django, Machine Learning, SQL, Git, scikit-learn

EXPERIENCE
Software Engineer, TechSolve (2021-Present)
- Developed Django web apps
- Experimented with scikit-learn for predictions
- Used SQL for data storage

Project Assistant, Research Lab (2020-2021)
- Built ML models for academic project

PROJECTS
- Attendance system with face recognition
- Expense tracker with Django

ACHIEVEMENTS
- Published paper on ML applications""",
    },
    # ---- Poor matches ----
    {
        'name': 'Sanjay Iyer',
        'email': 'sanjay.iyer@email.com',
        'phone': '+91-9828012346',
        'location': 'Coimbatore, Tamil Nadu',
        'education': 'B.A English Literature, Bharathiar University (2019)',
        'experience': 3,
        'skills': ['Content Writing', 'SEO', 'Excel', 'Social Media'],
        'certs': [],
        'text': """SANJAY IYER
Email: sanjay.iyer@email.com | Phone: +91-9828012346 | Coimbatore, Tamil Nadu

PROFILE
Content Writer and SEO specialist.

EDUCATION
Bachelor of Arts in English Literature, Bharathiar University, 2019

SKILLS
Content Writing, SEO, Excel, Social Media Marketing, Copywriting

EXPERIENCE
Content Writer, WriteWell (2019-Present)
- Wrote blog posts and website content
- Optimized articles for search engines
- Managed social media calendars

Intern, MediaHouse (2018-2019)
- Assisted with editorial tasks

PROJECTS
- SEO blog that reached 50k monthly visitors
- Email newsletter campaign

ACHIEVEMENTS
- Increased organic traffic by 200%""",
    },
    {
        'name': 'Gayatri Nair',
        'email': 'gayatri.nair@email.com',
        'phone': '+91-9878012346',
        'location': 'Thrissur, Kerala',
        'education': 'B.Sc Physics, Calicut University (2020)',
        'experience': 1,
        'skills': ['Teaching', 'Mathematics', 'Excel'],
        'certs': [],
        'text': """GAYATRI NAIR
Email: gayatri.nair@email.com | Phone: +91-9878012346 | Thrissur, Kerala

PROFILE
Physics teacher with tutoring experience.

EDUCATION
B.Sc in Physics, University of Calicut, 2020

SKILLS
Teaching, Mathematics, Excel, Physics, Communication

EXPERIENCE
Tutor, Home Tutoring (2020-Present)
- Taught mathematics and physics to high school students
- Created lesson plans and worksheets
- Tracked student progress in Excel

Student Teacher, Local School (2019-2020)
- Assisted with science classes

ACHIEVEMENTS
- Helped 20+ students improve grades""",
    },
    {
        'name': 'Mohit Agarwal',
        'email': 'mohit.agarwal@email.com',
        'phone': '+91-9819012346',
        'location': 'Jaipur, Rajasthan',
        'education': 'BBA, Rajasthan University (2021)',
        'experience': 2,
        'skills': ['Sales', 'Marketing', 'Excel', 'CRM'],
        'certs': [],
        'text': """MOHIT AGARWAL
Email: mohit.agarwal@email.com | Phone: +91-9819012346 | Jaipur, Rajasthan

PROFILE
Sales and Marketing executive.

EDUCATION
Bachelor of Business Administration, University of Rajasthan, 2021

SKILLS
Sales, Marketing, Excel, CRM, Communication, Lead Generation

EXPERIENCE
Sales Executive, MarketReach (2021-Present)
- Generated leads and managed client relationships
- Tracked pipeline in Excel and CRM
- Conducted product demos

Intern, SalesCorp (2020-2021)
- Supported field sales team

ACHIEVEMENTS
- Exceeded quarterly targets by 15%""",
    },
    {
        'name': 'Divya Krishnamurthy',
        'email': 'divya.krishnamurthy@email.com',
        'phone': '+91-9847012346',
        'location': 'Mysore, Karnataka',
        'education': 'B.Com, Mysore University (2020)',
        'experience': 3,
        'skills': ['Accounting', 'Tally', 'Excel', 'Taxation'],
        'certs': ['Tally Certified'],
        'text': """DIVYA KRISHNAMURTHY
Email: divya.krishnamurthy@email.com | Phone: +91-9847012346 | Mysore, Karnataka

PROFILE
Accountant with Tally expertise.

EDUCATION
Bachelor of Commerce, University of Mysore, 2020

SKILLS
Accounting, Tally, Excel, Taxation, GST, Bookkeeping

EXPERIENCE
Accountant, FinanceFirst (2020-Present)
- Managed books using Tally and Excel
- Prepared GST returns and tax filings
- Reconciled bank statements

Junior Accountant, AccountPro (2019-2020)
- Assisted with data entry

CERTIFICATIONS
- Tally Certified Professional

ACHIEVEMENTS
- Streamlined invoicing process""",
    },
    {
        'name': 'Ravi Chandra',
        'email': 'ravi.chandra@email.com',
        'phone': '+91-9949012346',
        'location': 'Vijayawada, Andhra Pradesh',
        'education': 'Diploma in Mechanical Engineering (2019)',
        'experience': 4,
        'skills': ['AutoCAD', 'Mechanical Design', 'Quality Control'],
        'certs': [],
        'text': """RAVI CHANDRA
Email: ravi.chandra@email.com | Phone: +91-9949012346 | Vijayawada, Andhra Pradesh

PROFILE
Mechanical Design Engineer.

EDUCATION
Diploma in Mechanical Engineering, Government Polytechnic, 2019

SKILLS
AutoCAD, Mechanical Design, Quality Control, Manufacturing, SolidWorks

EXPERIENCE
Design Engineer, MechWorks (2019-Present)
- Created 2D drawings with AutoCAD
- Performed quality inspections
- Supported production line

Trainee, FactoryTech (2018-2019)
- Learned CAD basics

ACHIEVEMENTS
- Reduced design errors by 25%""",
    },
]


class Command(BaseCommand):
    help = 'Seed the database with realistic fictional demo data for Hire Smart demonstration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete existing demo data before seeding',
        )

    def handle(self, *args, **options):
        from django.contrib.auth.models import User
        from accounts.models import RecruiterProfile
        from jobs.models import Job
        from resumes.models import Candidate, Resume
        from screening.models import ScreeningResult
        from screening.services import get_screening_service

        self.stdout.write(self.style.MIGRATE_HEADING('Starting Hire Smart demo data seeding...'))

        if options['reset']:
            self.stdout.write('Reset flag set - clearing existing demo data...')
            self._reset_data(User, RecruiterProfile, Job, Candidate, Resume, ScreeningResult)

        # 1. Create recruiter
        user, created = User.objects.get_or_create(
            username=RECRUITER_USERNAME,
            defaults={
                'email': RECRUITER_EMAIL,
                'first_name': 'Demo',
                'last_name': 'Recruiter',
                'is_staff': False,
            }
        )
        if created:
            user.set_password(RECRUITER_PASSWORD)
            user.save()
            RecruiterProfile.objects.get_or_create(
                user=user,
                defaults={'company_name': 'Hire Smart Demo Corp', 'designation': 'Lead Recruiter'}
            )
            self.stdout.write(self.style.SUCCESS(f'  Created recruiter: {RECRUITER_USERNAME}'))
        else:
            RecruiterProfile.objects.get_or_create(
                user=user,
                defaults={'company_name': 'Hire Smart Demo Corp', 'designation': 'Lead Recruiter'}
            )
            self.stdout.write(f'  Recruiter already exists: {RECRUITER_USERNAME}')

        # 2. Create jobs
        jobs_created = 0
        job_map = {}
        for job_data in JOBS_DATA:
            job, created = Job.objects.get_or_create(
                title=job_data['title'],
                company=user,
                defaults={
                    'description': job_data['description'],
                    'required_skills': job_data['required_skills'],
                    'preferred_skills': job_data['preferred_skills'],
                    'minimum_experience': job_data['minimum_experience'],
                    'education_requirement': job_data['education_requirement'],
                    'location': job_data['location'],
                    'employment_type': job_data['employment_type'],
                    'status': 'active',
                }
            )
            job_map[job_data['title']] = job
            if created:
                jobs_created += 1
                self.stdout.write(f'  Created job: {job.title}')
            else:
                self.stdout.write(f'  Job already exists: {job.title}')

        # 3. Create candidates + resumes + screening results
        service = get_screening_service()
        media_root = Path(settings.MEDIA_ROOT) / 'resumes'
        media_root.mkdir(parents=True, exist_ok=True)

        candidates_created = 0
        resumes_created = 0
        screenings_created = 0

        for cand_data in CANDIDATES_DATA:
            candidate, created = Candidate.objects.get_or_create(
                email=cand_data['email'],
                defaults={
                    'name': cand_data['name'],
                    'phone': cand_data['phone'],
                    'location': cand_data['location'],
                    'education': cand_data['education'],
                    'total_experience': cand_data['experience'],
                    'skills': cand_data['skills'],
                    'certifications': cand_data['certs'],
                }
            )
            if created:
                candidates_created += 1
                self.stdout.write(f'  Created candidate: {candidate.name}')
            else:
                self.stdout.write(f'  Candidate already exists: {candidate.name}')

            # Generate resume file (PDF) and process it through the real parser
            resume = self._create_or_skip_resume(candidate, user, cand_data, media_root)
            if resume:
                resumes_created += 1
                self.stdout.write(f'    Generated resume file: {resume.file.name}')

                # Run real text extraction
                service.extract_resume_text(resume)
                if resume.status != 'completed':
                    self.stdout.write(self.style.WARNING(
                        f'    WARNING: Text extraction failed for {candidate.name}: {resume.error_message}'
                    ))
                    continue

            # 4. Screen this candidate against the most relevant job
            target_job = self._find_best_job_for_candidate(cand_data, job_map)
            if not target_job:
                self.stdout.write(self.style.WARNING(f'    No target job found for {candidate.name}'))
                continue

            # Check if screening result already exists
            existing = ScreeningResult.objects.filter(candidate=candidate, job=target_job).first()
            if existing:
                self.stdout.write(f'    Screening already exists for {candidate.name} -> {target_job.title}')
                screenings_created += 1
                continue

            result = service.screen_candidate_for_job(candidate, target_job)
            if not result.get('success'):
                self.stdout.write(self.style.WARNING(
                    f'    WARNING: Screening failed for {candidate.name}: {result.get("error")}'
                ))
                continue

            screening_result = service.create_screening_result(candidate, target_job, result)
            screenings_created += 1
            self.stdout.write(self.style.SUCCESS(
                f'    Screened {candidate.name} for {target_job.title}: '
                f'{screening_result.overall_score:.1f}% ({screening_result.recommendation})'
            ))

        self.stdout.write(self.style.MIGRATE_HEADING('\n=== Demo Data Seeding Complete ==='))
        self.stdout.write(f'Jobs:            {Job.objects.filter(company=user).count()}')
        self.stdout.write(f'Candidates:      {Candidate.objects.count()}')
        self.stdout.write(f'Resumes:         {Resume.objects.count()}')
        self.stdout.write(f'Screening Results: {ScreeningResult.objects.filter(job__company=user).count()}')
        self.stdout.write(self.style.SUCCESS(
            f'\nLogin with: {RECRUITER_USERNAME} / {RECRUITER_PASSWORD}'
        ))

    def _reset_data(self, User, RecruiterProfile, Job, Candidate, Resume, ScreeningResult):
        """Delete existing demo data."""
        user = User.objects.filter(username=RECRUITER_USERNAME).first()
        if user:
            ScreeningResult.objects.filter(job__company=user).delete()
            Job.objects.filter(company=user).delete()
            Resume.objects.filter(uploaded_by=user).delete()
            Candidate.objects.all().delete()
            RecruiterProfile.objects.filter(user=user).delete()
            user.delete()
            self.stdout.write('  Cleared existing demo data.')

    def _create_or_skip_resume(self, candidate, user, cand_data, media_root):
        """Create a resume file from candidate text if not already present."""
        from resumes.models import Resume
        from django.core.files import File as DjangoFile

        # Check if resume already exists for this candidate+user
        existing = Resume.objects.filter(candidate=candidate, uploaded_by=user).first()
        if existing:
            return existing

        # Generate PDF file from text
        pdf_path = media_root / f"{cand_data['name'].replace(' ', '_')}_resume.pdf"
        self._write_text_to_pdf(pdf_path, cand_data['text'])

        resume = Resume(
            candidate=candidate,
            file_type='pdf',
            status='pending',
            file_size=pdf_path.stat().st_size,
            uploaded_by=user,
        )
        # Save file to model
        with open(pdf_path, 'rb') as f:
            resume.file.save(f"{cand_data['name'].replace(' ', '_')}_resume.pdf", DjangoFile(f), save=True)

        # Clean up temp file
        if pdf_path.exists():
            pdf_path.unlink()

        return resume

    def _write_text_to_pdf(self, pdf_path, text):
        """Write plain text into a simple PDF file using reportlab or manually."""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.units import inch
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.enums import TA_LEFT
            import html

            doc = SimpleDocTemplate(
                str(pdf_path),
                pagesize=letter,
                leftMargin=0.75 * inch,
                rightMargin=0.75 * inch,
                topMargin=0.75 * inch,
                bottomMargin=0.75 * inch,
            )

            styles = getSampleStyleSheet()
            body_style = ParagraphStyle(
                'ResumeBody',
                parent=styles['Normal'],
                fontSize=10,
                leading=14,
                alignment=TA_LEFT,
                spaceAfter=4,
            )
            heading_style = ParagraphStyle(
                'ResumeHeading',
                parent=styles['Heading3'],
                fontSize=12,
                leading=16,
                spaceBefore=8,
                spaceAfter=4,
            )

            story = []
            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    story.append(Spacer(1, 4))
                    continue
                # Detect headings (ALL CAPS or ends with colon)
                esc = html.escape(line)
                if line.isupper() and len(line) > 3:
                    story.append(Paragraph(esc, heading_style))
                elif line.endswith(':') and len(line) < 40:
                    story.append(Paragraph(f'<b>{esc}</b>', body_style))
                else:
                    story.append(Paragraph(esc, body_style))

            doc.build(story)
        except Exception as e:
            logger.error(f"Failed to create PDF with reportlab: {e}")
            # Fallback: simple text PDF using fitz
            self._write_text_to_pdf_fallback(pdf_path, text)

    def _write_text_to_pdf_fallback(self, pdf_path, text):
        """Fallback PDF writer using PyMuPDF."""
        import fitz
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 50), text)
        doc.save(str(pdf_path))
        doc.close()

    def _find_best_job_for_candidate(self, cand_data, job_map):
        """Find the most relevant job based on candidate's primary skills."""
        skills = set(s.lower() for s in cand_data['skills'])

        # Map candidate to best job by skill overlap
        best_job = None
        best_overlap = -1
        for title, job in job_map.items():
            req = set(s.lower() for s in job.get_required_skills_list())
            overlap = len(skills & req)
            if overlap > best_overlap:
                best_overlap = overlap
                best_job = job

        return best_job
