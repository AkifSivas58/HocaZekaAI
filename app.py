from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from dataclasses import dataclass
from typing import Optional, List
import google.generativeai as genai
from dotenv import load_dotenv
import os
import json

app = Flask(__name__)
CORS(app)
load_dotenv()

@dataclass
class AIResponse:
    content: str
    metadata: Optional[dict] = None
    error: Optional[str] = None

class GeminiAI:
    def __init__(self):
        genai.configure(api_key=os.getenv("API_KEY"))
        self.generation_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": 8192,
        }
    
    def create_model(self, system_instruction: str):
        return genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            generation_config=self.generation_config,
            system_instruction=system_instruction
        )

    def generate_response(self, prompt: str, system_instruction: str) -> AIResponse:
        try:
            model = self.create_model(system_instruction)
            response = model.start_chat().send_message(prompt)
            return AIResponse(content=response.text)
        except Exception as e:
            return AIResponse(content="", error=str(e))

class EducationAI:
    def __init__(self):
        self.ai = GeminiAI()
        
    def explain_topic(self, topic: str, grade_level: Optional[str] = None) -> AIResponse:
        system_instruction = """
        You are an educational assistant specialized in explaining complex topics to students.
        Follow these guidelines:
        1. Start with a clear, grade-appropriate definition
        2. Break down complex concepts into digestible parts
        3. Make sure to include common formulas or similar knowledge if exists.
        4. Use relevant real-world examples
        5. Address common misconceptions
        6. Include 2-3 key takeaways
        7. Add suggested further reading or exploration topics
        """
        
        prompt = f"""
        Topic: {topic}
        Grade Level: {grade_level if grade_level else 'General'}
        
        Please provide a comprehensive explanation following the structure above.
        """
        
        return self.ai.generate_response(prompt, system_instruction)

    def generate_quiz(self, topic: str, question_types: str, difficulty: str, num_questions: int = 5) -> AIResponse:
        system_instruction = """
        You are a professional quiz generator for students. Create balanced assessments that:
        1. Test different cognitive levels (recall, understanding, application)
        2. Make the students use their knowledge they learnt in that topic and ask challenging questions.
        3. Provide clear, educational explanations
        4. Include difficulty-appropriate distractors for multiple choice
        
        IMPORTANT: You must format your response as valid JSON following this exact structure:
        {
            "questions": [
                {
                    "type": "multiple_choice", // or "open_ended" or "true_false" 
                    "question": "question text",
                    "correct_answer": "answer",
                    "options": ["option1", "option2", "option3", "option4"], // only for multiple_choice
                    "explanation": "explanation text"
                }
            ]
        }
        Do not include any other text outside of this JSON structure.
        """
        
        prompt = f"""
        Generate a {difficulty} difficulty quiz about {topic} with {num_questions} questions.
        Questions should be of type: {question_types}
        For true/false questions, provide only two options: "True" and "False".
        For open-ended questions, do not provide options but include a clear correct answer.

        Remember to return ONLY valid JSON following the specified structure.
        """
        
        response = self.ai.generate_response(prompt, system_instruction)
        
        # Validate JSON structure
        try:
            quiz_data = json.loads(response.content)
        except json.JSONDecodeError:
            try:
                # Look for JSON-like structure in the text
                import re
                json_match = re.search(r'({[\s\S]*})', response.content)
                if json_match:
                    quiz_data = json.loads(json_match.group(1))
                else:
                    return AIResponse(content="", error="Failed to generate properly formatted quiz")
            except (json.JSONDecodeError, AttributeError):
                return AIResponse(content="", error="Failed to generate properly formatted quiz")

        return AIResponse(content=json.dumps(quiz_data, indent=2), metadata={"question_count": len(quiz_data["questions"])})

    def generate_teaching_notes(self, topic: str, duration: Optional[str] = "60 minutes") -> AIResponse:
        system_instruction = """
        You are a professional curriculum designer for teachers to use in their lectures. Create comprehensive teaching notes that include:
        1. Learning objectives
        2. Key concepts and definitions
        3. Suggested teaching activities and timings
        4. Discussion questions and prompts
        5. Common misconceptions and how to address them
        6. Assessment strategies
        7. Differentiation suggestions for different learning levels
        """
        
        prompt = f"""
        Create detailed teaching notes for a {duration} lesson on {topic}.
        Include suggestions for both in-person and online teaching modalities.
        """
        
        return self.ai.generate_response(prompt, system_instruction)

# Initialize the education AI
edu_ai = EducationAI()

@app.route('/')
def index():
    return render_template('index.html')

@app.route("/api/explain", methods=["POST"])
def explain():
    data = request.json
    response = edu_ai.explain_topic(
        topic=data["text"],
        grade_level=data.get("grade_level")
    )
    if response.error:
        return jsonify({"error": response.error}), 500
    return jsonify({"response": response.content})

@app.route("/api/generate-quiz", methods=["POST"])
def generate_quiz():
    data = request.json
    response = edu_ai.generate_quiz(
        topic=data["text"],
        difficulty=data.get("difficulty", "medium"),
        num_questions=data.get("num_questions", 5),
        question_types=data.get("question_types", "true_false")
    )
    if response.error:
        return jsonify({"error": response.error}), 500
    return jsonify({
        "response": response.content,
        "metadata": response.metadata
    })

@app.route("/api/teaching-notes", methods=["POST"])
def teaching_notes():
    data = request.json
    response = edu_ai.generate_teaching_notes(
        topic=data["text"],
        duration=data.get("duration", "60 minutes")
    )
    if response.error:
        return jsonify({"error": response.error}), 500
    return jsonify({"response": response.content})

if __name__ == "__main__":
    app.run(debug=True)