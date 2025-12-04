#!/usr/bin/env python3
"""
Flowchart Generator + Quiz - Terminal Version
Generates educational ASCII flowcharts and optionally creates a quiz (4 MCQ + 2 short answers)
based on the flowchart content using the Groq LLM.
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
    
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    
    @classmethod
    def validate(cls) -> bool:
        """Validate that required API keys are present."""
        if not cls.GROQ_API_KEY:
            print_error("Missing required API key: GROQ_API_KEY")
            print_info("Please set it in your .env file or environment variables.")
            print_info("Get your free key at: https://console.groq.com")
            return False
        return True


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


class FlowchartGenerator:
    """Handles educational flowchart generation using Groq."""
    
    def __init__(self, api_key: str):
        """Initialize Groq client."""
        self.client = Groq(api_key=api_key)
        self.model = Config.GROQ_MODEL
    
    def generate_flowchart(self, topic: str, grade_info: Dict[str, Any], complexity: str = "medium") -> Dict[str, Any]:
        """Generate an educational ASCII flowchart based on topic and grade level."""
        
        grade_level = grade_info["display_name"]
        board = grade_info["board_name"]
        level = grade_info["level"]
        
        # Complexity guidance
        complexity_map = {
            "simple": "3-5 steps with basic decision points",
            "medium": "6-10 steps with 2-3 decision points",
            "complex": "12+ steps with multiple decision branches and loops"
        }
        
        complexity_instruction = complexity_map.get(complexity, complexity_map["medium"])
        
        # Difficulty guidance based on level
        difficulty_map = {
            "beginner": "Use very simple language, basic boxes, and straightforward logic flow. Use START and END clearly.",
            "middle": "Use clear language with occasional technical terms. Show simple decision logic.",
            "intermediate": "Use technical terminology. Show multiple paths and decision logic clearly.",
            "advanced": "Use technical terminology freely. Include loops, complex conditions, and parallel processes.",
            "competitive": "Use advanced technical language. Include optimization paths, edge cases, and complex decision trees."
        }
        
        difficulty_guidance = difficulty_map.get(level, difficulty_map["beginner"])
        
        prompt = f"""Generate an educational ASCII flowchart about: "{topic}"

GRADE/LEVEL: {grade_level}
BOARD: {board}
COMPLEXITY: {complexity_instruction}

WRITING STYLE:
{difficulty_guidance}

RULES:
- Use ASCII art with boxes (╔════╗, ║, ╚════╝) or simple text boxes
- Show clear flow with arrows (→, ↓, ↑)
- Include START and END boxes
- Use decision diamonds or [DECISION] labels for conditionals
- Make each step clear and understandable for {grade_level}
- Use appropriate technical depth for {board} curriculum
- Add brief descriptions for each step
- Keep layout clean and readable in terminal

FORMAT:
Create a visual ASCII flowchart using:
- ╔════════════════╗ for boxes
- ║               ║
- ╚════════════════╝
- ↓ ↑ → for arrows
- [DECISION] for decision points
- Description below each element

Start with START → Flow through main steps → Show decisions → End with END

EXAMPLE STRUCTURE:
    ╔════════════════╗
    ║     START      ║
    ╚════════════════╝
           ↓
    ╔════════════════╗
    ║   Step 1       ║
    ╚════════════════╝
           ↓
    ◇ [DECISION] ◇
    ║         ║
   YES       NO
    ↓         ↓
  [Path 1] [Path 2]
    ↓         ↓
    ...continue...
           ↓
    ╚════════════════╝
    ║      END       ║
    ╚════════════════╝"""

        try:
            print_progress(f"Generating educational flowchart for {grade_level} - {board}")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content or ""
            
            return {
                "topic": topic,
                "grade_level": grade_level,
                "board": board,
                "complexity": complexity,
                "content": content,
                "success": True
            }
            
        except Exception as e:
            print_error(f"Error generating flowchart: {str(e)}")
            return {
                "topic": topic,
                "grade_level": grade_level,
                "board": board,
                "complexity": complexity,
                "content": "",
                "success": False
            }


class QuestionGenerator:
    """Generate 4 MCQs + 2 short answer questions using Groq, based on flowchart content."""
    
    def __init__(self, api_key: str):
        self.client = Groq(api_key=api_key)
        self.model = Config.GROQ_MODEL
    
    def generate_questions(self, topic: str, grade_info: Dict[str, Any], flowchart_text: str = "") -> Dict[str, Any]:
        """Generate MCQs and short answers using flowchart context when available."""
        grade_level = grade_info["display_name"]
        
        if flowchart_text:
            context = f"""FLOWCHART:
{flowchart_text}

