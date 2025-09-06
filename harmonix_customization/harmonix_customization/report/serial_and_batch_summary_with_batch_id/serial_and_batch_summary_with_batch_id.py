# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	filters = frappe._dict(filters or {})
	data = get_data(filters)
	columns = get_columns(filters, data)
	return columns, data


def get_data(filters):
	"""
	Fetch rows with explicit joins (no subqueries, no get_all()) so we can
	show & filter the custom Batch.batch_id safely.
	"""
	conds = ["sbb.docstatus = 1", "sbb.is_cancelled = 0"]
	vals = {}

	# Parent (bundle) filters
	if filters.get("company"):
		conds.append("sbb.company = %(company)s")
		vals["company"] = filters.company

	if filters.get("voucher_type"):
		conds.append("sbb.voucher_type = %(voucher_type)s")
		vals["voucher_type"] = filters.voucher_type

	if filters.get("voucher_no"):
		# voucher_no can be a list (MultiSelectList) or a single string
		v = filters.voucher_no
		if isinstance(v, (list, tuple, set)):
			conds.append("sbb.voucher_no IN %(voucher_no)s")
			vals["voucher_no"] = tuple(v)
		else:
			conds.append("sbb.voucher_no = %(voucher_no)s")
			vals["voucher_no"] = v

	if filters.get("item_code"):
		conds.append("sbb.item_code = %(item_code)s")
		vals["item_code"] = filters.item_code

	if filters.get("from_date") and filters.get("to_date"):
		conds.append("sbb.posting_date BETWEEN %(from_date)s AND %(to_date)s")
		vals["from_date"] = filters.from_date
		vals["to_date"] = filters.to_date

	# Child (entry) filters
	if filters.get("warehouse"):
		conds.append("sbe.warehouse = %(warehouse)s")
		vals["warehouse"] = filters.warehouse

	if filters.get("serial_no"):
		conds.append("sbe.serial_no = %(serial_no)s")
		vals["serial_no"] = filters.serial_no

	if filters.get("batch_no"):
		conds.append("sbe.batch_no = %(batch_no)s")
		vals["batch_no"] = filters.batch_no

	# Custom Batch ID filter (partial match)
	if filters.get("batch_id"):
		conds.append("b.batch_id LIKE %(batch_id)s")
		vals["batch_id"] = f"%{filters.batch_id}%"

	where_sql = " AND ".join(conds)

	query = f"""
		SELECT
			sbb.company                          AS company,
			sbb.name                             AS name,               -- bundle id
			sbb.posting_date                     AS posting_date,
			sbb.voucher_type                     AS voucher_type,
			sbb.voucher_no                       AS voucher_no,
			sbb.item_code                        AS item_code,
			sbb.item_name                        AS item_name,
			sbe.warehouse                        AS warehouse,
			sbe.serial_no                        AS serial_no,
			sbe.batch_no                         AS batch_no,
			b.batch_id                           AS batch_id,           -- ✅ custom field from Batch
			sbe.qty                              AS qty,
			sbe.incoming_rate                    AS incoming_rate,
			sbe.stock_value_difference           AS stock_value_difference
		FROM `tabSerial and Batch Bundle` sbb
		LEFT JOIN `tabSerial and Batch Entry` sbe
			ON sbe.parent = sbb.name
			AND sbe.parenttype = 'Serial and Batch Bundle'
		LEFT JOIN `tabBatch` b
			ON b.name = sbe.batch_no
		WHERE {where_sql}
		ORDER BY sbb.posting_date
	"""

	return frappe.db.sql(query, vals, as_dict=True)


