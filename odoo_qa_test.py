"""
Odoo QA Testing Script
Comprehensive testing of all Odoo modules and workflows
"""
import xmlrpc.client
from datetime import datetime, timedelta
import json
import sys

# Configuration
ODOO_URL = "http://51.20.91.45:8069"
ODOO_DB = "karem2"
ODOO_USERNAME = "karem.ceo@ailigent.ai"
ODOO_PASSWORD = "5066ea93f7ca68b38e55b153437958668fae7bd8"

# Test Results
test_results = {
    "passed": [],
    "failed": [],
    "warnings": [],
    "info": []
}

def log_result(category, message, details=None):
    """Log test result"""
    entry = {"message": message, "details": details, "timestamp": datetime.now().isoformat()}
    test_results[category].append(entry)
    symbol = {"passed": "[PASS]", "failed": "[FAIL]", "warnings": "[WARN]", "info": "[INFO]"}
    print(f"{symbol.get(category, '[----]')} {message}")
    if details:
        print(f"        Details: {details}")

def test_server_availability():
    """Test 1: Server Availability"""
    print("\n" + "="*60)
    print("TEST 1: SERVER AVAILABILITY")
    print("="*60)

    try:
        common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
        version = common.version()
        log_result("passed", f"Server is available", f"Odoo Version: {version.get('server_version', 'Unknown')}")
        log_result("info", f"Server Serie: {version.get('server_serie', 'Unknown')}")
        log_result("info", f"Protocol Version: {version.get('protocol_version', 'Unknown')}")
        return True, version
    except Exception as e:
        log_result("failed", f"Server not available", str(e))
        return False, None

def test_authentication():
    """Test 2: Authentication"""
    print("\n" + "="*60)
    print("TEST 2: AUTHENTICATION")
    print("="*60)

    try:
        common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
        uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})

        if uid:
            log_result("passed", f"Authentication successful", f"User ID: {uid}")
            return uid
        else:
            log_result("failed", "Authentication failed - Invalid credentials")
            return None
    except Exception as e:
        log_result("failed", f"Authentication error", str(e))
        return None

def get_models(models, uid):
    """Get object proxy for RPC calls"""
    return xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')

def test_installed_modules(models, uid):
    """Test 3: Explore Installed Modules"""
    print("\n" + "="*60)
    print("TEST 3: INSTALLED MODULES")
    print("="*60)

    try:
        modules = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'ir.module.module', 'search_read',
            [[['state', '=', 'installed']]],
            {'fields': ['name', 'shortdesc', 'state'], 'order': 'name'}
        )

        log_result("passed", f"Found {len(modules)} installed modules")

        # Categorize key modules
        key_modules = {
            'hr': None, 'hr_holidays': None, 'hr_attendance': None,
            'hr_recruitment': None, 'hr_payroll': None, 'project': None,
            'hr_contract': None, 'hr_appraisal': None, 'mail': None
        }

        for mod in modules:
            if mod['name'] in key_modules:
                key_modules[mod['name']] = mod['shortdesc']

        print("\nKey Module Status:")
        for mod_name, desc in key_modules.items():
            if desc:
                log_result("info", f"  {mod_name}: INSTALLED ({desc})")
            else:
                log_result("warnings", f"  {mod_name}: NOT INSTALLED")

        return modules, key_modules
    except Exception as e:
        log_result("failed", f"Failed to get modules", str(e))
        return [], {}

def test_model_access(models, uid, model_name):
    """Test model access rights"""
    try:
        # Check read access
        can_read = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            model_name, 'check_access_rights',
            ['read'], {'raise_exception': False}
        )
        # Check write access
        can_write = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            model_name, 'check_access_rights',
            ['write'], {'raise_exception': False}
        )
        # Check create access
        can_create = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            model_name, 'check_access_rights',
            ['create'], {'raise_exception': False}
        )
        return {'read': can_read, 'write': can_write, 'create': can_create}
    except Exception as e:
        return {'error': str(e)}

