import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import google.generativeai as genai
from flask_cors import CORS
import json

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure Gemini
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

genai.configure(api_key=api_key)
generation_config = {
    "temperature": 0.1,
    "top_p": 1,
    "top_k": 32,
    "max_output_tokens": 1024,
}

model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    generation_config=generation_config
)

def analyze_email(email_text):
    prompt = f"""Analyze this email carefully and extract information. Return ONLY a JSON object.

Input email:
{email_text}

Rules for extraction:
1. reply_type:
   - "acceptance" if confirming attendance
   - "reschedule" if suggesting new time
   - "decline" if refusing
   - "delegation" if forwarding to someone else
   - "info_request" for questions or information sharing
2. proposed_time: 
   - Extract ANY mentioned date/time (e.g., "Tuesday at 2 PM", "tomorrow afternoon", "next week")
   - Convert to ISO format (e.g., "2024-03-21T14:00:00Z")
   - If multiple times mentioned, use the most definitive one
3. meeting_link:
   - Look for URLs containing: zoom, meet, teams, webex, or any meeting links
4. delegate_to:
   - Extract email addresses or names of people being delegated to
5. additional_notes:
   - Include key information like agenda items, action items, or important context

Return EXACT format:
{{
    "reply_type": "acceptance" | "reschedule" | "decline" | "info_request" | "delegation",
    "proposed_time": "<ISO datetime or null>",
    "meeting_link": "<URL or null>",
    "delegate_to": "<email/name or null>",
    "additional_notes": "<important details or null>"
}}"""

    try:
        response = model.generate_content(prompt)
        
        if hasattr(response, 'text'):
            response_text = response.text.strip()
        else:
            # Handle structured response
            response_text = response.candidates[0].content.parts[0].text.strip()
            
        print("Raw Gemini response:", response_text)  # Debug log
        
        # Try to find JSON in the response
        try:
            # Find the first { and last } in the response
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start != -1 and end != 0:
                json_str = response_text[start:end]
                parsed_json = json.loads(json_str)
            else:
                raise ValueError("No JSON object found in response")
                
            # Validate required fields
            required_keys = ["reply_type", "proposed_time", "meeting_link", "delegate_to", "additional_notes"]
            normalized_data = {key: None for key in required_keys}
            
            valid_reply_types = ["acceptance", "reschedule", "decline", "info_request", "delegation"]
            
            for key, value in parsed_json.items():
                if key in normalized_data:
                    if key == "reply_type" and value not in valid_reply_types:
                        normalized_data[key] = "info_request"  # default if invalid
                    else:
                        normalized_data[key] = value if value and str(value).strip() != "" else None
            
            return normalized_data
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {str(e)}")
            print(f"Attempted to parse: {response_text}")
            raise
            
    except Exception as e:
        print(f"Error in analyze_email: {str(e)}")
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

        try:
            result = analyze_email(email_text)
            return jsonify(result)
            
        except Exception as e:
            print(f"Analysis error: {str(e)}")
            return jsonify({
                "error": "Failed to analyze email",
                "details": str(e)
            }), 500

    except Exception as e:
        print(f"Server error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)












