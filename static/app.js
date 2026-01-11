const promptInput = document.getElementById("prompt");
const charCount = document.getElementById("char-count");
const generateButton = document.getElementById("generate");
const clearButton = document.getElementById("clear-form");
const retryButton = document.getElementById("retry");
const resultMessage = document.getElementById("result-message");
const resultVideo = document.getElementById("result-video");

const durationSelect = document.getElementById("duration");
const resolutionSelect = document.getElementById("resolution");
const fpsSelect = document.getElementById("fps");

const updateCount = () => {
  const length = promptInput.value.length;
  charCount.textContent = `${length}/5000`;
};

const setStatus = (message, isError = false) => {
  resultMessage.querySelector("p").textContent = message;
  resultMessage.classList.toggle("error", isError);
  resultMessage.hidden = false;
};

const showVideo = (src) => {
  resultVideo.src = src;
  resultVideo.hidden = false;
  resultMessage.hidden = true;
};

const resetVideo = () => {
  resultVideo.pause();
  resultVideo.removeAttribute("src");
  resultVideo.load();
  resultVideo.hidden = true;
};

const durationMap = {
  "6 sec": 6,
  "10 sec": 10,
  "16 sec": 16,
};

const handleGenerate = async () => {
  resetVideo();
  setStatus("Generating video... This may take a few minutes.");
  generateButton.disabled = true;

  const payload = {
    prompt: promptInput.value.trim(),
    duration_seconds: durationMap[durationSelect.value] || 6,
    resolution: resolutionSelect.value,
    fps: Number.parseInt(fpsSelect.value, 10) || 25,
  };

  try {
    const response = await fetch("/generate", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Generation failed.");
    }

    showVideo(data.output_url);
  } catch (error) {
    setStatus(error.message, true);
  } finally {
    generateButton.disabled = false;
  }
};

promptInput.addEventListener("input", updateCount);
generateButton.addEventListener("click", handleGenerate);
retryButton.addEventListener("click", handleGenerate);
clearButton.addEventListener("click", () => {
  promptInput.value = "";
  updateCount();
  resetVideo();
  setStatus("Ready to generate. Configure your prompt and settings.");
});

updateCount();
