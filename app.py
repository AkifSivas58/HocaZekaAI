from flask import Flask, jsonify, request, render_template
import google.generativeai as genai
from dotenv import load_dotenv
import os

app = Flask(__name__)
load_dotenv()

genai.configure(api_key=os.getenv("API_KEY"))

# Create the model
generation_config = {
  "temperature": 0.7,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

def create_model(system_instruction):
    return genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        generation_config=generation_config,
        system_instruction=system_instruction
    )

@app.route("/")
def home():
    return render_template('index.html')


@app.route("/explain", methods=["POST"])
def explain():
    try:
        model = create_model(
            "You are an educational assistant. Explain the topic in simple terms with: "
            "1. Clear definitions "
            "2. Real-world examples "
            "3. Key takeaways "
            "Keep explanations concise but thorough."
        )
        
        input_data = request.json
        prompt = f"Please explain this topic: {input_data['text']}"
        response = model.start_chat().send_message(prompt)
        
        return jsonify({'response': response.text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

@app.route("/generate-quiz", methods=["POST"])
def generate_quiz():
    try:
        model = create_model(
            "You are a quiz generator. Create a mix of multiple choice and short answer questions. "
            "For each question, include: "
            "1. The question "
            "2. The correct answer "
            "3. For multiple choice, include 3-4 plausible options "
            "4. A brief explanation of why the answer is correct"
        )
        
        input_data = request.json
        difficulty = input_data.get('difficulty', 'medium')
        
        prompt = f"""
        Generate a quiz about: {input_data['text']}
        Difficulty level: {difficulty}
        Include 5 questions with a mix of multiple choice and short answer formats.
        """
        
        response = model.start_chat().send_message(prompt)
        return jsonify({"response": response.text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/summarize", methods=["POST"])
def summarize():
    try:
        model = create_model(
            "You are a note generator for teachers. Create comprehensive teaching notes that include: "
            "1. Main concepts and definitions "
            "2. Key points to emphasize "
            "3. Potential discussion questions "
            "4. Examples to share with students "
            "5. Common misconceptions to address"
        )
        
        input_data = request.json
        prompt = f"Generate teaching notes for: {input_data['text']}"
        response = model.start_chat().send_message(prompt)
        
        return jsonify({"response": response.text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)