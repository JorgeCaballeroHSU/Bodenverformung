console.log("Grid-search training script loaded");

document.addEventListener(
    "DOMContentLoaded",
    initializeTrainingPage
);


/* ================================================================
   CONSTANTS
   ================================================================ */

const benchmarkDefinitions = [
    {
        key: "persistence",
        label: "Persistence",
        color: "#2474b5",
        symbol: "circle"
    },
    {
        key: "moving_average",
        label: "Moving Average",
        color: "#e58224",
        symbol: "diamond"
    },
    {
        key: "linear_trend",
        label: "Linear Trend",
        color: "#2f8f55",
        symbol: "square"
    }
];


const listInputIds = [
    "lookbackSteps",
    "forecastHorizons",
    "epochs",
    "batchSizes",
    "learningRates",
    "dropouts",
    "units"
];


/* ================================================================
   INITIALIZATION
   ================================================================ */

async function initializeTrainingPage() {

    preselectFeatures();

    registerEventListeners();

    calculateExperimentCount();

    await loadExistingExperiments();
}


function registerEventListeners() {

    const trainButton = document.getElementById(
        "trainButton"
    );

    if (trainButton) {

        trainButton.addEventListener(
            "click",
            trainModel
        );
    }


    listInputIds.forEach(elementId => {

        const element = document.getElementById(
            elementId
        );

        if (element) {

            element.addEventListener(
                "input",
                calculateExperimentCount
            );
        }
    });
}


function preselectFeatures() {

    const defaultInputs = [
        "force_kn",
        "displacement_mm",
        "sample_height_mm",
        "water_content",
        "density_kg_m3"
    ];

    document
        .querySelectorAll(
            "#timeseriesFeatures input, #staticFeatures input"
        )
        .forEach(checkbox => {

            checkbox.checked = defaultInputs.includes(
                checkbox.value
            );
        });


    const defaultTargets = [
        "force_kn"
    ];

    document
        .querySelectorAll(
            "#targetFeatures input"
        )
        .forEach(checkbox => {

            checkbox.checked = defaultTargets.includes(
                checkbox.value
            );
        });
}

/* ================================================================
   CONFIGURATION PARSING
   ================================================================ */

function parseIntegerList(elementId) {

    const element = document.getElementById(
        elementId
    );

    if (!element) {
        throw new Error(
            `Element "${elementId}" was not found.`
        );
    }

    const rawValues = element.value
        .split(",")
        .map(value => value.trim())
        .filter(value => value !== "");

    if (rawValues.length === 0) {
        return [];
    }

    const values = rawValues.map(value => {

        const numericValue = Number(value);

        if (!Number.isInteger(numericValue)) {
            throw new Error(
                `The field "${elementId}" contains an invalid integer: ${value}.`
            );
        }

        return numericValue;
    });

    return [
        ...new Set(values)
    ];
}


function parseFloatList(elementId) {

    const element = document.getElementById(
        elementId
    );

    if (!element) {
        throw new Error(
            `Element "${elementId}" was not found.`
        );
    }

    const rawValues = element.value
        .split(",")
        .map(value => value.trim())
        .filter(value => value !== "");

    if (rawValues.length === 0) {
        return [];
    }

    const values = rawValues.map(value => {

        const numericValue = Number(value);

        if (!Number.isFinite(numericValue)) {
            throw new Error(
                `The field "${elementId}" contains an invalid number: ${value}.`
            );
        }

        return numericValue;
    });

    return [
        ...new Set(values)
    ];
}


function getCheckedValues(selector) {

    return [
        ...document.querySelectorAll(
            selector
        )
    ].map(
        checkbox => checkbox.value
    );
}


