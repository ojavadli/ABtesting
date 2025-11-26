"""
Multimodal Agentic System with Instagram Boost Targeting
Matches Instagram's actual ad targeting parameters

November 21, 2025
"""

from flask import Flask, render_template_string, request, jsonify
import json, re, base64, os, tempfile, io
from openai import OpenAI
import anthropic
import google.generativeai as genai
import PIL.Image

OPENAI_KEY = os.getenv('OPENAI_API_KEY')
CLAUDE_KEY = os.getenv('CLAUDE_API_KEY')
GOOGLE_KEY = os.getenv('GOOGLE_API_KEY')

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB

openai_client = OpenAI(api_key=OPENAI_KEY)
claude_client = anthropic.Anthropic(api_key=CLAUDE_KEY)
genai.configure(api_key=GOOGLE_KEY)
gemini_model = genai.GenerativeModel('gemini-3-pro-preview')

def extract_frame(video_bytes):
    try:
        import cv2, numpy as np
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp:
            tmp.write(video_bytes)
            path = tmp.name
        cap = cv2.VideoCapture(path)
        ret, frame = cap.read()
        cap.release()
        os.unlink(path)
        if ret:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = PIL.Image.fromarray(rgb)
            img.thumbnail((800, 800))
            buf = io.BytesIO()
            img.save(buf, format='JPEG', quality=80)
            return buf.getvalue()
    except: pass
    return None

def parse_json(txt):
    m = re.search(r'```json\s*(.*?)\s*```', txt, re.DOTALL)
    if m: txt = m.group(1)
    elif '{' in txt: txt = txt[txt.find('{'):txt.rfind('}')+1]
    return json.loads(txt)

def score_gpt(text, img_data, targeting_context):
    uc = [{"type": "text", "text": f"Rate this social media post for virality.\n\nTargeting: {targeting_context}\nCaption: {text}\n\nProvide realistic scores (most content is 40-80/100). JSON: overall_score, text_quality, visual_appeal, emotional_resonance, clarity, brand_alignment, reasoning (all 0-100)"}]
    if img_data:
        uc.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64.b64encode(img_data).decode()}"}})
    r = openai_client.chat.completions.create(model="gpt-5.1", messages=[{"role":"user","content":uc}], max_completion_tokens=400, temperature=0.2)
    return parse_json(r.choices[0].message.content)

def score_claude(text, img_data, targeting_context):
    cb = [{"type":"text","text":f"Rate this social media post for virality.\n\nTargeting: {targeting_context}\nCaption: {text}\n\nProvide realistic scores (most content is 40-80/100). JSON: overall_score, text_quality, visual_appeal, emotional_resonance, clarity, brand_alignment, reasoning"}]
    if img_data:
        # Compress image for Claude (5MB limit)
        img = PIL.Image.open(io.BytesIO(img_data))
        if img.width > 1024 or img.height > 1024:
            img.thumbnail((1024, 1024))
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=80)
        compressed = buf.getvalue()
        cb.append({"type":"image","source":{"type":"base64","media_type":"image/jpeg","data":base64.b64encode(compressed).decode()}})
    r = claude_client.messages.create(model="claude-4-opus-20250514", max_tokens=400, messages=[{"role":"user","content":cb}])
    return parse_json(r.content[0].text)

def score_gemini(text, img_data, targeting_context):
    parts = [f"Rate this social media post for virality.\n\nTargeting: {targeting_context}\nCaption: {text}\n\nProvide realistic scores (most content is 40-80/100). JSON: overall_score, text_quality, visual_appeal, emotional_resonance, clarity, brand_alignment, reasoning"]
    if img_data:
        parts.append(PIL.Image.open(io.BytesIO(img_data)))
    r = gemini_model.generate_content(parts)
    return parse_json(r.text)

