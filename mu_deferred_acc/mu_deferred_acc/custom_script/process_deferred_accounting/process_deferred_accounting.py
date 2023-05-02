# Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _

from mu_deferred_acc.mu_deferred_acc.custom_script.accounts.deferred_revenue import	build_conditions, convert_deferred_revenue_to_income_custom

from erpnext.accounts.deferred_revenue import (
	convert_deferred_expense_to_expense,
	convert_deferred_revenue_to_income,
)
from erpnext.accounts.doctype.process_deferred_accounting.process_deferred_accounting import ProcessDeferredAccounting

class custom_ProcessDeferredAccounting(ProcessDeferredAccounting):
	def on_submit(self):
		conditions = build_conditions(self.type, self.account, self.company, self.project)
		if self.type == "Income":
			convert_deferred_revenue_to_income_custom(self.name, self.company, self.project, self.start_date, self.end_date,conditions)
		else:
			convert_deferred_expense_to_expense(self.name, self.start_date, self.end_date, conditions)
