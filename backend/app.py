import json
import re
from datetime import datetime
from dateutil import parser
import spacy
import os  # For environment variables
import pg8000.native
from dotenv import load_dotenv
import google.generativeai as genai

import os
from flask import Flask, request, jsonify

load_dotenv()

app = Flask(__name__)

# Configure Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-pro')

# Database connection function
def get_db_connection():
    try:
        # Parse connection string
        conn_str = os.environ.get('POSTGRES_URL')
        # pg8000 connection
        conn = pg8000.native.Connection(
            user='your_user',
            password='your_password',
            host='your_host',
            port=5432,
            database='your_database'
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {str(e)}")
        raise

# Initialize database tables
def init_db():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS parsed_emails (
                        id SERIAL PRIMARY KEY,
                        input_text TEXT NOT NULL,
                        reply_type VARCHAR(50),
                        proposed_time TIMESTAMP,
                        meeting_link TEXT,
                        delegate_to VARCHAR(255),
                        additional_notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                conn.commit()
    except Exception as e:
        print(f"Database initialization error: {str(e)}")
        raise

# Initialize DB on startup
init_db()

@app.route('/api/health', methods=['GET'])
def health_check():
    try:
        # Test database connection
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT 1')
        return jsonify({'status': 'healthy', 'database': 'connected'})
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e)
        }), 500

def parse_email_reply(email_text):
    """Single Gemini API call to handle all NLP tasks"""
    prompt = f"""
    Analyze this email reply and extract the following information in JSON format.
    Return ONLY the JSON object, no other text.
    
    Required JSON format:
    {{
        "reply_type": "acceptance" | "reschedule" | "decline" | "info_request" | "delegation",
        "proposed_time": "ISO 8601 datetime or null",
        "meeting_link": "URL or null",
        "delegate_to": "email address or null",
        "additional_notes": "string or null"
    }}

    Email text:
    {email_text}
    """

    try:
        response = model.generate_content(prompt)
        parsed_json = json.loads(response.text)
        
        # Validate and normalize the response
        required_keys = ["reply_type", "proposed_time", "meeting_link", "delegate_to", "additional_notes"]
        normalized_data = {key: None for key in required_keys}
        
        for key, value in parsed_json.items():
            if key in normalized_data:
                # Convert empty strings to None
                normalized_data[key] = value if value and value != "" else None
        
        return normalized_data

    except Exception as e:
        print(f"Error parsing email: {str(e)}")
        return {key: None for key in required_keys}

@app.route('/api/parse', methods=['POST'])
def parse_email():
    try:
        email_text = request.json.get('email')
        if not email_text:
            return jsonify({'error': 'No email text provided'}), 400

        parsed_data = parse_email_reply(email_text)
        
        # Store in database using pg8000
        conn = get_db_connection()
        try:
            result = conn.run(
                """
                INSERT INTO parsed_emails 
                (input_text, reply_type, proposed_time, meeting_link, delegate_to, additional_notes)
                VALUES (:1, :2, :3, :4, :5, :6)
                RETURNING id, created_at
                """,
                (
                    email_text,
                    parsed_data.get('reply_type'),
                    parsed_data.get('proposed_time'),
                    parsed_data.get('meeting_link'),
                    parsed_data.get('delegate_to'),
                    parsed_data.get('additional_notes')
                )
            )
            conn.commit()
            
            # Add database ID to response
            parsed_data['id'] = result[0][0]
            parsed_data['created_at'] = result[0][1].isoformat()
            
            return jsonify(parsed_data)
        finally:
            conn.close()

    except Exception as e:
        print(f"Error in parse_email: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM parsed_emails 
                    ORDER BY created_at DESC 
                    LIMIT 50
                """)
                history = cur.fetchall()
                
                # Convert datetime objects to ISO format strings
                for row in history:
                    if row['created_at']:
                        row['created_at'] = row['created_at'].isoformat()
                    if row['proposed_time']:
                        row['proposed_time'] = row['proposed_time'].isoformat()
                
                return jsonify(history)

    except Exception as e:
        print(f"Error in get_history: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True)

nlp = spacy.load("en_core_web_sm")  # Load spaCy model once at module level

def classify_reply_gemini(email_text):
    """Classifies email reply and extracts information using Gemini."""
    
    # Enhance prompt for better context handling
    prompt = f"""
    Analyze this email(can be multiple emails) reply for meeting scheduling information. Extract and return a JSON object with these exact keys:
    - reply_type: (acceptance, reschedule, decline, info_request, delegation)
    - proposed_time: (ISO 8601 datetime or null)
    - meeting_link: (URL or null)
    - delegate_to: (email address or null)
    - additional_notes: (string or null)
   
    

 


    Email:
    {email_text}
    """

    try:
        response = text.generate_text(
            model="gemini-pro",
            prompt=prompt,
            temperature=0.1,  # Lower temperature for more consistent outputs
            max_output_tokens=300
        )

        # Validate and clean Gemini response
        json_output = response.result.strip()
        reply_data = json.loads(json_output)

        # Normalize the response
        expected_keys = ["reply_type", "proposed_time", "meeting_link", "delegate_to", "additional_notes"]
        normalized_data = {key: None for key in expected_keys}
        
        for key, value in reply_data.items():
            if key in normalized_data:
                if key == "proposed_time" and value:
                    try:
                        dt = parser.parse(value, fuzzy=True)
                        normalized_data[key] = dt.isoformat()
                    except ValueError:
                        normalized_data[key] = None
                else:
                    normalized_data[key] = value if value not in ("", None) else None

        return normalized_data

    except Exception as e:
        print(f"Error processing with Gemini: {str(e)}")
        return {key: None for key in expected_keys}

def parse_email_reply(email_text):
    """Main function to parse email replies and extract structured information."""
    if not email_text:
        raise ValueError("Email text cannot be empty")

    # Process email with Gemini for all information
    reply_data = classify_reply_gemini(email_text)
    
    # Additional validation or processing can be added here
    
    return reply_data