function getConfiguration() {

    const modelSelect = document.getElementById(
        "modelSelect"
    );

    const trainSplitElement = document.getElementById(
        "trainSplit"
    );

    const validationSplitElement = document.getElementById(
        "validationSplit"
    );

    const testSplitElement = document.getElementById(
        "testSplit"
    );

    if (
        !modelSelect ||
        !trainSplitElement ||
        !validationSplitElement ||
        !testSplitElement
    ) {
        throw new Error(
            "One or more configuration controls are missing from the HTML."
        );
    }

    return {
        model: modelSelect.value,

        lookback_steps: parseIntegerList(
            "lookbackSteps"
        ),

        horizons: parseIntegerList(
            "forecastHorizons"
        ),

        inputs: getCheckedValues(
            "#timeseriesFeatures input:checked"
        ),

        static_inputs: getCheckedValues(
            "#staticFeatures input:checked"
        ),

        targets: getCheckedValues(
            "#targetFeatures input:checked"
        ),

        train_split: Number(
            trainSplitElement.value
        ),

        validation_split: Number(
            validationSplitElement.value
        ),

        test_split: Number(
            testSplitElement.value
        ),

        epochs: parseIntegerList(
            "epochs"
        ),

        batch_sizes: parseIntegerList(
            "batchSizes"
        ),

        learning_rates: parseFloatList(
            "learningRates"
        ),

        dropouts: parseFloatList(
            "dropouts"
        ),

        units: parseIntegerList(
            "units"
        )
    };
}


function calculateExperimentCount() {

    const countElement = document.getElementById(
        "experimentCount"
    );

    if (!countElement) {
        return 0;
    }

    try {
        const config = getConfiguration();

        const totalExperiments =
            config.lookback_steps.length *
            config.horizons.length *
            config.epochs.length *
            config.batch_sizes.length *
            config.learning_rates.length *
            config.dropouts.length *
            config.units.length;

        countElement.innerText =
            totalExperiments.toLocaleString();

        countElement.dataset.count =
            String(totalExperiments);

        return totalExperiments;

    } catch (error) {

        countElement.innerText = "—";

        countElement.dataset.count = "0";

        return 0;
    }
}


/* ================================================================
   CONFIGURATION VALIDATION
   ================================================================ */

function validateConfiguration(config) {

    if (
        config.inputs.length === 0 &&
        config.static_inputs.length === 0
    ) {
        throw new Error(
            "Select at least one input variable."
        );
    }

    if (config.targets.length === 0) {
        throw new Error(
            "Select at least one prediction target."
        );
    }

    if (config.lookback_steps.length === 0) {
        throw new Error(
            "Provide at least one lookback value."
        );
    }

    if (config.horizons.length === 0) {
        throw new Error(
            "Provide at least one forecast horizon."
        );
    }

    if (config.epochs.length === 0) {
        throw new Error(
            "Provide at least one epoch value."
        );
    }

    if (config.batch_sizes.length === 0) {
        throw new Error(
            "Provide at least one batch size."
        );
    }

    if (config.learning_rates.length === 0) {
        throw new Error(
            "Provide at least one learning rate."
        );
    }

    if (config.dropouts.length === 0) {
        throw new Error(
            "Provide at least one dropout value."
        );
    }

    if (config.units.length === 0) {
        throw new Error(
            "Provide at least one units value."
        );
    }

    if (
        config.lookback_steps.some(
            value => value < 1
        )
    ) {
        throw new Error(
            "Lookback values must be at least 1."
        );
    }

    if (
        config.horizons.some(
            value => value < 1
        )
    ) {
        throw new Error(
            "Forecast horizons must be at least 1."
        );
    }

    if (
        config.epochs.some(
            value => value < 1
        )
    ) {
        throw new Error(
            "Epoch values must be at least 1."
        );
    }

    if (
        config.batch_sizes.some(
            value => value < 1
        )
    ) {
        throw new Error(
            "Batch sizes must be at least 1."
        );
    }

    if (
        config.learning_rates.some(
            value => value <= 0
        )
    ) {
        throw new Error(
            "Learning rates must be greater than zero."
        );
    }

    if (
        config.dropouts.some(
            value => value < 0 || value >= 1
        )
    ) {
        throw new Error(
            "Dropout values must satisfy 0 <= dropout < 1."
        );
    }

    if (
        config.units.some(
            value => value < 1
        )
    ) {
        throw new Error(
            "Units must be at least 1."
        );
    }

    if (
        !Number.isFinite(config.train_split) ||
        !Number.isFinite(config.validation_split) ||
        !Number.isFinite(config.test_split)
    ) {
        throw new Error(
            "Dataset split values must be valid numbers."
        );
    }

    if (
        config.train_split <= 0 ||
        config.validation_split <= 0 ||
        config.test_split <= 0
    ) {
        throw new Error(
            "Training, validation, and testing percentages must be greater than zero."
        );
    }

    const totalSplit =
        config.train_split +
        config.validation_split +
        config.test_split;

    if (
        Math.abs(totalSplit - 100) > 0.01
    ) {
        throw new Error(
            "Training, validation, and testing percentages must add up to 100."
        );
    }

    const totalExperiments =
        calculateExperimentCount();

    if (totalExperiments === 0) {
        throw new Error(
            "No experiment combinations were generated."
        );
    }

    if (totalExperiments > 100) {
        throw new Error(
            `The configuration generates ${totalExperiments} experiments. ` +
            "The maximum allowed is 100."
        );
    }
}

