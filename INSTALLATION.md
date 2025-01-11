Installation Guide

This guide will help you set up and run sharesfor on your local machine.
---

Prerequisites

Before you begin, ensure you have the following installed on your system:
1. Python: Version 3.8 or higher.
2. MongoDB: Installed and running locally or accessible via a remote server.
3. pip: Python package manager (comes with Python installation).
4. Git: To clone the repository (optional, if downloading as a ZIP file).
---

Step-by-Step Installation


1. Clone the Repository

Clone the repository to your local machine using Git or download it as a ZIP file.
```
git clone https://github.com/ceskinat/sharesfor.git
cd sharesfor

```

2. Set Up a Virtual Environment

It is recommended to use a virtual environment to manage dependencies.

On macOS/Linux:

```
python3 -m venv venv
source venv/bin/activate

```

On Windows:

```
python -m venv venv
venv\Scripts\activate

```

3. Install Dependencies

Use pip to install the required Python packages listed in requirements.txt.
```
pip install -r requirements.txt

```

4. Configure the Application

The configurations are made via config.py
```
LANG = "tr"
MONGO_CONN_STRING = None #localhost

SECRET_KEY = b'_5#y2L"F4Q8z\n\xec]/'

EMAIL_INTEGRATED = False
EMAIL_SENDER_ACC = "s4s4email@yourcompany.com"
EMAIL_SENDER_PWD = "youremailpassword"

S4S4_BASE = "http://localhost:5010"

STYLE_SHEET = "style_new.css"
```

5. Start MongoDB

Ensure MongoDB is running. If installed locally, you can start it using:
```
mongod

```
For a remote MongoDB server, ensure the MONGO_URI in your .env file points to the correct database URI.

6. Import Basic Data 

```
mongorestore --archive=initial.mongoarc
```
if your MongoDB is password protected:
```
mongorestore --archive=initial.mongoarc -u <user> -p <password>
```


7.Run the Application

Start the Flask application using the following command:
```
python3 s4s4.py
```
The application will run locally at http://127.0.0.1:5000.

Production Setup

For production, you will use Gunicorn to run the Flask application.

1. Install Gunicorn

Make sure your virtual environment is activated, then install Gunicorn:
```
pip install gunicorn

```

2. Run the Application with Gunicorn

Use the following command to run the Flask app with Gunicorn:

```
gunicorn -w 1 -k gevent -b 0.0.0.0:8000 s4s4:app

```
- -w 1: Specifies 1 worker processes (in order that socket.io operates properly
- -b 0.0.0.0:8000: Binds the server to all network interfaces on port 8000.
- app:app: Refers to the Python file (app.py) and the Flask application instance (app).
The application will now be available at http://127.0.0.1:8000.

3. (Optional) Set Up Nginx as a Reverse Proxy

For better performance, security, and scalability, it's recommended to use Nginx as a reverse proxy in front of Gunicorn. Here’s a basic example of an Nginx configuration:
```

server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}

```
After adding this configuration, restart Nginx:

```
sudo systemctl restart nginx

```

---