Generate questions that a student would be able to answer AFTER studying the flowchart above.
"""
        else:
            context = "Generate questions based on the topic."
        
        prompt = f"""Generate a quiz about the topic: "{topic}" for {grade_level}.

{context}

Create exactly 4 multiple choice questions (MCQ) and 2 simple short-answer questions.
Make sure the difficulty level is appropriate for {grade_level}.

RULES:
- Questions MUST be based on the flowchart (if provided)
- Keep questions appropriate for the grade level
- MCQ options should be realistic and related to the topic
- Short answers should need only 1-3 words
- Include common misconceptions in wrong MCQ options

FORMAT:
MCQ QUESTIONS (4):
1. [Question]
   A) [Option A]
   B) [Option B]
   C) [Option C]
   D) [Option D]
   Answer: [Correct letter]

2. [Question]
   A) [Option A]
   B) [Option B]
   C) [Option C]
   D) [Option D]
   Answer: [Correct letter]

3. [Question]
   A) [Option A]
   B) [Option B]
   C) [Option C]
   D) [Option D]
   Answer: [Correct letter]

4. [Question]
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
            print_progress("Generating quiz questions from flowchart/topic")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1400
            )
            content = response.choices[0].message.content or ""
            return self._parse_quiz(content)
        except Exception as e:
            print_error(f"Error generating questions: {str(e)}")
            return {"mcq": [], "short": [], "raw": ""}
    
    def _parse_quiz(self, content: str) -> Dict[str, Any]:
        """Parse the LLM output into structured quiz dict."""
        mcq_questions = []
        short_questions = []
        lines = content.splitlines()
        current_q = None
        options = []
        answer = ""
        in_mcq = True
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if "SHORT ANSWER" in line.upper():
                in_mcq = False
                continue
            if re.match(r'^[1-4][\.\)]', line):
                if current_q and options:
                    mcq_questions.append({
                        "question": current_q,
                        "options": options.copy(),
                        "answer": answer
                    })
                current_q = re.sub(r'^[1-4][\.\)]\s*', '', line)
                options = []
                answer = ""
            elif re.match(r'^[5-6][\.\)]', line):
                if current_q and in_mcq and options:
                    mcq_questions.append({
                        "question": current_q,
                        "options": options.copy(),
                        "answer": answer
                    })
                current_q = re.sub(r'^[5-6][\.\)]\s*', '', line)
                options = []
                answer = ""
                in_mcq = False
            elif re.match(r'^[A-D][\)\.]', line):
                options.append(line)
            elif line.lower().startswith("answer:"):
                answer = line.split(":", 1)[1].strip()
                if not in_mcq and current_q:
                    short_questions.append({"question": current_q, "answer": answer})
                    current_q = None
        
        if current_q:
            if in_mcq and options:
                mcq_questions.append({"question": current_q, "options": options.copy(), "answer": answer})
            elif not in_mcq:
                short_questions.append({"question": current_q, "answer": answer})
        
        return {"mcq": mcq_questions[:4], "short": short_questions[:2], "raw": content}


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

    Returns dict with is_correct, confidence, similarity, overlap.
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

    is_correct = False
    if sim >= 0.92 or overlap >= 0.85 or confidence >= 0.86:
        is_correct = True
    elif confidence >= 0.7 and len(ua.split()) >= 1:
        is_correct = True

    return {
        "is_correct": is_correct,
        "confidence": confidence,
        "similarity": sim,
        "overlap": overlap
    }


def evaluate_quiz_improved(mcq_answers: list, short_answers: list, quiz: dict) -> dict:
    """Evaluate MCQs (strict) and short answers (tolerant)."""
    results = []
    correct = 0
    total = 0

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
    return {"results": results, "correct": correct, "total": total, "percentage": percentage}


def display_and_collect_quiz(quiz: Dict[str, Any]) -> Dict[str, Any]:
    """Display quiz questions and collect answers from the user."""
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

    return {"mcq_answers": mcq_answers, "short_answers": short_answers, "correct_answers": correct_answers, "quiz": quiz}


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
        print(f"{Fore.YELLOW}👍 Good job! Review incorrect answers to improve.{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}📚 Keep practicing! Review the flowchart and try again.{Style.RESET_ALL}")