/* ================================================================
   TRAINING REQUEST
   ================================================================ */

async function trainModel() {

    let config;

    try {

        config = getConfiguration();

        validateConfiguration(
            config
        );

    } catch (error) {

        alert(
            error.message
        );

        return;
    }


    setTrainingState(
        "running",
        "RUNNING"
    );

    setTrainingMessage(
        "The experiment grid is running. Keep this page open until the backend returns the results."
    );


    try {

        const response = await fetch(
            "/api/train-model",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify(
                    config
                )
            }
        );


        const result = await response.json();


        if (!response.ok) {

            const detail =
                result.detail ?? "Training failed.";

            throw new Error(
                typeof detail === "string"
                    ? detail
                    : JSON.stringify(detail)
            );
        }


        console.log(
            "Training response:",
            result
        );


        if (!result.best_result) {

            throw new Error(
                "The backend did not return a best experiment."
            );
        }


        const completedExperiments =
            Array.isArray(result.experiments)
                ? result.experiments.filter(
                    experiment =>
                        experiment.status === "completed"
                )
                : [];


        renderBestExperiment(
            result.best_result
        );


        renderAllComparisonPlots(
            completedExperiments
        );


        setTrainingState(
            "completed",
            "COMPLETED"
        );


        setTrainingMessage(
            `${result.completed_runs} experiments completed. ` +
            `${result.failed_runs} experiments failed. ` +
            "The best experiment is displayed."
        );

    } catch (error) {

        console.error(
            "Training request failed:",
            error
        );


        setTrainingState(
            "failed",
            "FAILED"
        );


        setTrainingMessage(
            error.message
        );


        alert(
            error.message
        );
    }
}


/* ================================================================
   STATUS
   ================================================================ */

function setTrainingState(state, label) {

    const status = document.getElementById(
        "trainingStatus"
    );

    const button = document.getElementById(
        "trainButton"
    );

    if (status) {

        status.className =
            "status-indicator";

        status.classList.add(
            `status-${state}`
        );

        status.innerText =
            label;
    }

    if (button) {

        button.disabled =
            state === "running";
    }
}


function setTrainingMessage(message) {

    const element = document.getElementById(
        "trainingMessage"
    );

    if (element) {

        element.innerText =
            message;
    }
}


/* ================================================================
   BEST EXPERIMENT
   ================================================================ */

function renderBestExperiment(result) {

    updateBestConfiguration(
        result
    );

    updateMetrics(
        result
    );

    updateBenchmarkTable(
        result
    );

    renderPredictionPlot(
        result
    );

    renderTrainingHistory(
        result
    );
}


function updateBestConfiguration(result) {

    setText(
        "bestExperimentId",
        result.experiment_id
            ? `Experiment ${result.experiment_id}`
            : "Experiment —"
    );

    setText(
        "bestModel",
        result.model
    );

    setText(
        "bestLookback",
        result.lookback_steps
    );

    setText(
        "bestHorizon",
        result.horizon
    );

    setText(
        "bestEpochs",
        result.epochs
    );

    setText(
        "bestBatchSize",
        result.batch_size
    );

    setText(
        "bestLearningRate",
        formatScientific(
            result.learning_rate
        )
    );

    setText(
        "bestDropout",
        result.dropout
    );

    setText(
        "bestUnits",
        result.units
    );
}


function updateMetrics(result) {

    setMetricValue(
        "maeValue",
        result.mae
    );

    setMetricValue(
        "rmseValue",
        result.rmse
    );

    setMetricValue(
        "r2Value",
        result.r2
    );
}


