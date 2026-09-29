import json
import re
from typing import Dict, Any, List, Optional
try:
    import google.generativeai as genai
except ImportError:
    genai = None

try:
    import openai
except ImportError:
    openai = None

from ..config import settings

ROLE_BENCHMARKS = {
    "Full Stack Developer": {
        "title": "Full Stack Developer",
        "core_skills": ["JavaScript", "TypeScript", "React", "Node.js", "Python", "REST API", "SQL", "MongoDB", "Git"],
        "tools_frameworks": ["Express", "Docker", "Next.js", "PostgreSQL", "Tailwind CSS", "Redis"],
        "keywords": ["Responsive design", "Full-stack architecture", "API integration", "State management", "Authentication", "CI/CD"],
        "recommended_certifications": ["AWS Certified Developer", "Meta Full-Stack Developer Certificate"]
    },
    "Frontend Developer": {
        "title": "Frontend Developer",
        "core_skills": ["JavaScript", "TypeScript", "React", "HTML5", "CSS3", "Redux", "Responsive Design", "Git"],
        "tools_frameworks": ["Next.js", "Tailwind CSS", "Webpack", "Vite", "Vue.js", "Jest", "Figma"],
        "keywords": ["Component lifecycle", "Web performance optimization", "Cross-browser compatibility", "State management", "UI/UX implementation", "Accessibility (a11y)"],
        "recommended_certifications": ["Meta Front-End Developer", "FreeCodeCamp Frontend Libraries"]
    },
    "Backend Developer": {
        "title": "Backend Developer",
        "core_skills": ["Python", "Java", "Node.js", "FastAPI", "Django", "PostgreSQL", "MongoDB", "RESTful APIs", "Git"],
        "tools_frameworks": ["Docker", "Kubernetes", "Redis", "Spring Boot", "GraphQL", "Microservices", "RabbitMQ"],
        "keywords": ["Database indexing", "API rate limiting", "Authentication & JWT", "Microservice architecture", "Query optimization", "Scalability"],
        "recommended_certifications": ["AWS Solutions Architect Associate", "Oracle Certified Professional Java"]
    },
    "Python / Django Developer": {
        "title": "Python / Django Developer",
        "core_skills": ["Python", "Django", "Django REST Framework", "PostgreSQL", "SQL", "Git", "REST APIs"],
        "tools_frameworks": ["Celery", "Redis", "Docker", "Flask", "FastAPI", "PyTest", "Linux"],
        "keywords": ["ORM optimization", "Asynchronous tasks", "Database migrations", "Unit testing", "JWT authentication"],
        "recommended_certifications": ["PCAP – Certified Associate in Python Programming", "AWS Cloud Practitioner"]
    },
    "Data Scientist & AI / ML Engineer": {
        "title": "Data Scientist & AI / ML Engineer",
        "core_skills": ["Python", "Machine Learning", "Deep Learning", "Pandas", "NumPy", "Scikit-Learn", "SQL", "Git"],
        "tools_frameworks": ["PyTorch", "TensorFlow", "Prompt Engineering", "LLMs", "LangChain", "OpenAI API", "HuggingFace", "Jupyter"],
        "keywords": ["Model evaluation & metrics", "Feature engineering", "Exploratory data analysis", "NLP pipeline", "Model deployment", "Hyperparameter tuning"],
        "recommended_certifications": ["TensorFlow Developer Certificate", "AWS Certified Machine Learning – Specialty"]
    },
    "DevOps & Cloud Engineer": {
        "title": "DevOps & Cloud Engineer",
        "core_skills": ["Linux", "Docker", "Kubernetes", "AWS", "CI/CD", "Git", "Bash / Shell Scripting"],
        "tools_frameworks": ["Terraform", "GitHub Actions", "Jenkins", "Ansible", "Prometheus", "Grafana", "Azure"],
        "keywords": ["Infrastructure as Code", "Container orchestration", "Pipeline automation", "System monitoring", "High availability", "Cloud security"],
        "recommended_certifications": ["AWS Certified DevOps Engineer", "CKA (Certified Kubernetes Administrator)"]
    },
    "Mobile App Developer": {
        "title": "Mobile App Developer",
        "core_skills": ["Flutter", "Dart", "React Native", "JavaScript", "iOS", "Android", "REST APIs", "Git"],
        "tools_frameworks": ["Firebase", "Redux", "Bloc", "Xcode", "Android Studio", "SQLite"],
        "keywords": ["Native device APIs", "Offline synchronization", "App store deployment", "Mobile UI state management", "Push notifications"],
        "recommended_certifications": ["Google Associate Android Developer", "Meta React Native Specialization"]
    },
    "Cybersecurity Analyst": {
        "title": "Cybersecurity Analyst",
        "core_skills": ["Network Security", "Penetration Testing", "Vulnerability Assessment", "Firewalls", "OWASP", "Linux", "Python"],
        "tools_frameworks": ["Wireshark", "Metasploit", "Nmap", "SIEM", "Burp Suite", "Splunk"],
        "keywords": ["Incident response", "Threat modeling", "Security auditing", "Encryption standards", "Zero Trust architecture"],
        "recommended_certifications": ["CompTIA Security+", "CEH (Certified Ethical Hacker)"]
    },
    "Software QA & Automation Tester": {
        "title": "Software QA & Automation Tester",
        "core_skills": ["Selenium", "Test Automation", "Python", "Java", "API Testing", "Postman", "Git"],
        "tools_frameworks": ["Cypress", "Playwright", "PyTest", "JUnit", "JIRA", "Jenkins"],
        "keywords": ["Regression testing", "Test case design", "Automated test suites", "Bug lifecycle management", "Continuous testing"],
        "recommended_certifications": ["ISTQB Certified Tester", "Selenium Automation Specialist"]
    },
    "UI/UX & Product Designer": {
        "title": "UI/UX & Product Designer",
        "core_skills": ["Figma", "UI Design", "User Research", "Wireframing", "Prototyping", "Design Systems"],
        "tools_frameworks": ["Adobe XD", "HTML/CSS", "Sketch", "InVision", "Miro"],
        "keywords": ["User personas", "Information architecture", "Usability testing", "Responsive typography", "Design handoff"],
        "recommended_certifications": ["Google UX Design Professional Certificate", "Nielsen Norman Group UX"]
    }
}

