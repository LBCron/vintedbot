"""
Claude API Integration for Auto-Fixing
Utilise Claude pour analyser les changements et proposer des corrections automatiques
"""
import os
import json
from typing import Dict, Any, Optional, List
import anthropic
from loguru import logger
from pathlib import Path


class ClaudeAutoFix:
    """Auto-fix issues using Claude API"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            logger.warning("[WARN] ANTHROPIC_API_KEY not configured")
            self.client = None
        else:
            self.client = anthropic.Anthropic(api_key=self.api_key)

    def analyze_monitoring_results(self, results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Analyze monitoring results and suggest fixes

        Args:
            results: Monitoring results dictionary

        Returns:
            Analysis with suggested fixes or None
        """
        if not self.client:
            logger.error("[ERROR] Claude API not configured")
            return None

        try:
            # Build context for Claude
            changes = results.get("changes_detected", [])
            failed_tests = [t for t in results.get("tests", []) if t["status"] == "failed"]

            if not changes and not failed_tests:
                logger.info("[OK] No issues to analyze")
                return None

            # Read current vinted_client.py code
            client_code = self._read_vinted_client_code()

            prompt = self._build_analysis_prompt(results, changes, failed_tests, client_code)

            # Call Claude API
            message = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=4096,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Parse response
            response_text = message.content[0].text

            analysis = {
                "timestamp": results.get("timestamp"),
                "claude_response": response_text,
                "status": results.get("status"),
                "suggestions": self._parse_suggestions(response_text)
            }

            # Save analysis
            self._save_analysis(analysis)

            logger.info("[OK] Claude analysis complete")
            return analysis

        except Exception as e:
            logger.error(f"[ERROR] Claude analysis failed: {e}")
            return None

    def _build_analysis_prompt(
        self,
        results: Dict[str, Any],
        changes: List[Dict[str, Any]],
        failed_tests: List[Dict[str, Any]],
        client_code: str
    ) -> str:
        """Build prompt for Claude"""

        prompt = f"""Tu es un expert en automatisation web et en Playwright.

# Contexte
Mon bot Vinted utilise Playwright pour automatiser des publications sur Vinted.fr. Le système de monitoring automatique a détecté des changements ou des problèmes sur la plateforme Vinted.

# Résultats du Monitoring
Status: {results.get('status', 'unknown')}
Timestamp: {results.get('timestamp', 'N/A')}

## Changements Détectés ({len(changes)})
"""

        for i, change in enumerate(changes, 1):
            prompt += f"""
{i}. [{change.get('severity', 'unknown').upper()}] {change.get('message', 'Unknown')}
   Test: {change.get('test', 'N/A')}
   Détails: {json.dumps(change.get('details', {}), indent=2)}
"""

        prompt += f"\n## Tests Échoués ({len(failed_tests)})\n"
        for test in failed_tests:
            prompt += f"""
- {test.get('name', 'unknown')}: {test.get('error', test.get('message', 'Unknown error'))}
  Détails: {json.dumps({k: v for k, v in test.items() if k not in ['name', 'error', 'message']}, indent=2)}
"""

        prompt += f"""

# Code Actuel (vinted_client.py)
```python
{client_code[:10000]}  # Limité à 10k caractères pour le contexte
```

# Ta Mission
Analyse les changements détectés et propose des corrections spécifiques pour le code Python/Playwright.

## Format de Réponse
Réponds en JSON structuré avec ce format:

{{
  "analysis": "Explication détaillée des changements détectés et de leur impact",
  "severity": "critical|high|medium|low",
  "fixes": [
    {{
      "file": "backend/core/vinted_client.py",
      "function": "nom_de_la_fonction",
      "issue": "Description du problème",
      "solution": "Description de la solution",
      "code_change": {{
        "old_code": "code à remplacer",
        "new_code": "nouveau code"
      }},
      "line_range": "approximate line numbers if known"
    }}
  ],
  "testing_recommendations": [
    "Recommandation 1",
    "Recommandation 2"
  ],
  "alternative_selectors": {{
    "title": ["selector1", "selector2"],
    "description": ["selector1", "selector2"]
  }}
}}

Sois précis et fournis du code Python/Playwright fonctionnel.
"""

        return prompt

    def _parse_suggestions(self, response: str) -> Dict[str, Any]:
        """Parse Claude's suggestions from response"""
        try:
            # Try to extract JSON from response
            # Claude might return markdown with ```json blocks
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            elif "```" in response:
                json_start = response.find("```") + 3
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            else:
                json_str = response

            return json.loads(json_str)

        except json.JSONDecodeError:
            logger.warning("[WARN] Could not parse JSON from Claude response")
            return {"raw_response": response}

    def _read_vinted_client_code(self) -> str:
        """Read current vinted_client.py code"""
        try:
            client_path = Path("backend/core/vinted_client.py")
            if client_path.exists():
                return client_path.read_text(encoding='utf-8')
            return "# File not found"
        except Exception as e:
            logger.error(f"Failed to read vinted_client.py: {e}")
            return "# Error reading file"

    def _save_analysis(self, analysis: Dict[str, Any]):
        """Save Claude's analysis"""
        try:
            analysis_dir = Path("backend/monitoring/analyses")
            analysis_dir.mkdir(parents=True, exist_ok=True)

            from datetime import datetime
            filename = f"claude_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = analysis_dir / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, indent=2, ensure_ascii=False)

            # Save as latest
            latest_path = analysis_dir / "claude_analysis_latest.json"
            with open(latest_path, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, indent=2, ensure_ascii=False)

            logger.info(f"📝 Analysis saved to {filepath}")

        except Exception as e:
            logger.error(f"Failed to save analysis: {e}")

    def generate_fix_pr(self, analysis: Dict[str, Any]) -> Optional[str]:
        """
        Generate a pull request with fixes (placeholder)

        In production, this would:
        1. Create a new branch
        2. Apply the suggested code changes
        3. Commit the changes
        4. Create a PR with the analysis

        Args:
            analysis: Claude's analysis with fixes

        Returns:
            PR URL or None
        """
        # This is a placeholder - implementing this would require:
        # - Git operations (creating branch, committing, pushing)
        # - GitHub API integration (creating PR)
        # - Careful validation of suggested changes

        logger.info("🔧 Auto-fix PR generation would happen here")
        logger.info("For safety, manual review is recommended")

        return None


def analyze_with_claude(results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Helper function to analyze monitoring results with Claude

    Args:
        results: Monitoring results

    Returns:
        Analysis dictionary or None
    """
    auto_fix = ClaudeAutoFix()
    return auto_fix.analyze_monitoring_results(results)


if __name__ == "__main__":
    # Test with sample data
    sample_results = {
        "timestamp": "2025-01-15T08:00:00",
        "status": "critical",
        "tests": [
            {
                "name": "form_selectors",
                "status": "failed",
                "missing_selectors": [
                    {
                        "field": "title",
                        "selectors": ['input[name="title"]', 'input[placeholder*="Titre"]']
                    }
                ]
            }
        ],
        "changes_detected": [
            {
                "test": "form_selectors",
                "message": "Form selector missing: title",
                "severity": "critical",
                "details": {
                    "field": "title",
                    "tested_selectors": ['input[name="title"]', 'input[placeholder*="Titre"]']
                }
            }
        ]
    }

    auto_fix = ClaudeAutoFix()
    analysis = auto_fix.analyze_monitoring_results(sample_results)

    if analysis:
        print(json.dumps(analysis, indent=2, ensure_ascii=False))
