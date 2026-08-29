const labels = [];
const crowdValues = [];

const configuredApiBase = document
    .querySelector('meta[name="crowdsense-api-base"]')
    ?.content.trim();

const API_BASE = (
    configuredApiBase ||
    (window.location.protocol === "file:" ? "http://127.0.0.1:8000" : "")
).replace(/\/$/, "");

function apiUrl(path) {
    return `${API_BASE}${path}`;
}

function setText(id, value) {
    document.getElementById(id).innerText = value;
}

async function errorMessage(response) {
    try {
        const payload = await response.json();
        return payload.detail || payload.error || `Request failed (${response.status})`;
    } catch (_error) {
        return `Request failed (${response.status})`;
    }
}

const chartElement = document.getElementById("crowdChart");
const crowdChart = typeof Chart === "undefined"
    ? null
    : new Chart(chartElement, {
        type: "line",
        data: {
            labels,
            datasets: [
                {
                    label: "People Count",
                    data: crowdValues,
                    borderWidth: 3,
                    tension: 0.3,
                },
            ],
        },
        options: {
            responsive: true,
        },
    });

function showOfflineState(message = "API Unavailable") {
    setText("people", "--");
    setText("risk", "UNKNOWN");
    setText("confidence", "--");
    setText("occupancy", "--");
    setText("alert", message);
    setText("camera", "OFFLINE");

    document.getElementById("risk").style.color = "#94a3b8";
    document.getElementById("alert").style.color = "red";
    document.getElementById("camera").style.color = "red";
}

let loadingDashboard = false;

async function loadData() {
    if (loadingDashboard) {
        return;
    }

    loadingDashboard = true;

    try {
        const response = await fetch(apiUrl("/crowd"));

        if (!response.ok) {
            throw new Error(await errorMessage(response));
        }

        const data = await response.json();
        const cameraOnline = data.camera === "ONLINE";

        setText("people", cameraOnline ? data.people : "--");
        setText("risk", cameraOnline ? data.risk : "UNKNOWN");
        setText("confidence", cameraOnline ? `${data.confidence}%` : "--");
        setText("occupancy", cameraOnline ? `${data.occupancy}%` : "--");
        setText("alert", data.alert);
        setText("camera", data.camera);
        setText("peak", data.peak);
        setText("average", data.average);
        setText("records", data.records);
        setText("db_records", data.db_records);
        setText("high_risk", data.high_risk);
        setText("avg_occupancy", `${data.avg_occupancy}%`);

        const riskElement = document.getElementById("risk");
        const riskColors = {
            LOW: "lime",
            MEDIUM: "orange",
            HIGH: "red",
        };
        riskElement.style.color = riskColors[data.risk] || "#94a3b8";

        const alertElement = document.getElementById("alert");
        alertElement.style.color = data.alert === "No Alert" ? "lime" : "red";

        const cameraElement = document.getElementById("camera");
        cameraElement.style.color = cameraOnline ? "lime" : "red";

        if (cameraOnline) {
            labels.push(new Date().toLocaleTimeString());
            crowdValues.push(data.people);

            if (labels.length > 15) {
                labels.shift();
                crowdValues.shift();
            }

            crowdChart?.update();
        }
    } catch (error) {
        console.error("Error loading dashboard data:", error);
        showOfflineState(error.message);
    } finally {
        loadingDashboard = false;
    }
}

async function uploadVideo() {
    const fileInput = document.getElementById("videoFile");
    const button = document.getElementById("analyzeButton");
    const status = document.getElementById("video_status");
    const file = fileInput.files[0];

    if (!file) {
        status.innerText = "Please select a video file.";
        status.className = "status-message error";
        return;
    }

    const formData = new FormData();
    formData.append("file", file);
    button.disabled = true;
    status.innerText = "Analyzing video…";
    status.className = "status-message";

    try {
        const response = await fetch(apiUrl("/analyze-video"), {
            method: "POST",
            body: formData,
        });

        if (!response.ok) {
            throw new Error(await errorMessage(response));
        }

        const result = await response.json();
        if (!result.success) {
            throw new Error(result.error || "Video analysis failed");
        }

        setText("max_people", result.max_people);
        setText("average_people", result.average_people);
        setText("video_risk", result.high_risk_events);
        status.innerText = "Analysis complete.";
        status.className = "status-message success";
    } catch (error) {
        console.error("Video analysis failed:", error);
        status.innerText = error.message;
        status.className = "status-message error";
    } finally {
        button.disabled = false;
    }
}

function generateReport() {
    window.open(apiUrl("/generate-report"), "_blank", "noopener");
}

document.getElementById("analyzeButton").addEventListener("click", uploadVideo);
document.getElementById("reportButton").addEventListener("click", generateReport);

loadData();
setInterval(loadData, 2000);