def test_hr_module(models, uid):
    """Test 4: HR Module"""
    print("\n" + "="*60)
    print("TEST 4: HR MODULE")
    print("="*60)

    # Test hr.employee model
    try:
        # Check access rights
        access = test_model_access(models, uid, 'hr.employee')
        log_result("info", f"hr.employee access rights: {access}")

        # Get employees
        employees = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'hr.employee', 'search_read',
            [[]],
            {'fields': ['name', 'job_title', 'department_id', 'work_email', 'parent_id'], 'limit': 50}
        )

        log_result("passed", f"Found {len(employees)} employees")

        # Print employee summary
        print("\nEmployee Summary:")
        for emp in employees[:10]:
            dept = emp.get('department_id', [False, 'No Dept'])
            dept_name = dept[1] if dept else 'No Department'
            log_result("info", f"  - {emp['name']} | {emp.get('job_title') or 'No Title'} | {dept_name}")

        if len(employees) > 10:
            print(f"  ... and {len(employees) - 10} more employees")

        return employees
    except Exception as e:
        log_result("failed", f"HR Module test failed", str(e))
        return []

def test_departments(models, uid):
    """Test 5: Departments"""
    print("\n" + "="*60)
    print("TEST 5: DEPARTMENTS")
    print("="*60)

    try:
        departments = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'hr.department', 'search_read',
            [[]],
            {'fields': ['name', 'manager_id', 'parent_id', 'member_ids']}
        )

        log_result("passed", f"Found {len(departments)} departments")

        for dept in departments:
            manager = dept.get('manager_id', [False, 'No Manager'])
            manager_name = manager[1] if manager else 'No Manager'
            member_count = len(dept.get('member_ids', []))
            log_result("info", f"  - {dept['name']} | Manager: {manager_name} | Members: {member_count}")

        return departments
    except Exception as e:
        log_result("failed", f"Department test failed", str(e))
        return []

def test_leave_management(models, uid):
    """Test 6: Leave Management"""
    print("\n" + "="*60)
    print("TEST 6: LEAVE MANAGEMENT (hr.leave)")
    print("="*60)

    try:
        # Check if model exists
        access = test_model_access(models, uid, 'hr.leave')
        if 'error' in access:
            log_result("warnings", "hr.leave model not accessible", access['error'])
            return []

        log_result("info", f"hr.leave access rights: {access}")

        # Get leave types
        leave_types = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'hr.leave.type', 'search_read',
            [[]],
            {'fields': ['name', 'requires_allocation', 'allocation_type']}
        )
        log_result("passed", f"Found {len(leave_types)} leave types")
        for lt in leave_types:
            log_result("info", f"  - {lt['name']} | Requires Allocation: {lt.get('requires_allocation', 'N/A')}")

        # Get leave requests
        leaves = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'hr.leave', 'search_read',
            [[]],
            {'fields': ['employee_id', 'holiday_status_id', 'date_from', 'date_to', 'state', 'number_of_days'], 'limit': 20}
        )

        log_result("passed", f"Found {len(leaves)} leave requests")

        # Count by state
        states = {}
        for leave in leaves:
            state = leave.get('state', 'unknown')
            states[state] = states.get(state, 0) + 1

        print("\nLeave Requests by State:")
        for state, count in states.items():
            log_result("info", f"  - {state}: {count}")

        return leaves
    except Exception as e:
        log_result("failed", f"Leave management test failed", str(e))
        return []

