import frappe
from frappe import _
from frappe.email import sendmail_to_system_managers
from frappe.utils import (
	add_days,
	add_months,
	cint,
	date_diff,
	flt,
	get_first_day,
	get_last_day,
	get_link_to_form,
	getdate,
	rounded,
	today,
)

from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
	get_accounting_dimensions,
)
from erpnext.accounts.utils import get_account_currency

def build_conditions(process_type, account, company, project):
	conditions = ""
	deferred_account = (
		"item.deferred_revenue_account" if process_type == "Income" else "item.deferred_expense_account"
	)

	if account:
		conditions += "AND %s='%s'" % (deferred_account, account)
	elif company:
		conditions += f"AND p.company = {frappe.db.escape(company)}"
    
	if project:
		conditions += f" AND p.project = '{project}'"
	
	print(f"\n\n\n\nconditions: {conditions}\n\n\n")
	return conditions


def convert_deferred_revenue_to_income_custom(
	deferred_process, company, project, start_date=None, end_date=None, conditions=""
):
	# book the expense/income on the last day, but it will be trigger on the 1st of month at 12:00 AM

	if not start_date:
		start_date = add_months(today(), -1)
	if not end_date:
		end_date = add_days(today(), -1)

	#Checking if already booked the deferred revenue against the Project
	je_exist = frappe.db.sql(f"""SELECT je.name 
				FROM `tabJournal Entry Account` acc, `tabJournal Entry` je 	
				WHERE acc.parent=je.name AND acc.project= '{project}' 
				AND je.cumulative_reference ='Against Sales Invoice'
				AND je.docstatus = 1
				""")
	print(f"\n\n\n\nje_exist: {je_exist}\n\n\n")
	if je_exist:
		return

	# check for the sales invoice for which GL entries has to be done
	invoices = frappe.db.sql_list(
		"""
		select distinct item.parent
		from `tabSales Invoice Item` item, `tabSales Invoice` p
		where item.service_start_date<=%s and item.service_end_date>=%s
		and item.enable_deferred_revenue = 1 and item.parent=p.name
		and item.docstatus = 1 and ifnull(item.amount, 0) > 0
		{0}
	""".format(
			conditions
		),
		(end_date, start_date),
	)  # nosec

	print(f"\n\n\n\ninvoices: {invoices}\n\n\n")

	entries = []
	for invoice in invoices:
		doc = frappe.get_doc("Sales Invoice", invoice)
		entry = book_deferred_income(doc, end_date)
		print(f"\n\n\n\nentry: {entry}\n\n\n")

		if entry:
			entries.append(entry)

	submit_journal_entry = cint(
		frappe.db.get_singles_value("Accounts Settings", "submit_journal_entries")
	)

	if entries:
		book_revenue_via_journal_entry(sorted(entries, key=lambda x: (x['credit_account'],x['debit_account'])),
			company, deferred_process, project, submit_journal_entry, end_date)
	else:
		return

	if frappe.flags.deferred_accounting_error:
		send_mail(deferred_process)


def get_booking_dates(doc, item, posting_date=None):
	if not posting_date:
		posting_date = add_days(today(), -1)

	last_gl_entry = False

	deferred_account = (
		"deferred_revenue_account" if doc.doctype == "Sales Invoice" else "deferred_expense_account"
	)

	prev_gl_entry = frappe.db.sql(
		"""
		select name, posting_date from `tabGL Entry` where company=%s and account=%s and
		voucher_type=%s and voucher_no=%s and voucher_detail_no=%s
		and is_cancelled = 0
		order by posting_date desc limit 1
	""",
		(doc.company, item.get(deferred_account), doc.doctype, doc.name, item.name),
		as_dict=True,
	)

	prev_gl_via_je = frappe.db.sql(
		"""
		SELECT p.name, p.posting_date FROM `tabJournal Entry` p, `tabJournal Entry Account` c
		WHERE p.name = c.parent and p.company=%s and c.account=%s
		and c.reference_type=%s and c.reference_name=%s
		and c.reference_detail_no=%s and c.docstatus < 2 order by posting_date desc limit 1
	""",
		(doc.company, item.get(deferred_account), doc.doctype, doc.name, item.name),
		as_dict=True,
	)

	if prev_gl_via_je:
		if (not prev_gl_entry) or (
			prev_gl_entry and prev_gl_entry[0].posting_date < prev_gl_via_je[0].posting_date
		):
			prev_gl_entry = prev_gl_via_je

	if prev_gl_entry:
		start_date = getdate(add_days(prev_gl_entry[0].posting_date, 1))
	else:
		start_date = item.service_start_date

	end_date = get_last_day(start_date)
	if end_date >= item.service_end_date:
		end_date = item.service_end_date
		last_gl_entry = True
	elif item.service_stop_date and end_date >= item.service_stop_date:
		end_date = item.service_stop_date
		last_gl_entry = True

	if end_date > getdate(posting_date):
		end_date = posting_date

	if getdate(start_date) <= getdate(end_date):
		return start_date, end_date, last_gl_entry
	else:
		return None, None, None