function updateBenchmarkTable(result) {

    setMetricValue(
        "modelMae",
        result.mae
    );

    setMetricValue(
        "modelRmse",
        result.rmse
    );

    setMetricValue(
        "modelR2",
        result.r2
    );


    setMetricValue(
        "persMae",
        result.persistence?.mae
    );

    setMetricValue(
        "persRmse",
        result.persistence?.rmse
    );

    setMetricValue(
        "persR2",
        result.persistence?.r2
    );


    setMetricValue(
        "maMae",
        result.moving_average?.mae
    );

    setMetricValue(
        "maRmse",
        result.moving_average?.rmse
    );

    setMetricValue(
        "maR2",
        result.moving_average?.r2
    );


    setMetricValue(
        "trendMae",
        result.linear_trend?.mae
    );

    setMetricValue(
        "trendRmse",
        result.linear_trend?.rmse
    );

    setMetricValue(
        "trendR2",
        result.linear_trend?.r2
    );

    setMetricValue(
        "maMae",
        result.moving_average?.mae
    );

    setMetricValue(
        "maRmse",
        result.moving_average?.rmse
    );

    setMetricValue(
        "maR2",
        result.moving_average?.r2
    );


    setMetricValue(
        "trendMae",
        result.linear_trend?.mae
    );

    setMetricValue(
        "trendRmse",
        result.linear_trend?.rmse
    );

    setMetricValue(
        "trendR2",
        result.linear_trend?.r2
    );
}


/* ================================================================
   BENCHMARK SCATTER PLOTS
   ================================================================ */

function renderAllComparisonPlots(experiments) {

    renderMetricComparisonPlot(
        experiments,
        "mae",
        "maeComparisonPlot",
        "MAE",
        false
    );

    renderMetricComparisonPlot(
        experiments,
        "rmse",
        "rmseComparisonPlot",
        "RMSE",
        false
    );

    renderMetricComparisonPlot(
        experiments,
        "r2",
        "r2ComparisonPlot",
        "R²",
        true
    );
}


function renderMetricComparisonPlot(
    experiments,
    metricKey,
    elementId,
    metricLabel,
    higherIsBetter
) {

    const plotElement = document.getElementById(
        elementId
    );

    if (!plotElement) {

        console.error(
            `Plot container "${elementId}" was not found.`
        );

        return;
    }


    if (typeof Plotly === "undefined") {

        plotElement.innerHTML =
            "<p>Plotly could not be loaded.</p>";

        console.error(
            "Plotly is not loaded."
        );

        return;
    }


    const validExperiments =
        Array.isArray(experiments)
            ? experiments.filter(
                experiment =>
                    experiment.status === undefined ||
                    experiment.status === "completed"
            )
            : [];


    const traces = [];

    const allValues = [];


    benchmarkDefinitions.forEach(
        benchmark => {

            const xValues = [];

            const yValues = [];

            const hoverText = [];


            validExperiments.forEach(
                experiment => {

                    const annValue = Number(
                        experiment[metricKey]
                    );

                    const benchmarkValue = Number(
                        experiment[
                            benchmark.key
                        ]?.[metricKey]
                    );


                    if (
                        !Number.isFinite(annValue) ||
                        !Number.isFinite(benchmarkValue)
                    ) {

                        return;
                    }


                    xValues.push(
                        benchmarkValue
                    );

                    yValues.push(
                        annValue
                    );

                    allValues.push(
                        benchmarkValue,
                        annValue
                    );


                    const difference =
                        annValue - benchmarkValue;


                    let resultLabel;


                    if (
                        Math.abs(difference) < 1e-12
                    ) {

                        resultLabel =
                            "Approximately equal";

                    } else {

                        const annWins =
                            higherIsBetter
                                ? annValue > benchmarkValue
                                : annValue < benchmarkValue;


                        resultLabel =
                            annWins
                                ? "ANN better"
                                : `${benchmark.label} better`;
                    }


                    hoverText.push(
                        buildExperimentHoverText(
                            experiment,
                            benchmark.label,
                            metricLabel,
                            annValue,
                            benchmarkValue,
                            difference,
                            resultLabel
                        )
                    );
                }
            );


            traces.push({
                type: "scatter",

                mode: "markers",

                name: benchmark.label,

                x: xValues,

                y: yValues,

                text: hoverText,

                hovertemplate:
                    "%{text}<extra></extra>",

                marker: {
                    color: benchmark.color,

                    symbol: benchmark.symbol,

                    size: 10,

                    opacity: 0.8,

                    line: {
                        color: "#ffffff",

                        width: 1
                    }
                }
            });
        }
    );


    let minimum = 0;

    let maximum = 1;


    if (allValues.length > 0) {

        minimum = Math.min(
            ...allValues
        );

        maximum = Math.max(
            ...allValues
        );


        if (
            metricKey !== "r2" &&
            minimum > 0
        ) {

            minimum = 0;
        }


        const span =
            maximum - minimum;


        const padding =
            span > 0
                ? span * 0.08
                : Math.max(
                    Math.abs(maximum) * 0.08,
                    0.01
                );


        minimum -= padding;

        maximum += padding;
    }


    traces.push({
        type: "scatter",

        mode: "lines",

        name: "Equal performance",

        x: [
            minimum,
            maximum
        ],

        y: [
            minimum,
            maximum
        ],

        hoverinfo: "skip",

        line: {
            color: "#626972",

            width: 2,

            dash: "dash"
        }
    });


    Plotly.react(
        elementId,
        traces,
        {
            margin: {
                l: 75,

                r: 30,

                t: 45,

                b: 70
            },

            paper_bgcolor:
                "#ffffff",

            plot_bgcolor:
                "#ffffff",

            hovermode:
                "closest",

            legend: {
                orientation:
                    "h",

                x:
                    0,

                y:
                    1.12
            },

            xaxis: {
                title: {
                    text:
                        `Naive-model ${metricLabel}`
                },

                range: [
                    minimum,
                    maximum
                ],

                gridcolor:
                    "#e5e8eb",

                zerolinecolor:
                    "#b8bec6",

                constrain:
                    "domain"
            },

            yaxis: {
                title: {
                    text:
                        `ANN ${metricLabel}`
                },

                range: [
                    minimum,
                    maximum
                ],

                gridcolor:
                    "#e5e8eb",

                zerolinecolor:
                    "#b8bec6",

                scaleanchor:
                    "x",

                scaleratio:
                    1
            }
        },
        {
            responsive:
                true,

            displaylogo:
                false
        }
    );
}


