"""Dead Regulation Detector - Main analysis engine."""

from typing import Dict, List
import json
import time
import sys
import os
import html
import re
from difflib import SequenceMatcher, ndiff
sys.path.append(str(os.path.dirname(os.path.dirname(__file__))))


class DeadRegulationDetector:
    """Main engine for detecting dead regulations."""
    
    def __init__(self, ai_client=None):
        """Initialize detector with AI client."""
        self.ai_client = ai_client
        
        # Known patterns of dead regulations
        self.outdated_terms = [
            "Министерство связи и информации",
            "Агентство по статистике",
            "Министерство индустрии и новых технологий",
            # Add more known outdated entities
        ]
        self.article_pattern = r"(Статья\s+\d+[^\n]*)([\s\S]*?)(?=Статья\s+\d+|$)"
    
    def analyze_document(self, document: Dict) -> Dict:
        """
        Analyze a legal document for dead regulations.
        
        Args:
            document: Document dict with 'full_text' and metadata
            
        Returns:
            Analysis results with detected issues
        """
        text = document.get('full_text', '')
        title = document.get('title', 'Untitled')
        
        results = {
            "document_id": document.get('id', 'unknown'),
            "document_title": title,
            "analyzed_at": self._get_timestamp(),
            "issues_found": [],
            "severity_score": 0,
            "has_critical_issues": False,
            "law_dependencies": [],
            "risk_assessment": {},
            "timeline_points": []
        }
        
        # 1. Check for outdated terms
        outdated_issues = self._check_outdated_terms(text)
        results['issues_found'].extend(outdated_issues)
        
        # 2. Use AI for deeper analysis if available
        if self.ai_client and self.ai_client.is_available():
            results["ai_used"] = True
            results["ai_provider"] = getattr(self.ai_client, "provider", None)
            results["ai_model"] = getattr(self.ai_client, "model", None)
            results["ai_latency_sec"] = 0.0
            results["ai_issues_added"] = 0
            try:
                ai_started = time.time()
                ai_analysis = self.ai_client.detect_dead_regulations(text, title)
                results["ai_latency_sec"] = round(time.time() - ai_started, 2)
                ai_issues = ai_analysis.get('issues', [])
                if ai_issues:
                    for issue in ai_issues:
                        issue["detected_by"] = "ai"
                    results['issues_found'].extend(ai_issues)
                    results["ai_issues_added"] = len(ai_issues)
                results['ai_summary'] = ai_analysis.get('summary', '')
                if ai_analysis.get("error"):
                    results["ai_error"] = ai_analysis.get("error")
                # Add AI metadata for transparency
                results['ai_metadata'] = {
                    'chunks_analyzed': ai_analysis.get('chunks_analyzed', 1),
                    'total_length': ai_analysis.get('total_length', len(text))
                }
            except Exception as e:
                results['ai_error'] = str(e)
        elif self.ai_client:
            results['ai_note'] = "AI анализ недоступен (нет API ключа)"
        
        # 3. Calculate severity score
        results['severity_score'] = self._calculate_severity(results['issues_found'])
        results['has_critical_issues'] = any(
            issue.get('severity') == 'High' for issue in results['issues_found']
        )
        
        # 4. Extract law dependencies
        results['law_dependencies'] = self._extract_law_dependencies(text)
        
        # 5. Assess legal risks
        results['risk_assessment'] = self._assess_legal_risks(results['issues_found'], text)
        
        # 6. Extract timeline points
        results['timeline_points'] = self._extract_timeline_points(text)
        
        return results
    
    def _check_outdated_terms(self, text: str) -> List[Dict]:
        """Check for known outdated terms."""
        issues = []
        
        for term in self.outdated_terms:
            if term.lower() in text.lower():
                # Find full logical block (paragraph) around the term
                idx = text.lower().find(term.lower())
                para_start = text.rfind("\n\n", 0, idx)
                para_end = text.find("\n\n", idx)
                if para_start == -1:
                    para_start = 0
                else:
                    para_start += 2
                if para_end == -1:
                    para_end = len(text)
                context = text[para_start:para_end].strip()
                if not context:
                    context = text[max(0, idx - 400):min(len(text), idx + len(term) + 400)]
                
                issues.append({
                    "type": "outdated_terms",
                    "term": term,
                    "quote": context,
                    "explanation": f"Упоминание '{term}' - организация была упразднена или переименована",
                    "severity": "High",
                    "recommendation": "Проверить актуальность нормы и обновить ссылки на действующие органы",
                    "detected_by": "rules"
                })
        
        return issues
    
    def _calculate_severity(self, issues: List[Dict]) -> int:
        """Calculate overall severity score (0-100)."""
        if not issues:
            return 0
        
        severity_weights = {
            'High': 30,
            'Medium': 15,
            'Low': 5
        }
        
        total_score = sum(
            severity_weights.get(issue.get('severity', 'Low'), 5)
            for issue in issues
        )
        
        return min(100, total_score)
    
    def _extract_law_dependencies(self, text: str) -> List[Dict]:
        """Extract references to other laws and regulations."""
        dependencies = []
        
        # Patterns for different types of legal references
        patterns = [
            # Law references: Закон РК "О ..."
            (r'Закон[а-я\s]*(?:Республики Казахстан|РК)["\s]+[^"]+["\s]+от\s+(\d+\s+[а-я]+\s+\d{4})',
             'law_reference', 'Закон РК'),
            # Code references: Кодекс РК "О ..."  
            (r'Кодекс[а-я\s]*(?:Республики Казахстан|РК)["\s]+[^"]+["\s]+от\s+(\d+\s+[а-я]+\s+\d{4})',
             'code_reference', 'Кодекс РК'),
            # Article references: статья 123, ст. 45
            (r'(?:статья|статьи|ст\.)\s+(\d+(?:\s*-\s*\d+)?)',
             'article_reference', 'Статья'),
            # Section references: пункт 3, часть 2
            (r'(?:пункт|пункта|п\.)\s+(\d+)',
             'section_reference', 'Пункт'),
        ]
        
        for pattern, dep_type, label in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                # Get context around the match
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 60)
                context = text[start:end].strip()
                
                dependencies.append({
                    'type': dep_type,
                    'reference': match.group(0),
                    'details': match.group(1) if match.groups() else match.group(0),
                    'context': context,
                    'position': match.start()
                })
        
        # Deduplicate based on reference text and approximate position
        seen = set()
        unique_deps = []
        for dep in dependencies:
            key = (dep['type'], dep['reference'], dep['position'] // 100)
            if key not in seen:
                seen.add(key)
                unique_deps.append(dep)
        
        return unique_deps[:50]  # Limit to 50 dependencies
    
    def _assess_legal_risks(self, issues: List[Dict], text: str) -> Dict:
        """Assess legal risks based on detected issues."""
        risk_categories = {
            'compliance': {'score': 0, 'label': 'Соответствие законодательству'},
            'enforcement': {'score': 0, 'label': 'Применимость на практике'},
            'legal_certainty': {'score': 0, 'label': 'Правовая определенность'},
            'reputation': {'score': 0, 'label': 'Репутационный риск'},
            'operational': {'score': 0, 'label': 'Операционный риск'}
        }
        
        # Score each issue type
        for issue in issues:
            issue_type = issue.get('type', '')
            severity = issue.get('severity', 'Low')
            
            if issue_type == 'outdated_terms':
                risk_categories['compliance']['score'] += 15 if severity == 'High' else 8
                risk_categories['enforcement']['score'] += 10 if severity == 'High' else 5
                risk_categories['reputation']['score'] += 8
            elif issue_type == 'contradiction':
                risk_categories['legal_certainty']['score'] += 20 if severity == 'High' else 12
                risk_categories['compliance']['score'] += 10
            elif issue_type == 'duplication':
                risk_categories['legal_certainty']['score'] += 10
                risk_categories['operational']['score'] += 8
            elif issue_type == 'inapplicability':
                risk_categories['enforcement']['score'] += 15 if severity == 'High' else 10
                risk_categories['operational']['score'] += 10
        
        # Cap scores at 100
        for category in risk_categories.values():
            category['score'] = min(100, category['score'])
        
        # Calculate overall risk
        overall_risk = sum(cat['score'] for cat in risk_categories.values()) / len(risk_categories)
        
        # Determine risk level
        if overall_risk >= 70:
            risk_level = 'critical'
            risk_label = 'Критический'
        elif overall_risk >= 50:
            risk_level = 'high'
            risk_label = 'Высокий'
        elif overall_risk >= 30:
            risk_level = 'medium'
            risk_label = 'Средний'
        else:
            risk_level = 'low'
            risk_label = 'Низкий'
        
        # Generate recommendations
        recommendations = []
        if risk_categories['compliance']['score'] > 40:
            recommendations.append({
                'priority': 'High',
                'text': 'Срочно проверить соответствие текущему законодательству'
            })
        if risk_categories['legal_certainty']['score'] > 30:
            recommendations.append({
                'priority': 'Medium',
                'text': 'Уточнить правовую определенность норм'
            })
        if risk_categories['enforcement']['score'] > 40:
            recommendations.append({
                'priority': 'High',
                'text': 'Оценить применимость норм в текущих условиях'
            })
        
        return {
            'overall_risk': round(overall_risk, 1),
            'risk_level': risk_level,
            'risk_label': risk_label,
            'categories': risk_categories,
            'recommendations': recommendations
        }
    
    def _extract_timeline_points(self, text: str) -> List[Dict]:
        """Extract timeline points (years) from document text."""
        timeline = []
        
        # Pattern for years (1991-2099)
        year_pattern = r'\b(19\d{2}|20\d{2})\b'
        
        for match in re.finditer(year_pattern, text):
            year = int(match.group(1))
            # Get context
            start = max(0, match.start() - 40)
            end = min(len(text), match.end() + 40)
            context = text[start:end].strip()
            
            timeline.append({
                'year': year,
                'context': context,
                'position': match.start()
            })
        
        # Deduplicate and sort
        seen_years = {}
        for point in timeline:
            year = point['year']
            if year not in seen_years:
                seen_years[year] = point
        
        return sorted(seen_years.values(), key=lambda x: x['year'])
    
    def _get_timestamp(self):
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def batch_analyze(self, documents: List[Dict]) -> List[Dict]:
        """Analyze multiple documents."""
        results = []
        
        for i, doc in enumerate(documents, 1):
            print(f"📄 Analyzing {i}/{len(documents)}: {doc.get('title', 'Unknown')}")
            result = self.analyze_document(doc)
            results.append(result)
        
        return results

    def compare_versions(self, old_text: str, new_text: str) -> Dict:
        """Compare two versions with section-based AND line-based analysis."""
        import re
        
        # Light normalization only (preserve structure)
        def light_normalize(text: str) -> str:
            """Light normalization - only standardize line breaks and trim."""
            text = re.sub(r'\r\n?', '\n', text)
            text = text.strip()
            return text
        
        # Normalize lightly
        old_text_norm = light_normalize(old_text)
        new_text_norm = light_normalize(new_text)
        
        # Extract sections (статьи, главы, разделы)
        old_sections = self._extract_sections(old_text_norm)
        new_sections = self._extract_sections(new_text_norm)
        
        # Compare sections
        section_changes = self._compare_sections(old_sections, new_sections)
        
        # Line-by-line comparison (keep structure)
        old_lines = [l.strip() for l in old_text_norm.splitlines() if l.strip()]
        new_lines = [l.strip() for l in new_text_norm.splitlines() if l.strip()]
        
        # Calculate basic similarity
        ratio = SequenceMatcher(None, "\n".join(old_lines), "\n".join(new_lines)).ratio()
        
        # Find exact matches and differences
        old_set = set(old_lines)
        new_set = set(new_lines)
        
        removed = [line for line in old_lines if line not in new_set]
        added = [line for line in new_lines if line not in old_set]
        
        # Find modified lines (similar but not identical)
        modified = []
        used_added = set()
        
        for r in removed:
            best_match = None
            best_score = 0.0
            best_idx = -1
            
            for idx, a in enumerate(added):
                if idx in used_added:
                    continue
                score = SequenceMatcher(None, r, a).ratio()
                if score > best_score and score >= 0.5:  # threshold for "modified"
                    best_score = score
                    best_match = a
                    best_idx = idx
            
            if best_match:
                modified.append({
                    "before": r,
                    "after": best_match,
                    "similarity": round(best_score * 100, 1)
                })
                used_added.add(best_idx)
        
        # Remove matched items from removed/added
        modified_before = {m['before'] for m in modified}
        modified_after = {m['after'] for m in modified}
        removed = [r for r in removed if r not in modified_before]
        added = [a for a in added if a not in modified_after]
        
        # Build visual diff blocks
        visual_blocks = self._build_visual_diff_blocks(old_lines, new_lines)
        
        # Generate diff preview
        diff_lines = list(ndiff(old_lines, new_lines))
        diff_preview = [line for line in diff_lines if line.startswith("+ ") or line.startswith("- ")]
        
        total_changes = len(removed) + len(added) + len(modified)

        return {
            "similarity": round(ratio * 100, 2),
            "total_changes": total_changes,
            "added_count": len(added),
            "removed_count": len(removed),
            "modified_count": len(modified),
            "added_examples": added,
            "removed_examples": removed,
            "modified_examples": modified,
            "diff_preview": diff_preview,
            "visual_blocks": visual_blocks,
            "section_changes": section_changes
        }
    
    def _extract_sections(self, text: str) -> List[Dict]:
        """Extract sections (статьи, главы, разделы) from legal text."""
        import re
        sections = []
        
        # Patterns for section headers
        patterns = [
            r'(Статья\s+\d+[а-яА-Я\d\-\.]*)\.\s*(.+)',
            r'(Глава\s+\d+[а-яА-Я\d\-\.]*)\.\s*(.+)',
            r'(Раздел\s+\d+[а-яА-Я\d\-\.]*)\.\s*(.+)',
            r'(Пункт\s+\d+[а-яА-Я\d\-\.]*)\.\s*(.+)',
        ]
        
        lines = text.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            matched = False
            for pattern in patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    # Save previous section
                    if current_section:
                        sections.append({
                            'number': current_section['number'],
                            'title': current_section['title'],
                            'content': ' '.join(current_content).strip()
                        })
                    
                    # Start new section
                    current_section = {
                        'number': match.group(1),
                        'title': match.group(2)
                    }
                    current_content = []
                    matched = True
                    break
            
            if not matched and current_section:
                current_content.append(line)
        
        # Save last section
        if current_section:
            sections.append({
                'number': current_section['number'],
                'title': current_section['title'],
                'content': ' '.join(current_content).strip()
            })
        
        return sections
    
    def _compare_sections(self, old_sections: List[Dict], new_sections: List[Dict]) -> Dict:
        """Compare sections between versions."""
        old_nums = {s['number']: s for s in old_sections}
        new_nums = {s['number']: s for s in new_sections}
        
        added_sections = []
        removed_sections = []
        modified_sections = []
        
        # Find removed sections
        for num in old_nums:
            if num not in new_nums:
                removed_sections.append(old_nums[num])
        
        # Find added and modified sections
        for num in new_nums:
            if num not in old_nums:
                added_sections.append(new_nums[num])
            else:
                # Compare content
                old_content = old_nums[num]['content']
                new_content = new_nums[num]['content']
                if old_content != new_content:
                    similarity = SequenceMatcher(None, old_content, new_content).ratio()
                    modified_sections.append({
                        'number': num,
                        'title': new_nums[num]['title'],
                        'old_content': old_content[:200],
                        'new_content': new_content[:200],
                        'similarity': round(similarity * 100, 1)
                    })
        
        return {
            'added': added_sections,
            'removed': removed_sections,
            'modified': modified_sections,
            'total_sections_old': len(old_sections),
            'total_sections_new': len(new_sections)
        }

    def _build_visual_diff_blocks(self, old_lines: List[str], new_lines: List[str]) -> List[Dict]:
        """Build visual diff blocks suitable for UI rendering."""
        matcher = SequenceMatcher(None, old_lines, new_lines)
        blocks: List[Dict] = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                for line in old_lines[i1:i2]:
                    blocks.append({"type": "equal", "old": line, "new": line})
            elif tag == "delete":
                for line in old_lines[i1:i2]:
                    blocks.append({"type": "removed", "old": line, "new": ""})
            elif tag == "insert":
                for line in new_lines[j1:j2]:
                    blocks.append({"type": "added", "old": "", "new": line})
            else:  # replace
                old_chunk = old_lines[i1:i2]
                new_chunk = new_lines[j1:j2]
                size = max(len(old_chunk), len(new_chunk))
                for idx in range(size):
                    old_line = old_chunk[idx] if idx < len(old_chunk) else ""
                    new_line = new_chunk[idx] if idx < len(new_chunk) else ""
                    old_h, new_h = self._highlight_inline_diff(old_line, new_line)
                    blocks.append({
                        "type": "modified",
                        "old": old_line,
                        "new": new_line,
                        "old_html": old_h,
                        "new_html": new_h,
                    })
        return blocks

    def _highlight_inline_diff(self, old_line: str, new_line: str) -> tuple:
        """Highlight word-level changes for modified lines."""
        old_tokens = old_line.split()
        new_tokens = new_line.split()
        matcher = SequenceMatcher(None, old_tokens, new_tokens)
        old_parts = []
        new_parts = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            old_text = html.escape(" ".join(old_tokens[i1:i2]))
            new_text = html.escape(" ".join(new_tokens[j1:j2]))
            if tag == "equal":
                if old_text:
                    old_parts.append(old_text)
                if new_text:
                    new_parts.append(new_text)
            elif tag == "delete":
                if old_text:
                    old_parts.append(f"<span style='background:#fee2e2;color:#991b1b'>{old_text}</span>")
            elif tag == "insert":
                if new_text:
                    new_parts.append(f"<span style='background:#dcfce7;color:#166534'>{new_text}</span>")
            else:
                if old_text:
                    old_parts.append(f"<span style='background:#fee2e2;color:#991b1b'>{old_text}</span>")
                if new_text:
                    new_parts.append(f"<span style='background:#dcfce7;color:#166534'>{new_text}</span>")
        return " ".join(old_parts), " ".join(new_parts)


# Test
if __name__ == "__main__":
    # Test without Claude
    detector = DeadRegulationDetector()
    
    test_doc = {
        "id": "test_001",
        "title": "О Министерстве связи",
        "full_text": """
        Статья 1. Министерство связи и информации Республики Казахстан 
        осуществляет регулирование в сфере телекоммуникаций.
        
        Примечание: данное министерство было упразднено в 2019 году.
        """
    }
    
    result = detector.analyze_document(test_doc)
    print(json.dumps(result, ensure_ascii=False, indent=2))
