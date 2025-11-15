"""
Comprehensive Code Quality Analysis

Runs all code quality tools and generates a detailed report:
- Pylint (code quality)
- Mypy (type checking)
- Black (formatting)
- Isort (import sorting)
- Bandit (security)
- Custom AST analysis (anti-patterns)
"""
import subprocess
import sys
import os
import ast
from pathlib import Path
from typing import List, Dict, Tuple
import json


class CodeQualityChecker:
    """Runs all code quality checks and generates report"""

    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir).resolve()
        self.results = {
            "pylint": {"score": 0, "issues": 0, "passed": False},
            "mypy": {"errors": 0, "passed": False},
            "black": {"files_need_formatting": 0, "passed": False},
            "isort": {"files_need_sorting": 0, "passed": False},
            "bandit": {"issues": 0, "severity_high": 0, "passed": False},
            "ast_analysis": {"anti_patterns": [], "passed": False}
        }

    def run_pylint(self) -> Tuple[bool, str]:
        """Run Pylint"""
        print("\n" + "="*70)
        print("🔍 PYLINT - Code Quality Analysis")
        print("="*70)

        try:
            result = subprocess.run(
                ["pylint", ".", "--rcfile=.pylintrc"],
                cwd=self.root_dir,
                capture_output=True,
                text=True,
                timeout=120
            )

            output = result.stdout + result.stderr

            # Extract score (format: "Your code has been rated at 8.5/10")
            score = 0.0
            for line in output.split('\n'):
                if 'rated at' in line:
                    try:
                        score_str = line.split('rated at')[1].split('/')[0].strip()
                        score = float(score_str)
                    except:
                        pass

            self.results["pylint"]["score"] = score
            self.results["pylint"]["passed"] = score >= 7.0

            print(f"Score: {score}/10.0")
            print(f"Status: {'✅ PASS' if score >= 7.0 else '❌ FAIL'}")

            # Count issues
            issue_count = output.count('[')
            self.results["pylint"]["issues"] = issue_count
            print(f"Issues found: {issue_count}")

            return score >= 7.0, output

        except subprocess.TimeoutExpired:
            print("❌ Pylint timed out")
            return False, "Timeout"
        except FileNotFoundError:
            print("⚠️  Pylint not installed")
            self.results["pylint"]["passed"] = True  # Don't fail if not installed
            return True, "Not installed"
        except Exception as e:
            print(f"❌ Error running Pylint: {e}")
            return False, str(e)

    def run_mypy(self) -> Tuple[bool, str]:
        """Run Mypy type checking"""
        print("\n" + "="*70)
        print("🔍 MYPY - Type Checking")
        print("="*70)

        try:
            result = subprocess.run(
                ["mypy", ".", "--config-file=mypy.ini"],
                cwd=self.root_dir,
                capture_output=True,
                text=True,
                timeout=120
            )

            output = result.stdout + result.stderr

            # Count errors
            error_count = output.count('error:')
            self.results["mypy"]["errors"] = error_count
            self.results["mypy"]["passed"] = error_count == 0

            print(f"Errors found: {error_count}")
            print(f"Status: {'✅ PASS' if error_count == 0 else '⚠️  WARNINGS'}")

            return error_count == 0, output

        except FileNotFoundError:
            print("⚠️  Mypy not installed")
            self.results["mypy"]["passed"] = True
            return True, "Not installed"
        except Exception as e:
            print(f"❌ Error running Mypy: {e}")
            return False, str(e)

    def run_black(self) -> Tuple[bool, str]:
        """Run Black formatting check"""
        print("\n" + "="*70)
        print("🔍 BLACK - Code Formatting")
        print("="*70)

        try:
            result = subprocess.run(
                ["black", ".", "--check", "--config=pyproject.toml"],
                cwd=self.root_dir,
                capture_output=True,
                text=True,
                timeout=60
            )

            output = result.stdout + result.stderr

            # Black returns 0 if all files are formatted, 1 if some need formatting
            needs_formatting = "would reformat" in output
            file_count = output.count("would reformat")

            self.results["black"]["files_need_formatting"] = file_count
            self.results["black"]["passed"] = not needs_formatting

            print(f"Files needing formatting: {file_count}")
            print(f"Status: {'✅ PASS' if not needs_formatting else '⚠️  NEEDS FORMATTING'}")

            return not needs_formatting, output

        except FileNotFoundError:
            print("⚠️  Black not installed")
            self.results["black"]["passed"] = True
            return True, "Not installed"
        except Exception as e:
            print(f"❌ Error running Black: {e}")
            return False, str(e)

    def run_isort(self) -> Tuple[bool, str]:
        """Run isort import sorting check"""
        print("\n" + "="*70)
        print("🔍 ISORT - Import Sorting")
        print("="*70)

        try:
            result = subprocess.run(
                ["isort", ".", "--check-only", "--settings-path=pyproject.toml"],
                cwd=self.root_dir,
                capture_output=True,
                text=True,
                timeout=60
            )

            output = result.stdout + result.stderr

            needs_sorting = "would be reformatted" in output
            file_count = output.count("would be reformatted")

            self.results["isort"]["files_need_sorting"] = file_count
            self.results["isort"]["passed"] = not needs_sorting

            print(f"Files needing import sorting: {file_count}")
            print(f"Status: {'✅ PASS' if not needs_sorting else '⚠️  NEEDS SORTING'}")

            return not needs_sorting, output

        except FileNotFoundError:
            print("⚠️  Isort not installed")
            self.results["isort"]["passed"] = True
            return True, "Not installed"
        except Exception as e:
            print(f"❌ Error running Isort: {e}")
            return False, str(e)

    def run_bandit(self) -> Tuple[bool, str]:
        """Run Bandit security analysis"""
        print("\n" + "="*70)
        print("🔍 BANDIT - Security Analysis")
        print("="*70)

        try:
            result = subprocess.run(
                ["bandit", "-r", ".", "-c", ".bandit", "-f", "json"],
                cwd=self.root_dir,
                capture_output=True,
                text=True,
                timeout=120
            )

            try:
                data = json.loads(result.stdout)
                results = data.get("results", [])

                total_issues = len(results)
                high_severity = sum(1 for r in results if r.get("issue_severity") == "HIGH")

                self.results["bandit"]["issues"] = total_issues
                self.results["bandit"]["severity_high"] = high_severity
                self.results["bandit"]["passed"] = high_severity == 0

                print(f"Total security issues: {total_issues}")
                print(f"High severity: {high_severity}")
                print(f"Status: {'✅ PASS' if high_severity == 0 else '❌ HIGH SEVERITY ISSUES FOUND'}")

                return high_severity == 0, result.stdout

            except json.JSONDecodeError:
                # Fall back to text output
                output = result.stdout + result.stderr
                has_issues = "Issue:" in output
                self.results["bandit"]["passed"] = not has_issues
                print(f"Status: {'✅ PASS' if not has_issues else '⚠️  ISSUES FOUND'}")
                return not has_issues, output

        except FileNotFoundError:
            print("⚠️  Bandit not installed")
            self.results["bandit"]["passed"] = True
            return True, "Not installed"
        except Exception as e:
            print(f"❌ Error running Bandit: {e}")
            return False, str(e)

    def run_ast_analysis(self) -> Tuple[bool, List[Dict]]:
        """Run custom AST analysis for anti-patterns"""
        print("\n" + "="*70)
        print("🔍 AST ANALYSIS - Anti-Pattern Detection")
        print("="*70)

        anti_patterns = []

        # Find all Python files
        python_files = list(self.root_dir.glob("**/*.py"))
        python_files = [
            f for f in python_files
            if "venv" not in str(f) and "__pycache__" not in str(f)
        ]

        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    source = f.read()

                tree = ast.parse(source, filename=str(file_path))

                # Analyze the AST
                patterns = self._analyze_ast(tree, file_path)
                anti_patterns.extend(patterns)

            except SyntaxError:
                pass  # Skip files with syntax errors
            except Exception:
                pass  # Skip files that can't be parsed

        self.results["ast_analysis"]["anti_patterns"] = anti_patterns
        self.results["ast_analysis"]["passed"] = len(anti_patterns) == 0

        print(f"Anti-patterns found: {len(anti_patterns)}")

        if anti_patterns:
            print("\n⚠️  ISSUES FOUND:")
            for pattern in anti_patterns[:10]:  # Show first 10
                print(f"  • {pattern['file']}:{pattern['line']} - {pattern['issue']}")

        print(f"Status: {'✅ PASS' if len(anti_patterns) == 0 else '⚠️  ANTI-PATTERNS DETECTED'}")

        return len(anti_patterns) == 0, anti_patterns

    def _analyze_ast(self, tree: ast.AST, file_path: Path) -> List[Dict]:
        """Analyze AST for common anti-patterns"""
        issues = []

        for node in ast.walk(tree):
            # 1. Bare except clauses
            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    issues.append({
                        "file": str(file_path.relative_to(self.root_dir)),
                        "line": node.lineno,
                        "issue": "Bare except: clause (should catch specific exceptions)"
                    })

            # 2. Use of eval() or exec()
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ['eval', 'exec']:
                        issues.append({
                            "file": str(file_path.relative_to(self.root_dir)),
                            "line": node.lineno,
                            "issue": f"Use of {node.func.id}() (security risk)"
                        })

            # 3. Functions with too many lines
            if isinstance(node, ast.FunctionDef):
                if hasattr(node, 'end_lineno'):
                    lines = node.end_lineno - node.lineno
                    if lines > 100:
                        issues.append({
                            "file": str(file_path.relative_to(self.root_dir)),
                            "line": node.lineno,
                            "issue": f"Function '{node.name}' is too long ({lines} lines)"
                        })

            # 4. Mutable default arguments
            if isinstance(node, ast.FunctionDef):
                for default in node.args.defaults:
                    if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                        issues.append({
                            "file": str(file_path.relative_to(self.root_dir)),
                            "line": node.lineno,
                            "issue": f"Mutable default argument in function '{node.name}'"
                        })

        return issues

    def generate_report(self) -> str:
        """Generate comprehensive report"""
        print("\n" + "="*70)
        print("📊 CODE QUALITY REPORT")
        print("="*70)

        # Summary
        all_passed = all(
            tool["passed"]
            for tool in self.results.values()
        )

        print(f"\n{'='*70}")
        print(f"OVERALL STATUS: {'✅ PASS' if all_passed else '❌ NEEDS IMPROVEMENT'}")
        print(f"{'='*70}\n")

        # Individual results
        print("PYLINT:")
        print(f"  Score: {self.results['pylint']['score']}/10.0")
        print(f"  Issues: {self.results['pylint']['issues']}")
        print(f"  Status: {'✅' if self.results['pylint']['passed'] else '❌'}")

        print("\nMYPY:")
        print(f"  Type errors: {self.results['mypy']['errors']}")
        print(f"  Status: {'✅' if self.results['mypy']['passed'] else '⚠️'}")

        print("\nBLACK:")
        print(f"  Files needing formatting: {self.results['black']['files_need_formatting']}")
        print(f"  Status: {'✅' if self.results['black']['passed'] else '⚠️'}")

        print("\nISO RT:")
        print(f"  Files needing import sorting: {self.results['isort']['files_need_sorting']}")
        print(f"  Status: {'✅' if self.results['isort']['passed'] else '⚠️'}")

        print("\nBANDIT:")
        print(f"  Total issues: {self.results['bandit']['issues']}")
        print(f"  High severity: {self.results['bandit']['severity_high']}")
        print(f"  Status: {'✅' if self.results['bandit']['passed'] else '❌'}")

        print("\nAST ANALYSIS:")
        print(f"  Anti-patterns: {len(self.results['ast_analysis']['anti_patterns'])}")
        print(f"  Status: {'✅' if self.results['ast_analysis']['passed'] else '⚠️'}")

        print(f"\n{'='*70}\n")

        return json.dumps(self.results, indent=2)

    def run_all(self) -> bool:
        """Run all quality checks"""
        print("\n" + "="*70)
        print("🚀 RUNNING COMPREHENSIVE CODE QUALITY CHECKS")
        print("="*70)

        self.run_pylint()
        self.run_mypy()
        self.run_black()
        self.run_isort()
        self.run_bandit()
        self.run_ast_analysis()

        report = self.generate_report()

        # Save report
        with open("code_quality_report.json", "w") as f:
            f.write(report)

        print("📄 Full report saved to: code_quality_report.json")

        # Return True if all critical checks passed
        return (
            self.results["pylint"]["passed"] and
            self.results["bandit"]["passed"]
        )


if __name__ == "__main__":
    checker = CodeQualityChecker()
    success = checker.run_all()

    sys.exit(0 if success else 1)