def display_flowchart(flowchart: Dict[str, Any]) -> None:
    """Display the generated flowchart in a formatted way."""
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*60}")
    print(f"{'EDUCATIONAL FLOWCHART'.center(60)}")
    print(f"{'='*60}{Style.RESET_ALL}\n")

    print(f"{Fore.YELLOW}{Style.BRIGHT}Topic:{Style.RESET_ALL} {flowchart['topic']}")
    print(f"{Fore.YELLOW}{Style.BRIGHT}Grade Level:{Style.RESET_ALL} {flowchart['grade_level']}")
    print(f"{Fore.YELLOW}{Style.BRIGHT}Board:{Style.RESET_ALL} {flowchart['board']}")
    print(f"{Fore.YELLOW}{Style.BRIGHT}Complexity:{Style.RESET_ALL} {flowchart['complexity']}")
    print(f"\n{Fore.WHITE}{'─'*60}{Style.RESET_ALL}\n")

    print(f"{Fore.GREEN}{flowchart['content']}{Style.RESET_ALL}\n")
    print(f"{Fore.WHITE}{'─'*60}{Style.RESET_ALL}\n")


def save_flowchart(flowchart: Dict[str, Any], filename: str = None) -> bool:
    """Save flowchart to a file."""
    if filename is None:
        filename = f"flowchart_{flowchart['topic'].replace(' ', '_')}.txt"

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"Topic: {flowchart['topic']}\n")
            f.write(f"Grade Level: {flowchart['grade_level']}\n")
            f.write(f"Board: {flowchart['board']}\n")
            f.write(f"Complexity: {flowchart['complexity']}\n")
            f.write(f"\n{'='*60}\n\n")
            f.write(flowchart['content'])

        print_success(f"Flowchart saved to: {filename}")
        return True
    except Exception as e:
        print_error(f"Failed to save flowchart: {str(e)}")
        return False


def run_flowchart_generator() -> None:
    """Main flowchart generation session flow with optional quiz generation."""
    print_header("SMART FLOWCHART GENERATOR")
    print(f"{Fore.WHITE}Generate educational flowcharts tailored to your grade level!{Style.RESET_ALL}\n")

    if not Config.validate():
        sys.exit(1)

    # Select grade/class
    grade_info = select_class()

    # Enter topic
    topic = get_valid_input("Enter the topic for the flowchart: ", min_length=2, max_length=100)

    # Select flowchart complexity
    complexity_options = {
        "simple": "Simple (3-5 steps, basic decisions)",
        "medium": "Medium (6-10 steps, 2-3 decisions)",
        "complex": "Complex (12+ steps, multiple branches)"
    }

    print()
    selected_complexity = display_menu("Select Flowchart Complexity:", complexity_options)

    print()

    # Generate flowchart
    generator = FlowchartGenerator(Config.GROQ_API_KEY)
    flowchart = generator.generate_flowchart(topic, grade_info, selected_complexity)

    if not flowchart.get("success"):
        print_error("Could not generate flowchart. Please try again.")
        return

    # Display flowchart
    display_flowchart(flowchart)

    # Ask to generate quiz
    quiz_choice = input(f"{Fore.YELLOW}Generate a quiz from this flowchart? (yes/no): {Style.RESET_ALL}").strip().lower()
    if quiz_choice in ('yes', 'y'):
        qgen = QuestionGenerator(Config.GROQ_API_KEY)
        quiz = qgen.generate_questions(topic, grade_info, flowchart['content'])
        if not quiz.get("mcq") and not quiz.get("short"):
            print_error("Could not generate quiz questions. Please try again.")
        else:
            user_responses = display_and_collect_quiz(quiz)
            evaluation = evaluate_quiz_improved(
                user_responses["mcq_answers"],
                user_responses["short_answers"],
                quiz
            )
            display_quiz_results_enhanced(evaluation)

    # Ask to save flowchart (default filename used when user confirms)
    save_choice = input(f"{Fore.YELLOW}Do you want to save this flowchart? (yes/no): {Style.RESET_ALL}").strip().lower()
    if save_choice in ['yes', 'y']:
        save_flowchart(flowchart)

    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*60}")
    print(f"{'GENERATION COMPLETE'.center(60)}")
    print(f"{'='*60}{Style.RESET_ALL}")
    print(f"\n{Fore.GREEN}✓ Great job! You've generated a learning flowchart!{Style.RESET_ALL}")
    print(f"{Fore.WHITE}Grade Level: {flowchart['grade_level']}{Style.RESET_ALL}")
    print(f"{Fore.WHITE}Board: {flowchart['board']}{Style.RESET_ALL}")
    print(f"{Fore.WHITE}Topic: {topic}{Style.RESET_ALL}")
    print(f"\n{Fore.YELLOW}Use this flowchart for quick reference and learning!{Style.RESET_ALL}\n")


def main():
    """Entry point with error handling."""
    try:
        run_flowchart_generator()
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
