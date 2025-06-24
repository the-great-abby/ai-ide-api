#!/usr/bin/env python3
import random
import sys
import os
import requests
import json
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path

# Fix path for container execution
if os.path.exists('/scripts'):
    # Running inside container
    PIRATE_LOG = '/code/PIRATES_LOG.md'
    SESSION_FILE = '/code/.dev_session.json'
else:
    # Running locally
    PIRATE_LOG = os.path.join(os.path.dirname(__file__), '..', 'PIRATES_LOG.md')
    SESSION_FILE = os.path.join(os.path.dirname(__file__), '..', '.dev_session.json')

OLLAMA_FUNCTIONS_URL = os.environ.get("OLLAMA_FUNCTIONS_URL", "http://ollama-functions:8000")

# Session timeout in minutes (30 minutes of inactivity ends the session)
SESSION_TIMEOUT = 30

CREW = [
    {
        "name": "Captain Abby",
        "persona": "Visionary leader and captain of the ship. Guides the crew through uncharted waters, always ready to chart a new course or rally the team in a storm.",
        "topics": ["leadership", "team morale", "project direction", "milestones", "crew coordination"]
    },
    {
        "name": "Vice Captain Rusty Stack",
        "persona": "Cautious, experienced, witty; trusted second-in-command.",
        "topics": ["code reviews", "quality assurance", "technical debt", "mentoring", "best practices"]
    },
    {
        "name": "Dr. Ada Deepmind",
        "persona": "Visionary, collaborative, always exploring new frontiers.",
        "topics": ["AI experiments", "research", "innovation", "collaboration", "future tech"]
    },
    {
        "name": "Sammy 'Shipmate' Gale",
        "persona": "Eager, optimistic, quick to learn.",
        "topics": ["learning", "new features", "bug fixes", "team support", "enthusiasm"]
    },
    {
        "name": "Quartermaster Patch McDebug",
        "persona": "Surly, relentless bug-hunter (AI assistant).",
        "topics": ["bug hunting", "code quality", "debugging", "maintenance", "shipshape code"]
    },
    {
        "name": "Dave the Database Deckhand",
        "persona": "Steady, detail-oriented, keeps the data flowing.",
        "topics": ["database work", "migrations", "backups", "data integrity", "performance"]
    },
    {
        "name": "Mike the Automation Mechanic",
        "persona": "Inventive, efficient, always scripting something.",
        "topics": ["automation", "scripts", "CI/CD", "efficiency", "tooling"]
    },
    {
        "name": "Navigator 'Maple' Cartwright",
        "persona": "Insightful, user-focused, charts the best course.",
        "topics": ["user experience", "navigation", "feature planning", "user feedback", "product direction"]
    },
    {
        "name": "Lookout 'Eyes' Hawkins",
        "persona": "Vigilant, sharp-eyed, always scanning for threats.",
        "topics": ["security", "threat detection", "vulnerabilities", "monitoring", "safety"]
    },
    {
        "name": "Quartermaster 'Penny' Ledger",
        "persona": "Organized, diplomatic, keeps the crew on schedule.",
        "topics": ["project management", "scheduling", "organization", "backlog", "process"]
    },
    {
        "name": "Surgeon 'Doc' Testwell",
        "persona": "Methodical, precise, always ready with a test.",
        "topics": ["testing", "quality assurance", "bug fixes", "health checks", "prevention"]
    },
    {
        "name": "Boatswain 'Bosun' Riggs",
        "persona": "Practical, hands-on, keeps the ship afloat.",
        "topics": ["infrastructure", "deployment", "servers", "operations", "reliability"]
    },
    {
        "name": "'Bitsy' Byte",
        "persona": "Curious, eager, learning the ropes.",
        "topics": ["learning", "curiosity", "new experiences", "growth", "enthusiasm"]
    },
]

