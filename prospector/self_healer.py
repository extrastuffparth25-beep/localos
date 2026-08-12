"""
self_healer.py — AGI Auto-Patching Engine for LOCALOS.

If the system crashes, this agent acts as a Senior Software Engineer.
It reads the traceback, surgically replaces ONLY the broken lines of code using Gemini,
and pushes a hotfix to GitHub.
"""

import json
import logging
import os
import subprocess
import traceback
from pathlib import Path

try:
    import google.generativeai as genai
except ImportError:
    genai = None

log = logging.getLogger(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

if GEMINI_API_KEY and genai:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

def heal_codebase(error_msg: str, trace_str: str) -> bool:
    """Attempt to dynamically fix the source code and push a hotfix."""
    log.info("🤖 AGI Self-Healer Activated. Analyzing crash diagnostics...")
    
    if not model:
        log.error("Healer failed: Gemini API not configured.")
        return False
        
    try:
        # 1. Isolate the failing file and line from traceback
        lines = trace_str.strip().split('\n')
        target_file = ""
        target_line = 0
        
        # Traverse backwards to find the last file in our project
        for line in reversed(lines):
            if "File " in line and "localos/prospector/" in line:
                parts = line.split('"')
                if len(parts) >= 3:
                    file_path = parts[1]
                    line_part = parts[2].split("line ")
                    if len(line_part) > 1:
                        target_line = int(line_part[1].split(",")[0])
                        target_file = file_path
                        break
                        
        if not target_file or not os.path.exists(target_file):
            log.error("Healer could not isolate a local project file to fix.")
            return False
            
        log.info("Healer isolated fault to %s (Line %d)", target_file, target_line)
        
        # 2. Extract a surgical chunk of code around the error (context)
        with open(target_file, "r", encoding="utf-8") as f:
            code_lines = f.readlines()
            
        start_idx = max(0, target_line - 15)
        end_idx = min(len(code_lines), target_line + 15)
        code_chunk = "".join(code_lines[start_idx:end_idx])
        
        # 3. Consult Gemini for a surgical patch
        prompt = f"""
You are an elite Senior Python Engineer fixing a critical production crash in an automated system.
The system MUST NOT change its core business logic. You are only allowed to fix the exact bug.

Error Message: {error_msg}

Here is the exact chunk of code from the file where it crashed (around line {target_line}):
```python
{code_chunk}
```

Identify the broken lines and provide the EXACT target string to replace, and the EXACT replacement string.
The target string must match the source code perfectly so we can use string.replace().
Do NOT rewrite the whole file. Just fix the typo, missing import, or syntax error.

Return strictly JSON format:
{{
    "target_content": "exact lines to replace",
    "replacement_content": "the fixed lines"
}}
"""
        response = model.generate_content(prompt)
        raw_text = response.text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.startswith("```"):
            raw_text = raw_text[3:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
        patch = json.loads(raw_text.strip())
        
        target = patch.get("target_content", "")
        replacement = patch.get("replacement_content", "")
        
        if not target or target not in "".join(code_lines):
            log.error("Healer failed: Target string not found in source file.")
            return False
            
        # 4. Perform dynamic file surgery
        with open(target_file, "r", encoding="utf-8") as f:
            full_code = f.read()
            
        fixed_code = full_code.replace(target, replacement)
        
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(fixed_code)
            
        log.info("🩹 Surgery successful. Code patched on disk.")
        
        # 5. Push Hotfix to GitHub
        log.info("Pushing hotfix to repository...")
        subprocess.run(["git", "config", "--global", "user.name", "LOCALOS Healer Agent"], check=False)
        subprocess.run(["git", "config", "--global", "user.email", "healer@localos.ai"], check=False)
        subprocess.run(["git", "add", "."], check=False)
        subprocess.run(["git", "commit", "-m", f"🤖 Auto-Patch: Fixed {error_msg.split(':')[0]}"], check=False)
        subprocess.run(["git", "push"], check=False)
        
        log.info("✅ Hotfix deployed to cloud.")
        return True
        
    except Exception as e:
        log.error("Healer encountered a critical error during surgery: %s", str(e))
        return False
