#!/usr/bin/env python3
"""
Smart Study Assistant - Terminal Version
An improved educational tool that finds YouTube videos and generates quiz questions.
"""

import os
import re
import sys
import math
import time
import difflib
from typing import Optional, List, Dict, Any

from dotenv import load_dotenv
from colorama import init, Fore, Style
from groq import Groq
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

load_dotenv()
init(autoreset=True)


# Grade and Class Information
GRADE_LEVELS = {
    "1": {"name": "Class 1", "level": "beginner", "board": "Primary"},
    "2": {"name": "Class 2", "level": "beginner", "board": "Primary"},
    "3": {"name": "Class 3", "level": "beginner", "board": "Primary"},
    "4": {"name": "Class 4", "level": "beginner", "board": "Primary"},
    "5": {"name": "Class 5", "level": "beginner", "board": "Primary"},
    "6": {"name": "Class 6", "level": "middle", "board": "Secondary"},
    "7": {"name": "Class 7", "level": "middle", "board": "Secondary"},
    "8": {"name": "Class 8", "level": "middle", "board": "Secondary"},
    "9": {"name": "Class 9", "level": "intermediate", "board": "High School"},
    "10": {"name": "Class 10", "level": "intermediate", "board": "High School"},
    "11": {"name": "Class 11", "level": "advanced", "board": "Senior"},
    "12": {"name": "Class 12", "level": "advanced", "board": "Senior"},
    "jee": {"name": "JEE Main/Advanced", "level": "competitive", "board": "Competitive"},
    "neet": {"name": "NEET", "level": "competitive", "board": "Competitive"},
    "college": {"name": "College/University", "level": "advanced", "board": "Higher Education"},
}

BOARD_TYPES = {
    "cbse": "CBSE",
    "icse": "ICSE",
    "state": "State Board",
    "ncert": "NCERT",
}


class Config:
    """Configuration management for API keys and settings."""
    
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    YOUTUBE_API_KEY: str = os.getenv("YOUTUBE_API_KEY", "")
    
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    MAX_SEARCH_RESULTS: int = 15
    MIN_VIDEO_DURATION: int = 240
    MAX_VIDEO_DURATION: int = 900
    NUM_QUESTIONS: int = 6
    
    EDUCATIONAL_KEYWORDS: List[str] = [
        "explanation", "concept", "chapter", "lecture", 
        "introduction", "easy", "tutorial", "learn", "basics",
        "solved", "solution", "question", "example", "proof"
    ]
    
    @classmethod
    def validate(cls) -> bool:
        """Validate that required API keys are present."""
        if not cls.GROQ_API_KEY:
            print_error("Missing required API key: GROQ_API_KEY")
            print_info("Please set it in your .env file or environment variables.")
            print_info("Get your free key at: https://console.groq.com")
            return False
        return True
    
    @classmethod
    def has_youtube_key(cls) -> bool:
        """Check if YouTube API key is available."""
        return bool(cls.YOUTUBE_API_KEY)


def print_header(text: str) -> None:
    """Print a styled header."""
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*60}")
    print(f"{Fore.CYAN}{Style.BRIGHT}{text.center(60)}")
    print(f"{Fore.CYAN}{Style.BRIGHT}{'='*60}{Style.RESET_ALL}\n")


def print_success(text: str) -> None:
    """Print success message in green."""
    print(f"{Fore.GREEN}{Style.BRIGHT}[SUCCESS]{Style.RESET_ALL} {text}")


def print_error(text: str) -> None:
    """Print error message in red."""
    print(f"{Fore.RED}{Style.BRIGHT}[ERROR]{Style.RESET_ALL} {text}")


def print_warning(text: str) -> None:
    """Print warning message in yellow."""
    print(f"{Fore.YELLOW}{Style.BRIGHT}[WARNING]{Style.RESET_ALL} {text}")


def print_info(text: str) -> None:
    """Print info message in blue."""
    print(f"{Fore.BLUE}{Style.BRIGHT}[INFO]{Style.RESET_ALL} {text}")


def print_progress(text: str) -> None:
    """Print progress indicator."""
    print(f"{Fore.MAGENTA}>>> {text}...{Style.RESET_ALL}")


