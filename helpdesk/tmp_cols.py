import frappe

def show_meta_fields():
    m = frappe.get_meta('HD Ticket')
    keys = ['client','coach','dietitian','dietician','resolution','plan','escalation','refund','concerned','secondary','yoga','mind','fitness','tech']
    for f in m.fields:
        fn = (f.fieldname or '')
        lb = (f.label or '')
        t = (fn + ' ' + lb).lower()
        if any(k in t for k in keys):
            print(fn, '|', lb, '|', f.fieldtype)
import frappe

FIELD_DEFS = [
    {'fieldname':'custom_current_dietitian','label':'Current Dietitian','fieldtype':'Data'},
    {'fieldname':'custom_yoga_coach','label':'Yoga Coach','fieldtype':'Data'},
    {'fieldname':'custom_mind_coach','label':'Mind Coach','fieldtype':'Data'},
    {'fieldname':'custom_fitness_coach','label':'Fitness Coach','fieldtype':'Data'},
    {'fieldname':'custom_tech','label':'Tech','fieldtype':'Data'},
    {'fieldname':'custom_escalation_source','label':'Escalation Source','fieldtype':'Select','options':'Email\nCall\nChat\nOther'},
    {'fieldname':'custom_dietician_change_request','label':'Dietician Change Request','fieldtype':'Check'},
    {'fieldname':'custom_refund_request','label':'Refund Request','fieldtype':'Check'},
    {'fieldname':'custom_secondary_issue','label':'Secondary Issue','fieldtype':'Data'},
    {'fieldname':'custom_concerned_coach_name','label':'Concerned Coach Name','fieldtype':'Data'},
    {'fieldname':'custom_plan_category','label':'Plan Category','fieldtype':'Data'},
    {'fieldname':'custom_plan_status','label':'Plan Status','fieldtype':'Data'},
    {'fieldname':'custom_plan_type','label':'Plan Type','fieldtype':'Data'},
]

def ensure_disposition_fields():
    for f in FIELD_DEFS:
        if frappe.db.exists('Custom Field', {'dt':'HD Ticket', 'fieldname': f['fieldname']}):
            continue
        doc = frappe.get_doc({
            'doctype':'Custom Field',
            'dt':'HD Ticket',
            'insert_after':'custom_concerned_person',
            **f,
        })
        doc.insert(ignore_permissions=True)
        print('Created', f['fieldname'])
    frappe.db.commit()
    print('Done')
