import json
import operator
from typing import Any

import streamlit as st


# ---------------------------------------------------------
# DEFAULT RULE CONFIGURATION
# Keep these five rules exactly as provided in Lab Report 3.
# ---------------------------------------------------------
DEFAULT_RULES = [
    {
        "name": "Top merit candidate",
        "priority": 100,
        "conditions": [
            ["cgpa", ">=", 3.7],
            ["co_curricular_score", ">=", 80],
            ["family_income", "<=", 8000],
            ["disciplinary_actions", "==", 0]
        ],
        "action": {
            "decision": "AWARD_FULL",
            "reason": "Excellent academic & co-curricular performance, with acceptable need"
        }
    },
    {
        "name": "Good candidate - partial scholarship",
        "priority": 80,
        "conditions": [
            ["cgpa", ">=", 3.3],
            ["co_curricular_score", ">=", 60],
            ["family_income", "<=", 12000],
            ["disciplinary_actions", "<=", 1]
        ],
        "action": {
            "decision": "AWARD_PARTIAL",
            "reason": "Good academic & involvement record with moderate need"
        }
    },
    {
        "name": "Need-based review",
        "priority": 70,
        "conditions": [
            ["cgpa", ">=", 2.5],
            ["family_income", "<=", 4000]
        ],
        "action": {
            "decision": "REVIEW",
            "reason": "High need but borderline academic score"
        }
    },
    {
        "name": "Low CGPA – not eligible",
        "priority": 95,
        "conditions": [
            ["cgpa", "<", 2.5]
        ],
        "action": {
            "decision": "REJECT",
            "reason": "CGPA below minimum scholarship requirement"
        }
    },
    {
        "name": "Serious disciplinary record",
        "priority": 90,
        "conditions": [
            ["disciplinary_actions", ">=", 2]
        ],
        "action": {
            "decision": "REJECT",
            "reason": "Too many disciplinary records"
        }
    }
]

DEFAULT_RULES_JSON = json.dumps(DEFAULT_RULES, indent=4, ensure_ascii=False)

# Supported comparison operators for the JSON rule engine.
OPERATORS = {
    "==": operator.eq,
    "!=": operator.ne,
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
}

# These are the applicant facts used by the supplied rules.
RULE_FIELDS = {
    "cgpa",
    "co_curricular_score",
    "family_income",
    "disciplinary_actions",
}


def validate_rules(rules: Any) -> None:
    """Check that the JSON configuration has the expected structure."""
    if not isinstance(rules, list) or not rules:
        raise ValueError("The rules configuration must be a non-empty JSON list.")

    required_rule_keys = {"name", "priority", "conditions", "action"}
    required_action_keys = {"decision", "reason"}

    for index, rule in enumerate(rules, start=1):
        if not isinstance(rule, dict):
            raise ValueError(f"Rule {index} must be a JSON object.")

        missing = required_rule_keys - set(rule.keys())
        if missing:
            raise ValueError(
                f"Rule {index} is missing required field(s): {', '.join(sorted(missing))}."
            )

        if not isinstance(rule["name"], str) or not rule["name"].strip():
            raise ValueError(f"Rule {index} must have a non-empty name.")

        if not isinstance(rule["priority"], (int, float)):
            raise ValueError(f"Priority for rule {index} must be a number.")

        if not isinstance(rule["conditions"], list) or not rule["conditions"]:
            raise ValueError(f"Rule {index} must contain at least one condition.")

        for condition_index, condition in enumerate(rule["conditions"], start=1):
            if not isinstance(condition, list) or len(condition) != 3:
                raise ValueError(
                    f"Condition {condition_index} in rule {index} must contain "
                    "[field, operator, value]."
                )

            field, comparison, expected_value = condition

            if field not in RULE_FIELDS:
                raise ValueError(
                    f"Unknown field '{field}' in rule {index}. "
                    f"Allowed fields: {', '.join(sorted(RULE_FIELDS))}."
                )

            if comparison not in OPERATORS:
                raise ValueError(
                    f"Unsupported operator '{comparison}' in rule {index}."
                )

            if isinstance(expected_value, bool) or not isinstance(
                expected_value, (int, float)
            ):
                raise ValueError(
                    f"The comparison value in rule {index} must be numeric."
                )

        if not isinstance(rule["action"], dict):
            raise ValueError(f"Action for rule {index} must be a JSON object.")

        missing_action = required_action_keys - set(rule["action"].keys())
        if missing_action:
            raise ValueError(
                f"Action in rule {index} is missing: "
                f"{', '.join(sorted(missing_action))}."
            )