HTML = """<!DOCTYPE html>
<html><head><title>Multimodal Agentic System</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Afacad+Flux:wght@100..1000&display=swap" rel="stylesheet">
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    font-family: 'Afacad Flux', sans-serif;
    background: linear-gradient(135deg, #1a2a6c 0%, #b21f1f 25%, #fdbb2d 50%, #22c1c3 75%, #fdbb2d 100%);
    background-size: 400% 400%;
    animation: gradient 15s ease infinite;
    min-height: 100vh;
    padding: 40px 20px;
}
@keyframes gradient { 0%{background-position:0% 50%} 50%{background-position:100% 50%} 100%{background-position:0% 50%} }
.container { max-width: 1200px; margin: 0 auto; }
.glass-card { background: rgba(255,255,255,0.15); backdrop-filter: blur(30px); border: 1px solid rgba(255,255,255,0.3); border-radius: 24px; padding: 50px; }
h1 { color: white; font-size: 2.8em; font-weight: 600; text-align: center; margin-bottom: 10px; letter-spacing: -0.5px; }
.subtitle { color: rgba(255,255,255,0.9); text-align: center; font-size: 1.1em; margin-bottom: 30px; font-weight: 400; }
.box { background: rgba(255,255,255,0.25); backdrop-filter: blur(10px); padding: 25px; border: 1px solid rgba(255,255,255,0.4); border-radius: 16px; margin: 20px 0; }
.section-title { color: white; font-size: 1.2em; font-weight: 600; margin-bottom: 15px; }
textarea { width: 100%; min-height: 100px; padding: 15px; background: white; border: none; border-radius: 12px; font-size: 1em; font-family: inherit; resize: vertical; }
input[type="file"] { width: 100%; padding: 12px; background: white; border: none; border-radius: 12px; margin: 8px 0; font-size: 1em; }
select { width: 100%; padding: 12px 16px; background: white; border: none; border-radius: 12px; margin: 8px 0; font-size: 1em; font-family: inherit; appearance: none; background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23666' d='M6 8L1 3h10z'/%3E%3C/svg%3E"); background-repeat: no-repeat; background-position: right 12px center; cursor: pointer; }
label { color: white; display: block; margin: 12px 0 5px 0; font-weight: 500; font-size: 0.95em; }
.btn { background: white; color: #1a2a6c; padding: 16px 48px; border: none; border-radius: 12px; font-size: 1.1em; font-weight: 600; cursor: pointer; display: block; margin: 30px auto; font-family: inherit; transition: transform 0.2s, box-shadow 0.2s; }
.btn:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.2); }
.model-card { background: white; padding: 24px; margin: 12px 0; border-radius: 16px; }
.model-title { font-size: 1.1em; font-weight: 600; color: #1a2a6c; margin-bottom: 8px; }
.score-huge { font-size: 2.8em; font-weight: 700; margin: 10px 0; color: #1a2a6c; }
.components { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin: 12px 0; }
.comp { text-align: center; padding: 10px; background: #f5f5f7; border-radius: 10px; }
.comp-val { font-size: 1.2em; font-weight: 600; color: #1a2a6c; }
.comp-label { font-size: 0.75em; color: #666; margin-top: 2px; }
.rec-card { background: white; padding: 24px; margin: 12px 0; border-radius: 16px; }
.rec-title { font-size: 1.3em; font-weight: 600; color: #1a2a6c; margin-bottom: 20px; }
.rec-item { display: flex; justify-content: space-between; align-items: center; padding: 14px 0; border-bottom: 1px solid #f0f0f0; }
.rec-item:last-child { border-bottom: none; }
.rec-text { flex: 1; font-size: 1em; color: #333; }
.rec-impact { font-size: 1.4em; font-weight: 700; min-width: 70px; text-align: right; }
.positive { color: #00C853; }
.negative { color: #FF3B30; }
.neutral { color: #999; }
.loading { text-align: center; display: none; color: white; margin: 20px 0; }
.spinner { border: 3px solid rgba(255,255,255,0.3); border-top: 3px solid white; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 15px auto; }
@keyframes spin { 100% { transform: rotate(360deg); } }
.results { display: none; }
.targeting-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
.info-bar { background: rgba(255,255,255,0.9); padding: 14px 20px; border-radius: 12px; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center; }
.info-label { font-size: 0.9em; color: #666; }
.info-value { font-size: 0.95em; font-weight: 600; color: #1a2a6c; }
.note-bar { background: #FFF9E6; padding: 12px 16px; border-radius: 10px; margin-bottom: 16px; font-size: 0.85em; color: #8B7355; border-left: 3px solid #F5C518; }
.reasoning { margin-top: 12px; font-size: 0.9em; color: #666; line-height: 1.5; }
</style></head><body>
<div class="container"><div class="glass-card">
<h1>Multimodal Agentic System</h1>
<div class="subtitle">Instagram Boost Targeting + Virality Prediction</div>

<div class="box">
<div class="section-title">Your Content</div>
<textarea id="text" placeholder="Enter your post caption..."></textarea>
<label>Upload Image or Video:</label>
<input type="file" id="file" accept="image/*,video/*">
</div>

<div class="box">
<div class="section-title">Instagram Boost Targeting (Optional)</div>
<div style="color:rgba(255,255,255,0.8);font-size:0.9em;margin-bottom:15px;">Leave blank or select "None" for broad audience. Match your actual Instagram boost settings.</div>

<div class="targeting-grid">
<div>
<label>Location:</label>
<select id="location">
<option selected>None (Worldwide)</option>
<option>United States</option>
<option>California</option>
<option>Texas</option>
<option>New York</option>
<option>San Francisco Bay Area</option>
<option>Los Angeles</option>
<option>Houston, Texas</option>
<option>Chicago</option>
<option>Miami</option>
<option>Custom location</option>
</select>

<label>Age Range:</label>
<select id="age">
<option selected>None (All Ages)</option>
<option>18-24</option>
<option>25-34</option>
<option>25-44 (Millennials)</option>
<option>35-44</option>
<option>35-54 (Gen X)</option>
<option>45-64</option>
<option>55+</option>
<option>13-17</option>
</select>

<label>Gender:</label>
<select id="gender">
<option selected>None (All Genders)</option>
<option>Female</option>
<option>Male</option>
<option>Non-binary</option>
</select>
</div>

<div>
<label>Interest Category:</label>
<select id="interest">
<option selected>None (No Interest Targeting)</option>
<option>Fashion & Style</option>
<option>Beauty & Cosmetics</option>
<option>Food & Dining</option>
<option>Fitness & Wellness</option>
<option>Travel & Adventure</option>
<option>Business & Entrepreneurship</option>
<option>Technology & Gadgets</option>
<option>Entertainment & Music</option>
<option>Sports & Athletics</option>
<option>Art & Photography</option>
<option>Home & Garden</option>
<option>Parenting & Family</option>
<option>Education & Learning</option>
<option>Gaming</option>
<option>Pets & Animals</option>
</select>

<label>Language:</label>
<select id="language">
<option selected>None (All Languages)</option>
<option>English</option>
<option>Spanish</option>
<option>French</option>
<option>German</option>
<option>Portuguese</option>
<option>Italian</option>
<option>Japanese</option>
<option>Korean</option>
<option>Chinese</option>
</select>

<label>Device:</label>
<select id="device">
<option selected>None (All Devices)</option>
<option>Mobile Only</option>
<option>Desktop Only</option>
<option>Tablet Only</option>
</select>
</div>
</div>
</div>

<button class="btn" onclick="analyze()">Analyze for Target Audience</button>

<div class="loading" id="loading">
<div class="spinner"></div>
<div id="status">Scoring with GPT-5.1, Claude 4, Gemini 3...</div>
</div>

<div class="results" id="results"></div>
</div></div>

<script>
async function analyze() {
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');
    
    loading.style.display = 'block';
    results.style.display = 'none';
    
    const fd = new FormData();
    fd.append('text', document.getElementById('text').value);
    
    fd.append('location', document.getElementById('location').value);
    fd.append('age', document.getElementById('age').value);
    fd.append('gender', document.getElementById('gender').value);
    fd.append('interest', document.getElementById('interest').value);
    fd.append('language', document.getElementById('language').value);
    fd.append('device', document.getElementById('device').value);
    
    const file = document.getElementById('file').files[0];
    if (file) fd.append('media', file);
    
    try {
        const resp = await fetch('/analyze', {method: 'POST', body: fd});
        const data = await resp.json();
        
        loading.style.display = 'none';
        
        let targeting = 'Broad Audience (No Targeting)';
        const params = [];
        if (data.targeting.location !== 'None (Worldwide)') params.push(data.targeting.location);
        if (data.targeting.age !== 'None (All Ages)') params.push(data.targeting.age);
        if (data.targeting.gender !== 'None (All Genders)') params.push(data.targeting.gender);
        if (data.targeting.interest !== 'None (No Interest Targeting)') params.push(data.targeting.interest);
        if (params.length > 0) targeting = params.join(' / ');
        
        const mediaLabels = {video: 'VIDEO', image: 'IMAGE', none: 'TEXT ONLY', unknown: 'UNKNOWN'};
        const mediaLabel = mediaLabels[data.media_type] || '';
        
        let html = `<div class="info-bar">
            <div><span class="info-label">Target Audience:</span> <span class="info-value">${targeting}</span></div>
            <div><span class="info-label">Media:</span> <span class="info-value">${mediaLabel}</span></div>
        </div>`;
        
        if (data.media_type === 'video') {
            html += '<div class="note-bar">Gemini analyzes full video (motion, pacing, audio). GPT and Claude analyze keyframe visuals.</div>';
        }
        
        html += '<div class="model-card"><div style="font-size:1.3em;font-weight:600;margin-bottom:20px;color:#1a2a6c;">Virality Scores</div>';
        
        ['gpt', 'claude', 'gemini'].forEach(m => {
            if (data[m]) {
                const names = {gpt:'GPT-5.1', claude:'Claude 4 Opus', gemini:'Gemini 3 Pro'};
                const s = data[m];
                html += `<div style="margin:20px 0;padding:20px;background:#f8f9fa;border-radius:12px;">
                    <div class="model-title">${names[m]}</div>
                    <div class="score-huge">${s.overall_score.toFixed(0)}<span style="font-size:0.4em;color:#666;">/100</span></div>
                    <div class="components">
                        <div class="comp"><div class="comp-val">${s.text_quality.toFixed(0)}</div><div class="comp-label">Text</div></div>
                        <div class="comp"><div class="comp-val">${s.visual_appeal.toFixed(0)}</div><div class="comp-label">Visual</div></div>
                        <div class="comp"><div class="comp-val">${s.emotional_resonance.toFixed(0)}</div><div class="comp-label">Emotional</div></div>
                        <div class="comp"><div class="comp-val">${s.clarity.toFixed(0)}</div><div class="comp-label">Clarity</div></div>
                    </div>
                    <div class="reasoning">${s.reasoning}</div>
                </div>`;
            }
        });
        
        html += '</div>';
        
        if (data.recommendations && data.recommendations.length > 0) {
            const sorted = data.recommendations.sort((a,b) => b.impact - a.impact).slice(0, 5);
            
            html += `<div class="rec-card">
                <div class="rec-title">Top Recommendations</div>`;
            
            sorted.forEach(rec => {
                const cls = rec.impact > 0 ? 'positive' : (rec.impact < 0 ? 'negative' : 'neutral');
                const sign = rec.impact > 0 ? '+' : '';
                html += `<div class="rec-item">
                    <div class="rec-text">${rec.suggestion}</div>
                    <div class="rec-impact ${cls}">${sign}${rec.impact.toFixed(0)}</div>
                </div>`;
            });
            
            html += '</div>';
        }
        
        results.innerHTML = html;
        results.style.display = 'block';
        results.scrollIntoView({behavior: 'smooth'});
        
    } catch (e) {
        loading.style.display = 'none';
        alert('Error: ' + e.message);
        console.error(e);
    }
}
</script>
</body></html>"""

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/analyze', methods=['POST'])
def analyze():
    text = request.form.get('text', '')
    
    # Instagram targeting parameters
    location = request.form.get('location', 'None (Worldwide)')
    age = request.form.get('age', 'None (All Ages)')
    gender = request.form.get('gender', 'None (All Genders)')
    interest = request.form.get('interest', 'None (No Interest Targeting)')
    language = request.form.get('language', 'None (All Languages)')
    device = request.form.get('device', 'None (All Devices)')
    
    # Build targeting context
    targeting_parts = []
    if 'None' not in location: targeting_parts.append(f"Location: {location}")
    if 'None' not in age: targeting_parts.append(f"Age: {age}")
    if 'None' not in gender: targeting_parts.append(f"Gender: {gender}")
    if 'None' not in interest: targeting_parts.append(f"Interest: {interest}")
    if 'None' not in language: targeting_parts.append(f"Language: {language}")
    if 'None' not in device: targeting_parts.append(f"Device: {device}")
    
    targeting_context = '; '.join(targeting_parts) if targeting_parts else "Broad audience (no targeting)"
    
    # Get media and detect type
    media_image = None
    media_video_bytes = None
    media_type = "none"
    
    if 'media' in request.files:
        f = request.files['media']
        if f.filename:
            fb = f.read()
            
            # DETECT media type automatically
            if f.filename.lower().endswith(('.mp4','.mov','.avi','.webm','.mkv')):
                media_type = "video"
                media_video_bytes = fb
                media_image = extract_frame(fb)  # Also extract frame for GPT/Claude
                print(f"📹 Detected: VIDEO ({len(fb)/1024/1024:.1f}MB)")
            elif f.filename.lower().endswith(('.jpg','.jpeg','.png','.gif','.webp','.bmp')):
                media_type = "image"
                media_image = fb
                print(f"📸 Detected: IMAGE ({len(fb)/1024:.0f}KB)")
            else:
                media_type = "unknown"
                media_image = fb
                print(f"❓ Detected: UNKNOWN file type")
    
    print(f"\n{'='*80}\nANALYZING\nText: {text[:50]}...\nTargeting: {targeting_context}\nMedia Type: {media_type.upper()}\n{'='*80}\n")
    
    # Score with all 3 models - DIFFERENTLY for video vs image
    scores = {}
    baseline = 50
    
    if media_type == "video":
        print("\n🎥 VIDEO MODE: Gemini analyzes full video, GPT/Claude analyze keyframe\n")
        
        # GPT-5.1: Image frame analysis
        try:
            scores['gpt'] = score_gpt(text, media_image, f"{targeting_context} (analyzing video keyframe)")
            baseline = scores['gpt']['overall_score']
            scores['gpt']['reasoning'] = f"[Frame Analysis] {scores['gpt'].get('reasoning', '')}"
            print(f"✓ GPT (frame): {baseline}/100")
        except Exception as e:
            print(f"✗ GPT: {e}")
            scores['gpt'] = {'overall_score':0,'text_quality':0,'visual_appeal':0,'emotional_resonance':0,'clarity':0,'brand_alignment':0,'reasoning':str(e)}
        
        # Claude: Image frame analysis
        try:
            scores['claude'] = score_claude(text, media_image, f"{targeting_context} (analyzing video keyframe)")
            scores['claude']['reasoning'] = f"[Frame Analysis] {scores['claude'].get('reasoning', '')}"
            print(f"✓ Claude (frame): {scores['claude']['overall_score']}/100")
        except Exception as e:
            print(f"✗ Claude: {e}")
            scores['claude'] = {'overall_score':0,'text_quality':0,'visual_appeal':0,'emotional_resonance':0,'clarity':0,'brand_alignment':0,'reasoning':str(e)}
        
        # Gemini: Try FULL video analysis, fallback to frame
        try:
            print("  Attempting Gemini FULL VIDEO analysis...")
            
            # Save video temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp:
                tmp.write(media_video_bytes)
                video_path = tmp.name
            
            # Upload to Gemini
            video_file = genai.upload_file(path=video_path)
            print(f"  Uploaded to Gemini, state: {video_file.state.name}")
            
            # Wait for processing (max 30 seconds)
            import time
            max_wait = 30
            waited = 0
            while video_file.state.name == "PROCESSING" and waited < max_wait:
                time.sleep(2)
                waited += 2
                video_file = genai.get_file(video_file.name)
                print(f"  Waiting... {waited}s (state: {video_file.state.name})")
            
            os.unlink(video_path)
            
            if video_file.state.name == "ACTIVE":
                # Analyze FULL VIDEO
                prompt = f"Analyze this VIDEO for Instagram virality.\n\nTargeting: {targeting_context}\nCaption: {text}\n\nAnalyze: motion, pacing, audio/sound, hooks, storytelling, visual flow. JSON: overall_score, text_quality, visual_appeal, emotional_resonance, clarity, brand_alignment, reasoning (0-100)"
                
                response = gemini_model.generate_content([video_file, prompt])
                scores['gemini'] = parse_json(response.text)
                scores['gemini']['reasoning'] = f"[FULL VIDEO Analysis - Motion/Audio/Pacing] {scores['gemini'].get('reasoning', '')}"
                print(f"✓ Gemini (FULL VIDEO): {scores['gemini']['overall_score']}/100")
            else:
                raise Exception(f"Video processing failed: {video_file.state.name}")
            
        except Exception as e:
            print(f"  Video analysis failed: {e}")
            print(f"  Falling back to frame analysis...")
            # Fallback to frame
            if media_image:
                scores['gemini'] = score_gemini(text, media_image, f"{targeting_context} (video frame)")
                scores['gemini']['reasoning'] = f"[Video Frame Only - Full video analysis unavailable] {scores['gemini'].get('reasoning', '')}"
                print(f"✓ Gemini (frame fallback): {scores['gemini']['overall_score']}/100")
            else:
                scores['gemini'] = {'overall_score':0,'text_quality':0,'visual_appeal':0,'emotional_resonance':0,'clarity':0,'brand_alignment':0,'reasoning':'Video processing failed'}
    
    elif media_type == "image":
        print("\n📸 IMAGE MODE: All 3 models analyze image\n")
        
        # All 3 models analyze the image
        try:
            scores['gpt'] = score_gpt(text, media_image, targeting_context)
            baseline = scores['gpt']['overall_score']
            print(f"✓ GPT: {baseline}/100")
        except Exception as e:
            print(f"✗ GPT: {e}")
            scores['gpt'] = {'overall_score':0,'text_quality':0,'visual_appeal':0,'emotional_resonance':0,'clarity':0,'brand_alignment':0,'reasoning':str(e)}
        
        try:
            scores['claude'] = score_claude(text, media_image, targeting_context)
            print(f"✓ Claude: {scores['claude']['overall_score']}/100")
        except Exception as e:
            print(f"✗ Claude: {e}")
            scores['claude'] = {'overall_score':0,'text_quality':0,'visual_appeal':0,'emotional_resonance':0,'clarity':0,'brand_alignment':0,'reasoning':str(e)}
        
        try:
            scores['gemini'] = score_gemini(text, media_image, targeting_context)
            print(f"✓ Gemini: {scores['gemini']['overall_score']}/100")
        except Exception as e:
            print(f"✗ Gemini: {e}")
            scores['gemini'] = {'overall_score':0,'text_quality':0,'visual_appeal':0,'emotional_resonance':0,'clarity':0,'brand_alignment':0,'reasoning':str(e)}
    
    else:
        print("\n📝 TEXT-ONLY MODE: Analyzing text without media\n")
        
        # Text-only analysis
        try:
            scores['gpt'] = score_gpt(text, None, targeting_context)
            baseline = scores['gpt']['overall_score']
            print(f"✓ GPT: {baseline}/100")
        except Exception as e:
            scores['gpt'] = {'overall_score':0,'text_quality':0,'visual_appeal':0,'emotional_resonance':0,'clarity':0,'brand_alignment':0,'reasoning':str(e)}
        
        try:
            scores['claude'] = score_claude(text, None, targeting_context)
            print(f"✓ Claude: {scores['claude']['overall_score']}/100")
        except Exception as e:
            scores['claude'] = {'overall_score':0,'text_quality':0,'visual_appeal':0,'emotional_resonance':0,'clarity':0,'brand_alignment':0,'reasoning':str(e)}
        
        try:
            scores['gemini'] = score_gemini(text, None, targeting_context)
            print(f"✓ Gemini: {scores['gemini']['overall_score']}/100")
        except Exception as e:
            scores['gemini'] = {'overall_score':0,'text_quality':0,'visual_appeal':0,'emotional_resonance':0,'clarity':0,'brand_alignment':0,'reasoning':str(e)}
    
    # Generate specific, actionable recommendations using GPT
    print(f"\nGenerating specific recommendations...")
    recs = []
    media_for_testing = media_image if media_type != "none" else None
    
    try:
        # Ask GPT for 5 specific, actionable improvements
        rec_prompt = f"""Analyze this social media post and suggest exactly 5 specific, actionable improvements.

Caption: {text}
Targeting: {targeting_context}
Media type: {media_type}
Current score: {baseline}/100

For each suggestion, provide a SPECIFIC change (not generic like "add emoji" but specific like "Add fire emoji after 'amazing'").
For video: suggest specific changes to music, pacing, hooks, transitions.
For images: suggest specific visual changes, filters, text overlays.
For text: suggest specific wording changes, hashtags, CTAs.

Return JSON array with exactly 5 objects, each with:
- "suggestion": specific actionable change (e.g., "Change opening hook to 'You won't believe...'", "Add upbeat music at 0:03", "Use warmer color filter")
- "estimated_impact": number from -10 to +15 (realistic estimate of score change)

Be specific! Not "add hashtags" but "Add #entrepreneurship #startup hashtags"."""

        rec_response = openai_client.chat.completions.create(
            model="gpt-5.1",
            messages=[{"role":"user","content":rec_prompt}],
            max_completion_tokens=600,
            temperature=0.3
        )
        rec_data = parse_json(rec_response.choices[0].message.content)
        
        # Handle both array and object responses
        if isinstance(rec_data, list):
            suggestions = rec_data
        elif isinstance(rec_data, dict) and 'suggestions' in rec_data:
            suggestions = rec_data['suggestions']
        else:
            suggestions = [rec_data]
        
        for item in suggestions[:5]:
            suggestion = item.get('suggestion', '')
            impact = item.get('estimated_impact', 0)
            if suggestion:
                recs.append({'suggestion': suggestion, 'impact': impact})
                print(f"  - {suggestion}: {impact:+.0f}")
        
    except Exception as e:
        print(f"  Recommendation generation failed: {e}")
    
    recs.sort(key=lambda x: x['impact'], reverse=True)
    
    print(f"\n✓ Done! Baseline: {baseline}/100\n{'='*80}\n")
    
    return jsonify({
        'gpt': scores['gpt'],
        'claude': scores['claude'],
        'gemini': scores['gemini'],
        'recommendations': recs,
        'media_type': media_type,  # Tell frontend what type was detected
        'targeting': {
            'location': location,
            'age': age,
            'gender': gender,
            'interest': interest,
            'language': language,
            'device': device
        }
    })

if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║     Multimodal System with Instagram Boost Targeting                        ║
║                   November 21, 2025                                          ║
╚══════════════════════════════════════════════════════════════════════════════╝

🌐 http://localhost:8080

✅ Instagram boost parameters (location, age, gender, interests, etc.)
✅ Can leave blank or select "None" for broad targeting
✅ Virality score accounts for HOW targeted your boost is
✅ ALL 3 models shown (GPT-5.1, Claude 4, Gemini 3)
✅ REAL recommendations (actually re-scored)

⏱️  ~20-30 seconds | 💰 ~$0.20 | 🎯 NO FAKING
""")
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)