def test_attendance(models, uid):
    """Test 7: Attendance Module"""
    print("\n" + "="*60)
    print("TEST 7: ATTENDANCE MODULE")
    print("="*60)

    try:
        access = test_model_access(models, uid, 'hr.attendance')
        if 'error' in access:
            log_result("warnings", "hr.attendance model not accessible", access['error'])
            return []

        log_result("info", f"hr.attendance access rights: {access}")

        # Get recent attendance records
        attendances = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'hr.attendance', 'search_read',
            [[]],
            {'fields': ['employee_id', 'check_in', 'check_out', 'worked_hours'], 'limit': 20, 'order': 'check_in desc'}
        )

        log_result("passed", f"Found {len(attendances)} attendance records")

        # Sample records
        for att in attendances[:5]:
            emp = att.get('employee_id', [0, 'Unknown'])
            emp_name = emp[1] if emp else 'Unknown'
            log_result("info", f"  - {emp_name} | In: {att.get('check_in')} | Out: {att.get('check_out')} | Hours: {att.get('worked_hours', 0):.2f}")

        return attendances
    except Exception as e:
        log_result("failed", f"Attendance test failed", str(e))
        return []

def test_project_tasks(models, uid):
    """Test 8: Project & Tasks"""
    print("\n" + "="*60)
    print("TEST 8: PROJECT & TASKS")
    print("="*60)

    try:
        # Test projects
        projects = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'project.project', 'search_read',
            [[]],
            {'fields': ['name', 'user_id', 'partner_id', 'task_count']}
        )

        log_result("passed", f"Found {len(projects)} projects")
        for proj in projects:
            user = proj.get('user_id', [0, 'No Manager'])
            user_name = user[1] if user else 'No Manager'
            log_result("info", f"  - {proj['name']} | Manager: {user_name} | Tasks: {proj.get('task_count', 0)}")

        # Test tasks
        tasks = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'project.task', 'search_read',
            [[]],
            {'fields': ['name', 'project_id', 'user_ids', 'stage_id', 'date_deadline', 'priority'], 'limit': 30}
        )

        log_result("passed", f"Found {len(tasks)} tasks")

        # Tasks by stage
        stages = {}
        for task in tasks:
            stage = task.get('stage_id', [0, 'No Stage'])
            stage_name = stage[1] if stage else 'No Stage'
            stages[stage_name] = stages.get(stage_name, 0) + 1

        print("\nTasks by Stage:")
        for stage, count in stages.items():
            log_result("info", f"  - {stage}: {count}")

        # Check overdue tasks
        today = datetime.now().strftime('%Y-%m-%d')
        overdue = [t for t in tasks if t.get('date_deadline') and t['date_deadline'] < today]
        if overdue:
            log_result("warnings", f"Found {len(overdue)} overdue tasks")
        else:
            log_result("passed", "No overdue tasks found")

        return tasks
    except Exception as e:
        log_result("failed", f"Project/Tasks test failed", str(e))
        return []

def test_recruitment(models, uid):
    """Test 9: Recruitment Module"""
    print("\n" + "="*60)
    print("TEST 9: RECRUITMENT MODULE")
    print("="*60)

    try:
        # Test job positions
        jobs = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'hr.job', 'search_read',
            [[]],
            {'fields': ['name', 'department_id', 'no_of_recruitment', 'state']}
        )

        log_result("passed", f"Found {len(jobs)} job positions")
        for job in jobs:
            dept = job.get('department_id', [0, 'No Dept'])
            dept_name = dept[1] if dept else 'No Dept'
            log_result("info", f"  - {job['name']} | Dept: {dept_name} | Open: {job.get('no_of_recruitment', 0)}")

        # Test applicants
        applicants = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'hr.applicant', 'search_read',
            [[]],
            {'fields': ['name', 'partner_name', 'job_id', 'stage_id', 'email_from'], 'limit': 20}
        )

        log_result("passed", f"Found {len(applicants)} applicants")

        return jobs, applicants
    except Exception as e:
        log_result("warnings", f"Recruitment module test failed (may not be installed)", str(e))
        return [], []

