import DataTablesLib from "datatables.net-bs5";
import DataTable from "datatables.net-vue3";

DataTable.use(DataTablesLib);

new DataTablesLib("#tableNotifications", {
  order: [[0, "desc"]],
  pageLength: 25,
});
