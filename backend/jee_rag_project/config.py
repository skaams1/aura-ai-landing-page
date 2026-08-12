# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Keys
    GROQ_API_KEY = "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"
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "pcsk_2spFeC_QcNTWqZZms2xEACUJ4YeDfyEEivqsgJc6J6vfK6qUa9pbWCW5joNtVC2pT1z1mL")

    # Pinecone settings
    PINECONE_INDEX_NAME = "jee-chemistry"
    PINECONE_CLOUD = "aws"
    PINECONE_REGION = "us-east-1"

    # Embedding model
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"

    # Chunking settings
    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 100

    # JEE Chemistry specific topics (Class 11 & 12)
    JEE_CHEMISTRY_TOPICS = [
        # Physical Chemistry
        "mole concept", "stoichiometry", "atomic structure", "periodic table",
        "chemical bonding", "thermodynamics", "equilibrium", "ionic equilibrium",
        "electrochemistry", "chemical kinetics", "surface chemistry",

        # Inorganic Chemistry
        "s-block elements", "p-block elements", "d-block elements", "f-block elements",
        "coordination compounds", "metallurgy", "qualitative analysis",

        # Organic Chemistry
        "hybridization", "isomerism", "organic reactions", "hydrocarbons",
        "haloalkanes", "alcohols", "phenols", "ethers", "aldehydes", "ketones",
        "carboxylic acids", "amines", "polymers", "biomolecules"
    ]

    # System prompt for JEE Chemistry
    SYSTEM_PROMPT = """You are an elite JEE Chemistry mentor with expertise in NCERT-based content for JEE Main and Advanced preparation.

Your role:
- Provide accurate, conceptual explanations based on NCERT Chemistry (Class 11 & 12)
- Focus on JEE-relevant problem-solving techniques
- Highlight common mistakes and exam patterns

Always respond in this format:
1. **Concept Overview**: Brief explanation of the underlying concept
2. **Hint**: A guiding hint to approach the problem
3. **Step-by-Step Solution**: Detailed solution with reasoning
4. **Final Answer**: Clear, concise answer
5. **JEE Tip**: Exam-specific tip or shortcut
6. **Related Topics**: Other JEE topics this connects to

Use chemical equations, formulas, and numerical values where appropriate.
Reference NCERT concepts when applicable."""
