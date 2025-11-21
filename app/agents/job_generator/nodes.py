"""Node functions for job generator agent."""
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from app.agents.job_generator.state import JobGeneratorState
from app.core.config import get_settings
from app.core.logging import llm_logger


settings = get_settings()
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7, openai_api_key=settings.openai_api_key)


async def analyze_brief(state: JobGeneratorState) -> dict:
    """Analyze the brief description to extract role level and key information."""
    
    brief = state["brief_description"]
    
    system_prompt = """You are an expert HR specialist. Analyze the job brief and extract:
1. Suggested job title
2. Role level (junior/mid/senior/lead/principal)
3. Key technical skills required
4. Domain/industry context

Keep it concise and structured."""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Analyze this job brief: {brief}")
    ]
    
    response = await llm.ainvoke(messages)
    
    llm_logger.info("Analyzed job brief")
    
    return {
        "messages": [response],
        "job_title": state.get("job_title")  # Will be refined in next node
    }


async def generate_title(state: JobGeneratorState) -> dict:
    """Generate a professional job title."""
    
    brief = state["brief_description"]
    department = state.get("department")
    
    context = f"Brief: {brief}"
    if department:
        context += f"\nDepartment: {department}"
    
    system_prompt = """Generate a clear, professional job title. Examples:
- Senior Backend Engineer
- Full Stack Developer
- DevOps Engineer
- Product Manager
- Data Scientist

Just return the title, nothing else."""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=context)
    ]
    
    response = await llm.ainvoke(messages)
    title = response.content.strip()
    
    llm_logger.info(f"Generated job title: {title}")
    
    return {"job_title": title}


async def generate_responsibilities(state: JobGeneratorState) -> dict:
    """Generate key responsibilities for the role."""
    
    brief = state["brief_description"]
    title = state.get("job_title", "")
    
    system_prompt = f"""Generate 5-7 key responsibilities for a {title} role.
Each responsibility should be:
- Action-oriented (start with verbs)
- Specific and measurable
- Relevant to the role

Format as a numbered list."""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Based on: {brief}")
    ]
    
    response = await llm.ainvoke(messages)
    
    # Parse responsibilities
    responsibilities = []
    for line in response.content.split("\n"):
        line = line.strip()
        if line and (line[0].isdigit() or line.startswith("-") or line.startswith("•")):
            # Remove numbering/bullets
            clean_line = line.lstrip("0123456789.-•) ").strip()
            if clean_line:
                responsibilities.append(clean_line)
    
    llm_logger.info(f"Generated {len(responsibilities)} responsibilities")
    
    return {"responsibilities": responsibilities}


async def generate_qualifications(state: JobGeneratorState) -> dict:
    """Generate required and preferred qualifications."""
    
    brief = state["brief_description"]
    title = state.get("job_title", "")
    
    system_prompt = f"""Generate qualifications for a {title} role.

REQUIRED QUALIFICATIONS (4-6 items):
- Must-have skills and experience
- Essential technical competencies
- Critical certifications or education

PREFERRED QUALIFICATIONS (3-5 items):
- Nice-to-have skills
- Bonus experience areas
- Additional certifications

Format as two separate sections with bullet points."""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Based on: {brief}")
    ]
    
    response = await llm.ainvoke(messages)
    
    # Parse into required and preferred
    required = []
    preferred = []
    current_section = None
    
    for line in response.content.split("\n"):
        line = line.strip()
        
        if "REQUIRED" in line.upper():
            current_section = "required"
        elif "PREFERRED" in line.upper():
            current_section = "preferred"
        elif line and (line.startswith("-") or line.startswith("•") or line.startswith("*")):
            clean_line = line.lstrip("-•* ").strip()
            if clean_line:
                if current_section == "required":
                    required.append(clean_line)
                elif current_section == "preferred":
                    preferred.append(clean_line)
    
    llm_logger.info(f"Generated {len(required)} required and {len(preferred)} preferred qualifications")
    
    return {
        "required_qualifications": required,
        "preferred_qualifications": preferred
    }