def condition_is_true(condition: list, facts: dict) -> bool:
    """Evaluate one condition, for example: cgpa >= 3.7."""
    field, comparison, expected_value = condition
    return OPERATORS[comparison](facts[field], expected_value)


def rule_matches(rule: dict, facts: dict) -> bool:
    """A rule matches only when all its conditions are true (AND logic)."""
    return all(condition_is_true(condition, facts) for condition in rule["conditions"])


def evaluate_applicant(facts: dict, rules: list) -> dict:
    """
    Evaluate all rules and select the matching rule with the highest priority.
    If no rule matches, return NO_MATCH.
    """
    matching_rules = [
        rule for rule in rules if rule_matches(rule, facts)
    ]

    matching_rules.sort(key=lambda item: item["priority"], reverse=True)

    if not matching_rules:
        return {
            "decision": "NO_MATCH",
            "reason": (
                "The applicant does not match any configured scholarship rule. "
                "Further manual assessment may be required."
            ),
            "selected_rule": None,
            "matching_rules": [],
        }

    selected_rule = matching_rules[0]

    return {
        "decision": selected_rule["action"]["decision"],
        "reason": selected_rule["action"]["reason"],
        "selected_rule": selected_rule,
        "matching_rules": matching_rules,
    }


def decision_label(decision: str) -> str:
    labels = {
        "AWARD_FULL": "Full Scholarship",
        "AWARD_PARTIAL": "Partial Scholarship",
        "REVIEW": "Requires Committee Review",
        "REJECT": "Not Eligible",
        "NO_MATCH": "No Rule Matched",
    }
    return labels.get(decision, decision)


# ---------------------------------------------------------
# STREAMLIT USER INTERFACE
# ---------------------------------------------------------
st.set_page_config(
    page_title="Scholarship Advisory System",
    page_icon="🎓",
    layout="wide",
)

st.title("🎓 Scholarship Advisory System")
st.caption("A transparent rule-based decision support prototype")

st.markdown(
    """
This application evaluates scholarship applicants using an editable set of
**IF–THEN rules**. Enter the applicant's information, review the JSON rules,
and select **Evaluate Applicant** to obtain a recommendation.
"""
)

# JSON rule editor in the sidebar, as required by the assignment.
st.sidebar.header("Rule Configuration")
st.sidebar.write(
    "Review or edit the rules below. The editor is preloaded with the "
    "five rules supplied in Lab Report 3."
)

rules_json = st.sidebar.text_area(
    "JSON Rules Editor",
    value=DEFAULT_RULES_JSON,
    height=570,
    key="rules_json_editor",
)

if st.sidebar.button("Restore Original Rules"):
    st.session_state["rules_json_editor"] = DEFAULT_RULES_JSON
    st.rerun()

st.sidebar.caption(
    "Rule priority: the matching rule with the highest priority is selected."
)

# Applicant input form.
st.subheader("Applicant Information")

