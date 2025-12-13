"""
Tiered LLM Provider for Code Review Agent

Provides tiered LLM capabilities with Gemini priority:
1. Gemini 2.5 Pro (Google) - Primary model
2. Groq API - Fast, free tier
3. OpenRouter (kwaipilot/kat-coder-pro) - Backup FREE
4. OpenRouter (amazon/nova-2-lite-v1) - Backup FREE  
5. FLAN-T5 (Local) - Fallback, always available
"""

import os
from typing import Optional, Literal, List
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class LLMResponse:
    """Response from an LLM."""
    content: str
    model: str
    provider: str
    tokens_used: Optional[int] = None


class TieredLLMProvider:
    """
    Tiered LLM Provider with Gemini as primary.
    
    Priority order for code review:
    1. Gemini 2.5 Pro (Google - primary, always use)
    2. Groq llama-3.1-8b-instant (fast backup)
    3. kwaipilot/kat-coder-pro:free (OpenRouter - backup)
    4. amazon/nova-2-lite-v1:free (OpenRouter - backup)
    5. FLAN-T5 (local fallback)
    """
    
    # OpenRouter free models with their API keys
    OPENROUTER_MODELS = [
        {
            "model": "kwaipilot/kat-coder-pro:free",
            "api_key_env": "OPENROUTER_KEY_1",
            "name": "Kat Coder Pro"
        },
        {
            "model": "amazon/nova-2-lite-v1:free",
            "api_key_env": "OPENROUTER_KEY_2", 
            "name": "Amazon Nova 2 Lite"
        }
    ]
    
    def __init__(
        self,
        groq_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        default_complexity: Literal["low", "medium", "high"] = "medium"
    ):
        """
        Initialize the tiered LLM provider.
        
        Args:
            groq_api_key: Groq API key (or from env GROQ_API_KEY)
            openai_api_key: OpenAI API key (or from env OPENAI_API_KEY)
            default_complexity: Default complexity level for requests
        """
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.groq_api_key = groq_api_key or os.getenv("GROQ_API_KEY")
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.openrouter_key_1 = os.getenv("OPENROUTER_KEY_1")
        self.openrouter_key_2 = os.getenv("OPENROUTER_KEY_2")
        self.default_complexity = default_complexity
        
        # Initialize clients lazily
        self._gemini_model = None
        self._flan_model = None
        self._flan_tokenizer = None
        self._groq_client = None
        self._openrouter_client = None
        
        print("✓ TieredLLMProvider initialized")
        print(f"  - Gemini 2.5 Pro: {'Available' if self.gemini_api_key else 'Not configured'}")
        print(f"  - Groq: {'Available' if self.groq_api_key else 'Not configured'}")
        print(f"  - OpenRouter (Kat Coder): {'Available' if self.openrouter_key_1 else 'Not configured'}")
        print(f"  - OpenRouter (Nova 2): {'Available' if self.openrouter_key_2 else 'Not configured'}")
        print(f"  - FLAN-T5: Available (local fallback)")
    
    # =========================================================================
    # Main Generation Methods
    # =========================================================================
    
    def generate(
        self,
        prompt: str,
        complexity: Optional[Literal["low", "medium", "high"]] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ) -> LLMResponse:
        """
        Generate a response using the appropriate LLM based on complexity.
        
        Priority: Gemini Pro -> Groq -> Gemini Flash -> OpenRouter -> FLAN-T5
        """
        complexity = complexity or self.default_complexity
        
        if complexity == "low":
            return self._generate_flan(prompt, max_tokens, temperature)
        else:
            # Priority 1: Gemini 2.5 Pro (Best quality)
            result = self._try_gemini_pro(prompt, max_tokens, temperature, system_prompt)
            if result:
                return result
            
            # Priority 2: Groq (Great for code - 90% confidence)
            result = self._try_groq(prompt, max_tokens, temperature, system_prompt)
            if result:
                return result
            
            # Priority 3: Gemini 2.5 Flash (Fast backup)
            result = self._try_gemini_flash(prompt, max_tokens, temperature, system_prompt)
            if result:
                return result
            
            # Priority 4: Kat Coder Pro (OpenRouter free)
            result = self._try_openrouter_kat(prompt, max_tokens, temperature, system_prompt)
            if result:
                return result
            
            # Priority 5: Nova 2 (OpenRouter free)
            result = self._try_openrouter_nova(prompt, max_tokens, temperature, system_prompt)
            if result:
                return result
            
            # Priority 6: FLAN-T5 (local fallback)
            print("All cloud APIs failed, falling back to local FLAN-T5...")
            return self._generate_flan(prompt, max_tokens, temperature)
    
    def generate_code_review(
        self,
        code: str,
        context: str,
        static_issues: list,
        complexity: Literal["medium", "high"] = "medium"
    ) -> LLMResponse:
        """Generate a code review using RAG context and static analysis."""
        
        system_prompt = """You are an expert Python code reviewer. Your job is to:
1. Identify code issues (bugs, anti-patterns, security vulnerabilities)
2. Suggest improvements based on best practices
3. Provide clear, actionable feedback
4. Reference specific rules and guidelines when applicable

Be thorough but concise. Format your review in markdown."""

        prompt = f"""## Code to Review:
```python
{code}
```

## Relevant Best Practices (from knowledge base):
{context}

## Static Analysis Issues Found:
{self._format_static_issues(static_issues)}

## Instructions:
Provide a comprehensive code review that:
1. Lists all issues found (with severity: critical/major/minor)
2. Explains WHY each issue is problematic
3. Suggests specific fixes
4. References the relevant best practice or rule

Format your response as a structured markdown report."""

        return self.generate(
            prompt=prompt,
            complexity=complexity,
            max_tokens=2048,
            temperature=0.3,
            system_prompt=system_prompt
        )
    
    def generate_code_fix(
        self,
        code: str,
        issues: list,
        complexity: Literal["medium", "high"] = "high"
    ) -> LLMResponse:
        """Generate corrected code based on identified issues."""
        
        system_prompt = """You are an expert Python developer. Your job is to fix code issues while:
1. Preserving the original functionality
2. Following PEP8 and Python best practices
3. Making minimal, targeted changes
4. Adding helpful comments for non-obvious fixes

Return ONLY the corrected code without explanations."""

        prompt = f"""## Original Code:
```python
{code}
```

## Issues to Fix:
{self._format_issues_for_fix(issues)}

## Instructions:
Provide the corrected Python code. Make sure it:
1. Fixes ALL the listed issues
2. Maintains the same functionality
3. Follows Python best practices
4. Is properly formatted

Return only the corrected code block."""

        return self.generate(
            prompt=prompt,
            complexity=complexity,
            max_tokens=2048,
            temperature=0.2,
            system_prompt=system_prompt
        )
    
    def generate_reflection(
        self,
        original_code: str,
        review: str,
        suggested_fix: str
    ) -> LLMResponse:
        """Generate a reflection on the review quality."""
        
        system_prompt = """You are a senior code review quality assessor. Evaluate reviews for:
1. Completeness - Did it catch all issues?
2. Accuracy - Are the issues real problems?
3. Clarity - Are explanations clear?
4. Actionability - Are fixes practical?
5. Security - Were security concerns addressed?

Provide a confidence score (0.0-1.0) and suggestions for improvement."""

        prompt = f"""## Original Code:
```python
{original_code}
```

## Generated Review:
{review}

## Suggested Fix:
```python
{suggested_fix}
```

## Evaluate:
1. Are there any issues the review MISSED?
2. Are there any FALSE POSITIVES (non-issues flagged as issues)?
3. Is the suggested fix CORRECT and COMPLETE?
4. Would the fix introduce any NEW issues?
5. Rate overall confidence (0.0-1.0) with justification.

Format as JSON:
{{
    "missed_issues": [...],
    "false_positives": [...],
    "fix_issues": [...],
    "confidence": 0.0-1.0,
    "should_revise": true/false,
    "revision_suggestions": [...]
}}"""

        return self.generate(
            prompt=prompt,
            complexity="high",
            max_tokens=1024,
            temperature=0.3,
            system_prompt=system_prompt
        )
    
    # =========================================================================
    # Provider-Specific Methods
    # =========================================================================
    
    def _try_gemini_pro(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        system_prompt: Optional[str] = None
    ) -> Optional[LLMResponse]:
        """Try Gemini 2.5 Pro (Priority 1 - Best quality)."""
        return self._try_gemini_model("gemini-2.5-pro", prompt, max_tokens, temperature, system_prompt)
    
    def _try_gemini_flash(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        system_prompt: Optional[str] = None
    ) -> Optional[LLMResponse]:
        """Try Gemini 2.5 Flash (Priority 3 - Fast backup)."""
        return self._try_gemini_model("gemini-2.5-flash", prompt, max_tokens, temperature, system_prompt)
    
    def _try_gemini_model(
        self,
        model_name: str,
        prompt: str,
        max_tokens: int,
        temperature: float,
        system_prompt: Optional[str] = None
    ) -> Optional[LLMResponse]:
        """Try a specific Gemini model."""
        if not self.gemini_api_key:
            return None
        
        try:
            import google.generativeai as genai
            
            # Configure the API
            genai.configure(api_key=self.gemini_api_key)
            
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                }
            )
            
            # Build prompt with system instruction if provided
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            response = model.generate_content(full_prompt)
            
            print(f"  ✓ Using Gemini {model_name}")
            
            return LLMResponse(
                content=response.text,
                model=model_name,
                provider="google",
                tokens_used=None
            )
        except Exception as e:
            print(f"  ✗ Gemini {model_name} failed: {str(e)[:60]}")
            return None
    
    def _try_openai(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        system_prompt: Optional[str] = None
    ) -> Optional[LLMResponse]:
        """Try OpenAI API (Priority 1)."""
        if not self.openai_api_key:
            return None
        
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=self.openai_api_key)
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            print("  ✓ Using OpenAI gpt-4o")
            
            return LLMResponse(
                content=response.choices[0].message.content,
                model="gpt-4o",
                provider="openai",
                tokens_used=response.usage.total_tokens if response.usage else None
            )
        except Exception as e:
            print(f"  ✗ OpenAI failed: {str(e)[:80]}")
            return None
    
    def _try_openrouter_kat(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        system_prompt: Optional[str] = None
    ) -> Optional[LLMResponse]:
        """Try Kat Coder Pro via OpenRouter (Priority 2)."""
        if not self.openrouter_key_1:
            return None
        
        return self._generate_openrouter(
            prompt, max_tokens, temperature, system_prompt,
            model="kwaipilot/kat-coder-pro:free",
            api_key=self.openrouter_key_1,
            model_name="Kat Coder Pro"
        )
    
    def _try_openrouter_nova(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        system_prompt: Optional[str] = None
    ) -> Optional[LLMResponse]:
        """Try Amazon Nova 2 via OpenRouter (Priority 4)."""
        if not self.openrouter_key_2:
            return None
        
        return self._generate_openrouter(
            prompt, max_tokens, temperature, system_prompt,
            model="amazon/nova-2-lite-v1:free",
            api_key=self.openrouter_key_2,
            model_name="Amazon Nova 2 Lite"
        )
    
    def _generate_openrouter(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        system_prompt: Optional[str],
        model: str,
        api_key: str,
        model_name: str
    ) -> Optional[LLMResponse]:
        """Generate using OpenRouter API (OpenAI-compatible)."""
        try:
            from openai import OpenAI
            
            client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=api_key
            )
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            print(f"  ✓ Using {model_name} via OpenRouter")
            
            return LLMResponse(
                content=response.choices[0].message.content,
                model=model,
                provider="openrouter",
                tokens_used=response.usage.total_tokens if response.usage else None
            )
        except Exception as e:
            print(f"  ✗ {model_name} failed: {str(e)[:100]}")
            return None
    
    def _try_groq(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        system_prompt: Optional[str] = None
    ) -> Optional[LLMResponse]:
        """Try Groq API."""
        if not self.groq_api_key or self.groq_api_key.startswith("gsk_your"):
            return None
        
        try:
            from groq import Groq
            
            if self._groq_client is None:
                self._groq_client = Groq(api_key=self.groq_api_key)
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self._groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            print("  ✓ Using Groq llama-3.1-8b-instant")
            
            return LLMResponse(
                content=response.choices[0].message.content,
                model="llama-3.1-8b-instant",
                provider="groq",
                tokens_used=response.usage.total_tokens if response.usage else None
            )
        except Exception as e:
            print(f"  ✗ Groq failed: {str(e)[:100]}")
            return None
    
    def _generate_flan(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> LLMResponse:
        """Generate using local FLAN-T5 model."""
        if self._flan_model is None:
            self._load_flan_model()
        
        import torch
        
        inputs = self._flan_tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=512
        )
        
        if torch.cuda.is_available():
            inputs = inputs.to("cuda")
        
        with torch.no_grad():
            outputs = self._flan_model.generate(
                **inputs,
                max_new_tokens=min(max_tokens, 512),
                temperature=temperature if temperature > 0 else 1.0,
                do_sample=temperature > 0,
                pad_token_id=self._flan_tokenizer.pad_token_id
            )
        
        content = self._flan_tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        return LLMResponse(
            content=content,
            model="google/flan-t5-base",
            provider="local",
            tokens_used=len(outputs[0])
        )
    
    def _load_flan_model(self):
        """Lazy load FLAN-T5 model."""
        import torch
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
        
        print("Loading FLAN-T5 model...")
        model_name = "google/flan-t5-base"
        
        self._flan_tokenizer = AutoTokenizer.from_pretrained(model_name)
        self._flan_model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        
        if torch.cuda.is_available():
            self._flan_model = self._flan_model.to("cuda")
            print("✓ FLAN-T5 loaded on GPU")
        else:
            print("✓ FLAN-T5 loaded on CPU")
    
    # =========================================================================
    # Helper Methods
    # =========================================================================
    
    def _format_static_issues(self, issues: list) -> str:
        """Format static analysis issues for the prompt."""
        if not issues:
            return "No static analysis issues found."
        
        formatted = []
        for i, issue in enumerate(issues, 1):
            formatted.append(
                f"{i}. [{issue.get('severity', 'issue')}] Line {issue.get('line', '?')}: "
                f"{issue.get('message', str(issue))}"
            )
        return "\n".join(formatted)
    
    def _format_issues_for_fix(self, issues: list) -> str:
        """Format issues for the code fix prompt."""
        if not issues:
            return "No specific issues to fix."
        
        formatted = []
        for i, issue in enumerate(issues, 1):
            if isinstance(issue, dict):
                formatted.append(f"{i}. {issue.get('message', str(issue))}")
            else:
                formatted.append(f"{i}. {issue}")
        return "\n".join(formatted)


# =============================================================================
# Factory Function
# =============================================================================

def get_llm_provider(
    groq_api_key: Optional[str] = None,
    openai_api_key: Optional[str] = None,
    default_complexity: Literal["low", "medium", "high"] = "medium"
) -> TieredLLMProvider:
    """
    Factory function to create a TieredLLMProvider.
    """
    return TieredLLMProvider(
        groq_api_key=groq_api_key,
        openai_api_key=openai_api_key,
        default_complexity=default_complexity
    )


if __name__ == "__main__":
    # Quick test
    provider = get_llm_provider()
    
    response = provider.generate(
        "What is the purpose of docstrings in Python?",
        complexity="medium"
    )
    print(f"\nResponse from {response.provider}/{response.model}:")
    print(response.content[:500])
