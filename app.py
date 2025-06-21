import os
import json
import google.generativeai as genai
from flask import Flask, request, jsonify, render_template, abort

# --- 초기 설정 ---
app = Flask(__name__, template_folder='templates')

# Gemini API 키 설정
try:
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.")
    genai.configure(api_key=gemini_api_key)
except (ValueError, AttributeError) as e:
    # 이 부분은 서버 로그에만 표시됩니다.
    print(f"API 키 설정 오류: {e}")

# --- 라우팅 ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/find-recipe', methods=['POST'])
def find_recipe_api():
    if not genai.api_key:
        return jsonify({"error": "서버의 API 키가 설정되지 않았습니다. 관리자에게 문의하세요."}), 500

    data = request.get_json()
    if not data:
        abort(400, "잘못된 요청입니다. JSON 데이터를 보내주세요.")

    ingredients = data.get('ingredients')
    category = data.get('category')
    count = data.get('count')

    if not all([ingredients, category, count]):
        abort(400, "필수 정보(ingredients, category, count)가 누락되었습니다.")

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
You are a world-class AI Chef and YouTube recipe curator. Your task is to find relevant YouTube videos and create recipe summaries based on the user's request.

User's Request:
- Cuisine Category: "{category}"
- Ingredients: "{ingredients}"
- Number of recipes to find: {count}

Please follow these steps and provide the output as a single valid JSON array.

Step 1: Find YouTube Videos.
Based on the user's request, find the {count} most popular and highly-rated YouTube videos. For each video, provide its Korean title and videoId.

Step 2: Create Recipe Summaries.
For each video you've found, generate a detailed recipe summary as if you have watched the entire video. The summary MUST be in Korean and follow this Notion-style format using Markdown:

### 📜 요리 소개
(A brief, enticing introduction to the dish, 1-2 sentences.)

### 🥕 재료
* Ingredient 1 (e.g., 돼지고기 300g)
* Ingredient 2
* **양념:** Seasoning 1, Seasoning 2

### 📝 조리 순서
1. First step of the recipe.
2. Second step.
3. ...and so on.

Step 3: Format the Final Output.
Combine the information from the previous steps into a single JSON array. Each object in the array should represent one recipe and have the following structure:
{{
  "title": "The title of the YouTube video",
  "videoId": "The YouTube video ID (e.g., qWbHSOplcvI)",
  "summary": "The complete Notion-style recipe summary in Markdown format."
}}

Do not include any text or explanations outside of the final JSON array.
"""
        
        response = model.generate_content(prompt)
        
        # Gemini 응답이 올바른 JSON인지 백엔드에서 먼저 검증
        try:
            # response.text가 올바른 JSON 형식인지 파싱 시도
            parsed_json = json.loads(response.text)
            # 성공하면 jsonify를 사용해 안전하게 JSON 응답 생성
            return jsonify(parsed_json)
        except json.JSONDecodeError:
            # Gemini가 JSON이 아닌 다른 텍스트를 반환한 경우
            print("Warning: Gemini response was not valid JSON. Response text:", response.text)
            return jsonify({"error": "AI가 레시피를 생성하는 데 실패했습니다. 잠시 후 다른 재료로 시도해보세요."}), 500


    except Exception as e:
        print(f"An error occurred during Gemini API call: {e}")
        return jsonify({"error": "레시피를 검색하는 중 AI 서버에서 오류가 발생했습니다."}), 500

# 로컬 테스트용 서버 실행 코드
if __name__ == '__main__':
    app.run(port=5001, debug=True)