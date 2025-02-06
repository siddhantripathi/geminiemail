import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import google.generativeai as genai
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure Gemini with safety settings
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

genai.configure(api_key=api_key)
generation_config = {
    "temperature": 0.1,  # Lower temperature for more consistent output
    "top_p": 0.8,
    "top_k": 40,
    "max_output_tokens": 1024,
}

safety_settings = [
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_NONE"
    }
]

model = genai.GenerativeModel(
    model_name='gemini-pro',
    generation_config=generation_config,
    safety_settings=safety_settings
)

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

        prompt = """You are a helpful email analyzer. Your task is to extract information from the email below and return it in JSON format.
        
Email to analyze: "{}"

Return only a JSON object with these fields:
- reply_type: one of ["acceptance", "reschedule", "decline", "info_request", "delegation"]
- proposed_time: ISO 8601 datetime or null
- meeting_link: URL or null
- delegate_to: email address or null
- additional_notes: string or null

Example response:
{{"reply_type": "acceptance", "proposed_time": "2024-03-20T14:00:00Z", "meeting_link": null, "delegate_to": null, "additional_notes": "Will bring presentation materials"}}""".format(email_text)

        try:
            response = model.generate_content(prompt)
            
            if not response.candidates or not response.candidates[0].content:
                return jsonify({"error": "No valid response generated"}), 500
            
            response_text = response.candidates[0].content.parts[0].text.strip()
            print("Raw response:", response_text)  # Debug log
            
            if not response_text:
                return jsonify({"error": "Empty response received"}), 500

            try:
                import json
                parsed_json = json.loads(response_text)
                
                # Validate required fields
                required_keys = ["reply_type", "proposed_time", "meeting_link", "delegate_to", "additional_notes"]
                normalized_data = {key: None for key in required_keys}
                
                for key, value in parsed_json.items():
                    if key in normalized_data:
                        normalized_data[key] = value if value and str(value).strip() != "" else None
                
                return jsonify(normalized_data)
                
            except json.JSONDecodeError as e:
                print(f"JSON parsing error: {str(e)}")
                print(f"Response text: {response_text}")
                return jsonify({"error": f"Invalid JSON in response: {str(e)}"}), 500
            
        except Exception as e:
            print(f"Gemini API error: {str(e)}")
            return jsonify({"error": f"Error processing with Gemini: {str(e)}"}), 500

    except Exception as e:
        print(f"Server error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)