async def generate_benefits(state: JobGeneratorState) -> dict:
    """Generate benefits and perks."""
    
    system_prompt = """Generate 5-8 attractive benefits and perks for this role.
Include mix of:
- Compensation-related (equity, bonuses)
- Work-life balance (flexible hours, remote work)
- Professional development (learning budget, conferences)
- Health and wellness
- Team culture

Keep them appealing but realistic."""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"For role: {state.get('job_title', '')}")
    ]
    
    response = await llm.ainvoke(messages)
    
    # Parse benefits
    benefits = []
    for line in response.content.split("\n"):
        line = line.strip()
        if line and (line.startswith("-") or line.startswith("•") or line.startswith("*")):
            clean_line = line.lstrip("-•* ").strip()
            if clean_line:
                benefits.append(clean_line)
    
    llm_logger.info(f"Generated {len(benefits)} benefits")
    
    return {"benefits": benefits}


async def check_inclusivity(state: JobGeneratorState) -> dict:
    """Check for biased or non-inclusive language."""
    
    # Combine all generated content
    all_text = " ".join([
        state.get("job_title", ""),
        " ".join(state.get("responsibilities", [])),
        " ".join(state.get("required_qualifications", [])),
        " ".join(state.get("preferred_qualifications", [])),
    ])
    
    # Common problematic terms
    bias_keywords = [
        "young", "energetic", "ninja", "rockstar", "guru",
        "native speaker", "recent graduate", "digital native",
        "culture fit", "aggressive", "dominant"
    ]
    
    flagged = []
    for keyword in bias_keywords:
        if keyword.lower() in all_text.lower():
            flagged.append(keyword)
    
    # Score: 100 - (10 points per flagged term)
    score = max(0, 100 - (len(flagged) * 10))
    
    llm_logger.info(f"Inclusivity score: {score}, flagged terms: {flagged}")
    
    return {
        "inclusivity_score": score,
        "flagged_terms": flagged
    }


async def format_output(state: JobGeneratorState) -> dict:
    """Format the complete job description."""
    
    title = state.get("job_title", "")
    responsibilities = state.get("responsibilities", [])
    required = state.get("required_qualifications", [])
    preferred = state.get("preferred_qualifications", [])
    benefits = state.get("benefits", [])
    
    tone = state.get("tone", "professional")
    department = state.get("department")
    location = state.get("location")
    employment_type = state.get("employment_type")
    salary_range = state.get("salary_range")
    
    # Build the full description
    sections = []
    
    # Header
    header = f"# {title}\n"
    if department:
        header += f"**Department:** {department}\n"
    if location:
        header += f"**Location:** {location}\n"
    if employment_type:
        header += f"**Employment Type:** {employment_type}\n"
    if salary_range:
        header += f"**Salary Range:** {salary_range}\n"
    
    sections.append(header)
    
    # About the role (tone-dependent intro)
    if tone == "friendly":
        intro = "\n## About This Role\n\nWe're looking for someone awesome to join our team! "
    elif tone == "inclusive":
        intro = "\n## About This Opportunity\n\nWe believe diverse perspectives make us stronger. "
    else:
        intro = "\n## About the Role\n\nWe are seeking a qualified professional to join our organization. "
    
    sections.append(intro + "This is an exciting opportunity to make a real impact.")
    
    # Responsibilities
    if responsibilities:
        sections.append("\n## Key Responsibilities\n")
        for i, resp in enumerate(responsibilities, 1):
            sections.append(f"{i}. {resp}")
    
    # Required qualifications
    if required:
        sections.append("\n## Required Qualifications\n")
        for qual in required:
            sections.append(f"- {qual}")
    
    # Preferred qualifications
    if preferred:
        sections.append("\n## Preferred Qualifications\n")
        for qual in preferred:
            sections.append(f"- {qual}")
    
    # Benefits
    if benefits:
        sections.append("\n## What We Offer\n")
        for benefit in benefits:
            sections.append(f"- {benefit}")
    
    # Closing
    if tone == "friendly":
        closing = "\n## Apply Now!\n\nSound like a good fit? We'd love to hear from you! "
    elif tone == "inclusive":
        closing = "\n## We Encourage You to Apply\n\nWe welcome applicants from all backgrounds. "
    else:
        closing = "\n## How to Apply\n\nInterested candidates should submit their application. "
    
    sections.append(closing)
    
    full_description = "\n".join(sections)
    
    llm_logger.info(f"Formatted complete job description ({len(full_description)} chars)")
    
    return {"full_description": full_description}
