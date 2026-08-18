import httpx
from typing import Dict, Any, List
from app.core.config import settings


class AIService:
    """
    Handles LLM communication (DeepSeek / OpenAI compatible) for:
    1. Executive Summary Generation from Fact Sheets
    2. Grounded Natural Language Q&A
    """

    SYSTEM_PROMPT = """You are DataPilot AI, an elite automated senior data analyst.
Your job is to translate deterministic mathematical facts and statistical profiling reports into crystal-clear executive insights for business stakeholders.

RULES:
1. NEVER invent, hallucinate, or guess numbers.
2. ONLY use numbers explicitly provided in the FACT SHEET.
3. Format output cleanly with markdown bullet points and bold highlights.
4. If asked a question that cannot be answered from the facts, honestly state: "This metric is not present in the computed dataset profile."
"""

    @classmethod
    async def generate_executive_summary(cls, fact_sheet: Dict[str, Any]) -> str:
        """Calls LLM to generate an executive markdown summary from the fact sheet."""
        if settings.DEEPSEEK_API_KEY == "dummy_key_for_testing" or not settings.DEEPSEEK_API_KEY:
            return cls._generate_fallback_summary(fact_sheet)

        user_prompt = f"""Generate a concise 3-paragraph executive summary based on this dataset Fact Sheet:

FACT SHEET:
{fact_sheet}

Structure:
- **Overview & Data Health**: High-level dataset dimensions and health score.
- **Key Findings & Anomalies**: Important distributions, missing data alerts, or outliers.
- **Actionable Recommendations**: 2-3 specific business actions to clean or leverage this data.
"""

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{settings.DEEPSEEK_BASE_URL}/chat/completions",
                    headers={"Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}"},
                    json={
                        "model": settings.AI_MODEL_NAME,
                        "messages": [
                            {"role": "system", "content": cls.SYSTEM_PROMPT},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.2
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    return cls._generate_fallback_summary(fact_sheet)
        except Exception:
            return cls._generate_fallback_summary(fact_sheet)

    @classmethod
    async def answer_question(cls, question: str, dataset_context: Dict[str, Any]) -> str:
        """Answers a user's natural language question grounded in the dataset profile."""
        if settings.DEEPSEEK_API_KEY == "dummy_key_for_testing" or not settings.DEEPSEEK_API_KEY:
            return cls._generate_fallback_answer(question, dataset_context)

        prompt = f"""DATASET CONTEXT:
Summary: {dataset_context.get('quality')}
Schema: {dataset_context.get('schema')}
Statistics: {dataset_context.get('statistics')}
Outliers: {dataset_context.get('outliers')}

USER QUESTION:
"{question}"

Answer concisely and accurately using ONLY the numbers above:"""

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{settings.DEEPSEEK_BASE_URL}/chat/completions",
                    headers={"Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}"},
                    json={
                        "model": settings.AI_MODEL_NAME,
                        "messages": [
                            {"role": "system", "content": cls.SYSTEM_PROMPT},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.1
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    return cls._generate_fallback_answer(question, dataset_context)
        except Exception:
            return cls._generate_fallback_answer(question, dataset_context)

    @classmethod
    def _generate_fallback_summary(cls, fact_sheet: Dict[str, Any]) -> str:
        """Intelligent deterministic synthesis used when no external API key is active."""
        summary = fact_sheet.get("dataset_summary", {})
        findings = fact_sheet.get("top_prioritized_findings", [])
        
        findings_text = "\n".join([f"- **{f['title']}** ({f['category']}): {f['detail']}" for f in findings[:4]])

        return f"""### 📊 Executive Data Summary

**Dataset Health & Overview:**
The dataset `{summary.get('file_name', 'uploaded_file')}` contains **{summary.get('total_rows', 0)} records** across **{summary.get('total_columns', 0)} attributes**. The overall Data Health Score is **{summary.get('health_score', 100)}/100**, with {summary.get('duplicate_rows', 0)} duplicate records detected.

**Key Findings:**
{findings_text if findings_text else "- All column distributions appear standard with no high-severity quality warnings."}

**Recommendations:**
1. Clean duplicate and high-null records before downstream business modeling.
2. Review detected numerical anomalies to prevent skewed aggregation metrics.
"""

    @classmethod
    def _generate_fallback_answer(cls, question: str, ctx: Dict[str, Any]) -> str:
        q_lower = question.lower()
        quality = ctx.get("quality", {})
        stats = ctx.get("statistics", {})

        if "health" in q_lower or "score" in q_lower:
            return f"The overall Data Health Score is **{quality.get('health_score', 'N/A')}/100**."
        elif "duplicate" in q_lower or "duplicates" in q_lower:
            return f"There are **{quality.get('duplicate_rows', 0)} duplicate rows** ({quality.get('duplicate_percentage', 0)}% of total rows)."
        elif "row" in q_lower or "size" in q_lower or "count" in q_lower:
            return f"The dataset contains **{quality.get('total_rows', 0)} total rows** and **{quality.get('total_columns', 0)} columns**."
        else:
            return f"Based on the dataset profile: The dataset has {quality.get('total_rows')} rows with a health score of {quality.get('health_score')}/100."