def display_menu(title: str, options: Dict[str, str], allow_custom: bool = False) -> str:
    """
    Display a menu and get user selection.
    
    Args:
        title: Menu title
        options: Dictionary of option_key: option_label
        allow_custom: Whether to allow custom input
        
    Returns:
        Selected option key
    """
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{title}{Style.RESET_ALL}")
    print(f"{Fore.WHITE}{'─'*50}{Style.RESET_ALL}")
    
    sorted_options = list(options.items())
    for idx, (key, label) in enumerate(sorted_options, 1):
        print(f"{Fore.YELLOW}{idx}{Style.RESET_ALL}) {label}")
    
    if allow_custom:
        print(f"{Fore.YELLOW}{len(sorted_options) + 1}{Style.RESET_ALL}) Custom input")
    
    while True:
        try:
            choice = input(f"\n{Fore.GREEN}Enter your choice (1-{len(sorted_options) + (1 if allow_custom else 0)}): {Style.RESET_ALL}").strip()
            choice_idx = int(choice) - 1
            
            if 0 <= choice_idx < len(sorted_options):
                return sorted_options[choice_idx][0]
            elif allow_custom and choice_idx == len(sorted_options):
                custom = input(f"{Fore.YELLOW}Enter custom value: {Style.RESET_ALL}").strip()
                if custom:
                    return custom
                print_warning("Input cannot be empty!")
            else:
                print_warning(f"Please enter a number between 1 and {len(sorted_options) + (1 if allow_custom else 0)}")
        except ValueError:
            print_warning("Please enter a valid number!")


def get_valid_input(prompt: str, min_length: int = 1, max_length: int = 200) -> str:
    """Get validated user input with minimum and maximum length requirement."""
    while True:
        user_input = input(f"{Fore.YELLOW}{prompt}{Style.RESET_ALL}").strip()
        if len(user_input) < min_length:
            print_warning(f"Please enter at least {min_length} character(s).")
        elif len(user_input) > max_length:
            print_warning(f"Please enter no more than {max_length} character(s).")
        else:
            return user_input


def select_class() -> Dict[str, Any]:
    """Display class selection menu and return selected grade info."""
    print_header("SELECT YOUR CLASS/GRADE")
    
    grade_options = {
        "beginner": "Class 1-5 (Primary)",
        "middle": "Class 6-8 (Middle School)",
        "intermediate": "Class 9-10 (High School)",
        "advanced": "Class 11-12 (Senior Secondary)",
        "competitive": "JEE/NEET (Competitive)",
        "college": "College/University",
    }
    
    selected_level = display_menu("Select Education Level:", grade_options)
    
    print(f"\n{Fore.GREEN}✓ Selected: {grade_options[selected_level]}{Style.RESET_ALL}\n")
    
    # Board selection
    board_options = {
        "cbse": "CBSE (Central Board)",
        "icse": "ICSE (Indian Certificate)",
        "state": "State Board",
        "ncert": "NCERT (General)",
    }
    
    selected_board = display_menu("Select Board/Curriculum:", board_options)
    
    print(f"\n{Fore.GREEN}✓ Selected: {board_options[selected_board]}{Style.RESET_ALL}\n")
    
    return {
        "level": selected_level,
        "board": selected_board,
        "display_name": grade_options[selected_level],
        "board_name": board_options[selected_board]
    }


