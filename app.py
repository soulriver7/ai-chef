import os
import google.generativeai as genai
from flask import Flask, request, jsonify, render_template, abort

# --- 초기 설정 ---
# Flask 앱 초기화 및 템플릿 폴더 지정
app = Flask(__name__, template_folder='templates')

# Gemini API 키 설정
# Render와 같은 배포 플랫폼의 '환경 변수'에 키를 저장하는 것이 가장 안전합니다.
# 코드에 직접 API 키를 작성하지 마세요.
try:
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.")
    genai.configure(api_key=gemini_api_key)
except (ValueError, AttributeError) as e:
    # 이 부분은 서버 로그에만 표시됩니다.
    print(f"API 키 설정 오류: {e}")
    # 프로그램 실행을 중단하지 않고, 나중에 API 호출 시 오류를 처리합니다.


# --- 라우팅 (URL 경로 설정) ---

@app.route('/')
def index():
    """메인 HTML 페이지를 렌더링합니다."""
    return render_template('index.html')

@app.route('/api/find-recipe', methods=['POST'])
def find_recipe_api():
    """프론트엔드로부터 재료를 받아 Gemini API로 레시피를 검색하고 결과를 반환합니다."""
    
    # API 키가 설정되지 않았다면, 여기서 요청을 중단시킵니다.
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
        return response.text, 200, {'Content-Type': 'application/json'}

    except Exception as e:
        print(f"An error occurred during Gemini API call: {e}")
        return jsonify({"error": "레시피를 검색하는 중 AI 서버에서 오류가 발생했습니다."}), 500

# 로컬 테스트용 서버 실행 코드
if __name__ == '__main__':
    # debug=True는 코드 변경 시 서버 자동 재시작 (배포 시에는 False 또는 제거)
    app.run(port=5001, debug=True)