function buildExperimentHoverText(
    experiment,
    benchmarkLabel,
    metricLabel,
    annValue,
    benchmarkValue,
    difference,
    resultLabel
) {

    return [
        `<b>Experiment ${experiment.experiment_id ?? "—"}</b>`,

        `Benchmark: ${benchmarkLabel}`,

        `Metric: ${metricLabel}`,

        `ANN: ${formatMetric(annValue)}`,

        `Benchmark: ${formatMetric(benchmarkValue)}`,

        `Difference: ${formatMetric(difference)}`,

        `Result: ${resultLabel}`,

        "",

        `Model: ${experiment.model ?? "—"}`,

        `Lookback: ${experiment.lookback_steps ?? "—"}`,

        `Horizon: ${experiment.horizon ?? "—"}`,

        `Epochs: ${experiment.epochs ?? "—"}`,

        `Batch size: ${experiment.batch_size ?? "—"}`,

        `Learning rate: ${formatScientific(experiment.learning_rate)}`,

        `Dropout: ${experiment.dropout ?? "—"}`,

        `Units: ${experiment.units ?? "—"}`
    ].join(
        "<br>"
    );
}


function buildExperimentHoverText(
    experiment,
    benchmarkLabel,
    metricLabel,
    annValue,
    benchmarkValue,
    difference,
    resultLabel
) {

    return [
        `<b>Experiment ${experiment.experiment_id ?? "—"}</b>`,
        `Benchmark: ${benchmarkLabel}`,
        `Metric: ${metricLabel}`,
        `ANN: ${formatMetric(annValue)}`,
        `Benchmark: ${formatMetric(benchmarkValue)}`,
        `Difference: ${formatMetric(difference)}`,
        `Result: ${resultLabel}`,
        "",
        `Model: ${experiment.model ?? "—"}`,
        `Lookback: ${experiment.lookback_steps ?? "—"}`,
        `Horizon: ${experiment.horizon ?? "—"}`,
        `Epochs: ${experiment.epochs ?? "—"}`,
        `Batch size: ${experiment.batch_size ?? "—"}`,
        `Learning rate: ${formatScientific(experiment.learning_rate)}`,
        `Dropout: ${experiment.dropout ?? "—"}`,
        `Units: ${experiment.units ?? "—"}`
    ].join("<br>");
}

