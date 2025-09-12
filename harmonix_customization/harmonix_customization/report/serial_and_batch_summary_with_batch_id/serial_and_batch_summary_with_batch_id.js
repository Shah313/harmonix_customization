// File: harmonix_customization/harmonix_customization/report/serial_and_batch_summary_with_batch_id/serial_and_batch_summary.js

frappe.query_reports["Serial and Batch Summary with Batch ID"] = {
  filters: [
    {
      fieldname: "company",
      label: __("Company"),
      fieldtype: "Link",
      options: "Company",
      default: frappe.defaults.get_user_default("Company"),
      reqd: 1,
    },
    {
      fieldname: "from_date",
      label: __("From Date"),
      fieldtype: "Date",
      default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
      reqd: 1,
    },
    {
      fieldname: "to_date",
      label: __("To Date"),
      fieldtype: "Date",
      default: frappe.datetime.get_today(),
      reqd: 1,
    },

    // Voucher Type (limited to doctypes that contain SBB child)
    {
      fieldname: "voucher_type",
      label: __("Voucher Type"),
      fieldtype: "Link",
      options: "DocType",
      get_query() {
        return {
          query:
            "harmonix_customization.harmonix_customization.report.serial_and_batch_summary_with_batch_id.serial_and_batch_summary_with_batch_id.get_voucher_type",
        };
      },
    },

    // Voucher No (optional: keep as Data or MultiSelectList depending on your UI)
    // Using MultiSelectList here since your PY handles list OR single string
    {
      fieldname: "voucher_no",
      label: __("Voucher No"),
      fieldtype: "MultiSelectList",
      get_data: function (txt) {
        const vt = frappe.query_report.get_filter_value("voucher_type") || "";
        if (!vt) return Promise.resolve([]);

        // Standard helper: fetch link options for selected voucher type
        return frappe.db.get_link_options(vt, txt, { limit_page_length: 20 });
      },
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

    // --- Serial filter (points to YOUR whitelisted method) ---
    {
      fieldname: "serial_no",
      label: __("Serial No"),
      fieldtype: "Link",
      options: "Serial No",
      get_query() {
        return {
          query:
            "harmonix_customization.harmonix_customization.report.serial_and_batch_summary_with_batch_id.serial_and_batch_summary_with_batch_id.get_serial_nos",
          filters: {
            item_code: frappe.query_report.get_filter_value("item_code") || "",
            voucher_no: frappe.query_report.get_filter_value("voucher_no") || [],
            voucher_type:
              frappe.query_report.get_filter_value("voucher_type") || "",
          },
        };
      },
    },

    // --- Batch No filter (points to YOUR whitelisted method) ---
    {
      fieldname: "batch_no",
      label: __("Batch No"),
      fieldtype: "Link",
      options: "Batch",
      get_query() {
        return {
          query:
            "harmonix_customization.harmonix_customization.report.serial_and_batch_summary_with_batch_id.serial_and_batch_summary_with_batch_id.get_batch_nos",
          filters: {
            item_code: frappe.query_report.get_filter_value("item_code") || "",
            voucher_no: frappe.query_report.get_filter_value("voucher_no") || [],
            voucher_type:
              frappe.query_report.get_filter_value("voucher_type") || "",
          },
        };
      },
    },

    // Free-text Batch ID (supports partial match in your PY)
    {
      fieldname: "batch_id",
      label: __("Batch ID"),
      fieldtype: "Data",
      description: __("Partial match, e.g. A123"),
    },
  ],
};