def parse_duration_to_seconds(duration: str) -> Optional[int]:
    """
    Convert ISO 8601 duration format to seconds.
    Example: PT1H30M45S -> 5445 seconds
    """
    if not duration:
        return None
    
    match = re.search(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
    if not match:
        return None
    
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    
    return hours * 3600 + minutes * 60 + seconds


def format_duration(seconds: int) -> str:
    """Format seconds into human-readable duration."""
    minutes, secs = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def get_search_query(topic: str, grade_info: Dict[str, Any]) -> str:
    """Generate optimized search query based on topic and grade."""
    level = grade_info["level"]
    board = grade_info["board"]
    
    base_query = f"{topic}"
    
    if level == "competitive":
        query = f"{topic} JEE NEET solved problems detailed explanation"
    elif level == "advanced":
        query = f"{topic} class 11 12 {board} NCERT detailed explanation solved"
    elif level == "intermediate":
        query = f"{topic} class 9 10 {board} board exam solved examples"
    elif level == "middle":
        query = f"{topic} class 6 7 8 {board} explanation tutorial"
    elif level == "beginner":
        query = f"{topic} easy explanation for kids basics"
    else:
        query = f"{topic} {board} explanation tutorial"
    
    return query


def get_grade_level_keywords(grade_info: Dict[str, Any]) -> Dict[str, Any]:
    """Get grade-specific keywords for better filtering."""
    level = grade_info["level"]
    board = grade_info["board"]
    
    keyword_map = {
        "competitive": {
            "keywords": ["jee", "neet", "advanced", "competitive", "solved", "problem", "solution", "concept", "detailed"],
            "avoid": ["kids", "easy", "simple", "basic", "primary", "class 1", "class 2", "class 3"],
            "channels": ["vedantu", "unacademy", "physics wallah", "competishun"],
            "min_duration": 600,
            "max_duration": 1200
        },
        "advanced": {
            "keywords": ["class 11", "class 12", "ncert", "cbse", "icse", "board", "detailed", "solved", "important"],
            "avoid": ["kids", "baby", "kindergarten", "nursery", "class 1", "class 2"],
            "channels": ["vedantu", "byju", "unacademy", "ncert", "khan academy"],
            "min_duration": 480,
            "max_duration": 900
        },
        "intermediate": {
            "keywords": ["class 9", "class 10", "board exam", "ncert", "solved", "question", "important", "cbse"],
            "avoid": ["kids", "baby", "elementary", "class 1", "class 2", "class 3"],
            "channels": ["vedantu", "byju", "unacademy", "meritnation"],
            "min_duration": 360,
            "max_duration": 800
        },
        "middle": {
            "keywords": ["class 6", "class 7", "class 8", "middle school", "ncert", "explanation", "tutorial"],
            "avoid": ["kids", "baby", "elementary", "kindergarten", "class 1", "class 2"],
            "channels": ["vedantu", "byju", "unacademy", "khan academy"],
            "min_duration": 300,
            "max_duration": 720
        },
        "beginner": {
            "keywords": ["class 1", "class 2", "class 3", "class 4", "primary", "easy", "simple", "basics"],
            "avoid": ["advanced", "jee", "neet", "competitive", "complex"],
            "channels": ["kids learning", "education", "simple learning"],
            "min_duration": 180,
            "max_duration": 600
        }
    }
    
    board_keywords = {
        "cbse": ["cbse", "central board"],
        "icse": ["icse", "indian certificate"],
        "state": ["state board"],
        "ncert": ["ncert"]
    }
    
    base_config = keyword_map.get(level, keyword_map["beginner"])
    board_kw = board_keywords.get(board, [])
    
    return {
        "keywords": base_config["keywords"] + board_kw,
        "avoid": base_config["avoid"],
        "channels": base_config["channels"],
        "min_duration": base_config["min_duration"],
        "max_duration": base_config["max_duration"]
    }


def calculate_video_score(
    title: str, 
    description: str, 
    duration_secs: int, 
    view_count: int,
    topic: str,
    grade_info: Dict[str, Any],
    keywords_config: Dict[str, Any]
) -> float:
    """
    Calculate a relevance score for a video based on multiple factors.
    Higher score = more suitable for educational purposes and grade level.
    """
    score = 0.0
    title_lower = title.lower()
    desc_lower = description.lower()
    topic_lower = topic.lower()
    combined_text = title_lower + " " + desc_lower
    
    # Duration scoring with grade-specific ranges
    min_dur = keywords_config.get("min_duration", 240)
    max_dur = keywords_config.get("max_duration", 900)
    
    if min_dur <= duration_secs <= max_dur:
        score += 8.0
    elif min_dur <= duration_secs <= max_dur + 300:
        score += 5.0
    elif duration_secs >= min_dur:
        score += 3.0
    else:
        score += 1.0
    
    # Educational keywords in title (higher weight)
    for keyword in Config.EDUCATIONAL_KEYWORDS:
        if keyword in title_lower:
            score += 2.5
        elif keyword in desc_lower:
            score += 1.5
    
    # Grade-level specific keywords
    for keyword in keywords_config.get("keywords", []):
        if keyword in title_lower:
            score += 4.0
        elif keyword in desc_lower:
            score += 2.5
    
    # Topic matching with word boundaries
    topic_words = [w for w in topic_lower.split() if len(w) > 2]
    matched_words = 0
    for word in topic_words:
        if re.search(rf'\b{re.escape(word)}\b', title_lower):
            score += 5.0
            matched_words += 1
        elif re.search(rf'\b{re.escape(word)}\b', desc_lower):
            score += 2.5
            matched_words += 1
    
    # Penalize if no topic words matched
    if not matched_words and len(topic_words) > 0:
        score -= 10.0
    
    # View count (logarithmic scaling)
    if view_count > 1000:
        score += min(5.0, math.log10(view_count))
    elif view_count > 100:
        score += 2.0
    
    # Avoid words penalty (strong negative)
    for avoid_word in keywords_config.get("avoid", []):
        if avoid_word in combined_text:
            score -= 10.0
    
    # Quality channels (strong positive)
    for channel in keywords_config.get("channels", []):
        if channel in combined_text:
            score += 6.0
    
    # Bonus for official/verified content
    if any(x in combined_text for x in ["official", "verified", "certified", "ncert"]):
        score += 5.0
    
    return max(0.0, round(score, 2))


class YouTubeSearcher:
    """Handles YouTube video search and scoring."""
    
    MAX_RETRIES = 3
    RETRY_DELAY = 2
    
    def __init__(self, api_key: str):
        """Initialize YouTube API client."""
        try:
            self.youtube = build("youtube", "v3", developerKey=api_key)
        except Exception as e:
            raise ValueError(f"Failed to initialize YouTube API: {e}")
    
    def search_best_video(self, topic: str, grade_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Search for the best educational video on a topic.
        Returns video details including URL, title, and score.
        """
        keywords_config = get_grade_level_keywords(grade_info)
        query = get_search_query(topic, grade_info)
        
        for attempt in range(self.MAX_RETRIES):
            try:
                print_progress(f"Searching YouTube for {grade_info['display_name']} level videos on '{topic}'")
                
                search_response = self.youtube.search().list(
                    q=query,
                    part="snippet",
                    type="video",
                    maxResults=Config.MAX_SEARCH_RESULTS,
                    order="relevance",
                    videoDuration="medium",
                    safeSearch="strict",
                    relevanceLanguage="en"
                ).execute()
                
                video_ids = [
                    item["id"]["videoId"] 
                    for item in search_response.get("items", [])
                ]
                
                if not video_ids:
                    print_warning("No videos found for this search query.")
                    return None
                
                print_progress("Analyzing video quality and grade-level match")
                
                details_response = self.youtube.videos().list(
                    part="contentDetails,snippet,statistics",
                    id=",".join(video_ids)
                ).execute()
                
                candidates = []
                
                for item in details_response.get("items", []):
                    video_id = item["id"]
                    title = item["snippet"]["title"]
                    description = item["snippet"].get("description", "")
                    channel = item["snippet"].get("channelTitle", "Unknown")
                    
                    duration_iso = item["contentDetails"].get("duration")
                    duration_secs = parse_duration_to_seconds(duration_iso)
                    view_count = int(item["statistics"].get("viewCount", 0))
                    
                    if duration_secs is None:
                        continue
                    
                    score = calculate_video_score(
                        title, description, duration_secs, view_count, 
                        topic, grade_info, keywords_config
                    )
                    
                    candidates.append({
                        "id": video_id,
                        "title": title,
                        "description": description[:500],
                        "channel": channel,
                        "duration": duration_secs,
                        "views": view_count,
                        "score": score,
                        "url": f"https://www.youtube.com/watch?v={video_id}"
                    })
                
                if not candidates:
                    return None
                
                # Filter by minimum score threshold
                min_score = 10.0
                good_candidates = [c for c in candidates if c["score"] >= min_score]
                
                if not good_candidates:
                    print_warning(f"No videos found with sufficient relevance score (minimum {min_score})")
                    if candidates:
                        print_info("Showing best available option...")
                        return max(candidates, key=lambda x: x["score"])
                    return None
                
                return max(good_candidates, key=lambda x: x["score"])
                
            except HttpError as e:
                error_code = e.resp.status
                if error_code == 403:
                    print_error("YouTube API quota exceeded. Please try again later.")
                    return None
                elif error_code == 401:
                    print_error("Invalid YouTube API key.")
                    return None
                elif attempt < self.MAX_RETRIES - 1:
                    print_warning(f"Retrying... (Attempt {attempt + 1}/{self.MAX_RETRIES})")
                    time.sleep(self.RETRY_DELAY)
                else:
                    print_error(f"YouTube API error after retries: {e}")
                    return None
            except Exception as e:
                print_error(f"Error searching YouTube: {str(e)}")
                return None


class QuizGenerator:
    """Handles question generation and answer evaluation using Groq."""
    
    def __init__(self, api_key: str):
        """Initialize Groq client."""
        self.client = Groq(api_key=api_key)
        self.model = Config.GROQ_MODEL
    
    def generate_questions(self, topic: str, grade_info: Dict[str, Any], video_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate 4 MCQs and 2 short-answer questions based on video content and grade level."""
        
        grade_level = grade_info["display_name"]
        
        if video_info:
            video_context = f"""
VIDEO INFORMATION:
Title: {video_info.get('title', '')}
Channel: {video_info.get('channel', '')}
Description: {video_info.get('description', '')}

Generate questions that a student would be able to answer AFTER watching this specific video.
Focus on concepts that would likely be covered in this video based on its title and description."""
        else:
            video_context = "Generate general questions about this topic."
        
        prompt = f"""Generate a quiz about the topic: "{topic}" for {grade_level}.

{video_context}

Create exactly 4 multiple choice questions (MCQ) and 2 simple short-answer questions.
Make sure the difficulty level is appropriate for {grade_level}.

RULES:
- Questions MUST be based on what would be taught in the video
- Keep questions appropriate for the grade level
- MCQ options should be realistic and related to the topic
- Short answers should need only 1-3 words
- Include common misconceptions in wrong MCQ options

FORMAT:
MCQ QUESTIONS (4):
1. [Question based on video content]
   A) [Option A]
   B) [Option B]
   C) [Option C]
   D) [Option D]
   Answer: [Correct letter]

2. [Question based on video content]
   A) [Option A]
   B) [Option B]
   C) [Option C]
   D) [Option D]
   Answer: [Correct letter]

3. [Question based on video content]
   A) [Option A]
   B) [Option B]
   C) [Option C]
   D) [Option D]
   Answer: [Correct letter]

4. [Question based on video content]
   A) [Option A]
   B) [Option B]
   C) [Option C]
   D) [Option D]
   Answer: [Correct letter]

SHORT ANSWER QUESTIONS (2):
5. [Simple question requiring 1-2 word answer]
   Answer: [Correct answer]

6. [Simple question requiring 1-2 word answer]
   Answer: [Correct answer]"""

        try:
            print_progress("Generating quiz questions for your grade level")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content or ""
            
            return self._parse_quiz(content)
            
        except Exception as e:
            print_error(f"Error generating questions: {str(e)}")
            return {"mcq": [], "short": [], "raw": ""}
    
    def _parse_quiz(self, content: str) -> Dict[str, Any]:
        """Parse the generated quiz content into structured format."""
        mcq_questions = []
        short_questions = []
        
        lines = content.split("\n")
        current_question = None
        current_options = []
        current_answer = ""
        in_mcq = True
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if "SHORT ANSWER" in line.upper():
                in_mcq = False
                continue
            
            if re.match(r'^[1-4][\.\)]', line):
                if current_question and current_options:
                    mcq_questions.append({
                        "question": current_question,
                        "options": current_options.copy(),
                        "answer": current_answer
                    })
                current_question = re.sub(r'^[1-4][\.\)]\s*', '', line)
                current_options = []
                current_answer = ""
            
            elif re.match(r'^[5-6][\.\)]', line):
                if current_question and in_mcq and current_options:
                    mcq_questions.append({
                        "question": current_question,
                        "options": current_options.copy(),
                        "answer": current_answer
                    })
                current_question = re.sub(r'^[5-6][\.\)]\s*', '', line)
                current_options = []
                current_answer = ""
                in_mcq = False
            
            elif re.match(r'^[A-D][\)\.]', line):
                current_options.append(line)
            
            elif line.lower().startswith("answer:"):
                current_answer = line.split(":", 1)[1].strip()
                if not in_mcq and current_question:
                    short_questions.append({
                        "question": current_question,
                        "answer": current_answer
                    })
                    current_question = None
        
        if current_question:
            if in_mcq and current_options:
                mcq_questions.append({
                    "question": current_question,
                    "options": current_options.copy(),
                    "answer": current_answer
                })
            elif not in_mcq:
                short_questions.append({
                    "question": current_question,
                    "answer": current_answer
                })
        
        return {
            "mcq": mcq_questions[:4],
            "short": short_questions[:2],
            "raw": content
        }


def display_video_info(video: Dict[str, Any]) -> None:
    """Display video information in a formatted way."""
    print(f"\n{Fore.GREEN}{Style.BRIGHT}✓ Best Video Found!{Style.RESET_ALL}")
    print(f"{Fore.WHITE}{'─'*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Title:{Style.RESET_ALL} {video['title']}")
    print(f"{Fore.CYAN}Channel:{Style.RESET_ALL} {video['channel']}")
    print(f"{Fore.CYAN}Duration:{Style.RESET_ALL} {format_duration(video['duration'])}")
    print(f"{Fore.CYAN}Views:{Style.RESET_ALL} {video['views']:,}")
    print(f"{Fore.CYAN}Relevance Score:{Style.RESET_ALL} {video['score']}/30")
    print(f"{Fore.WHITE}{'─'*60}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}{Style.BRIGHT}Watch here:{Style.RESET_ALL} {video['url']}")


def display_and_collect_quiz(quiz: Dict[str, Any]) -> Dict[str, Any]:
    """Display quiz questions and collect answers."""
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*60}")
    print(f"{'QUIZ TIME!'.center(60)}")
    print(f"{'='*60}{Style.RESET_ALL}")
    
    mcq_answers = []
    short_answers = []
    correct_answers = []
    
    if quiz.get("mcq"):
        print(f"\n{Fore.YELLOW}{Style.BRIGHT}MULTIPLE CHOICE QUESTIONS (4){Style.RESET_ALL}")
        print(f"{Fore.WHITE}Enter A, B, C, or D for each question{Style.RESET_ALL}\n")
        
        for i, mcq in enumerate(quiz["mcq"], 1):
            print(f"{Fore.CYAN}{Style.BRIGHT}Q{i}.{Style.RESET_ALL} {mcq['question']}")
            for option in mcq.get("options", []):
                print(f"   {Fore.WHITE}{option}{Style.RESET_ALL}")
            
            while True:
                answer = input(f"{Fore.GREEN}Your Answer (A/B/C/D): {Style.RESET_ALL}").strip().upper()
                if answer in ['A', 'B', 'C', 'D']:
                    mcq_answers.append(answer)
                    correct_answers.append(mcq.get("answer", "").upper().strip())
                    break
                print_warning("Please enter A, B, C, or D")
            print()
    
    if quiz.get("short"):
        print(f"\n{Fore.YELLOW}{Style.BRIGHT}SHORT ANSWER QUESTIONS (2){Style.RESET_ALL}")
        print(f"{Fore.WHITE}Type a brief answer (1-3 words){Style.RESET_ALL}\n")
        
        for i, short in enumerate(quiz["short"], 5):
            print(f"{Fore.CYAN}{Style.BRIGHT}Q{i}.{Style.RESET_ALL} {short['question']}")
            answer = input(f"{Fore.GREEN}Your Answer: {Style.RESET_ALL}").strip()
            short_answers.append(answer if answer else "[No answer]")
            correct_answers.append(short.get("answer", ""))
            print()
    
    return {
        "mcq_answers": mcq_answers,
        "short_answers": short_answers,
        "correct_answers": correct_answers,
        "quiz": quiz
    }


# --- Short-answer / improved-evaluation helpers ---
def calculate_similarity(str1: str, str2: str) -> float:
    """Return similarity (0..1) using SequenceMatcher ratio."""
    s1 = (str1 or "").lower().strip()
    s2 = (str2 or "").lower().strip()
    if not s1 and not s2:
        return 1.0
    if not s1 or not s2:
        return 0.0
    return difflib.SequenceMatcher(None, s1, s2).ratio()


def extract_keywords(text: str) -> list:
    """Very small keyword extractor (lowercase, remove punctuation, drop short/common words)."""
    text = (text or "").lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    tokens = [t for t in text.split() if len(t) > 2]
    stop = {
        'the','and','for','with','that','this','these','those','are','is','a','an',
        'in','on','of','to','by','as','be','it','will','can','from','at'
    }
    return [t for t in tokens if t not in stop]


def evaluate_short_answer(user_answer: str, correct_answer: str, question: str = "") -> dict:
    """Evaluate a short answer with tolerance for typos and conceptual matches.

    Returns dict: {
      'is_correct': bool,
      'confidence': float (0..1),
      'similarity': float,
      'overlap': float
    }
    """
    ua = (user_answer or "").strip()
    ca = (correct_answer or "").strip()

    sim = calculate_similarity(ua, ca)

    ua_kw = set(extract_keywords(ua))
    ca_kw = set(extract_keywords(ca))
    overlap = 0.0
    if ca_kw:
        overlap = len(ua_kw & ca_kw) / len(ca_kw)

    # Combine signals: similarity weighted higher, overlap helps for conceptual matches
    confidence = max(0.0, min(1.0, 0.7 * sim + 0.3 * overlap))

    # Acceptance rules (tunable):
    # - Very high similarity => accept
    # - High overlap => accept
    # - Moderate confidence => accept as "close"
    is_correct = False
    if sim >= 0.92 or overlap >= 0.85 or confidence >= 0.86:
        is_correct = True
    elif confidence >= 0.7 and len(ua.split()) >= 1:
        # Accept as close/correct for learner-friendliness
        is_correct = True

    return {
        "is_correct": is_correct,
        "confidence": confidence,
        "similarity": sim,
        "overlap": overlap
    }


def evaluate_quiz_improved(mcq_answers: list, short_answers: list, quiz: dict) -> dict:
    """Evaluate MCQs (strict) and short answers (tolerant). Returns results summary."""
    results = []
    correct = 0
    total = 0

    # MCQ evaluation (strict)
    for i, (user_ans, mcq) in enumerate(zip(mcq_answers, quiz.get("mcq", [])), 1):
        correct_ans = mcq.get("answer", "").upper().strip()
        if len(correct_ans) > 1:
            correct_ans = correct_ans[0]
        is_correct = (user_ans == correct_ans)
        confidence = 1.0 if is_correct else 0.0
        if is_correct:
            correct += 1
        total += 1
        results.append({
            "q_num": i,
            "type": "MCQ",
            "user_answer": user_ans,
            "correct_answer": correct_ans,
            "is_correct": is_correct,
            "confidence": confidence
        })

    # Short-answer evaluation (tolerant)
    for i, (user_ans, short) in enumerate(zip(short_answers, quiz.get("short", [])), 5):
        correct_ans = short.get("answer", "")
        eval_res = evaluate_short_answer(user_ans, correct_ans, short.get("question", ""))
        if eval_res["is_correct"]:
            correct += 1
        total += 1
        results.append({
            "q_num": i,
            "type": "Short",
            "user_answer": user_ans,
            "correct_answer": correct_ans,
            "is_correct": eval_res["is_correct"],
            "confidence": eval_res["confidence"],
            "similarity": eval_res["similarity"],
            "overlap": eval_res["overlap"]
        })

    percentage = round((correct / total) * 100) if total > 0 else 0
    return {
        "results": results,
        "correct": correct,
        "total": total,
        "percentage": percentage
    }


def run_study_session() -> None:
    """Main study session flow."""
    print_header("SMART STUDY ASSISTANT")
    print(f"{Fore.WHITE}Your personal learning companion for video lessons and quizzes!{Style.RESET_ALL}\n")
    
    if not Config.validate():
        sys.exit(1)
    
    # Select grade/class
    grade_info = select_class()
    
    # Enter topic
    topic = get_valid_input("Enter the topic you want to study: ", min_length=2, max_length=100)
    
    print()
    
    video = None
    if Config.has_youtube_key():
        youtube_searcher = YouTubeSearcher(Config.YOUTUBE_API_KEY)
        video = youtube_searcher.search_best_video(topic, grade_info)
        
        if video:
            display_video_info(video)
            print(f"\n{Fore.YELLOW}Tip: Watch the video before attempting the quiz!{Style.RESET_ALL}")
            input(f"\n{Fore.WHITE}Press Enter when you're ready for the quiz...{Style.RESET_ALL}")
        else:
            print_warning("No suitable video found for this topic.")
            print_info("Continuing with quiz questions...\n")
    else:
        print_info("YouTube video search is disabled (no API key provided).")
        print_info("Proceeding directly to quiz questions...\n")
    
    quiz_generator = QuizGenerator(Config.GROQ_API_KEY)
    quiz = quiz_generator.generate_questions(topic, grade_info, video)
    
    if not quiz.get("mcq") and not quiz.get("short"):
        print_error("Could not generate questions. Please try again.")
        return
    
    user_responses = display_and_collect_quiz(quiz)
    
    # Use the improved evaluation function with tolerant short-answer checking
    evaluation = evaluate_quiz_improved(
        user_responses["mcq_answers"],
        user_responses["short_answers"],
        quiz
    )
    
    # Use the enhanced display function
    display_quiz_results_enhanced(evaluation)
    
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*60}")
    print(f"{'SESSION COMPLETE'.center(60)}")
    print(f"{'='*60}{Style.RESET_ALL}")
    print(f"\n{Fore.GREEN}✓ Great job completing this study session!{Style.RESET_ALL}")
    print(f"{Fore.WHITE}Grade Level: {grade_info['display_name']}{Style.RESET_ALL}")
    print(f"{Fore.WHITE}Board: {grade_info['board_name']}{Style.RESET_ALL}")
    print(f"{Fore.WHITE}Topic studied: {topic}{Style.RESET_ALL}")
    if video:
        print(f"{Fore.WHITE}Video watched: {video['title'][:50]}...{Style.RESET_ALL}")
    print(f"\n{Fore.YELLOW}Keep learning and improving!{Style.RESET_ALL}\n")