def get_columns(filters, data):
	columns = [
		{"label": _("Company"), "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 120},
		{"label": _("Serial and Batch Bundle"), "fieldname": "name", "fieldtype": "Link", "options": "Serial and Batch Bundle", "width": 150},
		{"label": _("Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 110},
	]

	item_details = {}
	item_codes = []
	if filters.get("voucher_type"):
		item_codes = [d.item_code for d in data]

	if filters.get("item_code") or (item_codes and len(set(item_codes)) == 1):
		item_details = frappe.get_cached_value(
			"Item",
			filters.get("item_code") or list(set(item_codes))[0],
			["has_serial_no", "has_batch_no"],
			as_dict=True,
		)

	if not filters.get("voucher_no"):
		columns.extend([
			{"label": _("Voucher Type"), "fieldname": "voucher_type", "fieldtype": "Link", "options": "DocType", "width": 140},
			{"label": _("Voucher No"), "fieldname": "voucher_no", "fieldtype": "Dynamic Link", "options": "voucher_type", "width": 180},
		])

	if not filters.get("item_code"):
		columns.extend([
			{"label": _("Item Code"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 130},
			{"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 150},
		])

	if not filters.get("warehouse"):
		columns.append({"label": _("Warehouse"), "fieldname": "warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 160})

	if not item_details or item_details.get("has_serial_no"):
		columns.append({"label": _("Serial No"), "fieldname": "serial_no", "fieldtype": "Data", "width": 160})

	if not item_details or item_details.get("has_batch_no"):
		columns.extend([
			{"label": _("Batch No"), "fieldname": "batch_no", "fieldtype": "Link", "options": "Batch", "width": 160},
			{"label": _("Batch ID"), "fieldname": "batch_id", "fieldtype": "Data", "width": 140},   # ✅ visible
			{"label": _("Batch Qty"), "fieldname": "qty", "fieldtype": "Float", "width": 110},
		])

	columns.extend([
		{"label": _("Incoming Rate"), "fieldname": "incoming_rate", "fieldtype": "Float", "width": 120},
		{"label": _("Change in Stock Value"), "fieldname": "stock_value_difference", "fieldtype": "Float", "width": 140},
	])

	return columns


# The whitelisted helper endpoints below are unchanged (used by the report UI)
@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_voucher_type(doctype, txt, searchfield, start, page_len, filters):
	child_doctypes = frappe.get_all(
		"DocField",
		filters={"fieldname": "serial_and_batch_bundle"},
		fields=["distinct parent as parent"],
	)
	query_filters = {"options": ["in", [d.parent for d in child_doctypes]]}
	if txt:
		query_filters["parent"] = ["like", f"%{txt}%"]
	return frappe.get_all("DocField", filters=query_filters, fields=["distinct parent"], as_list=True)


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_serial_nos(doctype, txt, searchfield, start, page_len, filters):
	query_filters = {}
	if txt:
		query_filters["serial_no"] = ["like", f"%{txt}%"]
	if filters.get("voucher_no"):
		serial_batch_bundle = frappe.get_cached_value(
			"Serial and Batch Bundle",
			{"voucher_no": ("in", filters.get("voucher_no")), "docstatus": 1, "is_cancelled": 0},
			"name",
		)
		query_filters["parent"] = serial_batch_bundle
		if not txt:
			query_filters["serial_no"] = ("is", "set")
		return frappe.get_all("Serial and Batch Entry", filters=query_filters, fields=["serial_no"], as_list=True)
	else:
		query_filters["item_code"] = filters.get("item_code")
		return frappe.get_all("Serial No", filters=query_filters, as_list=True)


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_batch_nos(doctype, txt, searchfield, start, page_len, filters):
	query_filters = {}
	if txt:
		query_filters["batch_no"] = ["like", f"%{txt}%"]
	if filters.get("voucher_no"):
		serial_batch_bundle = frappe.get_cached_value(
			"Serial and Batch Bundle",
			{"voucher_no": ("in", filters.get("voucher_no")), "docstatus": 1, "is_cancelled": 0},
			"name",
		)
		query_filters["parent"] = serial_batch_bundle
		if not txt:
			query_filters["batch_no"] = ("is", "set")
		return frappe.get_all("Serial and Batch Entry", filters=query_filters, fields=["batch_no"], as_list=True)
	else:
		query_filters["item"] = filters.get("item_code")
		return frappe.get_all("Batch", filters=query_filters, as_list=True)
