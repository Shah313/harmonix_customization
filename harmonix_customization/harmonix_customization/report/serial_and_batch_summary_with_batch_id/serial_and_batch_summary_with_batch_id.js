// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Serial and Batch Summary with Batch ID"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
		},
		{
			fieldname: "item_code",
			label: __("Item"),
			fieldtype: "Link",
			options: "Item",
		},
		{
			fieldname: "warehouse",
			label: __("Warehouse"),
			fieldtype: "Link",
			options: "Warehouse",
		},
		{
			fieldname: "voucher_type",
			label: __("Voucher Type"),
			fieldtype: "Link",
			options: "DocType",
			get_query: function () {
				return {
					query: "erpnext.stock.report.serial_and_batch_summary_with_batch_id.serial_and_batch_summary_with_batch_id.get_voucher_type",
				};
			},
		},
		{
			fieldname: "voucher_no",
			label: __("Voucher No"),
			fieldtype: "MultiSelectList",
			get_data: function (txt) {
				if (!frappe.query_report.filters) return;

				let voucher_type = frappe.query_report.get_filter_value("voucher_type");
				if (!voucher_type) return;

				return frappe.db.get_link_options(voucher_type, txt);
			},
		},
		{
			fieldname: "serial_no",
			label: __("Serial No"),
			fieldtype: "Link",
			options: "Serial No",
			get_query: function () {
				return {
					query: "erpnext.stock.report.serial_and_batch_summary_with_batch_id.serial_and_batch_summary_with_batch_id.get_serial_nos",
					filters: {
						item_code: frappe.query_report.get_filter_value("item_code"),
						voucher_type: frappe.query_report.get_filter_value("voucher_type"),
						voucher_no: frappe.query_report.get_filter_value("voucher_no"),
					},
				};
			},
		},
		{
			fieldname: "batch_no",
			label: __("Batch No"),
			fieldtype: "Link",
			options: "Batch",
			get_query: function () {
				return {
					query: "erpnext.stock.report.serial_and_batch_summary_with_batch_id.serial_and_batch_summary_with_batch_id.get_batch_nos",
					filters: {
						item_code: frappe.query_report.get_filter_value("item_code"),
						voucher_type: frappe.query_report.get_filter_value("voucher_type"),
						voucher_no: frappe.query_report.get_filter_value("voucher_no"),
					},
				};
			},
		},
		// 👇 NEW FILTER ADDED HERE
		{
			fieldname: "batch_id",
			label: __("Batch ID"),
			fieldtype: "Data",
			description: __("Search by Batch ID (partial match allowed)")
		},
	],
};