def test_crud_operations(models, uid):
    """Test 10: CRUD Operations"""
    print("\n" + "="*60)
    print("TEST 10: CRUD OPERATIONS TEST")
    print("="*60)

    # Test Create, Read, Update, Delete on a safe model (project.task)
    try:
        # CREATE a test task
        test_task_id = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'project.task', 'create',
            [{'name': 'QA Test Task - DELETE ME', 'description': 'Created by QA automation test'}]
        )
        log_result("passed", f"CREATE: Task created with ID {test_task_id}")

        # READ the task
        task = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'project.task', 'read',
            [test_task_id],
            {'fields': ['name', 'description']}
        )
        log_result("passed", f"READ: Task retrieved - {task[0]['name']}")

        # UPDATE the task
        models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'project.task', 'write',
            [[test_task_id], {'name': 'QA Test Task - UPDATED'}]
        )
        log_result("passed", f"UPDATE: Task updated successfully")

        # DELETE the task
        models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'project.task', 'unlink',
            [[test_task_id]]
        )
        log_result("passed", f"DELETE: Task deleted successfully")

        log_result("passed", "All CRUD operations working correctly")
        return True
    except Exception as e:
        log_result("failed", f"CRUD operations test failed", str(e))
        return False

def test_user_permissions(models, uid):
    """Test 11: User Permissions"""
    print("\n" + "="*60)
    print("TEST 11: USER & PERMISSIONS")
    print("="*60)

    try:
        # Get current user info
        user = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'res.users', 'read',
            [uid],
            {'fields': ['name', 'login', 'groups_id', 'company_id']}
        )

        log_result("passed", f"Current User: {user[0]['name']} ({user[0]['login']})")
        log_result("info", f"User belongs to {len(user[0].get('groups_id', []))} groups")

        # Get groups
        group_ids = user[0].get('groups_id', [])
        if group_ids:
            groups = models.execute_kw(
                ODOO_DB, uid, ODOO_PASSWORD,
                'res.groups', 'read',
                [group_ids[:20]],  # Limit to first 20 groups
                {'fields': ['name', 'full_name']}
            )

            print("\nUser Groups (first 20):")
            for group in groups:
                log_result("info", f"  - {group.get('full_name', group['name'])}")

        return user
    except Exception as e:
        log_result("failed", f"User permissions test failed", str(e))
        return []

def test_ir_config_parameters(models, uid):
    """Test 12: System Configuration"""
    print("\n" + "="*60)
    print("TEST 12: SYSTEM CONFIGURATION (ir.config_parameter)")
    print("="*60)

    try:
        # Get telegram links (custom parameters)
        params = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'ir.config_parameter', 'search_read',
            [[['key', 'like', 'telegram_link%']]],
            {'fields': ['key', 'value']}
        )

        if params:
            log_result("passed", f"Found {len(params)} Telegram link parameters")
            for param in params:
                log_result("info", f"  - {param['key']}: {param['value']}")
        else:
            log_result("info", "No Telegram links configured yet")

        # Get web.base.url
        base_url = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'ir.config_parameter', 'search_read',
            [[['key', '=', 'web.base.url']]],
            {'fields': ['key', 'value']}
        )
        if base_url:
            log_result("info", f"Web Base URL: {base_url[0]['value']}")

        return params
    except Exception as e:
        log_result("failed", f"System configuration test failed", str(e))
        return []

def test_mail_module(models, uid):
    """Test 13: Mail Module"""
    print("\n" + "="*60)
    print("TEST 13: MAIL MODULE")
    print("="*60)

    try:
        # Check mail templates
        templates = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'mail.template', 'search_read',
            [[]],
            {'fields': ['name', 'model_id', 'subject'], 'limit': 10}
        )

        log_result("passed", f"Found {len(templates)} mail templates")
        for tpl in templates[:5]:
            model = tpl.get('model_id', [0, 'No Model'])
            model_name = model[1] if model else 'No Model'
            log_result("info", f"  - {tpl['name']} | Model: {model_name}")

        return templates
    except Exception as e:
        log_result("warnings", f"Mail module test failed", str(e))
        return []