with st.form("applicant_form"):
    applicant_name = st.text_input("Applicant Name", placeholder="Enter applicant name")

    col1, col2 = st.columns(2)

    with col1:
        cgpa = st.number_input(
            "Cumulative GPA (CGPA)",
            min_value=0.0,
            max_value=4.0,
            value=3.50,
            step=0.01,
            format="%.2f",
            help="Enter a CGPA between 0.00 and 4.00.",
        )

        family_income = st.number_input(
            "Monthly Family Income",
            min_value=0.0,
            value=5000.0,
            step=100.0,
            help="Enter the monthly family income in your local currency.",
        )

        co_curricular_score = st.number_input(
            "Co-curricular Involvement Score",
            min_value=0,
            max_value=100,
            value=75,
            step=1,
            help="Enter a score between 0 and 100.",
        )

    with col2:
        community_service_hours = st.number_input(
            "Community Service Hours",
            min_value=0,
            value=20,
            step=1,
        )

        current_semester = st.number_input(
            "Current Semester",
            min_value=1,
            max_value=20,
            value=3,
            step=1,
        )

        disciplinary_actions = st.number_input(
            "Number of Disciplinary Actions",
            min_value=0,
            value=0,
            step=1,
        )

    submitted = st.form_submit_button(
        "Evaluate Applicant",
        type="primary",
        width="stretch",
    )


if submitted:
    # Parse and validate the JSON rules before evaluating the applicant.
    try:
        rules = json.loads(rules_json)
        validate_rules(rules)
    except json.JSONDecodeError as error:
        st.error(
            f"Invalid JSON syntax: {error.msg} "
            f"(line {error.lineno}, column {error.colno}). "
            "Please correct the JSON in the sidebar editor."
        )
        st.stop()
    except ValueError as error:
        st.error(f"Rule configuration error: {error}")
        st.stop()

    applicant_facts = {
        "cgpa": float(cgpa),
        "family_income": float(family_income),
        "co_curricular_score": int(co_curricular_score),
        "disciplinary_actions": int(disciplinary_actions),
    }

    result = evaluate_applicant(applicant_facts, rules)

    st.divider()
    st.subheader("Evaluation Result")

    if applicant_name.strip():
        st.write(f"**Applicant:** {applicant_name.strip()}")

    decision = result["decision"]
    label = decision_label(decision)

    if decision == "AWARD_FULL":
        st.success(f"Recommendation: {label}")
    elif decision == "AWARD_PARTIAL":
        st.success(f"Recommendation: {label}")
    elif decision == "REVIEW":
        st.warning(f"Recommendation: {label}")
    elif decision == "REJECT":
        st.error(f"Recommendation: {label}")
    else:
        st.info(f"Recommendation: {label}")

    st.write(f"**Reason:** {result['reason']}")

    if result["selected_rule"] is not None:
        st.write(f"**Selected Rule:** {result['selected_rule']['name']}")
        st.write(f"**Rule Priority:** {result['selected_rule']['priority']}")

    st.subheader("Applicant Facts")
    facts_for_display = {
        "CGPA": applicant_facts["cgpa"],
        "Monthly family income": applicant_facts["family_income"],
        "Co-curricular score": applicant_facts["co_curricular_score"],
        "Disciplinary actions": applicant_facts["disciplinary_actions"],
        "Community service hours": int(community_service_hours),
        "Current semester": int(current_semester),
    }
    st.table(
        {
            "Applicant Information": list(facts_for_display.keys()),
            "Value": list(facts_for_display.values()),
        }
    )

    st.subheader("Rule Evaluation Details")
    if result["matching_rules"]:
        st.write(
            "The following rules matched. The rule with the highest priority "
            "was selected."
        )
        for matched_rule in result["matching_rules"]:
            with st.expander(
                f"{matched_rule['name']} — Priority {matched_rule['priority']}"
            ):
                st.write(f"**Decision:** {matched_rule['action']['decision']}")
                st.write(f"**Reason:** {matched_rule['action']['reason']}")
                st.write("**Conditions:**")
                for condition in matched_rule["conditions"]:
                    st.code(
                        f"{condition[0]} {condition[1]} {condition[2]}",
                        language="text",
                    )
    else:
        st.info(
            "No configured rule matched this applicant. "
            "The case may be referred for manual assessment."
        )

    st.caption(
        "This is an advisory prototype. Final scholarship decisions should "
        "be reviewed and approved by the university scholarship committee."
    )

else:
    st.info(
        "Complete the applicant information and click **Evaluate Applicant** "
        "to see the scholarship recommendation."
    )

st.divider()
st.caption("Lab Report 3 | Knowledge Representation System | Rule-Based System")
