import os
from flask import Flask, request, jsonify
import json
from dotenv import load_dotenv
import google.generativeai as genai
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure Gemini
try:
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')
except Exception as e:
    print(f"Error configuring Gemini: {str(e)}")
    raise

@app.route('/')
def home():
    return jsonify({"status": "API is running"})

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"})

@app.route('/api/parse', methods=['POST'])
def parse_email():
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400
        
        data = request.get_json()
        email_text = data.get('email')
        
        if not email_text:
            return jsonify({"error": "No email text provided"}), 400

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
            
            required_keys = ["reply_type", "proposed_time", "meeting_link", "delegate_to", "additional_notes"]
            normalized_data = {key: None for key in required_keys}
            
            for key, value in parsed_json.items():
                if key in normalized_data:
                    normalized_data[key] = value if value and value != "" else None
            
            return jsonify(normalized_data)
            
        except Exception as e:
            print(f"Gemini API error: {str(e)}")
            return jsonify({"error": f"Error processing with Gemini: {str(e)}"}), 500

    except Exception as e:
        print(f"Server error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)












