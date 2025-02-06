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
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in environment variables")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-pro')

@app.route('/')
def home():
    return jsonify({"status": "API is running"})

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "gemini": "configured" if api_key else "not configured"})

@app.route('/api/parse', methods=['POST'])
def parse_email():
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400
        
        data = request.get_json()
        email_text = data.get('email')
        
        if not email_text:
            return jsonify({"error": "No email text provided"}), 400

        # Modified prompt to be more explicit about JSON formatting
        prompt = """You are a JSON generator. Your task is to analyze this email and return ONLY a JSON object with no additional text or formatting.

        Analyze this email:
        \"\"\"
        {}
        \"\"\"

        Return a JSON object in this exact format:
        {{
            "reply_type": "acceptance" | "reschedule" | "decline" | "info_request" | "delegation",
            "proposed_time": "ISO 8601 datetime or null",
            "meeting_link": "URL or null",
            "delegate_to": "email address or null",
            "additional_notes": "string or null"
        }}""".format(email_text)

        try:
            # Debug: Print the prompt
            print("Sending prompt to Gemini:", prompt)
            
            response = model.generate_content(prompt)
            
            # Debug: Print raw response
            print("Raw Gemini response:", repr(response.text))
            
            # Clean the response text
            response_text = response.text.strip()
            
            # Debug: Print cleaned response
            print("Cleaned response text:", repr(response_text))
            
            if not response_text:
                return jsonify({"error": "Empty response from Gemini"}), 500

            try:
                parsed_json = json.loads(response_text)
                # Debug: Print parsed JSON
                print("Successfully parsed JSON:", parsed_json)
                
                required_keys = ["reply_type", "proposed_time", "meeting_link", "delegate_to", "additional_notes"]
                normalized_data = {key: None for key in required_keys}
                
                for key, value in parsed_json.items():
                    if key in normalized_data:
                        normalized_data[key] = value if value and str(value).strip() != "" else None
                
                return jsonify(normalized_data)
                
            except json.JSONDecodeError as e:
                print(f"JSON parsing error: {str(e)}")
                print(f"Response text causing error: {repr(response_text)}")
                return jsonify({
                    "error": "Invalid JSON response", 
                    "details": str(e),
                    "raw_response": response_text
                }), 500
            
        except Exception as e:
            print(f"Gemini API error: {str(e)}")
            return jsonify({"error": f"Error processing with Gemini: {str(e)}"}), 500

    except Exception as e:
        print(f"Server error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)












