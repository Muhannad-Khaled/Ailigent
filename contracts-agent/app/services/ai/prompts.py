"""AI Prompt Templates for Contract Analysis."""

CONTRACT_SUMMARY_PROMPT = """Analyze this contract and provide a comprehensive summary including:
1. Executive summary (2-3 sentences)
2. Contract type and purpose
3. Key parties involved
4. Main obligations for each party
5. Financial terms and value
6. Important dates and deadlines
7. Key risks and concerns
8. Recommendations

Provide the response as a JSON object with these fields:
- summary: string
- contract_type: string
- parties: array of {name, role}
- obligations: array of {party, obligation}
- financial_terms: {value, currency, payment_schedule, penalties}
- important_dates: array of {type, date, description}
- risks: array of {level, description, mitigation}
- recommendations: array of strings
"""

CLAUSE_EXTRACTION_PROMPT = """Extract all distinct clauses from this contract document.

For each clause, identify:
1. clause_type: One of [payment_terms, delivery, warranty, liability, termination, confidentiality, penalty, renewal, force_majeure, compliance, indemnification, intellectual_property, dispute_resolution, governing_law, other]
2. title: A descriptive title for the clause
3. content: The full text of the clause
4. section_reference: The section number/reference if available (e.g., "Section 5.2", "Article III")

Return a JSON object with:
- clauses: array of extracted clauses
- total_count: number of clauses found

Important:
- Extract complete clause text, not summaries
- Identify implicit clauses even if not explicitly labeled
- Group related sub-clauses under their parent clause
"""

CLAUSE_RISK_ANALYSIS_PROMPT = """Analyze this contract clause for potential risks.

Evaluate:
1. Risk level: low, medium, high, or critical
2. Risk factors: Specific concerns with this clause
3. Key obligations: What actions are required
4. Key dates: Any deadlines or time-sensitive elements
5. Financial impact: Potential monetary implications
6. Recommendations: How to mitigate identified risks

Return a JSON object with:
- risk_level: string
- risk_factors: array of strings
- key_obligations: array of strings
- key_dates: array of {date_type, value, description}
- financial_impact: string or null
- recommendations: array of strings
- confidence: float (0-1)
"""

KEY_DATE_EXTRACTION_PROMPT = """Extract all important dates and deadlines from this contract.

For each date, identify:
1. date_type: One of [start, end, milestone, deadline, renewal, termination_notice, payment, delivery, review]
2. date_value: The actual date in ISO format (YYYY-MM-DD) or description if relative
3. description: What this date represents
4. is_recurring: true/false
5. notice_period: Number of days notice required, if applicable

Return a JSON object with:
- dates: array of date objects
- date_summary: Brief summary of the contract timeline
"""

COMPLIANCE_CHECK_PROMPT = """Check this contract clause against the following compliance requirement:

Requirement: {requirement}

Evaluate whether the clause:
1. Fully complies with the requirement
2. Partially complies (with gaps)
3. Does not comply
4. Is not applicable to this requirement

Return a JSON object with:
- status: compliant, partial, non_compliant, not_applicable
- assessment: Detailed explanation
- gaps: array of identified gaps (if any)
- recommendations: How to achieve full compliance
"""

CONTRACT_COMPARISON_PROMPT = """Compare these two contracts and identify:

1. Key differences in terms and conditions
2. More favorable terms in each contract
3. Missing clauses in either contract
4. Risk comparison
5. Recommendations for negotiation

Return a JSON object with:
- differences: array of {area, contract1, contract2, significance}
- favorable_terms: {contract1: array, contract2: array}
- missing_clauses: {contract1: array, contract2: array}
- risk_comparison: {contract1_risk_level, contract2_risk_level, analysis}
- recommendations: array of strings
"""

FINANCIAL_ANALYSIS_PROMPT = """Analyze the financial terms in this contract including:

1. Total contract value
2. Payment schedule and terms
3. Penalties and late fees
4. Price adjustment clauses
5. Hidden costs or ambiguous financial terms
6. Financial risks

Return a JSON object with:
- total_value: {amount, currency}
- payment_terms: {schedule, method, due_dates}
- penalties: array of {type, amount, trigger}
- price_adjustments: array of {type, mechanism, cap}
- hidden_costs: array of strings
- financial_risks: array of {risk, potential_impact, mitigation}
- recommendations: array of strings
"""

RISK_ASSESSMENT_PROMPT = """Perform a comprehensive risk assessment of this contract.

Evaluate risks in these categories:
1. Legal risks
2. Financial risks
3. Operational risks
4. Compliance risks
5. Reputational risks

For each risk, provide:
- Category
- Description
- Likelihood (low, medium, high)
- Impact (low, medium, high, critical)
- Mitigation strategies

Return a JSON object with:
- overall_risk_level: string
- risk_score: number (1-100)
- risks_by_category: object with category arrays
- critical_risks: array of most important risks
- mitigation_plan: array of recommended actions
- executive_summary: string
"""
