document.addEventListener("DOMContentLoaded", function () {

    const fileInput = document.getElementById('id_file');
    const fileListDisplay = document.getElementById('file-list');
    let selectedFiles = []; // Массив для хранения выбранных файлов

    fileInput.addEventListener('change', function (event) {
        const files = Array.from(event.target.files);

        // Добавляем новые файлы в массив, избегая дубликатов
        files.forEach(file => {
            if (!selectedFiles.some(f => f.name === file.name && f.size === file.size)) {
                selectedFiles.push(file);
            }
        });

        updateFileList();
    });

    function updateFileList() {
        fileListDisplay.innerHTML = ''; // Очистить текущий список

        selectedFiles.forEach((file, index) => {
            const fileSize = (file.size / 1024 / 1024).toFixed(2); // Размер в МБ

            const listItem = document.createElement('li');
            listItem.className = 'list-group-item d-flex justify-content-between align-items-center';
            listItem.innerHTML = `
                <span>${file.name} (${fileSize} MB)</span>
                <button class="btn btn-sm p-0 py-0 px-1 bg-danger text-danger bg-opacity-25 remove-file" 
                        type="button" data-index="${index}">×</button>
            `;

            fileListDisplay.appendChild(listItem);
        });

        // Добавляем обработчики удаления
        document.querySelectorAll('.remove-file').forEach(button => {
            button.addEventListener('click', function () {
                const index = parseInt(this.getAttribute('data-index'));
                removeFile(index);
            });
        });

        refreshFileInput();
    }

    function removeFile(index) {
        selectedFiles.splice(index, 1); // Удаляем файл из массива
        updateFileList();
    }

    function refreshFileInput() {
        const dataTransfer = new DataTransfer(); // Создаем новый объект для передачи файлов
        selectedFiles.forEach(file => dataTransfer.items.add(file)); // Добавляем файлы из массива
        fileInput.files = dataTransfer.files; // Обновляем файлы в поле ввода
    }

    // Переопределяем отправку формы
    document.querySelector('form').addEventListener('submit', function (event) {
        const formData = new FormData(this);
        selectedFiles.forEach(file => formData.append('file', file));
    });

});
