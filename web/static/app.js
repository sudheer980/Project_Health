function $(id){ 
  return document.getElementById(id); 
}

/* ======================
   TAB SWITCHING
====================== */

const tabAssess = $("tabAssess");
const tabChat = $("tabChat");

const assessPanel = $("assessPanel");
const chatPanel = $("chatPanel");

tabAssess.onclick = () => {
  tabAssess.classList.add("active");
  tabChat.classList.remove("active");
  assessPanel.classList.remove("hidden");
  chatPanel.classList.add("hidden");
};

tabChat.onclick = () => {
  tabChat.classList.add("active");
  tabAssess.classList.remove("active");
  chatPanel.classList.remove("hidden");
  assessPanel.classList.add("hidden");
};

/* ======================
   PART 1 – ASSESSMENT
====================== */

$("runBtn").onclick = async () => {

  const patientId = $("patientId").value.trim();
  const topK = parseInt($("topK").value || "5");

  const result = $("result");

  result.classList.remove("hidden");
  result.innerHTML = `<div class="loading">Running assessment...</div>`;

  try {

    const res = await fetch("/assess", {
      method:"POST",
      headers:{ "Content-Type":"application/json" },
      body: JSON.stringify({
        patient_id: patientId,
        top_k: topK
      })
    });

    const data = await res.json();

    /* ---------- Render Citations ---------- */

    let citationHTML = "";

    if(data.citations && data.citations.length > 0){

      citationHTML = "<h4>Citations</h4><ul>";

      data.citations.forEach(c => {

        citationHTML += `
          <li>
            <b>[${c.chunk_id} | p.${c.page}]</b><br/>
            ${c.excerpt || ""}
          </li>
        `;

      });

      citationHTML += "</ul>";
    }

    /* ---------- Render Result ---------- */

    result.innerHTML = `
      <h3>Assessment Result</h3>
      <p><b>Decision:</b> ${data.decision}</p>
      <p><b>Confidence:</b> ${data.confidence}</p>
      <p>${data.summary}</p>
      ${citationHTML}
    `;

  } catch(err){

    result.innerHTML = "Error running assessment";

    console.error(err);
  }
};


/* ======================
   PART 2 – CHAT MODE
====================== */

function appendChat(role, text){

  const div = document.createElement("div");

  div.classList.add("chat-message");
  div.classList.add(role === "You" ? "user" : "bot");

  div.innerHTML = text;

  $("chatWindow").appendChild(div);

  $("chatWindow").scrollTop = $("chatWindow").scrollHeight;
}


$("sendChat").onclick = async () => {

  const message = $("chatMsg").value.trim();
  const sessionId = $("sessionId").value;

  if(!message) return;

  appendChat("You", message);

  $("chatMsg").value = "";

  try {

    const res = await fetch("/chat", {
      method:"POST",
      headers:{ "Content-Type":"application/json" },
      body: JSON.stringify({
        session_id: sessionId,
        message: message
      })
    });

    const data = await res.json();

    let answer = data.answer;

    /* ---------- CHAT CITATIONS ---------- */

    if(data.citations && data.citations.length > 0){

      answer += "<br/><br/><b>Citations:</b><ul>";

      data.citations.forEach(c => {
        answer += `
          <li>
            [${c.chunk_id} | p.${c.page}]
          </li>
        `;
      });

      answer += "</ul>";
    }

    appendChat("Bot", answer);

  } catch(err){

    appendChat("Bot", "Error contacting backend");

    console.error(err);
  }
};
