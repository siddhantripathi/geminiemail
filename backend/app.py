import os
from flask import Flask, request, jsonify
from datetime import datetime
import json
from dotenv import load_dotenv
import google.generativeai as genai
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-pro')

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
                normalized_data[key] = value if value and value != "" else None
        
        return normalized_data

    except Exception as e:
        print(f"Error parsing email: {str(e)}")
        return {key: None for key in required_keys}

@app.route('/api/parse', methods=['POST'])
def parse_email():
    try:
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
            
        email_text = request.json.get('email')
        if not email_text:
            return jsonify({'error': 'No email text provided'}), 400

        # Parse email and return results
        parsed_data = parse_email_reply(email_text)
        return jsonify(parsed_data)

    except Exception as e:
        print(f"Error in parse_email: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Add a health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(debug=True)












