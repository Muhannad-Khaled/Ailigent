"""
Odoo 18 Field Structure Investigation
"""
import xmlrpc.client

ODOO_URL = "http://51.20.91.45:8069"
ODOO_DB = "karem2"
ODOO_USERNAME = "karem.ceo@ailigent.ai"
ODOO_PASSWORD = "5066ea93f7ca68b38e55b153437958668fae7bd8"

def get_model_fields(models, uid, model_name):
    """Get all fields for a model"""
    try:
        fields = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            model_name, 'fields_get',
            [],
            {'attributes': ['string', 'type', 'required']}
        )
        return fields
    except Exception as e:
        return {'error': str(e)}

def main():
    common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
    uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})
    models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')

    print("="*60)
    print("ODOO 18 FIELD STRUCTURE INVESTIGATION")
    print("="*60)

    # Check hr.leave.type fields
    print("\n--- hr.leave.type FIELDS ---")
    fields = get_model_fields(models, uid, 'hr.leave.type')
    if 'error' not in fields:
        for name, info in sorted(fields.items()):
            print(f"  {name}: {info.get('type')} - {info.get('string')}")
    else:
        print(f"Error: {fields['error']}")

    # Check hr.job fields
    print("\n--- hr.job FIELDS ---")
    fields = get_model_fields(models, uid, 'hr.job')
    if 'error' not in fields:
        for name, info in sorted(fields.items()):
            print(f"  {name}: {info.get('type')} - {info.get('string')}")
    else:
        print(f"Error: {fields['error']}")

    # Check hr.leave fields
    print("\n--- hr.leave FIELDS ---")
    fields = get_model_fields(models, uid, 'hr.leave')
    if 'error' not in fields:
        for name, info in sorted(fields.items()):
            print(f"  {name}: {info.get('type')} - {info.get('string')}")
    else:
        print(f"Error: {fields['error']}")

    # Check project.task stage fields
    print("\n--- project.task.type (Stage) FIELDS ---")
    fields = get_model_fields(models, uid, 'project.task.type')
    if 'error' not in fields:
        for name, info in sorted(fields.items()):
            print(f"  {name}: {info.get('type')} - {info.get('string')}")
    else:
        print(f"Error: {fields['error']}")

    # Get leave types actual data
    print("\n--- LEAVE TYPES DATA ---")
    try:
        leave_types = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'hr.leave.type', 'search_read',
            [[]],
            {'fields': ['name', 'requires_allocation'], 'limit': 10}
        )
        for lt in leave_types:
            print(f"  - {lt['name']} | Requires Allocation: {lt.get('requires_allocation')}")
    except Exception as e:
        print(f"Error: {e}")

    # Get leave requests actual data
    print("\n--- LEAVE REQUESTS DATA ---")
    try:
        leaves = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'hr.leave', 'search_read',
            [[]],
            {'fields': ['employee_id', 'holiday_status_id', 'date_from', 'date_to', 'state', 'number_of_days'], 'limit': 10}
        )
        print(f"Found {len(leaves)} leave requests")
        for leave in leaves[:5]:
            emp = leave.get('employee_id', [0, 'Unknown'])
            emp_name = emp[1] if emp else 'Unknown'
            leave_type = leave.get('holiday_status_id', [0, 'Unknown'])
            type_name = leave_type[1] if leave_type else 'Unknown'
            print(f"  - {emp_name} | {type_name} | {leave.get('date_from')} to {leave.get('date_to')} | {leave.get('state')}")
    except Exception as e:
        print(f"Error: {e}")

    # Get job positions actual data
    print("\n--- JOB POSITIONS DATA ---")
    try:
        jobs = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'hr.job', 'search_read',
            [[]],
            {'fields': ['name', 'department_id', 'no_of_recruitment'], 'limit': 10}
        )
        print(f"Found {len(jobs)} job positions")
        for job in jobs[:5]:
            dept = job.get('department_id', [0, 'Unknown'])
            dept_name = dept[1] if dept else 'No Dept'
            print(f"  - {job['name']} | {dept_name} | Open positions: {job.get('no_of_recruitment', 0)}")
    except Exception as e:
        print(f"Error: {e}")

    # Get applicants actual data
    print("\n--- APPLICANTS DATA ---")
    try:
        applicants = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'hr.applicant', 'search_read',
            [[]],
            {'fields': ['name', 'partner_name', 'job_id', 'stage_id', 'email_from'], 'limit': 10}
        )
        print(f"Found {len(applicants)} applicants")
        for app in applicants[:5]:
            job = app.get('job_id', [0, 'Unknown'])
            job_name = job[1] if job else 'No Job'
            stage = app.get('stage_id', [0, 'Unknown'])
            stage_name = stage[1] if stage else 'No Stage'
            print(f"  - {app.get('partner_name', app['name'])} | {job_name} | Stage: {stage_name}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
