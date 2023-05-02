import frappe
from frappe.model.mapper import get_mapped_doc


@frappe.whitelist()
def process_dr(source_name, target_doc=None):
    jr_entry = frappe.db.exists("Journal Entry Account",{"reference_type":"Sales Invoice","reference_name":source_name, "docstatus":1})
    if jr_entry:
        frappe.throw("Account is settled for this Trasaction!")
    def postprocess(source, doc):
        doc.type = "Income"

    doc = get_mapped_doc(
        "Sales Invoice",
        source_name,
        {
            "Sales Invoice": {
                "doctype": "Process Deferred Accounting",
                "validation": {"docstatus": ["=", 1]},
            },
        },
        target_doc,
        postprocess,
    )
    return doc