def calculate_amount(doc, item, last_gl_entry, total_days, total_booking_days, account_currency):
	amount, base_amount = 0, 0
	if not last_gl_entry:
		base_amount = flt(
			item.base_net_amount * total_booking_days / flt(total_days), item.precision("base_net_amount")
		)
		if account_currency == doc.company_currency:
			amount = base_amount
		else:
			amount = flt(
				item.net_amount * total_booking_days / flt(total_days), item.precision("net_amount")
			)
	else:
		already_booked_amount, already_booked_amount_in_account_currency = get_already_booked_amount(
			doc, item
		)

		base_amount = flt(
			item.base_net_amount - already_booked_amount, item.precision("base_net_amount")
		)
		if account_currency == doc.company_currency:
			amount = base_amount
		else:
			amount = flt(
				item.net_amount - already_booked_amount_in_account_currency, item.precision("net_amount")
			)

	return amount, base_amount


def get_already_booked_amount(doc, item):
	if doc.doctype == "Sales Invoice":
		total_credit_debit, total_credit_debit_currency = "debit", "debit_in_account_currency"
		deferred_account = "deferred_revenue_account"

	gl_entries_details = frappe.db.sql(
		"""
		select sum({0}) as total_credit, sum({1}) as total_credit_in_account_currency, voucher_detail_no
		from `tabGL Entry` where company=%s and account=%s and voucher_type=%s and voucher_no=%s and voucher_detail_no=%s
		and is_cancelled = 0
		group by voucher_detail_no
	""".format(
			total_credit_debit, total_credit_debit_currency
		),
		(doc.company, item.get(deferred_account), doc.doctype, doc.name, item.name),
		as_dict=True,
	)

	journal_entry_details = frappe.db.sql(
		"""
		SELECT sum(c.{0}) as total_credit, sum(c.{1}) as total_credit_in_account_currency, reference_detail_no
		FROM `tabJournal Entry` p , `tabJournal Entry Account` c WHERE p.name = c.parent and
		p.company = %s and c.account=%s and c.reference_type=%s and c.reference_name=%s and c.reference_detail_no=%s
		and p.docstatus < 2 group by reference_detail_no
	""".format(
			total_credit_debit, total_credit_debit_currency
		),
		(doc.company, item.get(deferred_account), doc.doctype, doc.name, item.name),
		as_dict=True,
	)

	already_booked_amount = gl_entries_details[0].total_credit if gl_entries_details else 0
	already_booked_amount += journal_entry_details[0].total_credit if journal_entry_details else 0

	if doc.currency == doc.company_currency:
		already_booked_amount_in_account_currency = already_booked_amount
	else:
		already_booked_amount_in_account_currency = (
			gl_entries_details[0].total_credit_in_account_currency if gl_entries_details else 0
		)
		already_booked_amount_in_account_currency += (
			journal_entry_details[0].total_credit_in_account_currency if journal_entry_details else 0
		)

	return already_booked_amount, already_booked_amount_in_account_currency


