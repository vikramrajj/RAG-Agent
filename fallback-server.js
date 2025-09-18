// fallback-server.js

const express = require("express");
const { exec } = require("child_process");
const path = require("path");
const fs = require("fs");

const app = express();
app.use(express.json());

const SARA_PATH = `"C:\\Program Files\\Microsoft Support and Recovery Assistant\\SaRAcmd.exe"`;
const OUTPUT_DIR = "C:\\Diagnostics\\Outlook";

function runSaRA(outlookScenario = "OutlookScenario") {
  return new Promise((resolve, reject) => {
    const command = `${SARA_PATH} -ScenarioId ${outlookScenario} -OutputDirectory "${OUTPUT_DIR}"`;
    exec(command, { windowsHide: true }, (error, stdout, stderr) => {
      if (error) return reject(stderr || error.message);
      resolve(stdout || "Diagnostics completed.");
    });
  });
}

function readFileSafe(filePath) {
  try {
    return fs.readFileSync(filePath, "utf-8");
  } catch {
    return "No data available.";
  }
}

app.post("/fallback/outlook", async (req, res) => {
  try {
    const result = await runSaRA();
    res.send(result);
  } catch (err) {
    res.status(500).send("SaRA failed: " + err);
  }
});

app.get("/fallback/outlook/logs", (req, res) => {
  const logFile = path.join(OUTPUT_DIR, "SaRA.log");
  res.send(readFileSafe(logFile));
});

app.get("/fallback/outlook/registry", (req, res) => {
  const regFile = path.join(OUTPUT_DIR, "RegistryDump.txt");
  res.send(readFileSafe(regFile));
});

app.listen(5000, () => {
  console.log("✅ SaRA fallback server running on http://localhost:5000");
});