/* ================================================================
   BEST-EXPERIMENT PREDICTION PLOT
   ================================================================ */

function renderPredictionPlot(result) {

    const container = document.getElementById(
        "predictionPlots"
    );

    const selector = document.getElementById(
        "plotTarget"
    );

    if (!container || !selector) {

        console.error(
            "Prediction plot container or target selector was not found."
        );

        return;
    }

    container.innerHTML = "";

    selector.innerHTML = "";

    if (
        !Array.isArray(result.samples) ||
        result.samples.length === 0
    ) {

        container.innerHTML =
            '<p class="chart-explanation">' +
            "Prediction curves are unavailable." +
            "</p>";

        return;
    }

    const targets = Object.keys(
        result.samples[0].plots ?? {}
    );

    if (targets.length === 0) {

        container.innerHTML =
            '<p class="chart-explanation">' +
            "No prediction targets are available." +
            "</p>";

        return;
    }

    targets.forEach(target => {

        selector.add(
            new Option(
                target,
                target
            )
        );
    });


    function drawTarget(target) {

        const traces = [];

        result.samples.forEach(
            (sample, sampleIndex) => {

                const targetPlot =
                    sample.plots?.[target];

                if (
                    !targetPlot ||
                    !Array.isArray(targetPlot.actual) ||
                    !Array.isArray(targetPlot.predicted)
                ) {
                    return;
                }

                const colors =
                    getPredictionColors(
                        sampleIndex
                    );

                traces.push({
                    type: "scatter",

                    mode: "lines",

                    name:
                        `Actual Test ${sample.test_id}`,

                    y:
                        targetPlot.actual,

                    line: {
                        color:
                            colors.actual,

                        width:
                            2
                    }
                });

                traces.push({
                    type: "scatter",

                    mode: "lines",

                    name:
                        `Predicted Test ${sample.test_id}`,

                    y:
                        targetPlot.predicted,

                    line: {
                        color:
                            colors.predicted,

                        width:
                            2,

                        dash:
                            "dot"
                    }
                });
            }
        );

        if (traces.length === 0) {

            container.innerHTML =
                '<p class="chart-explanation">' +
                `No valid plot data are available for ${target}.` +
                "</p>";

            return;
        }

        if (typeof Plotly === "undefined") {

            container.innerHTML =
                '<p class="chart-explanation">' +
                "Plotly could not be loaded." +
                "</p>";

            console.error(
                "Plotly is not available."
            );

            return;
        }

        Plotly.react(
            "predictionPlots",
            traces,
            {
                title: {
                    text:
                        `Actual vs Predicted | ${target}`
                },

                margin: {
                    l:
                        75,

                    r:
                        40,

                    t:
                        60,

                    b:
                        65
                },

                paper_bgcolor:
                    "#ffffff",

                plot_bgcolor:
                    "#ffffff",

                hovermode:
                    "x unified",

                xaxis: {
                    title: {
                        text:
                            "Sequence index"
                    },

                    gridcolor:
                        "#e5e8eb",

                    zerolinecolor:
                        "#b8bec6"
                },

                yaxis: {
                    title: {
                        text:
                            target
                    },

                    gridcolor:
                        "#e5e8eb",

                    zerolinecolor:
                        "#b8bec6"
                },

                legend: {
                    orientation:
                        "v",

                    x:
                        1.01,

                    y:
                        1
                }
            },
            {
                responsive:
                    true,

                displaylogo:
                    false
            }
        );
    }

    drawTarget(
        targets[0]
    );

    selector.onchange = () => {

        drawTarget(
            selector.value
        );
    };
}


function getPredictionColors(index) {

    const colorPairs = [
        {
            actual:
                "#2474b5",

            predicted:
                "#e58224"
        },
        {
            actual:
                "#2f8f55",

            predicted:
                "#c73535"
        },
        {
            actual:
                "#7b55a3",

            predicted:
                "#795548"
        }
    ];

    return colorPairs[
        index % colorPairs.length
    ];
}