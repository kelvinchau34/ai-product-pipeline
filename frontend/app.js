const processBtn = document.getElementById("processBtn");
const statusEl = document.getElementById("status");

processBtn?.addEventListener("click", () => {
  statusEl.textContent = "Hook this button to your API Gateway /process endpoint.";
});
