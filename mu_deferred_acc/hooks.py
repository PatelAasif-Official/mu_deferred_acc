from . import __version__ as app_version

app_name = "mu_deferred_acc"
app_title = "mu_deferred_acc"
app_publisher = "asif patel"
app_description = "mu_deferred_acc"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "patelasif52@gmail.com"
app_license = "MIT"


doctype_js = {
    "Sales Invoice":"mu_deferred_acc/custom_script/sales_invoice/sales_invoice.js",
    }

override_doctype_class = {
	"Process Deferred Accounting":"mu_deferred_acc.mu_deferred_acc.custom_script.process_deferred_accounting.process_deferred_accounting.custom_ProcessDeferredAccounting",
}
# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/mu_deferred_acc/css/mu_deferred_acc.css"
# app_include_js = "/assets/mu_deferred_acc/js/mu_deferred_acc.js"

# include js, css files in header of web template
# web_include_css = "/assets/mu_deferred_acc/css/mu_deferred_acc.css"
# web_include_js = "/assets/mu_deferred_acc/js/mu_deferred_acc.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "mu_deferred_acc/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "mu_deferred_acc.install.before_install"
# after_install = "mu_deferred_acc.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "mu_deferred_acc.uninstall.before_uninstall"
# after_uninstall = "mu_deferred_acc.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "mu_deferred_acc.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
#	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
#	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
#	"*": {
#		"on_update": "method",
#		"on_cancel": "method",
#		"on_trash": "method"
#	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
#	"all": [
#		"mu_deferred_acc.tasks.all"
#	],
#	"daily": [
#		"mu_deferred_acc.tasks.daily"
#	],
#	"hourly": [
#		"mu_deferred_acc.tasks.hourly"
#	],
#	"weekly": [
#		"mu_deferred_acc.tasks.weekly"
#	]
#	"monthly": [
#		"mu_deferred_acc.tasks.monthly"
#	]
# }

# Testing
# -------

# before_tests = "mu_deferred_acc.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
#	"frappe.desk.doctype.event.event.get_events": "mu_deferred_acc.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#	"Task": "mu_deferred_acc.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]


# User Data Protection
# --------------------

user_data_fields = [
	{
		"doctype": "{doctype_1}",
		"filter_by": "{filter_by}",
		"redact_fields": ["{field_1}", "{field_2}"],
		"partial": 1,
	},
	{
		"doctype": "{doctype_2}",
		"filter_by": "{filter_by}",
		"partial": 1,
	},
	{
		"doctype": "{doctype_3}",
		"strict": False,
	},
	{
		"doctype": "{doctype_4}"
	}
]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
#	"mu_deferred_acc.auth.validate"
# ]

