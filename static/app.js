const promptInput = document.getElementById("prompt");
const charCount = document.getElementById("char-count");

const updateCount = () => {
  const length = promptInput.value.length;
  charCount.textContent = `${length}/5000`;
};

promptInput.addEventListener("input", updateCount);
updateCount();
