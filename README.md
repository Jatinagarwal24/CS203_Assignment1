# CS203_Lab_01
This repository contains the submission for Assignment 1 of the course CS 203 - Software Tools and Techniques for AI, offered at the Indian Institute of Technology, Gandhinagar

# Setup
**1.Install the Dependencies**
 ```bash
pip install flask opentelemetry-api opentelemetry-sdk opentelemetry-exporter-jaeger opentelemetry-instrumentation-flask
```

**2.Save the file** 
```bash
app.py
```
**3.Run the Flask Application**
```bash
Open a terminal, navigate to the directory where app.py is saved, and run the following command:
python app.py
```
**4.Open the Application in a Browser**
```bash
Once the app starts, you should see output similar to this in the terminal
 * Running on http://127.0.0.1:5000/
Open your browser and go to http://127.0.0.1:5000/ to access the application
```


# Jaegar 
**1.Install Docker Desktop on your pc.**

**2.On Docker Terminal write the following command:**
```bash
docker run -d -p 16686:16686 -p 6831:6831/udp jaegertracing/all-in-one:latest
```

**3.Open the Jaeger UI in your browser at:**
```bash
http://localhost:16686
```