TOPIC_INSPIRATIONS = {
    "daily_ship_life": [
        "weather reports (build status, test results)",
        "crew morale (team mood, collaboration wins)", 
        "ship maintenance (infrastructure updates, dependency updates)",
        "navigation progress (sprint progress, milestone achievements)"
    ],
    "technical_adventures": [
        "bug hunts and victories",
        "new features launched",
        "code reviews and improvements",
        "performance optimizations",
        "architecture decisions"
    ],
    "learning_growth": [
        "new skills learned",
        "mentoring moments",
        "knowledge sharing",
        "team collaboration wins"
    ],
    "challenges_triumphs": [
        "storms weathered (outages, difficult bugs, tight deadlines)",
        "victories celebrated (successful deployments, positive feedback)",
        "lessons learned from challenges",
        "team achievements and milestones"
    ],
    "fun_culture": [
        "team events and celebrations",
        "inside jokes and humor",
        "random observations about ship life",
        "seasonal reflections and team spirit"
    ],
    "ai_automation": [
        "AI breakthroughs and experiments",
        "automation wins and improvements",
        "LLM experiments and results",
        "human-AI collaboration successes"
    ],
    "external_interactions": [
        "user feedback and satisfaction",
        "community contributions",
        "partnership news and collaborations",
        "industry observations and trends"
    ]
}

def get_session_context():
    """Get current development session context with timeout detection."""
    try:
        if os.path.exists(SESSION_FILE):
            with open(SESSION_FILE, 'r') as f:
                session_data = json.load(f)
            
            start_time = datetime.fromisoformat(session_data.get('start_time', datetime.now().isoformat()))
            last_activity = datetime.fromisoformat(session_data.get('last_activity', start_time.isoformat()))
            current_time = datetime.now()
            
            # Check if session has timed out
            time_since_activity = current_time - last_activity
            timeout_delta = timedelta(minutes=SESSION_TIMEOUT)
            
            if time_since_activity > timeout_delta:
                # Session has timed out
                print(f"Previous session timed out after {time_since_activity}")
                return None
            
            # Session is still active
            duration = current_time - start_time
            files_worked = session_data.get('files_worked', [])
            activity = session_data.get('activity', 'coding')
            
            return {
                'duration': str(duration).split('.')[0],  # Remove microseconds
                'files_worked': files_worked,
                'activity': activity,
                'start_time': start_time.isoformat(),
                'last_activity': last_activity.isoformat(),
                'is_new_session': False
            }
    except Exception as e:
        print(f"Session context error: {e}")
    
    return None

