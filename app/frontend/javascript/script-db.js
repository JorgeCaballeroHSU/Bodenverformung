console.log("Database script loaded");

let selectedExcelFiles = [];

/*** Wait until page is loaded ***/
document.addEventListener("DOMContentLoaded", () => {

    const folderPicker = document.getElementById("folderPicker");

    if (!folderPicker) {
        console.error("folderPicker not found");
        return;
    }

    folderPicker.addEventListener(
        "change",
        handleFolderSelection
    );
});

/*** Triggered when folder is selected ***/
async function handleFolderSelection(event) {

    const files = [...event.target.files];

    selectedExcelFiles = files.filter(file => {

        const fileName = file.name.toLowerCase();

        return (
            fileName.includes("einax") &&
            (
                fileName.endsWith(".xlsx") ||
                fileName.endsWith(".xls")
            )
        );
    });

    updateFolderInfo();

    try {

        const response = await fetch(
            "/api/check-files",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    files: selectedExcelFiles.map(
                        file => file.name
                    )
                })
            }
        );

        const result = await response.json();

        console.log(result);

        populateFileTable(result.uploaded);

    }
    catch(error) {

        console.error(
            "Error checking uploaded files:",
            error
        );

        populateFileTable([]);
    }
}

/**
 * Updates summary information
 */
function updateFolderInfo() {

    const folderInfo =
        document.getElementById("folderInfo");

    if (!folderInfo) return;

    folderInfo.innerHTML = `
        <strong>Excel files found:</strong>
        ${selectedExcelFiles.length}
    `;
}

/**
 * Populates table
 */
function populateFileTable(uploadedFiles = []) {

    const tableBody = document.getElementById("fileBody");

    tableBody.innerHTML = "";

    selectedExcelFiles.forEach((file,index) => {

        const uploaded = uploadedFiles.includes(file.name);

        const row = document.createElement("tr");

        row.innerHTML = `
            <td>
                ${
                    uploaded
                    ? ''
                    : `<input type="checkbox"
                            class="fileCheckbox"
                            value="${index}"
                            checked>`
                }
            </td>

            <td>${file.name}</td>

            <td>
                ${
                    uploaded
                    ? 'Already imported'
                    : 'New'
                }
            </td>
        `;

        tableBody.appendChild(row);
    });
}

/*** Upload selected files ***/
async function uploadSelectedFiles() {

    const selectedIndexes = [
        ...document.querySelectorAll(
            ".fileCheckbox:checked"
        )
    ].map(cb => parseInt(cb.value));

    if (selectedIndexes.length === 0) {

        alert("No files selected.");
        return;
    }

    const formData = new FormData();

    selectedIndexes.forEach(index => {

        const file = selectedExcelFiles[index];

        console.log("INDEX:", index);
        console.log("FILE:", file);

        console.log("selectedExcelFiles:", selectedExcelFiles);
        console.log("selectedIndexes:", selectedIndexes);

        formData.append(
            "files",
            file,
            file.name
        );
    });

    console.log("FORM DATA:");


    for (const pair of formData.entries()) {

        console.log(
            pair[0],
            pair[1],
            pair[1] instanceof File
        );
    }

    try {

        console.log("FormData contents:");

        for (const pair of formData.entries()) {
            console.log(pair[0], pair[1]);
        }
        
        const response = await fetch("/api/upload-files",{method: "POST", body: formData});

        const result = await response.json();

        alert(
            `Imported: ${result.imported_count}\n` +
            `Failed: ${result.failed_count}`
        );

    } catch(error) {

        console.error(error);

        alert("Error uploading files.");
    }
}

/*** Connect button ***/
document.addEventListener("click", event => {

    if (event.target.id === "uploadButton") {

        uploadSelectedFiles();
    }
});