def clean_json_response(text: str) -> Dict[str, Any]:
    """
    Cleans markdown backticks block or formatting from AI response and returns parsed dict.
    """
    text_clean = text.strip()
    if text_clean.startswith("```"):
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text_clean)
        if match:
            text_clean = match.group(1)
    
    try:
        return json.loads(text_clean)
    except json.JSONDecodeError:
        match = re.search(r"(\{[\s\S]*\})", text_clean)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        raise ValueError("AI response was not valid JSON.")

def compute_token_analysis(resume_text: str) -> Dict[str, Any]:
    """
    Analyzes resume length, word count, estimated tokens, and brevity metrics.
    Emphasizes prompt-engineering style conciseness over wordy filler.
    """
    words = re.findall(r'\b\w+\b', resume_text)
    word_count = len(words)
    # Estimate tokens: typically 1 word ~ 1.33 tokens in technical English
    estimated_tokens = int(word_count * 1.33) if word_count > 0 else 0

    # Recommended token budget for modern 1-2 page high-impact ATS resume
    target_min = 600
    target_max = 850

    if target_min <= estimated_tokens <= target_max:
        token_score = 95 - abs(estimated_tokens - 720) * 0.04
        token_status = "optimal"
        status_label = "Optimal ATS Token Budget"
        brevity_advice = (
            f"Excellent! Your resume uses approximately {estimated_tokens:,} tokens ({word_count:,} words), "
            f"which is in the optimal ATS target window ({target_min}–{target_max} tokens). "
            f"Your bullet points are concise, allowing ATS scanners and hiring managers to quickly grasp your technical impact."
        )
    elif estimated_tokens > target_max:
        excess = estimated_tokens - target_max
        token_score = max(38, 92 - (excess // 14))
        token_status = "too_wordy"
        status_label = "High Token Count (Resume Too Wordy)"
        suggested_cut = int(excess * 0.65)
        brevity_advice = (
            f"Your resume is currently ~{estimated_tokens:,} tokens ({word_count:,} words), which exceeds the ideal ATS target "
            f"of {target_max} tokens. Recruiters scan resumes in 6–8 seconds. "
            f"Trimming ~{suggested_cut} tokens by cutting filler phrases ('responsible for', 'successfully worked on') "
            f"and using crisp, metric-focused bullet points will significantly increase your ATS score and readability."
        )
    else:
        deficit = target_min - estimated_tokens
        token_score = max(42, 90 - (deficit // 10))
        token_status = "too_brief"
        status_label = "Low Token Count (Too Brief)"
        brevity_advice = (
            f"Your resume is currently ~{estimated_tokens:,} tokens ({word_count:,} words), which is below the recommended "
            f"{target_min} tokens threshold. Adding 2–3 quantified project bullet points with tools, responsibilities, "
            f"and business outcomes will improve your ATS keyword density and score."
        )

    token_score = round(min(max(float(token_score), 30.0), 99.0), 1)

    # Prompt Engineering style bullet optimization examples
    bullet_optimizations = [
        {
            "category": "Experience Bullet Optimization",
            "before": "I was actively involved in working with my team members to build and implement the user interface for our e-commerce platform using React.js and CSS, fixing bugs whenever they occurred.",
            "before_tokens": 34,
            "after": "Architected responsive React e-commerce UI components; resolved 35+ interface bugs and increased user checkout completion rate by 22%.",
            "after_tokens": 19,
            "token_reduction_pct": 44,
            "ats_impact": "Replaces passive filler words ('actively involved in working') with strong action verbs ('Architected') and measurable metric impact (+22%)."
        },
        {
            "category": "Project Description Optimization",
            "before": "Created a machine learning predictive model using Python and Scikit-Learn that had the goal of forecasting customer churn and helping the business retain users.",
            "before_tokens": 28,
            "after": "Trained Python & Scikit-Learn churn prediction model achieving 91% accuracy, identifying at-risk customer accounts for retention campaigns.",
            "after_tokens": 18,
            "token_reduction_pct": 36,
            "ats_impact": "Directly highlights model accuracy metric (91%) while cutting fluff tokens."
        },
        {
            "category": "Backend / API Bullet Optimization",
            "before": "Responsible for designing and making REST APIs for our database queries using Node.js and MongoDB so that mobile and web clients could get their data.",
            "before_tokens": 29,
            "after": "Engineered high-throughput REST APIs in Node.js & MongoDB, slashing mobile data query latency by 40%.",
            "after_tokens": 16,
            "token_reduction_pct": 45,
            "ats_impact": "Emphasizes performance metric ('slashing latency by 40%') with 45% fewer tokens."
        }
    ]

    return {
        "word_count": word_count,
        "estimated_tokens": estimated_tokens,
        "recommended_tokens_min": target_min,
        "recommended_tokens_max": target_max,
        "token_status": token_status,
        "status_label": status_label,
        "token_efficiency_score": token_score,
        "brevity_advice": brevity_advice,
        "bullet_optimizations": bullet_optimizations,
        "est_reading_time_sec": max(15, int(word_count / 3.5)) if word_count else 0
    }

def compute_role_match(resume_text: str, detected_skills: Dict[str, List[str]], target_role: str) -> Dict[str, Any]:
    """
    Compares candidate credentials against benchmark requirements for target_role.
    Calculates role match score, missing critical skills, missing tools, and action checklist.
    """
    all_found_skills = set()
    for cat, slist in detected_skills.items():
        if isinstance(slist, list):
            for s in slist:
                all_found_skills.add(s.lower().strip())

    lower_text = resume_text.lower()

    benchmark = None
    target_clean = target_role.strip().lower()
    for role_name, data in ROLE_BENCHMARKS.items():
        if role_name.lower() == target_clean or target_clean in role_name.lower() or role_name.lower() in target_clean:
            benchmark = data
            break

    if not benchmark:
        clean_title = target_role.strip().title()
        role_tokens = [w for w in re.findall(r'\w+', target_role.lower()) if len(w) > 2]
        benchmark = {
            "title": clean_title,
            "core_skills": [w.capitalize() for w in role_tokens] + ["Git", "System Design", "Problem Solving"],
            "tools_frameworks": ["Docker", "CI/CD", "Cloud Platforms"],
            "keywords": ["Architecture", "Optimization", "Testing", "Collaboration"],
            "recommended_certifications": [f"{clean_title} Professional Certification"]
        }

    core = benchmark["core_skills"]
    tools = benchmark["tools_frameworks"]
    keywords = benchmark["keywords"]

    matched_core = []
    missing_core = []
    for sk in core:
        sk_lower = sk.lower()
        if sk_lower in all_found_skills or re.search(r'\b' + re.escape(sk_lower) + r'\b', lower_text):
            matched_core.append(sk)
        else:
            missing_core.append(sk)

    matched_tools = []
    missing_tools = []
    for t in tools:
        t_lower = t.lower()
        if t_lower in all_found_skills or re.search(r'\b' + re.escape(t_lower) + r'\b', lower_text):
            matched_tools.append(t)
        else:
            missing_tools.append(t)

    missing_kw = []
    matched_kw = []
    for kw in keywords:
        if kw.lower() in lower_text:
            matched_kw.append(kw)
        else:
            missing_kw.append(kw)

    total_weight = len(core) * 2 + len(tools) + len(keywords)
    matched_weight = len(matched_core) * 2 + len(matched_tools) + len(matched_kw)
    raw_match = int((matched_weight / max(1, total_weight)) * 100)
    match_score = min(max(raw_match, 25), 98)

    if match_score >= 80:
        readiness = "High Match (Ready for Interview)"
    elif match_score >= 60:
        readiness = "Moderate Match (A Few Critical Skills Missing)"
    else:
        readiness = "Early Match (Skill Gap Detected)"

    action_checklist = []
    if missing_core:
        action_checklist.append(f"Add key technical skill(s): {', '.join(missing_core[:3])}")
    if missing_tools:
        action_checklist.append(f"Demonstrate hands-on tooling: {', '.join(missing_tools[:3])}")
    if missing_kw:
        action_checklist.append(f"Include role action keywords: {', '.join(missing_kw[:3])}")

    return {
        "target_role": benchmark["title"],
        "role_match_score": match_score,
        "readiness_level": readiness,
        "matched_skills": matched_core + matched_tools,
        "missing_critical_skills": missing_core,
        "missing_tools": missing_tools,
        "missing_keywords": missing_kw,
        "action_checklist": action_checklist,
        "recommended_certifications": benchmark["recommended_certifications"]
    }

def compute_composite_scores(
    role_score: float,
    token_score: float,
    base_ats: float,
    skills_score: float,
    experience_score: float
) -> Dict[str, float]:
    """
    Computes holistic scores where role match (35%) and token efficiency (20%)
    directly influence overall rating and ATS compatibility.
    """
    overall = (
        role_score * 0.35 +
        token_score * 0.20 +
        base_ats * 0.15 +
        skills_score * 0.15 +
        experience_score * 0.15
    )
    overall = round(min(max(overall, 20.0), 99.0), 1)

    ats_compatibility = round(
        min(max((base_ats * 0.45) + (token_score * 0.30) + (role_score * 0.25), 25.0), 99.0),
        1
    )

    return {
        "overall": overall,
        "ats_compatibility": ats_compatibility,
        "role_match": round(role_score, 1),
        "token_efficiency": round(token_score, 1),
        "skills": round(skills_score, 1),
        "experience": round(experience_score, 1)
    }

class AIService:
    def __init__(self):
        self.use_openai = bool(settings.OPENAI_API_KEY) and (openai is not None)
        self.use_gemini = bool(settings.GEMINI_API_KEY) and (genai is not None)

        if self.use_openai and openai:
            openai.api_key = settings.OPENAI_API_KEY
        elif self.use_gemini and genai:
            genai.configure(api_key=settings.GEMINI_API_KEY)

    def analyze_resume(self, resume_text: str, target_role: str = "Full Stack Developer") -> Dict[str, Any]:
        prompt = f"""
        You are an expert ATS & Resume Evaluation AI.
        Analyze the candidate's resume for the target role: "{target_role}".
        Provide a structured JSON response containing:
        1. candidate_name: String (or Null)
        2. email: String (or Null)
        3. phone: String (or Null)
        4. education: List of objects with [college, degree, year]
        5. experience: List of objects with [company, role, duration, description]
        6. projects: List of objects with [title, technologies_used, description]
        7. certifications: List of strings
        8. skills: Object mapping category lists:
           - programming_languages: List of strings
           - web_technologies: List of strings
           - databases: List of strings
           - cloud_technologies: List of strings
           - tools: List of strings
           - frameworks: List of strings
           - cybersecurity_skills: List of strings
           - soft_skills: List of strings
        9. scores: Object containing scores (integer 0 to 100):
           - ats_compatibility: Integer
           - skills: Integer
           - projects: Integer
           - experience: Integer
           - content_quality: Integer
        10. insights: Object containing:
            - top_strengths: List of strings
            - weak_areas: List of strings
            - missing_sections: List of strings
            - suggestions: List of strings
            - recommended_skills: List of strings

        IMPORTANT: Your output MUST be strict, valid JSON ONLY.
        
        RESUME TEXT:
        {resume_text}
        """

        if not self.use_openai and not self.use_gemini:
            return self._generate_mock_analysis(resume_text, target_role=target_role)

        try:
            if self.use_openai:
                response = openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"}
                )
                parsed = json.loads(response.choices[0].message.content)
            else:
                model = genai.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content(prompt)
                parsed = clean_json_response(response.text)

            # Augment with Token Analysis & Role Gap Analysis
            token_analysis = compute_token_analysis(resume_text)
            role_match = compute_role_match(resume_text, parsed.get("skills", {}), target_role)

            scores = parsed.get("scores", {})
            comp_scores = compute_composite_scores(
                role_score=role_match["role_match_score"],
                token_score=token_analysis["token_efficiency_score"],
                base_ats=scores.get("ats_compatibility", 70),
                skills_score=scores.get("skills", 70),
                experience_score=scores.get("experience", 70)
            )

            scores["overall"] = comp_scores["overall"]
            scores["ats_compatibility"] = comp_scores["ats_compatibility"]
            scores["role_match"] = comp_scores["role_match"]
            scores["token_efficiency"] = comp_scores["token_efficiency"]
            parsed["scores"] = scores

            parsed["target_role"] = target_role
            parsed["role_match"] = role_match
            parsed["token_analysis"] = token_analysis
            return parsed

        except Exception as e:
            return self._generate_mock_analysis(resume_text, target_role=target_role, error=str(e))

    def analyze_for_role(
        self,
        resume_text: str,
        target_role: str,
        detected_skills: Optional[Dict[str, List[str]]] = None,
        existing_scores: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Re-computes role match, gap highlights, token analysis, and scores for a switched target role.
        """
        if not detected_skills:
            detected_skills = self._extract_skills_from_text(resume_text)

        token_analysis = compute_token_analysis(resume_text)
        role_match = compute_role_match(resume_text, detected_skills, target_role)

        base_ats = existing_scores.get("ats_compatibility", 72) if existing_scores else 72
        skills_score = existing_scores.get("skills", 75) if existing_scores else 75
        experience_score = existing_scores.get("experience", 70) if existing_scores else 70

        comp_scores = compute_composite_scores(
            role_score=role_match["role_match_score"],
            token_score=token_analysis["token_efficiency_score"],
            base_ats=base_ats,
            skills_score=skills_score,
            experience_score=experience_score
        )

        return {
            "target_role": role_match["target_role"],
            "overall_score": comp_scores["overall"],
            "ats_score": comp_scores["ats_compatibility"],
            "role_match_score": comp_scores["role_match"],
            "token_efficiency_score": comp_scores["token_efficiency"],
            "skills_score": comp_scores["skills"],
            "role_match": role_match,
            "token_analysis": token_analysis
        }

    def _extract_skills_from_text(self, text: str) -> Dict[str, List[str]]:
        skills_keywords = {
            "programming_languages": ["python", "javascript", "typescript", "java", "cpp", "c#", "golang", "rust", "php", "dart", "ruby"],
            "web_technologies": ["html", "html5", "css", "css3", "react", "vue", "angular", "node", "next.js", "tailwind", "redux"],
            "databases": ["mysql", "mongodb", "postgresql", "redis", "sqlite", "oracle", "sql"],
            "cloud_technologies": ["aws", "azure", "gcp", "docker", "kubernetes", "linux", "terraform"],
            "frameworks": ["django", "fastapi", "flask", "spring", "express", "flutter", "react native"],
            "tools": ["git", "github", "jira", "vscode", "postman", "figma", "jenkins"],
            "cybersecurity_skills": ["firewall", "encryption", "penetration testing", "owasp", "siem", "network security"],
            "soft_skills": ["communication", "leadership", "teamwork", "problem solving", "critical thinking"]
        }

        found_skills = {cat: [] for cat in skills_keywords}
        for cat, keywords in skills_keywords.items():
            for kw in keywords:
                if re.search(r'\b' + re.escape(kw) + r'\b', text.lower()):
                    found_skills[cat].append(kw.capitalize())
        return found_skills

    def match_job(self, resume_text: str, job_description: str) -> Dict[str, Any]:
        prompt = f"""
        You are an expert ResumeIQ ATS Matching Assistant.
        Compare the candidate's Resume Text with the provided Job Description.
        Calculate an estimated job match score (0 to 100).
        Extract matching skills (found in both), missing skills (required/desired in Job Description but not found in Resume), and key actionable improvement recommendations.
        Never suggest adding false experiences.
        
        Provide a structured JSON response containing:
        1. match_score: Integer (0 to 100)
        2. matched_skills: List of strings
        3. missing_skills: List of strings
        4. recommendations: List of strings

        IMPORTANT: Output MUST be valid JSON only.
        
        RESUME TEXT:
        {resume_text}

        JOB DESCRIPTION:
        {job_description}
        """

        if not self.use_openai and not self.use_gemini:
            return self._generate_mock_match(resume_text, job_description)

        try:
            if self.use_openai:
                response = openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"}
                )
                return json.loads(response.choices[0].message.content)
            else:
                model = genai.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content(prompt)
                return clean_json_response(response.text)
        except Exception as e:
            return self._generate_mock_match(resume_text, job_description, error=str(e))

    def _generate_mock_analysis(self, text: str, target_role: str = "Full Stack Developer", error: str = None) -> Dict[str, Any]:
        found_skills = self._extract_skills_from_text(text)
        num_skills = sum(len(lst) for lst in found_skills.values())

        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        phone_match = re.search(r'[\+\d\-\(\)\s]{10,15}', text)

        token_analysis = compute_token_analysis(text)
        role_match = compute_role_match(text, found_skills, target_role)

        base_skills = min(45 + num_skills * 4, 96)
        base_experience = 74
        base_projects = 76
        base_ats = min(50 + num_skills * 3, 90)

        comp_scores = compute_composite_scores(
            role_score=role_match["role_match_score"],
            token_score=token_analysis["token_efficiency_score"],
            base_ats=base_ats,
            skills_score=base_skills,
            experience_score=base_experience
        )

        return {
            "candidate_name": "Applicant" if not error else "Analysis Mode (Offline)",
            "email": email_match.group(0) if email_match else "candidate@resumeiq.ai",
            "phone": phone_match.group(0).strip() if phone_match else "+1-555-0199",
            "education": [{"college": "University Institute of Technology", "degree": "B.E. Computer Science & Engineering", "year": "2024"}],
            "experience": [{"company": "Tech Innovations Ltd.", "role": target_role, "duration": "1 Year", "description": "Engineered responsive applications and microservices."}],
            "projects": [{"title": "Cloud Resume & Portfolio", "technologies_used": "React, Python, Fastapi, Docker", "description": "Developed full-stack web application with high responsiveness."}],
            "certifications": role_match["recommended_certifications"][:1] if role_match["recommended_certifications"] else ["Certified Developer"],
            "skills": found_skills,
            "target_role": role_match["target_role"],
            "role_match": role_match,
            "token_analysis": token_analysis,
            "scores": {
                "overall": comp_scores["overall"],
                "ats_compatibility": comp_scores["ats_compatibility"],
                "role_match": comp_scores["role_match"],
                "token_efficiency": comp_scores["token_efficiency"],
                "skills": comp_scores["skills"],
                "projects": base_projects,
                "experience": comp_scores["experience"],
                "content_quality": 82
            },
            "insights": {
                "top_strengths": [
                    f"Strong baseline alignment with {role_match['target_role']} core principles.",
                    f"Detected {len(role_match['matched_skills'])} relevant role skills in resume."
                ],
                "weak_areas": [
                    f"Missing {len(role_match['missing_critical_skills'])} critical skills required for {role_match['target_role']} roles.",
                    token_analysis["status_label"]
                ] if not error else [f"API Fallback: {error}"],
                "missing_sections": ["Quantified Impact Metrics", "Certifications Summary"],
                "suggestions": [
                    f"Incorporate missing core skills: {', '.join(role_match['missing_critical_skills'][:3])} into project bullet points.",
                    token_analysis["brevity_advice"]
                ],
                "recommended_skills": role_match["missing_critical_skills"][:4] + role_match["missing_tools"][:2]
            }
        }

    def _generate_mock_match(self, resume: str, job: str, error: str = None) -> Dict[str, Any]:
        resume_words = set(re.findall(r'\w+', resume.lower()))
        job_words = set(re.findall(r'\w+', job.lower()))

        skills_pool = ["python", "javascript", "typescript", "react", "sql", "aws", "docker", "kubernetes", "fastapi", "django", "nodejs", "css", "html", "git", "mongodb", "postgresql"]
        matched = []
        missing = []

        for sk in skills_pool:
            in_job = sk in job_words
            in_resume = sk in resume_words
            if in_job and in_resume:
                matched.append(sk.capitalize())
            elif in_job and not in_resume:
                missing.append(sk.capitalize())

        match_score = 50 + (len(matched) * 10) - (len(missing) * 4)
        match_score = max(min(match_score, 100), 25)

        return {
            "match_score": match_score,
            "matched_skills": matched if matched else ["Git", "Communication"],
            "missing_skills": missing if missing else ["Docker", "Kubernetes", "AWS"],
            "recommendations": [
                "Tailor your project descriptions to highlight matching tech stack skills.",
                "Ensure keywords requested in the JD are represented in your skills section."
            ]
        }

ai_service = AIService()
