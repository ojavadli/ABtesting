"""
Complete Multimodal Web Interface with Photo/Video Upload
Access: http://localhost:8080

Authors: Anni Zimina & Orkhan Javadli
Stanford GSB - November 21, 2025
"""

from flask import Flask, render_template_string, request, jsonify
import json
import re
import base64
import os
from openai import OpenAI
import anthropic

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

GPT_MODEL = "gpt-5.1"
CLAUDE_MODEL = "claude-4-opus-20250514"
GEMINI_MODEL = "gemini-3-pro-preview"  # Gemini 3 Pro Preview (Nov 2025)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

openai_client = OpenAI(api_key=OPENAI_API_KEY)
claude_client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

# Initialize Gemini
import google.generativeai as genai
genai.configure(api_key=GOOGLE_API_KEY)
gemini_model = genai.GenerativeModel(GEMINI_MODEL)

HTML = """<!DOCTYPE html>
<html>
<head>
    <title>Multimodal Agentic System</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif;
            background: linear-gradient(135deg, #1a2a6c 0%, #b21f1f 25%, #fdbb2d 50%, #22c1c3 75%, #fdbb2d 100%);
            background-size: 400% 400%;
            animation: gradient 15s ease infinite;
            min-height: 100vh;
            padding: 40px 20px;
        }
        
        @keyframes gradient {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        
        .container { max-width: 1100px; margin: 0 auto; }
        
        .glass-card {
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(30px) saturate(180%);
            border: 1px solid rgba(255, 255, 255, 0.3);
            padding: 50px;
            margin-bottom: 30px;
        }
        
        h1 { color: white; font-size: 3.5em; font-weight: 700; text-align: center; margin-bottom: 15px; letter-spacing: -1px; }
        .subtitle { color: rgba(255, 255, 255, 0.9); text-align: center; font-size: 1.3em; font-weight: 300; margin-bottom: 30px; }
        
        .mode-selector { display: flex; gap: 20px; justify-content: center; margin: 30px 0; }
        
        .mode-btn {
            background: rgba(255, 255, 255, 0.2);
            backdrop-filter: blur(10px);
            color: white;
            padding: 15px 30px;
            border: 1px solid rgba(255, 255, 255, 0.3);
            cursor: pointer;
            font-size: 1.1em;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        
        .mode-btn:hover { background: rgba(255, 255, 255, 0.3); transform: translateY(-2px); }
        .mode-btn.active { background: white; color: #1a2a6c; }
        
        .content-section { display: none; }
        .content-section.active { display: block; }
        
        .variant-box {
            background: rgba(255, 255, 255, 0.25);
            backdrop-filter: blur(10px);
            padding: 30px;
            border: 1px solid rgba(255, 255, 255, 0.4);
            margin: 20px 0;
        }
        
        .variant-label { color: white; font-size: 1.5em; font-weight: 600; margin-bottom: 15px; }
        
        textarea {
            width: 100%;
            min-height: 120px;
            padding: 18px;
            background: rgba(255, 255, 255, 0.95);
            border: none;
            font-size: 1em;
            font-family: inherit;
            color: #1d1d1f;
        }
        
        textarea:focus { outline: none; background: white; box-shadow: 0 8px 25px rgba(0,0,0,0.15); }
        textarea::placeholder { color: #86868b; }
        
        input[type="text"], input[type="file"] {
            width: 100%;
            padding: 15px 20px;
            background: rgba(255, 255, 255, 0.95);
            border: none;
            font-size: 1em;
            margin: 10px 0;
            color: #1d1d1f;
        }
        
        input:focus { outline: none; background: white; }
        input::placeholder { color: #86868b; }
        
        .upload-label {
            color: white;
            font-size: 1em;
            font-weight: 500;
            margin: 15px 0 8px 0;
            display: block;
        }
        
        .file-input-wrapper {
            position: relative;
            display: inline-block;
            width: 100%;
        }
        
        input[type="file"] {
            cursor: pointer;
        }
        
        .btn {
            background: white;
            color: #1a2a6c;
            padding: 18px 50px;
            border: none;
            font-size: 1.3em;
            font-weight: 600;
            cursor: pointer;
            display: block;
            margin: 40px auto;
            transition: all 0.3s ease;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        
        .btn:hover { transform: translateY(-3px); box-shadow: 0 15px 40px rgba(0,0,0,0.3); }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; }
        
        .results { margin-top: 40px; display: none; }
        
        .score-display { background: rgba(255, 255, 255, 0.95); padding: 40px; color: #1d1d1f; }
        
        .score-huge { font-size: 4em; font-weight: 700; text-align: center; margin: 20px 0; }
        .score-label { font-size: 0.4em; color: #86868b; font-weight: 400; }
        
        .component-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin: 30px 0;
        }
        
        .component-item { text-align: center; padding: 15px; background: rgba(0,0,0,0.03); }
        .component-value { font-size: 1.8em; font-weight: 600; color: #1a2a6c; }
        .component-label { font-size: 0.9em; color: #86868b; margin-top: 5px; }
        
        .loading { text-align: center; display: none; color: white; margin: 30px 0; }
        .spinner { border: 3px solid rgba(255,255,255,0.3); border-top: 3px solid white; width: 50px; height: 50px; animation: spin 1s linear infinite; margin: 20px auto; }
        @keyframes spin { 100% { transform: rotate(360deg); } }
        
        .preview-img { max-width: 100%; height: auto; margin: 15px 0; border: 2px solid rgba(255,255,255,0.5); }
    </style>
</head>
<body>
    <div class="container">
        <div class="glass-card">
            <h1>Multimodal Agentic System</h1>
            <div class="subtitle">Virality Prediction & A/B Testing</div>
            
            <div class="mode-selector">
                <button class="mode-btn active" onclick="switchMode('single')">Score Single Content</button>
                <button class="mode-btn" onclick="switchMode('ab')">A/B Comparison</button>
            </div>
            
            <!-- Single Content Scoring -->
            <div id="singleMode" class="content-section active">
                <div class="variant-box">
                    <div class="variant-label">Content to Score</div>
                    <textarea id="singleText" placeholder="Enter your content text..."></textarea>
                    
                    <label class="upload-label">Upload Image or Video (optional):</label>
                    <input type="file" id="singleFile" accept="image/*,video/*" onchange="previewFile('singleFile', 'singlePreview')">
                    <div id="singlePreview"></div>
                </div>
                <input type="text" id="singleAudience" placeholder="Target Audience" value="urban professionals, ages 25-40">
                <input type="text" id="singleCategory" placeholder="Business Category" value="restaurant">
                <button class="btn" onclick="scoreSingle()">Get Virality Score</button>
            </div>
            
            <!-- A/B Comparison -->
            <div id="abMode" class="content-section">
                <div class="variant-box">
                    <div class="variant-label">Variant A</div>
                    <textarea id="textA" placeholder="Enter content for Variant A..."></textarea>
                    <label class="upload-label">Upload Image/Video A (optional):</label>
                    <input type="file" id="fileA" accept="image/*,video/*" onchange="previewFile('fileA', 'previewA')">
                    <div id="previewA"></div>
                </div>
                
                <div class="variant-box">
                    <div class="variant-label">Variant B</div>
                    <textarea id="textB" placeholder="Enter content for Variant B..."></textarea>
                    <label class="upload-label">Upload Image/Video B (optional):</label>
                    <input type="file" id="fileB" accept="image/*,video/*" onchange="previewFile('fileB', 'previewB')">
                    <div id="previewB"></div>
                </div>
                
                <input type="text" id="abAudience" placeholder="Target Audience" value="urban professionals, ages 25-40">
                <input type="text" id="abCategory" placeholder="Business Category" value="restaurant">
                <button class="btn" onclick="predictAB()">Predict Winner</button>
            </div>
            
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <div>Analyzing with GPT-5.1 & Claude 4 Opus...</div>
            </div>
            
            <div class="results" id="results"></div>
        </div>
    </div>
    
    <script>
        function switchMode(mode) {
            document.querySelectorAll('.mode-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            
            document.getElementById('singleMode').classList.remove('active');
            document.getElementById('abMode').classList.remove('active');
            document.getElementById(mode + 'Mode').classList.add('active');
            document.getElementById('results').style.display = 'none';
        }
        
        function previewFile(inputId, previewId) {
            const file = document.getElementById(inputId).files[0];
            const preview = document.getElementById(previewId);
            
            if (file) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    if (file.type.startsWith('image/')) {
                        preview.innerHTML = `<img src="${e.target.result}" class="preview-img">`;
                    } else {
                        preview.innerHTML = `<div style="color:white; padding:10px;">✓ Video selected: ${file.name}</div>`;
                    }
                };
                reader.readAsDataURL(file);
            }
        }
        
        async function scoreSingle() {
            document.getElementById('loading').style.display = 'block';
            document.getElementById('results').style.display = 'none';
            
            const formData = new FormData();
            formData.append('text', document.getElementById('singleText').value);
            formData.append('target_audience', document.getElementById('singleAudience').value);
            formData.append('business_category', document.getElementById('singleCategory').value);
            
            const fileInput = document.getElementById('singleFile');
            if (fileInput.files[0]) {
                formData.append('image', fileInput.files[0]);
            }
            
            const response = await fetch('/score_single', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            document.getElementById('loading').style.display = 'none';
            
            document.getElementById('results').innerHTML = `
                <div class="score-display">
                    <div class="score-huge">${result.overall_score.toFixed(0)}<span class="score-label">/100</span></div>
                    <div style="text-align:center;font-size:1.2em;color:#86868b;margin-bottom:30px;">Virality Score</div>
                    
                    <div class="component-grid">
                        <div class="component-item"><div class="component-value">${result.text_quality.toFixed(0)}</div><div class="component-label">Text</div></div>
                        <div class="component-item"><div class="component-value">${result.visual_appeal.toFixed(0)}</div><div class="component-label">Visual</div></div>
                        <div class="component-item"><div class="component-value">${result.emotional_resonance.toFixed(0)}</div><div class="component-label">Emotional</div></div>
                        <div class="component-item"><div class="component-value">${result.clarity.toFixed(0)}</div><div class="component-label">Clarity</div></div>
                        <div class="component-item"><div class="component-value">${result.brand_alignment.toFixed(0)}</div><div class="component-label">Brand</div></div>
                        <div class="component-item"><div class="component-value">${result.confidence.toFixed(0)}</div><div class="component-label">Confidence</div></div>
                    </div>
                    
                    <div style="margin-top:30px;padding:20px;background:rgba(0,0,0,0.03);">
                        <strong>Analysis:</strong> ${result.reasoning}
                    </div>
                </div>
            `;
            document.getElementById('results').style.display = 'block';
            document.getElementById('results').scrollIntoView({ behavior: 'smooth' });
        }
        
        async function predictAB() {
            document.getElementById('loading').style.display = 'block';
            document.getElementById('results').style.display = 'none';
            
            const formData = new FormData();
            formData.append('text_a', document.getElementById('textA').value);
            formData.append('text_b', document.getElementById('textB').value);
            formData.append('target_audience', document.getElementById('abAudience').value);
            formData.append('business_category', document.getElementById('abCategory').value);
            
            const fileA = document.getElementById('fileA').files[0];
            const fileB = document.getElementById('fileB').files[0];
            if (fileA) formData.append('image_a', fileA);
            if (fileB) formData.append('image_b', fileB);
            
            const response = await fetch('/predict_ab', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            document.getElementById('loading').style.display = 'none';
            
            document.getElementById('results').innerHTML = `
                <div class="score-display">
                    <div style="font-size:3em;font-weight:700;text-align:center;margin:30px 0;">Variant ${result.winner} Wins</div>
                    <div style="text-align:center;font-size:1.5em;color:#86868b;margin-bottom:40px;">${result.confidence.toFixed(0)}% Confidence</div>
                    
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:30px;">
                        <div>
                            <div style="font-size:1.3em;font-weight:600;margin-bottom:15px;">Variant A</div>
                            <div style="font-size:3em;font-weight:700;">${result.score_a.toFixed(0)}<span style="font-size:0.4em;color:#86868b;">/100</span></div>
                            <div class="component-grid" style="grid-template-columns:1fr 1fr;margin-top:20px;">
                                <div class="component-item"><div class="component-value">${result.text_a.toFixed(0)}</div><div class="component-label">Text</div></div>
                                <div class="component-item"><div class="component-value">${result.visual_a.toFixed(0)}</div><div class="component-label">Visual</div></div>
                                <div class="component-item"><div class="component-value">${result.emotional_a.toFixed(0)}</div><div class="component-label">Emotional</div></div>
                                <div class="component-item"><div class="component-value">${result.clarity_a.toFixed(0)}</div><div class="component-label">Clarity</div></div>
                            </div>
                        </div>
                        <div>
                            <div style="font-size:1.3em;font-weight:600;margin-bottom:15px;">Variant B</div>
                            <div style="font-size:3em;font-weight:700;">${result.score_b.toFixed(0)}<span style="font-size:0.4em;color:#86868b;">/100</span></div>
                            <div class="component-grid" style="grid-template-columns:1fr 1fr;margin-top:20px;">
                                <div class="component-item"><div class="component-value">${result.text_b.toFixed(0)}</div><div class="component-label">Text</div></div>
                                <div class="component-item"><div class="component-value">${result.visual_b.toFixed(0)}</div><div class="component-label">Visual</div></div>
                                <div class="component-item"><div class="component-value">${result.emotional_b.toFixed(0)}</div><div class="component-label">Emotional</div></div>
                                <div class="component-item"><div class="component-value">${result.clarity_b.toFixed(0)}</div><div class="component-label">Clarity</div></div>
                            </div>
                        </div>
                    </div>
                    
                    <div style="margin-top:30px;padding:20px;background:rgba(0,0,0,0.03);">
                        <strong>Analysis:</strong> ${result.reasoning}
                    </div>
                </div>
            `;
            document.getElementById('results').style.display = 'block';
            document.getElementById('results').scrollIntoView({ behavior: 'smooth' });
        }
    </script>
</body>
</html>"""

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/score_single', methods=['POST'])
def score_single():
    """Score a single content variant with optional image/video"""
    text = request.form.get('text', '')
    target_audience = request.form.get('target_audience', '')
    business_category = request.form.get('business_category', '')
    
    # Build message content
    user_content = [{
        "type": "text",
        "text": f"""Analyze this {business_category} content for {target_audience}.

Text: {text}

Provide JSON: overall_score, text_quality, visual_appeal, emotional_resonance, clarity, brand_alignment, reasoning, confidence (all 0-100)"""
    }]
    
    # Add image if uploaded
    if 'image' in request.files:
        file = request.files['image']
        if file.filename:
            image_data = base64.b64encode(file.read()).decode('utf-8')
            user_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
            })
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-5.1",
            messages=[
                {"role": "system", "content": "Marketing analyst. JSON only."},
                {"role": "user", "content": user_content}
            ],
            max_completion_tokens=500,
            temperature=0.2
        )
        
        text_response = response.choices[0].message.content
        match = re.search(r'```json\s*(.*?)\s*```', text_response, re.DOTALL)
        if match: text_response = match.group(1)
        elif '{' in text_response: text_response = text_response[text_response.find('{'):text_response.rfind('}')+1]
        
        return jsonify(json.loads(text_response))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/predict_ab', methods=['POST'])
