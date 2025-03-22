function getColumnIndexByHeader(headerText) {
    const headers = document.querySelectorAll(".tasks-list thead th");
    let columnIndex = -1;

    headers.forEach((header, index) => {
        if (header.textContent.trim() === headerText) {
            columnIndex = index;
        }
    });

    return columnIndex;
}

function saveFiltersToLocalStorage() {
    const checkboxes = document.querySelectorAll("input[name='statusFilter']");
    const selectedStatuses = Array.from(checkboxes)
        .filter(checkbox => checkbox.checked)
        .map(checkbox => checkbox.value);

    localStorage.setItem('selectedStatuses', JSON.stringify(selectedStatuses));
}

function loadFiltersFromLocalStorage() {
    const savedStatuses = JSON.parse(localStorage.getItem('selectedStatuses')) || [];
    const checkboxes = document.querySelectorAll("input[name='statusFilter']");

    checkboxes.forEach(checkbox => {
        checkbox.checked = savedStatuses.includes(checkbox.value);
    });

    filterTasksByStatus();
}

function filterTasksByStatus() {
    const checkboxes = document.querySelectorAll("input[name='statusFilter']:checked");
    const selectedStatuses = Array.from(checkboxes).map(checkbox => checkbox.value);
    const rows = document.querySelectorAll(".tasks-list tbody tr");
    const statusColumnIndex = getColumnIndexByHeader("Status");

    if (statusColumnIndex === -1) {
        console.error("Column with header 'Status' not found.");
        return;
    }

    rows.forEach(row => {
        const statusCell = row.querySelector(`td:nth-child(${statusColumnIndex + 1})`);
        const statusSpan = statusCell?.querySelector("span"); 
        const statusText = statusSpan ? statusSpan.textContent.trim() : ""; 

        if (selectedStatuses.length === 0 || selectedStatuses.includes(statusText)) {
            row.style.display = ""; 
        } else {
            row.style.display = "none"; 
        }
    });

    saveFiltersToLocalStorage();
}

function resetFilters() {
    document.querySelectorAll("input[name='statusFilter']").forEach(checkbox => {
        checkbox.checked = false;
    });
    filterTasksByStatus();
    localStorage.removeItem('selectedStatuses');
}

window.addEventListener("DOMContentLoaded", () => {
    const filterContainer = document.createElement("div");
    filterContainer.classList.add("form-control-feedback", "form-control-feedback-end");

    filterContainer.innerHTML = `
        <div class="dropdown mb-3">
            <button class="btn btn-outline-secondary dropdown-toggle" type="button" id="statusFilterDropdown" data-bs-toggle="dropdown" aria-expanded="false">
                Status
            </button>
            <ul class="dropdown-menu" aria-labelledby="statusFilterDropdown">
                <li><label class="dropdown-item"><input class="form-check-input me-2" type="checkbox" name="statusFilter" value="New"> New</label></li>
                <li><label class="dropdown-item"><input class="form-check-input me-2" type="checkbox" name="statusFilter" value="Working"> Working</label></li>
                <li><label class="dropdown-item"><input class="form-check-input me-2" type="checkbox" name="statusFilter" value="Pause"> Pause</label></li>
                <li><label class="dropdown-item"><input class="form-check-input me-2" type="checkbox" name="statusFilter" value="Done"> Done</label></li>
                <li><label class="dropdown-item"><input class="form-check-input me-2" type="checkbox" name="statusFilter" value="Closed"> Closed</label></li>
                <li><hr class="dropdown-divider"></li>
                <li><button class="dropdown-item text-danger" id="resetFilters">Reset Filters</button></li>
            </ul>
        </div>
    `;

    const dataTableHeader = document.querySelector(".datatable-header");
    dataTableHeader.appendChild(filterContainer);

    document.querySelectorAll("input[name='statusFilter']").forEach(checkbox => {
        checkbox.addEventListener("change", filterTasksByStatus);
    });

    document.querySelectorAll(".dropdown-item").forEach(item => {
        item.addEventListener("click", (event) => {
            event.stopPropagation();
        });
    });

    document.getElementById("resetFilters").addEventListener("click", (event) => {
        resetFilters();
        event.stopPropagation();
    });

    loadFiltersFromLocalStorage();
});
