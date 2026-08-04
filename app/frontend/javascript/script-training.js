console.log("Training script loaded");

document.addEventListener(
    "DOMContentLoaded",
    initializeTrainingPage
);

function initializeTrainingPage(){

    preselectFeatures();

    const trainButton =
        document.getElementById(
            "trainButton"
        );

    trainButton.addEventListener(
        "click",
        trainModel
    );
}

function preselectFeatures(){

    const defaults = [

        "force_kn",
        "displacement_mm",
        "sample_height_mm",
        "water_content",
        "density_kg_m3"

    ];

    document
        .querySelectorAll(
            'input[type="checkbox"]'
        )
        .forEach(cb => {

            if(
                defaults.includes(
                    cb.value
                )
            ){
                cb.checked = true;
            }

        });

}

function getConfiguration(){

    const inputFeatures =
        [
            ...document.querySelectorAll(
                '#timeseriesFeatures input:checked'
            )
        ]
        .map(cb => cb.value);

    const staticFeatures =
        [
            ...document.querySelectorAll(
                '#staticFeatures input:checked'
            )
        ]
        .map(cb => cb.value);

    const targets =
        [
            ...document.querySelectorAll(
                '#targetFeatures input:checked'
            )
        ]
        .map(cb => cb.value);

    return {

        model:
            document.getElementById(
                "modelSelect"
            ).value,

        lookback_steps:
            parseInt(
                document.getElementById(
                    "lookbackSteps"
                ).value
            ),

        horizon:
            parseInt(
                document.getElementById(
                    "forecastHorizon"
                ).value
            ),

        inputs:
            inputFeatures,

        static_inputs:
            staticFeatures,

        targets:
            targets,

        epochs:
            parseInt(
                document.getElementById(
                    "epochs"
                ).value
            ),

        batch_size:
            parseInt(
                document.getElementById(
                    "batchSize"
                ).value
            ),

        learning_rate:
            parseFloat(
                document.getElementById(
                    "learningRate"
                ).value
            ),

        dropout:
            parseFloat(
                document.getElementById(
                    "dropout"
                ).value
            ),

        units:
            parseInt(
                document.getElementById(
                    "units"
                ).value
            )
    };
}


async function trainModel(){

    const config =
        getConfiguration();

    if(config.inputs.length === 0){

        alert(
            "Select at least one input variable."
        );

        return;
    }

    if(config.targets.length === 0){

        alert(
            "Select at least one target variable."
        );

        return;
    }


    try{

        const response =
            await fetch(
                "/api/train-model",
                {
                    method:"POST",
                    headers:{
                        "Content-Type":
                            "application/json"
                    },
                    body:JSON.stringify(
                        config
                    )
                }
            );

        const result =
            await response.json();

        updateMetrics(result);

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
    catch(error){

        console.error(error);

        alert(
            "Training failed."
        );

    }
}

function updateMetrics(result){

    document.getElementById(
        "maeValue"
    ).innerText =
        result.mae.toFixed(4);

    document.getElementById(
        "rmseValue"
    ).innerText =
        result.rmse.toFixed(4);

    document.getElementById(
        "r2Value"
    ).innerText =
        result.r2.toFixed(4);

}

function updateBenchmarkTable(
    result
){

    document.getElementById(
        "modelMae"
    ).innerText =
        result.mae.toFixed(4);

    document.getElementById(
        "modelRmse"
    ).innerText =
        result.rmse.toFixed(4);

    document.getElementById(
        "modelR2"
    ).innerText =
        result.r2.toFixed(4);

    document.getElementById(
        "persMae"
    ).innerText =
        result.persistence.mae;

    document.getElementById(
        "persRmse"
    ).innerText =
        result.persistence.rmse;

    document.getElementById(
        "persR2"
    ).innerText =
        result.persistence.r2;

    document.getElementById(
        "maMae"
    ).innerText =
        result.moving_average.mae;

    document.getElementById(
        "maRmse"
    ).innerText =
        result.moving_average.rmse;

    document.getElementById(
        "maR2"
    ).innerText =
        result.moving_average.r2;

    document.getElementById(
        "trendMae"
    ).innerText =
        result.linear_trend.mae;

    document.getElementById(
        "trendRmse"
    ).innerText =
        result.linear_trend.rmse;

    document.getElementById(
        "trendR2"
    ).innerText =
        result.linear_trend.r2;

}

function renderPredictionPlot(
    result
){

    Plotly.newPlot(
        "predictionPlot",
        [

            {
                y:result.actual,
                mode:"lines",
                name:"Actual"
            },

            {
                y:result.predicted,
                mode:"lines",
                name:"Model"
            },

            {
                y:result.naive,
                mode:"lines",
                name:"Naive"
            }

        ],

        {
            title:
                "Actual vs Predictions"
        },

        {
            responsive:true
        }
    );

}

function renderTrainingHistory(
    result
){

    Plotly.newPlot(
        "trainingHistoryPlot",

        [
            {
                y:result.loss,
                mode:"lines",
                name:"Loss"
            },

            {
                y:result.val_loss,
                mode:"lines",
                name:"Validation Loss"
            }
        ],

        {
            title:
                "Training History"
        },

        {
            responsive:true
        }
    );

}