def book_deferred_income(doc, posting_date=None):
	enable_check = "enable_deferred_revenue"

	accounts_frozen_upto = frappe.get_cached_value("Accounts Settings", "None", "acc_frozen_upto")

	via_journal_entry = cint(
		frappe.db.get_singles_value("Accounts Settings", "book_deferred_entries_via_journal_entry")
	)

	book_deferred_entries_based_on = frappe.db.get_singles_value(
		"Accounts Settings", "book_deferred_entries_based_on"
	)

	def _book_deferred_revenue(
		item, via_journal_entry, book_deferred_entries_based_on
	):
		start_date, end_date, last_gl_entry = get_booking_dates(doc, item, posting_date=posting_date)
		if not (start_date and end_date):
			return

		account_currency = get_account_currency(item.expense_account or item.income_account)
		if doc.doctype == "Sales Invoice":
			against, project = doc.customer, doc.project
			credit_account, debit_account = item.income_account, item.deferred_revenue_account

		total_days = date_diff(item.service_end_date, item.service_start_date) + 1
		total_booking_days = date_diff(end_date, start_date) + 1

		amount, base_amount = calculate_amount(
			doc, item, last_gl_entry, total_days, total_booking_days, account_currency
		)

		if not amount:
			return

		# check if books nor frozen till endate:
		if accounts_frozen_upto and (end_date) <= getdate(accounts_frozen_upto):
			end_date = get_last_day(add_days(accounts_frozen_upto, 1))

		if via_journal_entry:
			return {"sales_invoice_name":doc.name,
	   				"credit_account":credit_account,
					"debit_account":debit_account,
					"amount":amount,
					"base_amount":base_amount,
					"account_currency":account_currency,
					"item_cost_center":item.cost_center,
					"item_code":item.item_code
					}
		else:
			pass

		# Returned in case of any errors because it tries to submit the same record again and again in case of errors
		if frappe.flags.deferred_accounting_error:
			return

		if getdate(end_date) < getdate(posting_date) and not last_gl_entry:
			return _book_deferred_revenue(
				item, via_journal_entry, book_deferred_entries_based_on
			)
	for item in doc.get("items"):
		if item.get(enable_check):

			return _book_deferred_revenue(
				item, via_journal_entry, book_deferred_entries_based_on
			)


def send_mail(deferred_process):
	title = _("Error while processing deferred accounting for {0}").format(deferred_process)
	link = get_link_to_form("Process Deferred Accounting", deferred_process)
	content = _("Deferred accounting failed for some invoices:") + "\n"
	content += _(
		"Please check Process Deferred Accounting {0} and submit manually after resolving errors."
	).format(link)
	sendmail_to_system_managers(title, content)


def book_revenue_via_journal_entry(entries, company, deferred_process, project, submit_journal_entry=None, posting_date=None):
	final = []
	temp = None
	for entry in entries:
		if not temp:
			temp = entry.copy()
			temp["remark"]=temp.get("sales_invoice_name")
		else:
			if temp['credit_account'] == entry['credit_account'] and temp['debit_account'] == entry['debit_account']:
				temp['amount'] += entry['amount']
				temp['base_amount'] += entry['base_amount']
				temp['remark'] +=", "+entry['sales_invoice_name']
			else:
				final.append(temp)
				temp = entry.copy()
				temp["remark"]=temp.get("sales_invoice_name")
	final.append(temp)

	for entry in final:
		if entry.get("amount") == 0:
			return

	journal_entry = frappe.new_doc("Journal Entry")
	journal_entry.posting_date = (posting_date if posting_date else add_days(today(), -1))
	journal_entry.company = company
	journal_entry.voucher_type = "Deferred Revenue"
	journal_entry.cumulative_reference = "Against Sales Invoice"
	journal_entry.user_remark = "Journal Entry against Sales Invoice "
	journal_entry.process_deferred_accounting = deferred_process

	for entry in final:
		journal_entry.user_remark += entry.get("remark")
		credit_entry = {
			"account": entry.get("credit_account"),
			"credit": entry.get("base_amount"),
			"credit_in_account_currency": entry.get("amount"),
			"account_currency": entry.get("account_currency"),
			"reference_detail_no": entry.get("sales_invoice_name"),
			"cost_center": entry.get("cost_center"),
			"project": project,
			"user_remark":entry.get("remark")
		}

		debit_entry = {
			"account": entry.get("debit_account"),
			"debit": entry.get("base_amount"),
			"debit_in_account_currency": entry.get("amount"),
			"account_currency": entry.get("account_currency"),
			"reference_detail_no": entry.get("sales_invoice_name"),
			"cost_center": entry.get("cost_center"),
			"project": project,
			"user_remark":entry.get("remark")
		}
		journal_entry.append("accounts", debit_entry)
		journal_entry.append("accounts", credit_entry)

	try:
		journal_entry.save()

		if submit_journal_entry:
			journal_entry.submit()

		frappe.db.commit()
	except Exception:
		frappe.db.rollback()
		traceback = frappe.get_traceback()
		frappe.log_error(
			title=_("Error while processing deferred accounting for project {0}").format(final[0].get("project")),
			message=traceback,
		)

		frappe.flags.deferred_accounting_error = True