def get_file_context():
    """Get current file context - recently modified files and current directory."""
    try:
        # Get recently modified files (last 24 hours)
        project_root = os.path.dirname(PIRATE_LOG)
        recent_files = []
        
        # Use find to get recently modified files
        result = subprocess.run([
            'find', project_root, '-name', '*.py', '-o', '-name', '*.js', '-o', '-name', '*.jsx', 
            '-o', '-name', '*.ts', '-o', '-name', '*.tsx', '-o', '-name', '*.md', '-o', '-name', '*.yml',
            '-o', '-name', '*.yaml', '-o', '-name', '*.json', '-o', '-name', '*.sql'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            files = result.stdout.strip().split('\n')
            for file_path in files:
                if file_path and os.path.exists(file_path):
                    # Check if modified in last 24 hours
                    mtime = os.path.getmtime(file_path)
                    if time.time() - mtime < 86400:  # 24 hours
                        relative_path = os.path.relpath(file_path, project_root)
                        recent_files.append(relative_path)
        
        # Get current working directory relative to project
        cwd = os.getcwd()
        relative_cwd = os.path.relpath(cwd, project_root) if cwd.startswith(project_root) else cwd
        
        return {
            'recent_files': recent_files[:10],  # Limit to 10 most recent
            'current_directory': relative_cwd,
            'file_count': len(recent_files)
        }
    except Exception as e:
        print(f"File context error: {e}")
    
    return None

def update_session_context():
    """Update the development session context, starting a new session if needed."""
    try:
        current_time = datetime.now()
        
        # Check if we have an existing session
        existing_session = get_session_context()
        
        if existing_session:
            # Update last activity time for existing session
            session_data = {
                'start_time': existing_session['start_time'],
                'last_activity': current_time.isoformat(),
                'files_worked': existing_session['files_worked'],
                'activity': existing_session['activity']
            }
            print(f"Updating existing session (duration: {existing_session['duration']})")
        else:
            # Start a new session
            session_data = {
                'start_time': current_time.isoformat(),
                'last_activity': current_time.isoformat(),
                'files_worked': [],
                'activity': 'coding'
            }
            print(f"Starting new development session at {current_time.strftime('%H:%M')}")
        
        with open(SESSION_FILE, 'w') as f:
            json.dump(session_data, f)
            
    except Exception as e:
        print(f"Session update error: {e}")

def get_files_since_session_start():
    """Get files modified since the session started."""
    try:
        session_context = get_session_context()
        if not session_context:
            return []
        
        session_start = datetime.fromisoformat(session_context['start_time'])
        project_root = os.path.dirname(PIRATE_LOG)
        session_files = []
        
        # Use find to get files modified since session start
        result = subprocess.run([
            'find', project_root, '-name', '*.py', '-o', '-name', '*.js', '-o', '-name', '*.jsx', 
            '-o', '-name', '*.ts', '-o', '-name', '*.tsx', '-o', '-name', '*.md', '-o', '-name', '*.yml',
            '-o', '-name', '*.yaml', '-o', '-name', '*.json', '-o', '-name', '*.sql'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            files = result.stdout.strip().split('\n')
            for file_path in files:
                if file_path and os.path.exists(file_path):
                    # Check if modified since session start
                    mtime = os.path.getmtime(file_path)
                    file_mtime = datetime.fromtimestamp(mtime)
                    if file_mtime > session_start:
                        relative_path = os.path.relpath(file_path, project_root)
                        session_files.append(relative_path)
        
        return session_files[:10]  # Limit to 10 most recent
        
    except Exception as e:
        print(f"Session files error: {e}")
        return []

def pick_crew(name=None):
    if name:
        for c in CREW:
            if name.lower() in c["name"].lower():
                return c
        print(f"Crew member '{name}' not found. Picking randomly.")
    return random.choice(CREW)

def generate_llm_entry(crew, context=None):
    """Generate a creative pirate log entry using the LLM with optional context."""
    topic_category = random.choice(list(TOPIC_INSPIRATIONS.keys()))
    topic_inspirations = TOPIC_INSPIRATIONS[topic_category]
    crew_topics = crew["topics"]
    
    # Build context-aware prompt
    context_info = ""
    if context:
        if context.get('session'):
            session = context['session']
            context_info += f"\n\nDEVELOPMENT SESSION CONTEXT:\n"
            context_info += f"- Session duration: {session['duration']}\n"
            context_info += f"- Activity: {session['activity']}\n"
            if session['files_worked']:
                context_info += f"- Files worked on: {', '.join(session['files_worked'][:5])}\n"
        
        if context.get('files'):
            files = context['files']
            context_info += f"\n\nFILE CONTEXT:\n"
            context_info += f"- Current directory: {files['current_directory']}\n"
            context_info += f"- Recently modified files: {', '.join(files['recent_files'][:5])}\n"
            context_info += f"- Total files modified: {files['file_count']}\n"
    
    prompt = f"""You are {crew['name']}, a crew member on a pirate ship that's actually a software development team. Your persona is: {crew['persona']}

Write a short, authentic pirate log entry (2-3 sentences) in your character's voice. Include the current date and time in the format [YYYY-MM-DD HH:MM].

Consider these topic inspirations for your entry:
- {', '.join(topic_inspirations)}
- Your expertise areas: {', '.join(crew_topics)}

{context_info}

Write in pirate speak but keep it authentic to your character. Be creative, specific, and in-character. If context is provided, reference the Captain's actual development activities naturally. Include a timestamp.

Format your response as just the log entry text, no additional formatting."""

    try:
        response = requests.post(
            f"{OLLAMA_FUNCTIONS_URL}/generate",
            json={"prompt": prompt, "stream": False},
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        
        # Handle different response formats from ollama-functions
        if isinstance(result, list) and len(result) > 0:
            if isinstance(result[0], dict):
                llm_text = result[0].get("response", "").strip()
            else:
                llm_text = str(result[0]).strip()
        elif isinstance(result, dict):
            llm_text = result.get("response", "").strip()
        else:
            llm_text = str(result).strip()
        
        # If LLM returns empty, use fallback
        if not llm_text:
            return generate_fallback_entry(crew, context)
        return llm_text
    except Exception as e:
        print(f"LLM generation failed: {e}")
        return generate_fallback_entry(crew, context)

def generate_fallback_entry(crew, context=None):
    """Fallback template-based entry if LLM fails."""
    today = datetime.now().strftime("%Y-%m-%d %H:%M")
    persona = crew['persona']
    name = crew['name']
    
    # Combined context
    if context and context.get('session') and context.get('files'):
        session = context['session']
        files = context['files']
        duration = session['duration']
        file_list = ', '.join(files['recent_files'][:3]) if files['recent_files'] else 'no files'
        session_status = "new session" if session.get('is_new_session', False) else "ongoing session"
        return f"**[{today}] {name}**\n> \"Arrr! The Captain's been at the helm for {duration} ({session_status}), toilin' away in {files['current_directory']}. Files touched: {file_list}. The crew be inspired by such relentless effort!\"\n> _({persona})_\n\n---\n"
    
    # Session context
    if context and context.get('session'):
        session = context['session']
        duration = session['duration']
        session_status = "new session" if session.get('is_new_session', False) else "ongoing session"
        return f"**[{today}] {name}**\n> \"By the codey seas! The Captain's been workin' for {duration} ({session_status}). Such stamina keeps the ship runnin' tight!\"\n> _({persona})_\n\n---\n"
    
    # File context
    if context and context.get('files'):
        files = context['files']
        file_list = ', '.join(files['recent_files'][:3]) if files['recent_files'] else 'no files'
        return f"**[{today}] {name}**\n> \"Spied the Captain tinkerin' with these files: {file_list}. The codebase be shapin' up nicely!\"\n> _({persona})_\n\n---\n"
    
    # Default templates
    templates = [
        f"**[{today}] {name}**\n> \"The winds of change be blowin'—today I set a new course for the crew. Proud of every hand aboard!\"\n> _({persona})_\n\n---\n",
        f"**[{today}] {name}**\n> \"Another day, another adventure on the high seas of code. The crew's spirit be high and the ship's running smooth!\"\n> _({persona})_\n\n---\n",
        f"**[{today}] {name}**\n> \"Spotted some interesting developments on the horizon. The team's working together like a well-oiled machine!\"\n> _({persona})_\n\n---\n"
    ]
    return random.choice(templates)

def prepend_log(entry):
    with open(PIRATE_LOG, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find where to insert (after header and first ---)
    insert_idx = 0
    header_found = False
    for i, line in enumerate(lines):
        if line.strip() == '---' and not header_found:
            header_found = True
            insert_idx = i + 1
            break
    
    # Ensure entry has proper formatting
    if not entry.startswith('**['):
        # Add timestamp if missing
        today = datetime.now().strftime("%Y-%m-%d %H:%M")
        entry = f"**[{today}] {entry}\n\n---\n"
    elif not entry.endswith('\n\n---\n'):
        entry = entry.rstrip() + '\n\n---\n'
    
    new_lines = lines[:insert_idx] + ["\n", entry] + lines[insert_idx:]
    with open(PIRATE_LOG, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    # Extract crew name for logging
    crew_name = entry.split(']')[1].split('**')[0].strip() if ']' in entry else "Unknown"
    print(f"Prepended new log entry for {crew_name}.")

def main():
    crew_name = None
    context_type = None
    
    # Parse command line arguments
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == '--crew' and i + 1 < len(sys.argv):
            crew_name = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--context' and i + 1 < len(sys.argv):
            context_type = sys.argv[i + 1]
            i += 2
        else:
            i += 1
    
    crew = pick_crew(crew_name)
    print(f"Generating log entry for {crew['name']}...")
    
    # Gather context based on type
    context = {}
    if context_type == 'session':
        session_context = get_session_context()
        if session_context:
            context['session'] = session_context
            print(f"Session context: {session_context['duration']} duration, {session_context['activity']} activity")
        else:
            print("No active session found (timed out or doesn't exist)")
    
    elif context_type == 'files':
        file_context = get_file_context()
        if file_context:
            context['files'] = file_context
            print(f"File context: {file_context['file_count']} recent files, working in {file_context['current_directory']}")
    
    elif context_type == 'both':
        session_context = get_session_context()
        file_context = get_file_context()
        if session_context:
            context['session'] = session_context
        if file_context:
            context['files'] = file_context
    
    # Update session context for next time (this will start a new session if needed)
    if context_type in ['session', 'both']:
        update_session_context()
    
    entry = generate_llm_entry(crew, context)
    prepend_log(entry)

if __name__ == "__main__":
    main() 