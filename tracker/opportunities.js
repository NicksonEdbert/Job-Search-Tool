// Opportunities tab: student jobs, volunteering, companies to contact directly, communities, small paid gigs.
// Uses helpers the main page shares on window.TRACKER. Progress is stored in the browser (state.opps / state.customOpps)
// and included in Export/Import backups.
(function () {
  "use strict";
  const T = window.TRACKER;
  if (!T) return;
  const { state, save, esc, toast, copy, daysAgo, ago, today, waLink, $ } = T;
  state.opps = state.opps || {};
  state.customOpps = state.customOpps || [];

  const STATUSES = ["To do", "Contacted", "Applied", "Replied", "Doing it", "Not now"];
  const KINDS = [
    ["student", "Student jobs"],
    ["volunteer", "Volunteering"],
    ["company", "Companies to contact directly"],
    ["community", "Communities & events"],
    ["gig", "Small paid jobs (gigs)"],
    ["contact", "Your own contacts"],
  ];
  const CITY = { melbourne: "Melbourne", jakarta: "Jakarta", any: "Anywhere" };
  let ITEMS = [], STATUS = {}, cityFilter = "all";
  try { cityFilter = sessionStorage.getItem("opps.city") || "all"; } catch (e) {}

  // ---------------- ready-made messages ----------------
  const MSG = {
    EN: {
      company: (city) => `Subject: Cybersecurity student available for IT/security work, Dec–Feb

Hi [Name / hiring team],

I'm a Bachelor of IT (Cybersecurity) student at [University] and I'm available full-time from December to February in ${CITY[city] || "[city]"}. I'd love to help your IT or security team: service desk, security monitoring, documentation, or any project where an extra pair of hands is useful.

A bit about me: Python, JavaScript and Linux shell; [1–2 projects, e.g. a security tool you built or CTF results]; and I'm reliable and used to customer-facing work.

${city === "melbourne" ? "I'd be glad to discuss a paid casual role or a short paid internship." : "Paid or unpaid is fine. Above all I want real experience."}

My CV is attached. Would you be open to a 15-minute chat?

Thank you,
[Your name]
[Phone] · [LinkedIn]`,
      linkedin: (city) => `Hi [Name], I'm a cybersecurity student available full-time Dec–Feb in ${CITY[city] || "[city]"}. I'd love to help your IT/security team (service desk, monitoring or projects). Could I send you my CV? Thank you!`,
      volunteer: () => `Hi,

I'm a cybersecurity student with IT-support and tutoring experience, available [days per week] from December to February. I'd love to volunteer with [organisation], for example helping with IT support, online-safety sessions for your community, or your website.

Is there a role where I could help? Happy to do a police check if needed.

Thank you,
[Your name]`,
      family: () => `Hi [Name]! My brother is studying cybersecurity and is free from December to February. Does your company (or anyone you know) need help with IT support or security for a few weeks? He's reliable and keen to learn. Happy to send his CV 🙏`,
      gig: () => `IT & security check-up for small businesses

In 2–3 hours I'll:
• turn on 2-step login for your email, social media and banking-admin accounts
• check that your backups actually work (and set them up if needed)
• secure your Wi-Fi and router (strong passwords, updates, guest network)
• tidy sharing and admin settings in Google Workspace / Microsoft 365
• give a 20-minute "spot the scam" phishing talk for staff
• fix small website issues

Price: [your price], or free for the first one in exchange for a short reference.
[Your name] · cybersecurity student · [phone]`,
      checklist: () => `Gig checklist
☐ Agree what's in scope and get written OK to look at their systems
☐ List accounts (email, socials, banking admin, website) → turn on 2-step login
☐ Password manager set up for the owner
☐ Backups: what's backed up, where, last successful restore test
☐ Router: admin password changed, firmware updated, WPA2/WPA3, guest network
☐ Google Workspace / M365: admin accounts, sharing settings, unused users removed
☐ Devices: updates on, screen lock, antivirus/Defender on
☐ 20-min phishing talk; leave a one-page summary of what changed
☐ Ask for a short reference / testimonial`,
      cvline: () => `IT & security check-ups for [N] small businesses: turned on multi-factor login for [N] accounts, set up and tested backups, secured Wi-Fi and routers, and ran phishing-awareness sessions for staff.`,
      followup: (it) => `Hi [Name], just following up on my message about ${{ volunteer: "volunteering", student: "a student job", community: "helping out" }[it.kind] || "a short IT/security role"} with ${it.title}. I'm still available from December to February and happy to help however is useful. Thank you!`,
      wa: (it) => `Hi! Something to try for real-world experience:\n\n${it.title} (${CITY[it.city] || "anywhere"})\n${it.why || ""}\n${it.url ? "Link: " + it.url + "\n" : ""}\nNext step: ${{ student: "sign up / apply this week", volunteer: "send the volunteer message (I've got it ready)", company: "send them the email + CV (I've got it ready)", community: "go to their next event and say hi", gig: "send the offer", contact: "message them" }[it.kind] || "have a look"}`,
    },
    ID: {
      company: (city) => `Subjek: Mahasiswa cybersecurity siap membantu tim IT/keamanan, Des–Feb

Halo [Nama / tim rekrutmen],

Saya mahasiswa Bachelor of IT (Cybersecurity) di [Universitas] dan bisa bekerja penuh waktu dari Desember sampai Februari di ${CITY[city] || "[kota]"}. Saya ingin membantu tim IT atau keamanan Anda: service desk, monitoring keamanan, dokumentasi, atau proyek apa pun yang butuh tenaga tambahan.

Tentang saya: Python, JavaScript dan Linux shell; [1–2 proyek, mis. tool keamanan yang saya buat atau hasil CTF]; dan saya terbiasa melayani pelanggan.

${city === "melbourne" ? "Saya terbuka untuk posisi casual berbayar atau magang singkat berbayar." : "Berbayar maupun tidak, tidak masalah. Yang terpenting saya mendapat pengalaman nyata."}

CV saya terlampir. Apakah Anda bersedia ngobrol 15 menit?

Terima kasih,
[Nama Anda]
[Telepon] · [LinkedIn]`,
      linkedin: (city) => `Halo [Nama], saya mahasiswa cybersecurity yang bisa bekerja penuh waktu Des–Feb di ${CITY[city] || "[kota]"}. Saya ingin membantu tim IT/keamanan Anda (service desk, monitoring atau proyek). Boleh saya kirim CV saya? Terima kasih!`,
      volunteer: () => `Halo,

Saya mahasiswa cybersecurity dengan pengalaman IT support dan mengajar, bisa [hari per minggu] dari Desember sampai Februari. Saya ingin menjadi relawan di [organisasi], misalnya membantu IT support, sesi keamanan digital untuk komunitas Anda, atau website Anda.

Apakah ada peran yang bisa saya bantu?

Terima kasih,
[Nama Anda]`,
      family: () => `Halo [Nama]! Adik saya kuliah cybersecurity dan sedang libur dari Desember sampai Februari. Apakah kantor Anda (atau kenalan Anda) butuh bantuan IT support atau keamanan untuk beberapa minggu? Dia rajin dan mau belajar. Boleh saya kirim CV-nya 🙏`,
      gig: () => `Cek IT & keamanan untuk usaha kecil

Dalam 2–3 jam saya akan:
• mengaktifkan login 2 langkah untuk email, media sosial dan akun admin bank
• memastikan backup benar-benar berjalan (dan menyiapkannya bila perlu)
• mengamankan Wi-Fi dan router (password kuat, update, jaringan tamu)
• merapikan pengaturan berbagi dan admin di Google Workspace / Microsoft 365
• sesi 20 menit "kenali penipuan" (phishing) untuk karyawan
• memperbaiki masalah kecil di website

Biaya: [harga Anda], atau gratis untuk yang pertama dengan imbalan testimoni singkat.
[Nama Anda] · mahasiswa cybersecurity · [telepon]`,
      checklist: () => MSG.EN.checklist(),
      cvline: () => MSG.EN.cvline(),
      followup: (it) => `Halo [Nama], saya ingin menindaklanjuti pesan saya tentang ${{ volunteer: "menjadi relawan", student: "pekerjaan mahasiswa", community: "membantu kegiatan" }[it.kind] || "posisi IT/keamanan singkat"} di ${it.title}. Saya masih bisa dari Desember sampai Februari dan siap membantu. Terima kasih!`,
      wa: (it) => `Halo! Ini bisa dicoba untuk pengalaman kerja nyata:\n\n${it.title} (${CITY[it.city] || "di mana saja"})\n${it.why || ""}\n${it.url ? "Link: " + it.url + "\n" : ""}\nLangkah berikutnya: ${{ student: "daftar / lamar minggu ini", volunteer: "kirim pesan relawan (sudah aku siapkan)", company: "kirim email + CV (sudah aku siapkan)", community: "datang ke acara berikutnya dan kenalan", gig: "kirim penawarannya", contact: "hubungi mereka" }[it.kind] || "coba lihat"}`,
    },
  };
  const lang = () => (state.settings.msgLang === "ID" ? "ID" : "EN");

  // ---------------- data ----------------
  function allItems() {
    const custom = state.customOpps.map((o) => Object.assign({ custom: true, key: o.id }, o));
    return ITEMS.map((it) => Object.assign({ key: it.url || it.title }, it)).concat(custom);
  }
  function info(key) { return state.opps[key] || {}; }
  function followUpDue(it) {
    const s = info(it.key);
    if (!["Contacted", "Applied"].includes(s.status) || !s.date) return null;
    const d = daysAgo(s.date + "T00:00:00");
    return d != null && d >= Number(state.settings.followUpDays || 7) ? d : null;
  }

  // ---------------- render ----------------
  function itemHtml(it) {
    const s = info(it.key);
    const dead = STATUS[it.url] === "dead" ? ` <span class="badge bad">Link looks dead</span>` : "";
    const due = followUpDue(it);
    const opts = STATUSES.map((x) => `<option ${x === (s.status || "To do") ? "selected" : ""}>${x}</option>`).join("");
    return `<div class="exp-item" style="display:block">
      <div><b>${it.url ? `<a href="${esc(it.url)}" target="_blank" rel="noopener">${esc(it.title)} ↗</a>` : esc(it.title)}</b>
        <span class="badge">${esc(CITY[it.city] || "Anywhere")}</span>${dead}
        ${s.status && s.status !== "To do" ? `<span class="badge ok">${esc(s.status)}${s.date ? " · " + esc(ago(s.date + "T00:00:00")) : ""}</span>` : ""}</div>
      ${it.why ? `<p>${esc(it.why)}</p>` : ""}
      <div class="row" style="margin-top:6px">
        <select data-oact="status" data-key="${esc(it.key)}" aria-label="Status">${opts}</select>
        <button class="btn" data-oact="wa" data-key="${esc(it.key)}">Send to him ↗</button>
        ${it.custom ? `<button class="btn" data-oact="remove" data-key="${esc(it.key)}">Remove</button>` : ""}
      </div>
      ${due != null ? `<div class="followup">No reply for ${due} days.
        <button class="btn" data-oact="follow" data-key="${esc(it.key)}">Copy follow-up</button>
        <button class="btn" data-oact="followed" data-key="${esc(it.key)}">I followed up</button></div>` : ""}
      <details style="margin-top:6px" ${s.notes ? "open" : ""}><summary>Notes${s.notes ? " ✎" : ""}</summary>
        <textarea data-oact="notes" data-key="${esc(it.key)}" placeholder="Who you talked to, what they said, next step…">${esc(s.notes || "")}</textarea></details>
    </div>`;
  }

  function render() {
    const root = $("#tab-opps");
    const items = allItems().filter((it) => cityFilter === "all" || it.city === cityFilter || it.city === "any");
    const groups = KINDS.map(([kind, label]) => {
      const list = items.filter((it) => it.kind === kind);
      if (!list.length && kind !== "gig" && kind !== "contact") return "";
      const body = list.length ? list.map(itemHtml).join("")
        : `<p class="note">${kind === "gig" ? "Add each small job here once someone says yes (use “+ Add” below)." : "Add people or companies you know with “+ Add” below."}</p>`;
      return `<div class="panel"><h3 style="margin:0 0 4px;font-size:1rem">${label}</h3>${body}</div>`;
    }).join("");
    const counts = STATUSES.slice(1, 5).map((x) => [x, Object.values(state.opps).filter((o) => o.status === x).length]);
    root.innerHTML = `
      <div class="panel">
        <p style="margin-top:0"><b>Real-world work that isn't on job boards.</b> Student jobs, volunteering, companies to contact directly and small paid jobs all count as experience on a CV.</p>
        <div class="row" style="margin-top:0">
          <select id="oppCity" aria-label="City"><option value="all">Melbourne + Jakarta</option><option value="melbourne">Melbourne</option><option value="jakarta">Jakarta</option></select>
          ${counts.map(([k, v]) => `<span class="stat">${k} <b>${v}</b></span>`).join("")}
        </div>
        <p class="note" style="margin-bottom:0">Australia: internships there should be <b>paid</b> unless they're part of his course; volunteering for genuine non-profits is fine. On a student visa he can usually work unlimited hours during official breaks (check VEVO / Monash's visa page).</p>
      </div>
      ${groups}
      <div class="panel">
        <details id="oppAddBox"><summary>+ Add a company, contact or gig</summary>
          <form id="oppAdd" class="addform">
            <div class="field"><label for="oName">Name</label><input id="oName" type="text" required placeholder="e.g. Uncle's office, a café's Wi-Fi job"></div>
            <div class="field"><label for="oKind">Type</label><select id="oKind">
              <option value="contact">Contact</option><option value="company">Company</option><option value="gig">Gig (small paid job)</option>
              <option value="volunteer">Volunteering</option><option value="student">Student job</option></select></div>
            <div class="field"><label for="oCity">City</label><select id="oCity"><option value="melbourne">Melbourne</option><option value="jakarta">Jakarta</option><option value="any">Anywhere</option></select></div>
            <div class="field"><label for="oUrl">Link (optional)</label><input id="oUrl" type="url" placeholder="https://"></div>
            <div class="field"><label for="oWhy">Note</label><input id="oWhy" type="text" placeholder="Who to ask, what they need"></div>
            <div class="field" style="align-self:end"><button class="btn primary" type="submit">Add</button></div>
          </form></details>
      </div>
      <div class="panel" id="oppMsgs">
        <h3 style="margin:0 0 6px;font-size:1rem">Ready messages</h3>
        <p class="note" style="margin-top:0">Fill in the [brackets] before sending. Language follows <b>Backup &amp; settings</b> (now: ${lang() === "ID" ? "Bahasa Indonesia" : "English"}).</p>
        <div class="row" style="margin-top:0">
          <button class="btn" data-msg="company" data-city="melbourne">Company email · Melbourne</button>
          <button class="btn" data-msg="company" data-city="jakarta">Company email · Jakarta</button>
          <button class="btn" data-msg="linkedin" data-city="melbourne">LinkedIn note · Melbourne</button>
          <button class="btn" data-msg="linkedin" data-city="jakarta">LinkedIn note · Jakarta</button>
          <button class="btn" data-msg="volunteer">Volunteer enquiry</button>
          <button class="btn" data-msg="family">WhatsApp to family/friends</button>
        </div>
        <h3 style="margin:12px 0 6px;font-size:1rem">Small paid jobs</h3>
        <div class="row" style="margin-top:0">
          <button class="btn" data-msg="gig">Gig offer</button>
          <button class="btn" data-msg="checklist">Gig checklist</button>
          <button class="btn" data-msg="cvline">CV line</button>
        </div>
      </div>`;
    $("#oppCity").value = cityFilter;
  }

  // ---------------- events ----------------
  document.addEventListener("change", (e) => {
    const el = e.target;
    if (el.id === "oppCity") { cityFilter = el.value; try { sessionStorage.setItem("opps.city", cityFilter); } catch (x) {} render(); return; }
    const act = el.dataset && el.dataset.oact; if (!act) return;
    const key = el.dataset.key, s = state.opps[key] = state.opps[key] || {};
    if (act === "status") {
      s.status = el.value;
      s.date = ["Contacted", "Applied", "Replied", "Doing it"].includes(el.value) ? today() : s.date;
      save(); render();
    }
    if (act === "notes") { s.notes = el.value; save(); }
  });
  document.addEventListener("click", (e) => {
    const m = e.target.closest("[data-msg]");
    if (m && m.closest("#tab-opps")) {
      copy(MSG[lang()][m.dataset.msg](m.dataset.city), "Copied. Fill in the [brackets] and send");
      return;
    }
    const el = e.target.closest("[data-oact]"); if (!el || !el.closest("#tab-opps")) return;
    const it = allItems().find((x) => x.key === el.dataset.key); if (!it) return;
    const act = el.dataset.oact;
    if (act === "wa") {
      window.open(waLink(MSG[lang()].wa(it)), "_blank", "noopener");
      const s = state.opps[it.key] = state.opps[it.key] || {};
      s.sentAt = today(); save(); toast("Opened WhatsApp");
    }
    if (act === "follow") copy(MSG[lang()].followup(it), "Copied follow-up message");
    if (act === "followed") { state.opps[it.key].date = today(); save(); render(); toast("Next reminder in " + state.settings.followUpDays + " days"); }
    if (act === "remove") { state.customOpps = state.customOpps.filter((o) => o.id !== it.key); delete state.opps[it.key]; save(); render(); }
  });
  document.addEventListener("submit", (e) => {
    if (e.target.id !== "oppAdd") return;
    e.preventDefault();
    state.customOpps.push({ id: "custom:" + Date.now().toString(36), title: $("#oName").value.trim(), kind: $("#oKind").value,
      city: $("#oCity").value, url: $("#oUrl").value.trim(), why: $("#oWhy").value.trim() });
    save(); render(); toast("Added");
  });

  // ---------------- load ----------------
  async function load() {
    try { ITEMS = (await (await fetch("../config/opportunities.json", { cache: "no-cache" })).json()).items || []; } catch (e) { ITEMS = []; }
    try { STATUS = (await (await fetch("../data/experience_status.json", { cache: "no-cache" })).json()).status || {}; } catch (e) { STATUS = {}; }
    render();
  }
  window.renderOpps = render;
  load();
})();
