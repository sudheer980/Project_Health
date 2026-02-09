const btn = document.getElementById("runBtn");
const resultDiv = document.getElementById("result");

function esc(s) {
  return (s || "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
}

btn.addEventListener("click", async () => {
  const patient_id = document.getElementById("patientId").value.trim();
  const topKRaw = document.getElementById("topK").value.trim();
  const top_k = topKRaw ? parseInt(topKRaw, 10) : undefined;

  if (!patient_id) {
    alert("Please enter a Patient ID");
    return;
  }

  resultDiv.classList.add("hidden");
  resultDiv.innerHTML = "";

  try {
    const res = await fetch("/assess", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ patient_id, top_k })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Request failed");
    }

    const data = await res.json();

    let html = `
      <h2>Result</h2>
      <div class="grid">
        <div><b>Patient</b><br/>${esc(data.patient_id)}</div>
        <div><b>Decision</b><br/>${esc(data.decision)}</div>
        <div><b>Confidence</b><br/>${esc(String(data.confidence))}</div>
      </div>
      <p><b>Summary:</b> ${esc(data.summary)}</p>
      <p><b>Reasoning:</b> ${esc(data.reasoning)}</p>
      <h3>Citations</h3>
    `;

    if (data.citations && data.citations.length) {
      html += "<ul>";
      for (const c of data.citations) {
        html += `<li><b>[${esc(c.chunk_id)} | p.${esc(String(c.page))}]</b> ${esc(c.excerpt)}</li>`;
      }
      html += "</ul>";
    } else {
      html += "<p>No citations returned.</p>";
    }

    resultDiv.innerHTML = html;
    resultDiv.classList.remove("hidden");
  } catch (e) {
    resultDiv.innerHTML = `<h2>Error</h2><p>${esc(e.message)}</p>`;
    resultDiv.classList.remove("hidden");
  }
});
