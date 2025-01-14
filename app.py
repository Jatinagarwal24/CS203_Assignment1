import json
import os
import logging
import time
from flask import Flask, render_template, request, redirect, url_for, flash
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.trace import SpanKind

# Flask App Initialization
app = Flask(__name__)
app.secret_key = 'secret'
COURSE_FILE = 'course_catalog.json'

# OpenTelemetry Setup for Tracing
resource = Resource.create({"service.name": "course-catalog-service"})
trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer(__name__)

# Jaeger Exporter Setup
jaeger_exporter = JaegerExporter(
    agent_host_name="localhost",
    agent_port=6831,
)
span_processor = BatchSpanProcessor(jaeger_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# Instrument the Flask app for OpenTelemetry
FlaskInstrumentor().instrument_app(app)

# Structured Logging Setup
log_file = "logoutput.json"

# Ensure log file exists and initialize it as an empty JSON array if needed
if not os.path.exists(log_file):
    with open(log_file, 'w') as file:
        file.write("[]")  # Initialize as an empty JSON array

class JsonFileHandler(logging.FileHandler):
    """Custom log handler to append JSON entries to a file."""
    def emit(self, record):
        log_entry = self.format(record)
        with open(self.baseFilename, 'r+') as file:
            data = json.load(file)  # Read existing JSON array
            data.append(json.loads(log_entry))  # Add new log entry
            file.seek(0)  # Move to the beginning of the file
            json.dump(data, file, indent=4)  # Write updated JSON array

# Configure the logger
json_handler = JsonFileHandler(log_file)
json_handler.setFormatter(logging.Formatter('%(message)s'))
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(json_handler)
logger.propagate = False  # Prevent logging to other handlers (e.g., terminal)

# Utility Functions
def load_courses():
    """Load courses from the JSON file."""
    if not os.path.exists(COURSE_FILE):
        return []  # Return an empty list if the file doesn't exist
    with open(COURSE_FILE, 'r') as file:
        return json.load(file)

def save_courses(data):
    """Save new course data to the JSON file."""
    courses = load_courses()  # Load existing courses
    courses.append(data)  # Append the new course
    with open(COURSE_FILE, 'w') as file:
        json.dump(courses, file, indent=4)

# Routes
@app.route('/')
def index():
    start_time = time.time()  # Start time for processing
    with tracer.start_as_current_span("index-page", kind=SpanKind.SERVER) as span:
        span.set_attribute("http.method", request.method)
        span.set_attribute("http.url", request.url)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        span.set_attribute("processing_time", processing_time)  # Add processing time to span
        
        logger.info(json.dumps({"event": "index-page", "method": request.method, "url": request.url, "processing_time": processing_time}))
        return render_template('index.html')

@app.route('/catalog')
def course_catalog():
    start_time = time.time()  # Start time for processing
    with tracer.start_as_current_span("course-catalog", kind=SpanKind.SERVER) as span:
        span.set_attribute("http.method", request.method)
        span.set_attribute("http.url", request.url)
        span.set_attribute("user.ip", request.remote_addr)
        
        courses = load_courses()
        span.set_attribute("course.count", len(courses))

        # Calculate processing time
        processing_time = time.time() - start_time
        span.set_attribute("processing_time", processing_time)  # Add processing time to span
        
        logger.info(json.dumps({"event": "catalog-page", "method": request.method, "course_count": len(courses), "processing_time": processing_time}))
        return render_template('course_catalog.html', courses=courses)

@app.route('/add_course', methods=['GET', 'POST'])
def add_course():
    start_time = time.time()  # Start time for processing
    with tracer.start_as_current_span("add-course-submit", kind=SpanKind.SERVER) as span:
        span.set_attribute("http.method", request.method)
        span.set_attribute("http.url", request.url)
        
        if request.method == 'POST':
            course = {
                'code': request.form['code'].strip(),
                'name': request.form['name'].strip(),
                'instructor': request.form['instructor'].strip(),
                'semester': request.form['semester'].strip(),
                'schedule': request.form['schedule'].strip(),
                'classroom': request.form['classroom'].strip(),
                'prerequisites': request.form['prerequisites'].strip(),
                'grading': request.form['grading'].strip()
            }

            # Validate required fields
            missing_fields = [field for field in ['code', 'name', 'instructor'] if not course[field]]
            if missing_fields:
                logger.warning(json.dumps({"event": "add-course-error", "missing_fields": missing_fields}))
                flash(f"The following required fields are missing: {', '.join(missing_fields)}", "error")
                return render_template('add_course.html')

            save_courses(course)
            span.set_attribute("course.code", course['code'])
            span.set_attribute("course.name", course['name'])

            # Calculate processing time
            processing_time = time.time() - start_time
            span.set_attribute("processing_time", processing_time)  # Add processing time to span
            
            logger.info(json.dumps({"event": "course-added", "course_code": course['code'], "course_name": course['name'], "processing_time": processing_time}))
            return redirect(url_for('course_catalog'))
        
        # Calculate processing time
        processing_time = time.time() - start_time
        span.set_attribute("processing_time", processing_time)  # Add processing time to span
        logger.info(json.dumps({"event": "add-course-page", "method": request.method, "url": request.url, "processing_time": processing_time}))
        return render_template('add_course.html')

@app.route('/course/<code>')
def course_details(code):
    start_time = time.time()  # Start time for processing
    with tracer.start_as_current_span("course-details", kind=SpanKind.SERVER) as span:
        span.set_attribute("http.method", request.method)
        span.set_attribute("http.url", request.url)
        span.set_attribute("course.code", code)
        
        courses = load_courses()
        course = next((course for course in courses if course['code'] == code), None)
        if not course:
            flash(f"No course found with code '{code}'.", "error")
            logger.warning(json.dumps({"event": "course-not-found", "course_code": code}))
            return redirect(url_for('course_catalog'))
        
        # Calculate processing time
        processing_time = time.time() - start_time
        span.set_attribute("processing_time", processing_time)  # Add processing time to span
        
        logger.info(json.dumps({"event": "course-details-viewed", "course_code": code, "processing_time": processing_time}))
        return render_template('course_details.html', course=course)

@app.route('/delete_course/<code>', methods=['POST'])
def delete_course(code):
    start_time = time.time()  # Start time for processing
    with tracer.start_as_current_span("delete-course", kind=SpanKind.SERVER) as span:
        span.set_attribute("http.method", request.method)
        span.set_attribute("http.url", request.url)
        span.set_attribute("course.code", code)

        # Load existing courses
        courses = load_courses()

        # Find the course to delete
        course_to_delete = next((course for course in courses if course['code'] == code), None)

        if course_to_delete:
            # Remove the course from the list
            courses = [course for course in courses if course['code'] != code]

            # Save updated courses back to JSON
            with open(COURSE_FILE, 'w') as file:
                json.dump(courses, file, indent=4)

            logger.info(json.dumps({"event": "course-deleted", "course_code": code}))
            flash(f"Course with code {code} has been deleted successfully.", "success")
        else:
            flash(f"No course found with code '{code}'.", "error")

        # Calculate processing time
        processing_time = time.time() - start_time
        span.set_attribute("processing_time", processing_time)  # Add processing time to span
        
        logger.info(json.dumps({"event": "course-deleted", "course_code": code, "processing_time": processing_time}))
        return redirect(url_for('course_catalog'))

@app.route("/manual-trace")
def manual_trace():
    start_time = time.time()  # Start time for processing
    with tracer.start_as_current_span("manual-span", kind=SpanKind.SERVER) as span:
        span.set_attribute("http.method", request.method)
        span.set_attribute("http.url", request.url)
        

        # Calculate processing time
        processing_time = time.time() - start_time
        span.set_attribute("processing_time", processing_time)  # Add processing time to span
        
        logger.info(json.dumps({"event": "manual-trace", "method": request.method, "url": request.url, "processing_time": processing_time}))
        return "Manual trace finished"

if __name__ == '__main__':
    app.run(debug=True)
