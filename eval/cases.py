CASES = [
    # Core leave policy cases
    {"id": "policy_doctor_note", "query": "Do I need a doctor's note for 3 days sick leave?", "employee_id": "EMP101",
     "expected_tools": ["vector_search_hr_policy"], "answer_contains": ["doctor"]},
    {"id": "policy_casual_count", "query": "How many casual leaves per year?", "employee_id": "EMP101",
     "expected_tools": ["vector_search_hr_policy"], "answer_contains": ["12"]},
    {"id": "policy_wfh", "query": "What is the work from home policy?", "employee_id": "EMP101",
     "expected_tools": ["vector_search_hr_policy"], "answer_contains": ["4 days"]},
    {"id": "policy_maternity", "query": "How many weeks of maternity leave?", "employee_id": "EMP101",
     "expected_tools": ["vector_search_hr_policy"], "answer_contains": ["26"]},
    {"id": "policy_paternity", "query": "Paternity leave details", "employee_id": "EMP101",
     "expected_tools": ["vector_search_hr_policy"], "answer_contains": ["15"]},

    # Handbook governance & fringe policy cases
    {"id": "policy_probation_notice", "query": "What is the notice period during probation?", "employee_id": "EMP101",
     "expected_tools": ["vector_search_hr_policy"], "answer_contains": ["14"]},
    {"id": "policy_probation_wfh", "query": "Can I work from home during my 90-day probation?", "employee_id": "EMP101",
     "expected_tools": ["vector_search_hr_policy"], "answer_contains": ["probation"]},
    {"id": "policy_sabbatical", "query": "How many years of service do I need to take a sabbatical?", "employee_id": "EMP101",
     "expected_tools": ["vector_search_hr_policy"], "answer_contains": ["3"]},
    {"id": "policy_equipment_stipend", "query": "How much is the home office equipment allowance?", "employee_id": "EMP101",
     "expected_tools": ["vector_search_hr_policy"], "answer_contains": ["500"]},
    {"id": "policy_bereavement", "query": "How many days of bereavement leave for an immediate family member?", "employee_id": "EMP101",
     "expected_tools": ["vector_search_hr_policy"], "answer_contains": ["5"]},

    # Action / booking cases
    {"id": "action_casual_ok", "query": "Deduct 2 casual leave days starting 2026-06-10", "employee_id": "EMP101",
     "expected_tools": ["submit_leave_request"], "answer_contains": ["approved"]},
    {"id": "action_medical_ok", "query": "Book 1 medical leave starting 2026-07-01", "employee_id": "EMP101",
     "expected_tools": ["submit_leave_request"], "answer_contains": ["approved"]},
    {"id": "action_insufficient", "query": "Deduct 100 casual days starting 2026-06-10", "employee_id": "EMP101",
     "expected_tools": ["submit_leave_request"], "answer_contains": ["available"]},
    {"id": "missing_args", "query": "Book me leave next week", "employee_id": "EMP101",
     "expected_tools": [], "answer_contains": []},
]
