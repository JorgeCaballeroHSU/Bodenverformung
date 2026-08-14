console.log("Training script loaded");

document.addEventListener(
    "DOMContentLoaded",
    initializeTrainingPage
);

async function loadLatestExperiment(){

    try{

        const response =
            await fetch(
                "/api/latest-experiment"
            );

        const experiment =
            await response.json();

        if(!experiment){
            return;
        }

        document.getElementById(
            "maeValue"
        ).innerText =
            Number(
                experiment.mae
            ).toFixed(4);

        document.getElementById(
            "rmseValue"
        ).innerText =
            Number(
                experiment.rmse
            ).toFixed(4);

        document.getElementById(
            "r2Value"
        ).innerText =
            Number(
                experiment.r2
            ).toFixed(4);

        populateBenchmarkFromExperiment(experiment)

    }

    catch(error){

        console.error(
            "Unable to load latest experiment",
            error
        );

    }

}

function populateBenchmarkFromExperiment(
    experiment
){
    document.getElementById(
        "modelMae"
    ).innerText =
        Number(
            experiment.mae
        ).toFixed(4);

    document.getElementById(
        "modelRmse"
    ).innerText =
        Number(
            experiment.rmse
        ).toFixed(4);

    document.getElementById(
        "modelR2"
    ).innerText =
        Number(
            experiment.r2
        ).toFixed(4);

    document.getElementById(
        "persMae"
    ).innerText =
        Number(
            experiment.persistence_mae
        ).toFixed(4);

    document.getElementById(
        "persRmse"
    ).innerText =
        Number(
            experiment.persistence_rmse
        ).toFixed(4);

    document.getElementById(
        "persR2"
    ).innerText =
        Number(
            experiment.persistence_r2
        ).toFixed(4);

    document.getElementById(
        "maMae"
    ).innerText =
        Number(
            experiment.moving_average_mae
        ).toFixed(4);

    document.getElementById(
        "maRmse"
    ).innerText =
        Number(
            experiment.moving_average_rmse
        ).toFixed(4);

    document.getElementById(
        "maR2"
    ).innerText =
        Number(
            experiment.moving_average_r2
        ).toFixed(4);

    document.getElementById(
        "trendMae"
    ).innerText =
        Number(
            experiment.linear_trend_mae
        ).toFixed(4);

    document.getElementById(
        "trendRmse"
    ).innerText =
        Number(
            experiment.linear_trend_rmse
        ).toFixed(4);

    document.getElementById(
        "trendR2"
    ).innerText =
        Number(
            experiment.linear_trend_r2
        ).toFixed(4);
}

function initializeTrainingPage(){

    preselectFeatures();
    loadLatestExperiment();

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

        train_split:
            parseFloat(
                document.getElementById(
                    "trainSplit"
                ).value
            ),

        validation_split:
            parseFloat(
                document.getElementById(
                    "validationSplit"
                ).value
            ),

        test_split:
            parseFloat(
                document.getElementById(
                    "testSplit"
                ).value
            ),

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

    const totalSplit =
        config.train_split +
        config.validation_split +
        config.test_split;

    if(Math.abs(totalSplit - 100) > 0.01){

        alert(
            "Train, Validation and Test percentages must add up to 100."
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
        result.persistence.mae.toFixed(4);

    document.getElementById(
        "persRmse"
    ).innerText =
        result.persistence.rmse.toFixed(4);

    document.getElementById(
        "persR2"
    ).innerText =
        result.persistence.r2.toFixed(4);

    document.getElementById(
        "maMae"
    ).innerText =
        result.moving_average.mae.toFixed(4);

    document.getElementById(
        "maRmse"
    ).innerText =
        result.moving_average.rmse.toFixed(4);

    document.getElementById(
        "maR2"
    ).innerText =
        result.moving_average.r2.toFixed(4);

    document.getElementById(
        "trendMae"
    ).innerText =
        result.linear_trend.mae.toFixed(4);

    document.getElementById(
        "trendRmse"
    ).innerText =
        result.linear_trend.rmse.toFixed(4);

    document.getElementById(
        "trendR2"
    ).innerText =
        result.linear_trend.r2.toFixed(4);

}

function renderPredictionPlot(result){

    const selector = document.getElementById("plotTarget");

    if(!result.plots){
        return;
    }

    const targets = Object.keys( result.plots);

    if(targets.length === 0){
        return;
    }

    selector.innerHTML = "";

    if(targets.length === 0){
        return;
    }


    targets.forEach(target => {

        selector.add(new Option(target, target));
    });

    function drawTarget( target ){

        Plotly.newPlot(
            "predictionPlot",
            [
                {
                    y:
                        result.plots[target].actual,
                    mode:"lines",
                    name:"Actual"
                },

                {
                    y:result.plots[target].predicted,

                    mode:"lines",
                    name:"Predicted"
                }

            ],

            {
                title:`Actual vs Predicted: ${target}`,
                paper_bgcolor:"#fff",
                plot_bgcolor:"#fff"

            },

            {responsive:true}

        );

    }

    drawTarget(
        targets[0]
    );

    selector.onchange =
        () =>
            drawTarget(
                selector.value
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