def test_leave_allocations(models, uid):
    """Test 14: Leave Allocations"""
    print("\n" + "="*60)
    print("TEST 14: LEAVE ALLOCATIONS")
    print("="*60)

    try:
        allocations = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'hr.leave.allocation', 'search_read',
            [[]],
            {'fields': ['employee_id', 'holiday_status_id', 'number_of_days', 'state'], 'limit': 30}
        )

        log_result("passed", f"Found {len(allocations)} leave allocations")

        # Group by leave type
        by_type = {}
        for alloc in allocations:
            leave_type = alloc.get('holiday_status_id', [0, 'Unknown'])
            type_name = leave_type[1] if leave_type else 'Unknown'
            if type_name not in by_type:
                by_type[type_name] = {'count': 0, 'total_days': 0}
            by_type[type_name]['count'] += 1
            by_type[type_name]['total_days'] += alloc.get('number_of_days', 0)

        print("\nAllocations by Leave Type:")
        for type_name, data in by_type.items():
            log_result("info", f"  - {type_name}: {data['count']} allocations, {data['total_days']} total days")

        return allocations
    except Exception as e:
        log_result("warnings", f"Leave allocations test failed", str(e))
        return []

def generate_summary():
    """Generate final test summary"""
    print("\n" + "="*60)
    print("FINAL TEST SUMMARY")
    print("="*60)

    total = len(test_results['passed']) + len(test_results['failed']) + len(test_results['warnings'])

    print(f"\nRESULTS:")
    print(f"   PASSED:   {len(test_results['passed'])}")
    print(f"   FAILED:   {len(test_results['failed'])}")
    print(f"   WARNINGS: {len(test_results['warnings'])}")
    print(f"   INFO:     {len(test_results['info'])}")
    print(f"   -------------")
    print(f"   Total Tests: {total}")

    if test_results['failed']:
        print("\nFAILURES REQUIRING ATTENTION:")
        for fail in test_results['failed']:
            print(f"   * {fail['message']}")
            if fail.get('details'):
                print(f"     Details: {fail['details']}")

    if test_results['warnings']:
        print("\nWARNINGS (may need attention):")
        for warn in test_results['warnings']:
            print(f"   * {warn['message']}")

    # Calculate pass rate
    if total > 0:
        pass_rate = (len(test_results['passed']) / total) * 100
        print(f"\nPass Rate: {pass_rate:.1f}%")

    return test_results

def main():
    """Main QA test runner"""
    print("="*60)
    print("ODOO QA TESTING SUITE")
    print(f"Target: {ODOO_URL}")
    print(f"Database: {ODOO_DB}")
    print(f"Started: {datetime.now().isoformat()}")
    print("="*60)

    # Test 1: Server availability
    available, version = test_server_availability()
    if not available:
        print("\n⛔ Server not available. Aborting tests.")
        return generate_summary()

    # Test 2: Authentication
    uid = test_authentication()
    if not uid:
        print("\n⛔ Authentication failed. Aborting tests.")
        return generate_summary()

    # Get models proxy
    models = get_models(None, uid)

    # Test 3: Installed Modules
    modules, key_modules = test_installed_modules(models, uid)

    # Test 4: HR Module
    employees = test_hr_module(models, uid)

    # Test 5: Departments
    departments = test_departments(models, uid)

    # Test 6: Leave Management
    leaves = test_leave_management(models, uid)

    # Test 7: Attendance
    attendances = test_attendance(models, uid)

    # Test 8: Project & Tasks
    tasks = test_project_tasks(models, uid)

    # Test 9: Recruitment
    jobs, applicants = test_recruitment(models, uid)

    # Test 10: CRUD Operations
    crud_ok = test_crud_operations(models, uid)

    # Test 11: User Permissions
    user = test_user_permissions(models, uid)

    # Test 12: System Configuration
    config = test_ir_config_parameters(models, uid)

    # Test 13: Mail Module
    mail = test_mail_module(models, uid)

    # Test 14: Leave Allocations
    allocations = test_leave_allocations(models, uid)

    # Generate summary
    return generate_summary()

if __name__ == "__main__":
    results = main()
