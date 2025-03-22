/* ------------------------------------------------------------------------------
 *
 *  # Task list view
 *
 *  Demo JS code for task_manager_list.html page
 *
 * ---------------------------------------------------------------------------- */


// Setup module
// ------------------------------

function getColumnIndexByHeader(headerText) {
    const headers = document.querySelectorAll(".tasks-list thead th");
    let columnIndex = 0;

    headers.forEach((header, index) => {
        if (header.textContent.trim() === headerText) {
            columnIndex = index;
        }
    });

    return columnIndex;
}

var TaskManagerList = function () {


    //
    // Setup components
    //

    // Datatable
    var _componentDatatable = function() {
        if (!$().DataTable) {
            console.warn('Warning - datatables.min.js is not loaded.');
            return;
        }

        // Create an array with the values of all the input boxes in a column
        $.fn.dataTable.ext.order['dom-text'] = function (settings, col) {
            return this.api().column(col, {order:'index'}).nodes().map( function (td, i) {
                return $('input', td).val();
            });
        };
         
        // Create an array with the values of all the select options in a column
        $.fn.dataTable.ext.order['dom-select'] = function (settings, col) {
            return this.api().column(col, {order:'index'}).nodes().map( function (td, i) {
                return $('select', td).val();
            });
        };

        // Пользовательская сортировка статусов
        $.fn.dataTable.ext.order['status-order'] = function (settings, col) {
            // Задаем порядок статусов
            const statusOrder = {
                "new": 1,
                "working": 2,
                "done": 3,
                "closed": 4
            };
        
            return this.api().column(col, { order: 'index' }).nodes().map(function (td) {
                // Извлекаем статус из класса элемента <span> с id="status-display-{{ act_item.id }}"
                const statusClass = $(td).find('span').attr('class');
                let status = 'closed';  // значение по умолчанию
        
                // Определяем статус по классу
                if (statusClass.includes('bg-warning')) {
                    status = 'new';
                } else if (statusClass.includes('bg-info')) {
                    status = 'working';
                } else if (statusClass.includes('bg-success')) {
                    status = 'done';
                } else if (statusClass.includes('bg-secondary')) {
                    status = 'closed';
                } else if (statusClass.includes('bg-dark')) {
                    status = 'pause';
                }
        
                // Возвращаем порядок сортировки, основываясь на статусе
                return statusOrder[status] || 6; // Если статус неизвестен, присваиваем больший индекс
            });
        };

        const def_size_column = "0.05%"

        // Initialize data table
        $('.tasks-list').DataTable({
            autoWidth: false,
            order: [
                // Сортировка по статусу (главный критерий)
                [getColumnIndexByHeader("Status"), "asc"], 
                // Сортировка по приоритету (второй критерий)
                [getColumnIndexByHeader("Priority"), "asc"]
            ],
            deferRender: true,
            columnDefs: [
                {
                    width: def_size_column,
                    targets: getColumnIndexByHeader("Members")
                },
                {
                    width: def_size_column,
                    targets: getColumnIndexByHeader("Status"),
                    orderDataType: "status-order"
                },
                {
                    width: def_size_column,
                    targets: getColumnIndexByHeader("Priority")
                },
                {
                    width: def_size_column,
                    targets: getColumnIndexByHeader("Deadline")
                },
                {
                    orderable: false,
                    width: "0.001%",
                    targets: -1
                },
                {
                    width: "10%",
                    targets: getColumnIndexByHeader("Name")
                },
                {
                    width: "20%",
                    targets: getColumnIndexByHeader("Task")
                },
                {
                    width: "20%",
                    targets: getColumnIndexByHeader("Description")
                },
                {
                    width: def_size_column,
                    targets: getColumnIndexByHeader("Owner")
                },
                {
                    width: def_size_column,
                    targets: getColumnIndexByHeader("Assignee")
                },
                {
                    width: def_size_column,
                    targets: getColumnIndexByHeader("Created")
                },
                {
                    width: def_size_column,
                    targets: getColumnIndexByHeader("Modified")
                },
                {
                    width: "10%",
                    targets: getColumnIndexByHeader("Folder")
                },
                {
                    width: "10%",
                    targets: getColumnIndexByHeader("Subfolder")
                },
                {
                    width: "10%",
                    targets: getColumnIndexByHeader("Project")
                },
                {
                    width: "5%",
                    targets: getColumnIndexByHeader("File")
                },
                {
                    width: "10%",
                    targets: getColumnIndexByHeader("Client")
                },

                {
                    width: def_size_column,
                    targets: getColumnIndexByHeader("Projects")
                },
                {
                    width: def_size_column,
                    targets: getColumnIndexByHeader("Folders")
                },

                {
                    width: "0.02%",
                    targets: getColumnIndexByHeader("New")
                },
                {
                    width: "0.02%",
                    targets: getColumnIndexByHeader("Working")
                },
                {
                    width: "0.02%",
                    targets: getColumnIndexByHeader("Pause")
                },
                {
                    width: "0.02%",
                    targets: getColumnIndexByHeader("Done")
                },
                {
                    width: "0.02%",
                    targets: getColumnIndexByHeader("Closed")
                },
                {
                    width: "0.02%",
                    targets: getColumnIndexByHeader("Archive")
                },


                {
                    orderable: false,
                    width: "10%",
                    targets: getColumnIndexByHeader("User")
                },
                {
                    width: "50%",
                    targets: getColumnIndexByHeader("Text")
                },
                {
                    width: "50%",
                    targets: getColumnIndexByHeader("Link")
                },
                {
                    width: "1%",
                    targets: getColumnIndexByHeader("Size")
                },
                {
                    width: def_size_column,
                    targets: getColumnIndexByHeader("Tasks")
                },


                {
                    width: def_size_column,
                    targets: getColumnIndexByHeader("Last Screenshot")
                },
                {
                    width: def_size_column,
                    targets: getColumnIndexByHeader("Today")
                },
                {
                    width: def_size_column,
                    targets: getColumnIndexByHeader("Yesterday")
                },
                {
                    width: def_size_column,
                    targets: getColumnIndexByHeader("Week")
                },
                {
                    width: def_size_column,
                    targets: getColumnIndexByHeader("Month")
                },
            ],
            dom: '<"datatable-header"fl><"datatable-scroll-lg"t><"datatable-footer"ip>',
            language: {
                search: '<span class="me-3">Filter:</span> <div class="form-control-feedback form-control-feedback-end flex-fill">_INPUT_<div class="form-control-feedback-icon"><i class="ph-magnifying-glass opacity-50"></i></div></div>',
                searchPlaceholder: 'Type to filter...',
                lengthMenu: '<span class="me-3">Show:</span> _MENU_',
                paginate: { 'first': 'First', 'last': 'Last', 'next': document.dir == "rtl" ? '&larr;' : '&rarr;', 'previous': document.dir == "rtl" ? '&rarr;' : '&larr;' }
            },
            lengthMenu: [15, 25, 50, 75, 100],
            displayLength: 50,

            // drawCallback: function (settings) {
            //     var api = this.api();
            //     var rows = api.rows({page:'current'}).nodes();
            //     var last=null;
     
            //     // Grouod rows
            //     api.column(1, {page:'current'}).data().each(function (group, i) {
            //         if (last !== group) {
            //             $(rows).eq(i).before(
            //                 '<tr class="table-light"><td colspan="12" class="fw-semibold">'+group+'</td></tr>'
            //             );
     
            //             last = group;
            //         }
            //     });
            // }
        });
    };


    //
    // Return objects assigned to module
    //

    return {
        init: function() {
            _componentDatatable();
        }
    }
}();


// Initialize module
// ------------------------------

document.addEventListener('DOMContentLoaded', function() {
    TaskManagerList.init();
});