def display_quiz_results_enhanced(evaluation: Dict[str, Any]) -> None:
    """Display quiz results with confidence indicators and improved feedback."""
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*60}")
    print(f"{'QUIZ RESULTS'.center(60)}")
    print(f"{'='*60}{Style.RESET_ALL}\n")
    
    for result in evaluation.get("results", []):
        q_num = result["q_num"]
        q_type = result["type"]
        user_ans = result["user_answer"]
        correct_ans = result["correct_answer"]
        is_correct = result["is_correct"]
        confidence = result.get("confidence", 1.0)
        
        if is_correct:
            if confidence >= 0.95:
                status = f"{Fore.GREEN}✓ CORRECT{Style.RESET_ALL}"
            else:
                status = f"{Fore.GREEN}✓ ACCEPTED{Style.RESET_ALL} {Fore.CYAN}(Similar/Close){Style.RESET_ALL}"
        else:
            status = f"{Fore.RED}✗ INCORRECT{Style.RESET_ALL}"
        
        print(f"{Fore.CYAN}Q{q_num} ({q_type}):{Style.RESET_ALL} {status}")
        print(f"   Your answer: {Fore.YELLOW}{user_ans}{Style.RESET_ALL}")
        
        if not is_correct or confidence < 0.95:
            print(f"   Expected: {Fore.GREEN}{correct_ans}{Style.RESET_ALL}")
        
        if q_type == "Short" and confidence < 1.0 and confidence > 0.0:
            print(f"   Match quality: {Fore.CYAN}{int(confidence * 100)}%{Style.RESET_ALL}")
        
        print()
    
    correct = evaluation.get("correct", 0)
    total = evaluation.get("total", 6)
    percentage = evaluation.get("percentage", 0)
    
    print(f"{Fore.WHITE}{'─'*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}FINAL SCORE: {correct}/{total} ({percentage}%){Style.RESET_ALL}")
    
    if percentage >= 80:
        print(f"{Fore.GREEN}🎉 Excellent work! You've mastered this topic!{Style.RESET_ALL}")
    elif percentage >= 60:
        print(f"{Fore.YELLOW}👍 Good job! Review the incorrect answers to improve.{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}📚 Keep practicing! Watch the video again and try once more.{Style.RESET_ALL}")


def main():
    """Entry point with error handling."""
    try:
        run_study_session()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Session interrupted. Goodbye!{Style.RESET_ALL}\n")
        sys.exit(0)
    except Exception as e:
        print_error(f"An unexpected error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
