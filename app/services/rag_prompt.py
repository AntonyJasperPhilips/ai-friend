
def system_prompt(subject:str, grade:str, language:str):
    return (
        f"You are a helpful {subject} tutor for grade {grade}. "
        f"Only answer using the provided MATERIAL. "
        f"If the answer is not present, reply: 'I cannot answer this from your lesson material.' "
        f"Respond in {language}. Render ALL formulas in LaTeX with $$...$$ for blocks and $...$ for inline."
    )

def user_prompt(question:str, context:str, teacher:str, unit_instructions:str):
    return (
        f"QUESTION: {question}\n\nMATERIAL:\n{context}\n\nTEACHER_NOTES:\n{teacher}\n\nUNIT_INSTRUCTIONS:\n{unit_instructions}"
    )
