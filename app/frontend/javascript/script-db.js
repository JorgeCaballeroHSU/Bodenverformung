console.log("Database script loaded - VERSION 999");

let selectedExcelFiles = [];

/*** Wait until page is loaded ***/
document.addEventListener("DOMContentLoaded", () => {

    const folderPicker =
        document.getElementById("folderPicker");

    if (!folderPicker) {
        console.error("folderPicker not found");
        return;
    }

    folderPicker.addEventListener(
        "change",
        handleFolderSelection
    );

    loadDashboard();

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

        /*** Loads the dashboard***/
        loadDashboard()

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

/*** main dashboard loader***/
async function loadDashboard(){

    try{

        loadSummary();
        loadStressStrain();
        loadForceDisplacement();
        loadStressHistogram();
        loadStrainHistogram();
        loadCorrelationMatrix();

    }
    catch(error){

        console.error(
            "Dashboard loading error:",
            error
        );

    }

}

/***KPI cards***/
async function loadSummary(){

    const response =
        await fetch("/api/database-summary");

    const data =
        await response.json();

    document.getElementById(
        "totalTests"
    ).innerText =
        data.total_tests;

    document.getElementById(
        "totalMeasurements"
    ).innerText =
        data.total_measurements;

    document.getElementById(
        "avgStress"
    ).innerText =
        data.avg_stress.toFixed(2);

    document.getElementById(
        "maxForce"
    ).innerText =
        data.max_force.toFixed(2);

}

/***Stress-Strian Plot ***/
async function loadStressStrain(){

    const response =
        await fetch("/api/stress-strain");

    const data =
        await response.json();

    Plotly.newPlot(
        "stressStrainPlot",
        [
            {
                x:data.strain_pct,
                y:data.stress_kpa,
                mode:"markers",
                type:"scatter",
                marker:{
                    size:4
                }
            }
        ],
        {
            title:"Stress vs Strain",
            xaxis:{
                title:"Strain (%)"
            },
            yaxis:{
                title:"Stress (kPa)"
            }
        },
        {
            responsive:true
        }
    );

}

/*** Force vs Displacement***/
async function loadForceDisplacement(){

    const response =
        await fetch("/api/force-displacement");

    const data =
        await response.json();

    Plotly.newPlot(
        "forceDisplacementPlot",
        [
            {
                x:data.displacement_mm,
                y:data.force_kn,
                mode:"markers",
                type:"scatter"
            }
        ],
        {
            title:"Force vs Displacement",
            xaxis:{
                title:"Displacement (mm)"
            },
            yaxis:{
                title:"Force (kN)"
            }
        },
        {
            responsive:true
        }
    );

}

/***Stress Histogram***/
async function loadStressHistogram(){

    const response =
        await fetch("/api/stress-histogram");

    const data =
        await response.json();

    Plotly.newPlot(
        "stressHistogram",
        [
            {
                x:data.stress_kpa,
                type:"histogram"
            }
        ],
        {
            title:"Stress Distribution"
        },
        {
            responsive:true
        }
    );

}

/***Strain Histogram***/
async function loadStrainHistogram(){

    const response =
        await fetch("/api/strain-histogram");

    const data =
        await response.json();

    Plotly.newPlot(
        "strainHistogram",
        [
            {
                x:data.strain_pct,
                type:"histogram"
            }
        ],
        {
            title:"Strain Distribution"
        },
        {
            responsive:true
        }
    );

}

/***Correlation Matrix***/
async function loadCorrelationMatrix(){

    const response =
        await fetch("/api/correlation");

    const data =
        await response.json();

    Plotly.newPlot(
        "correlationMatrix",
        [
            {
                z:data.matrix,
                x:data.columns,
                y:data.columns,
                type:"heatmap",
                colorscale:"Viridis"
            }
        ],
        {
            title:"Correlation Matrix"
        },
        {
            responsive:true
        }
    );

}