def predict_ab():
    """A/B comparison with optional images/videos"""
    
    def score_variant(text, image_file=None):
        user_content = [{
            "type": "text",
            "text": f"Analyze: {text}\nContext: {request.form.get('business_category')} for {request.form.get('target_audience')}\nJSON: overall_score, text_quality, visual_appeal, emotional_resonance, clarity, brand_alignment, reasoning, confidence"
        }]
        
        if image_file and image_file.filename:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
            user_content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}})
        
        response = openai_client.chat.completions.create(
            model="gpt-5.1",
            messages=[{"role": "system", "content": "Marketing analyst. JSON."}, {"role": "user", "content": user_content}],
            max_completion_tokens=500,
            temperature=0.2
        )
        
        text = response.choices[0].message.content
        match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if match: text = match.group(1)
        elif '{' in text: text = text[text.find('{'):text.rfind('}')+1]
        return json.loads(text)
    
    try:
        score_a = score_variant(request.form.get('text_a'), request.files.get('image_a'))
        score_b = score_variant(request.form.get('text_b'), request.files.get('image_b'))
        
        overall_a = score_a.get('overall_score', 50)
        overall_b = score_b.get('overall_score', 50)
        winner = 'A' if overall_a > overall_b else 'B'
        confidence = min(50 + abs(overall_a - overall_b) * 0.8, 95)
        
        return jsonify({
            'winner': winner,
            'confidence': confidence,
            'score_a': overall_a, 'score_b': overall_b,
            'text_a': score_a.get('text_quality', 50), 'text_b': score_b.get('text_quality', 50),
            'visual_a': score_a.get('visual_appeal', 50), 'visual_b': score_b.get('visual_appeal', 50),
            'emotional_a': score_a.get('emotional_resonance', 50), 'emotional_b': score_b.get('emotional_resonance', 50),
            'clarity_a': score_a.get('clarity', 50), 'clarity_b': score_b.get('clarity', 50),
            'reasoning': score_a.get('reasoning', '') if winner=='A' else score_b.get('reasoning', '')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║      Multimodal Agentic System - COMPLETE with Image/Video Upload           ║
║                Stanford GSB - November 21, 2025                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

🌐 Access: http://localhost:8080

✨ Features:
  • Individual Virality Scoring (0-100)
  • A/B Winner Prediction
  • Image Upload Support ✓
  • Video Upload Support ✓
  • Text Analysis ✓
  
🤖 Models: GPT-5.1 ✓ | Claude 4 Opus ✓ | Gemini 3 Pro (add key)
🎨 Design: Sharp edges, blue-red-yellow-teal gradient, Apple fonts
""")
    app.run(host='0.0.0.0', port=8080, debug=False)

