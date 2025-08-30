app_name = "zatca_tax_fix"
app_title = "Zatca Tax Fix"
app_publisher = "sammish"
app_description = "zatca_tax_fix"
app_email = "sammish.thundiyil@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "zatca_tax_fix",
# 		"logo": "/assets/zatca_tax_fix/logo.png",
# 		"title": "Zatca Tax Fix",
# 		"route": "/zatca_tax_fix",
# 		"has_permission": "zatca_tax_fix.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/zatca_tax_fix/css/zatca_tax_fix.css"
# app_include_js = "/assets/zatca_tax_fix/js/zatca_tax_fix.js"

# include js, css files in header of web template
# web_include_css = "/assets/zatca_tax_fix/css/zatca_tax_fix.css"
# web_include_js = "/assets/zatca_tax_fix/js/zatca_tax_fix.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "zatca_tax_fix/public/scss/website"

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

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "zatca_tax_fix/public/icons.svg"
# DocType Class Override - Sales Invoice Only
override_doctype_class = {
	"Sales Invoice": "zatca_tax_fix.overrides.sales_invoice.CustomSalesInvoice"
}

# Document Events - Sales Invoice Only
doc_events = {
	"Sales Invoice": {
		"before_validate": "zatca_tax_fix.events.sales_invoice.before_validate",
		"before_save": "zatca_tax_fix.events.sales_invoice.before_save",
		"validate": "zatca_tax_fix.events.sales_invoice.validate"
	}
}
# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "zatca_tax_fix.utils.jinja_methods",
# 	"filters": "zatca_tax_fix.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "zatca_tax_fix.install.before_install"
# after_install = "zatca_tax_fix.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "zatca_tax_fix.uninstall.before_uninstall"
# after_uninstall = "zatca_tax_fix.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "zatca_tax_fix.utils.before_app_install"
# after_app_install = "zatca_tax_fix.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "zatca_tax_fix.utils.before_app_uninstall"
# after_app_uninstall = "zatca_tax_fix.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "zatca_tax_fix.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"zatca_tax_fix.tasks.all"
# 	],
# 	"daily": [
# 		"zatca_tax_fix.tasks.daily"
# 	],
# 	"hourly": [
# 		"zatca_tax_fix.tasks.hourly"
# 	],
# 	"weekly": [
# 		"zatca_tax_fix.tasks.weekly"
# 	],
# 	"monthly": [
# 		"zatca_tax_fix.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "zatca_tax_fix.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "zatca_tax_fix.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "zatca_tax_fix.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["zatca_tax_fix.utils.before_request"]
# after_request = ["zatca_tax_fix.utils.after_request"]

# Job Events
# ----------
# before_job = ["zatca_tax_fix.utils.before_job"]
# after_job = ["zatca_tax_fix.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"zatca_tax_fix.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

