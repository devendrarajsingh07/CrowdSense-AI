const labels = [];
const crowdValues = [];

const ctx =
document.getElementById(
    "crowdChart"
);

const crowdChart =
new Chart(ctx, {

    type: "line",

    data: {

        labels: labels,

        datasets: [{

            label: "People Count",

            data: crowdValues,

            borderWidth: 3,

            tension: 0.3

        }]
    },

    options: {

        responsive: true

    }

});

async function loadData() {

    try {

        const response =
        await fetch(
            "http://127.0.0.1:8000/crowd"
        );

        const data =
        await response.json();

        document.getElementById("people").innerText = data.people;
        document.getElementById("confidence").innerText = data.confidence + "%";
        document.getElementById("occupancy").innerText = data.occupancy + "%";

        document.getElementById("peak").innerText = data.peak;
        document.getElementById("average").innerText = data.average;
        document.getElementById("records").innerText = data.records;

        document.getElementById("db_records").innerText = data.db_records;
        document.getElementById("high_risk").innerText = data.high_risk;
        document.getElementById("avg_occupancy").innerText = data.avg_occupancy + "%";

        const riskElement = document.getElementById("risk");
        riskElement.innerText = data.risk;

        if(data.risk === "LOW")
            riskElement.style.color = "lime";
        else if(data.risk === "MEDIUM")
            riskElement.style.color = "orange";
        else
            riskElement.style.color = "red";

        const alertElement = document.getElementById("alert");

        alertElement.innerText = data.alert;

        if(data.alert === "HIGH CROWD DETECTED")
            alertElement.style.color = "red";
        else
            alertElement.style.color = "lime";

        const currentTime =
        new Date()
        .toLocaleTimeString();

        labels.push(currentTime);
        crowdValues.push(data.people);

        if(labels.length > 15){

            labels.shift();
            crowdValues.shift();

        }

        crowdChart.update();

    }

    catch(error){

        console.log(error);

    }

}

loadData();

setInterval(
    loadData,
    2000
);

async function uploadVideo(){

    const fileInput =
    document.getElementById(
        "videoFile"
    );

    const file =
    fileInput.files[0];

    if(!file){

        alert(
            "Please select a video"
        );

        return;

    }

    const formData =
    new FormData();

    formData.append(
        "file",
        file
    );

    const response =
    await fetch(
        "http://127.0.0.1:8000/analyze-video",
        {
            method:"POST",
            body:formData
        }
    );

    const result =
    await response.json();

    document.getElementById("max_people").innerText =
    result.max_people;

    document.getElementById("average_people").innerText =
    result.average_people;

    document.getElementById("video_risk").innerText =
    result.high_risk_events;

}

function generateReport(){

    window.open(
        "http://127.0.0.1:8000/generate-report",
        "_blank"
    );

}