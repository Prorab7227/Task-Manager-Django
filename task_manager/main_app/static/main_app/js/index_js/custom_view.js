document.addEventListener("DOMContentLoaded", function () {
    // Колонки, которые отключены по умолчанию
    const hiddenByDefault = ["Folder", "Client"];

    const pageKey = `columnStates_${window.location.pathname}`;

    function getColumnIndexByHeader(headerText) {
        const headers = document.querySelectorAll(".tasks-list thead th");
        return Array.from(headers).findIndex(header => header.textContent.trim() === headerText);
    }

    function saveColumnState(columnName, isVisible) {
        const columnStates = JSON.parse(localStorage.getItem(pageKey)) || { columnsOrder: [] };
        columnStates[columnName] = isVisible;
        localStorage.setItem(pageKey, JSON.stringify(columnStates));
    }

    function saveColumnsOrder(order) {
        const columnStates = JSON.parse(localStorage.getItem(pageKey)) || {};
        columnStates.columnsOrder = order;
        localStorage.setItem(pageKey, JSON.stringify(columnStates));
    }

    function loadColumnStates() {
        const columnStates = JSON.parse(localStorage.getItem(pageKey)) || { columnsOrder: [] };
        hiddenByDefault.forEach(column => {
            if (!(column in columnStates)) columnStates[column] = false; // По умолчанию скрываем
        });
        return columnStates;
    }

    function loadColumnsOrder() {
        const columnStates = JSON.parse(localStorage.getItem(pageKey)) || {};
        return columnStates.columnsOrder || [];
    }

    function resetToDefaultOrder() {
        localStorage.removeItem(pageKey);
        location.reload();
    }

    const filterContainer = document.createElement("div");
    filterContainer.classList.add("form-control-feedback", "form-control-feedback-end");
    filterContainer.innerHTML = `
        <div class="dropdown d-flex align-items-center ms-3 mb-3">
            <button class="btn btn-outline-secondary dropdown-toggle" type="button" id="viewButton" data-bs-toggle="dropdown" aria-expanded="false">
                View
            </button>
            <ul id="view-dropdown" class="dropdown-menu" aria-labelledby="viewButton" style="max-height: 300px; overflow-y: auto;">
                <li>
                    <button class="dropdown-item" id="selectAll">Select All</button>
                </li>
                <li>
                    <button class="dropdown-item" id="deselectAll">Deselect All</button>
                </li>
                <li>
                    <button class="dropdown-item" id="resetOrder">Reset Order</button>
                </li>
                <li><hr class="dropdown-divider"></li>
            </ul>
        </div>
    `;

    const dataTableHeader = document.querySelector(".datatable-header");
    if (dataTableHeader) {
        dataTableHeader.appendChild(filterContainer);
    } else {
        console.error("Container for filtering not found.");
        return;
    }

    const headers = document.querySelectorAll(".tasks-list thead th");
    const dropdownMenu = document.querySelector("#view-dropdown");
    const columnStates = loadColumnStates();
    const savedOrder = loadColumnsOrder();

    if (headers.length === 0) {
        console.error("Table headers not found.");
        return;
    }

    const headersArray = Array.from(headers);
    const sortedHeaders = savedOrder.length > 0
        ? savedOrder.map(name => headersArray.find(header => header.textContent.trim() === name)).filter(Boolean)
        : headersArray;

    const table = document.querySelector(".tasks-list");
    const tbody = table.querySelector("tbody");
    const rows = Array.from(tbody.rows);
    const thead = table.querySelector("thead");

    // Функция для скрытия/показа столбца
    function updateColumnVisibility() {
        const columnStates = loadColumnStates();
        const headers = document.querySelectorAll(".tasks-list thead th");

        headers.forEach((header, index) => {
            const columnName = header.textContent.trim();
            const isVisible = columnStates[columnName] !== false;
            const columnCells = document.querySelectorAll(`.tasks-list td:nth-child(${index + 1}), .tasks-list th:nth-child(${index + 1})`);

            columnCells.forEach(cell => {
                cell.style.display = isVisible ? "" : "none";
            });
        });
    }

    // Инициализация состояния видимости колонок
    updateColumnVisibility();

    // Используем MutationObserver для отслеживания изменений в таблице
    const observer = new MutationObserver(() => {
        updateColumnVisibility();
    });     

    // Настройка наблюдателя на изменения в tbody
    observer.observe(tbody, {
        childList: true,  // Отслеживаем добавление/удаление строк
        subtree: true     // Отслеживаем изменения в поддереве (включая строки)
    });

    sortedHeaders.forEach((header, newIndex) => {
        const columnName = header.textContent.trim();
        const isVisible = columnStates[columnName] !== false;

        const oldIndex = getColumnIndexByHeader(columnName);
        rows.forEach(row => {
            const cell = row.children[oldIndex];
            row.insertBefore(cell, row.children[newIndex]);
        });
        const headerCell = thead.rows[0].children[oldIndex];
        thead.rows[0].insertBefore(headerCell, thead.rows[0].children[newIndex]);

        const columnCells = document.querySelectorAll(`.tasks-list td:nth-child(${newIndex + 1}), .tasks-list th:nth-child(${newIndex + 1})`);
        columnCells.forEach(cell => {
            cell.style.display = isVisible ? "" : "none";
        });
    });

    sortedHeaders.forEach((header, newIndex) => {
        const columnName = header.textContent.trim();

        if (!columnName || header.innerHTML.trim() === "") return;

        const listItem = document.createElement("li");
        listItem.classList.add("dropdown-item", "d-flex", "align-items-center", "py-2");
        listItem.draggable = true;
        listItem.dataset.columnName = columnName;

        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.id = `show${columnName.replace(/\s+/g, '')}`;
        checkbox.checked = columnStates[columnName] !== false;
        checkbox.classList.add("form-check-input", "me-2");

        const label = document.createElement("label");
        label.setAttribute("for", checkbox.id);
        label.textContent = columnName;
        label.classList.add("form-check-label", "mb-0");

        listItem.appendChild(checkbox);
        listItem.appendChild(label);
        dropdownMenu.appendChild(listItem);

        // Обработчики событий для перетаскивания
        listItem.addEventListener("dragstart", function (e) {
            e.dataTransfer.setData("text/plain", columnName);
        });

        listItem.addEventListener("dragover", function (e) {
            e.preventDefault();
        });

        listItem.addEventListener("drop", function (e) {
            e.preventDefault();
            const draggedColumnName = e.dataTransfer.getData("text/plain");
            if (draggedColumnName !== columnName) {
                const draggedItem = Array.from(dropdownMenu.children).find(item => item.dataset.columnName === draggedColumnName);
                dropdownMenu.insertBefore(draggedItem, listItem.nextSibling);

                const newOrder = Array.from(dropdownMenu.children)
                    .map(item => item.dataset.columnName)
                    .filter(Boolean);
                saveColumnsOrder(newOrder);

                const newHeaders = newOrder.map(name => headersArray.find(header => header.textContent.trim() === name));
                newHeaders.forEach((header, newIndex) => {
                    const oldIndex = getColumnIndexByHeader(header.textContent.trim());
                    rows.forEach(row => {
                        const cell = row.children[oldIndex];
                        row.insertBefore(cell, row.children[newIndex]);
                    });
                    const headerCell = thead.rows[0].children[oldIndex];
                    thead.rows[0].insertBefore(headerCell, thead.rows[0].children[newIndex]);
                });
            }
        });

        checkbox.addEventListener("change", function () {
            saveColumnState(columnName, checkbox.checked);
            const columnIndex = getColumnIndexByHeader(columnName);

            if (columnIndex !== -1) {
                const columnCells = document.querySelectorAll(`.tasks-list td:nth-child(${columnIndex + 1}), .tasks-list th:nth-child(${columnIndex + 1})`);
                columnCells.forEach(cell => {
                    cell.style.display = checkbox.checked ? "" : "none";
                });
            }
        });
    });

    document.getElementById("selectAll").addEventListener("click", function () {
        dropdownMenu.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
            checkbox.checked = true;
            const columnName = checkbox.parentNode.dataset.columnName;
            saveColumnState(columnName, true);

            const columnIndex = getColumnIndexByHeader(columnName);
            if (columnIndex !== -1) {
                const columnCells = document.querySelectorAll(`.tasks-list td:nth-child(${columnIndex + 1}), .tasks-list th:nth-child(${columnIndex + 1})`);
                columnCells.forEach(cell => {
                    cell.style.display = "";
                });
            }
        });
    });

    document.getElementById("deselectAll").addEventListener("click", function () {
        dropdownMenu.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
            checkbox.checked = false;
            const columnName = checkbox.parentNode.dataset.columnName;
            saveColumnState(columnName, false);

            const columnIndex = getColumnIndexByHeader(columnName);
            if (columnIndex !== -1) {
                const columnCells = document.querySelectorAll(`.tasks-list td:nth-child(${columnIndex + 1}), .tasks-list th:nth-child(${columnIndex + 1})`);
                columnCells.forEach(cell => {
                    cell.style.display = "none";
                });
            }
        });
    });

    document.getElementById("resetOrder").addEventListener("click", function () {
        resetToDefaultOrder();
    });
});
