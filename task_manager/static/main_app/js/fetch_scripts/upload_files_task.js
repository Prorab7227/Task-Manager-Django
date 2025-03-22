document.addEventListener("DOMContentLoaded", function () {
    const fileInput = document.getElementById("id_file");
    const fileListDisplay = document.getElementById("file-list");

    // Get token from localStorage
    let token = localStorage.getItem("access_token");

    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    fetch("/api/auth/session-token/", {  // New endpoint for getting token by session
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.key) {
            token = data.key;
            localStorage.setItem("access_token", token);
            console.log("Token received and saved");
        } else {
            console.error("Error getting token:", data);
        }
    })
    .catch(error => {
        console.error("Error getting token:", error);
    });

    // Handler for file uploads
    fileInput.addEventListener("change", function (event) {
        const files = Array.from(event.target.files);
        files.forEach(file => uploadFile(file));
    });

    function uploadFile(file) {
        const formData = new FormData();
        formData.append("file", file);

        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        const taskSlug = document.getElementById("file-upload-form").dataset.taskSlug;
        const uploadUrl = `/task/file/upload/${taskSlug}/`;

        // Создаем элемент списка и прогресс-бар
        const listItem = document.createElement("li");
        listItem.className = "list-group-item d-flex justify-content-between align-items-center";
        listItem.innerHTML = `<span>${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)</span>
                              <div class="progress w-50">
                                  <div class="progress-bar progress-bar-striped progress-bar-animated" style="width: 50%"></div>
                              </div>
                              <i class="ph-x text-danger" style="cursor: pointer;"></i>`;
        fileListDisplay.appendChild(listItem);

        const progressBar = listItem.querySelector(".progress-bar");
        const deleteButton = listItem.querySelector(".ph-x");

        // Удаление файла из списка
        deleteButton.addEventListener("click", function () {
            listItem.remove();
        });

        // Отправляем файл
        fetch(uploadUrl, {
            method: "POST",
            body: formData,
            headers: { 
                "X-CSRFToken": csrfToken,
                'Authorization': `Bearer ${token}`,  // Передаем Bearer Token
                "Accept": "application/json", // Указываем, что ожидаем JSON
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.uploaded_files && data.uploaded_files.length > 0) {
                progressBar.classList.remove("progress-bar-animated");
                progressBar.style.width = "100%";
                progressBar.classList.add("bg-success");

                // Добавляем ссылку на загруженный файл
                listItem.innerHTML = `<a href="${data.uploaded_files[0].url}" target="_blank">${file.name}</a>
                                      <span class="text-muted">${(file.size / 1024 / 1024).toFixed(2)} MB</span>
                                      <i class="ph-x text-danger" style="cursor: pointer;"></i>`;
                
                // Добавляем обработчик удаления после загрузки
                listItem.querySelector(".ph-x").addEventListener("click", function () {
                    listItem.remove();
                });
            } else {
                throw new Error("Upload failed");
            }
        })
        .catch(error => {
            console.error("Upload error:", error);
            progressBar.classList.remove("progress-bar-animated");
            progressBar.classList.add("bg-danger");
            progressBar.style.width = "100%";
        });
    }
});
