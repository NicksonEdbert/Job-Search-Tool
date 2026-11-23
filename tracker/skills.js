// Skill dictionary for matching a job's text against the student's skills.
// Each entry: canonical name -> regular expressions that mean that skill.
// Add entries freely; matching is case-insensitive unless the pattern sets its own flags.
window.SKILLS = [
  // Programming & web
  ["Python", [/\bpython\b/i]],
  ["JavaScript", [/\bjavascript\b/i, /\bJS\b/, /\becmascript\b/i]],
  ["TypeScript", [/\btypescript\b/i]],
  ["Java", [/\bjava\b(?!\s*script)/i]],
  ["C / C++", [/\bc\+\+/i, /\bcpp\b/i, /(?<![\w+#])C(?=[,/)]| or | and | programming)/]],
  ["C#", [/\bc#/i, /\.net\b/i]],
  ["Go", [/\bgolang\b/i, /(?<=[(,/] ?)Go\b/, /\bGo(?=[,)/])/]],
  ["PHP", [/\bphp\b/i]],
  ["Kotlin / Swift", [/\bkotlin\b/i, /\bswift\b/i]],
  ["HTML", [/\bhtml5?\b/i]],
  ["CSS", [/\bcss3?\b/i, /\btailwind\b/i]],
  ["React", [/\breact(\.js|js)?\b/i]],
  ["Node.js", [/\bnode(\.js|js)?\b/i]],
  ["SQL", [/\bsql\b/i, /\bmysql\b/i, /\bpostgres(ql)?\b/i]],
  ["Git", [/\bgit\b/i, /\bgithub\b/i, /\bgitlab\b/i]],
  ["REST APIs", [/\brest(ful)?\b/i, /\bAPIs?\b/]],
  ["Bash / shell", [/\bbash\b/i, /\bshell( scripting| commands)?\b/i, /\bunix shell\b/i]],
  ["PowerShell", [/\bpowershell\b/i]],
  ["Browser extensions", [/\b(browser|chrome) extensions?\b/i]],
  ["Algorithms & data structures", [/\balgorithms?\b/i, /\bdata structures?\b/i, /\bleetcode\b/i]],
  // Systems, networks & cloud
  ["Linux", [/\blinux\b/i, /\bubuntu\b/i, /\bkali\b/i]],
  ["Unix", [/\bunix\b/i]],
  ["Windows / Active Directory", [/\bactive directory\b/i, /\bwindows server\b/i, /\bAD\b/]],
  ["Networking (TCP/IP)", [/\bnetwork(ing)?\b/i, /\btcp\/?ip\b/i, /\bccna\b/i, /\brouting\b/i]],
  ["Firewalls & VPN", [/\bfirewalls?\b/i, /\bvpn\b/i, /\bwaf\b/i]],
  ["Cloud (AWS/Azure/GCP)", [/\baws\b/i, /\bazure\b/i, /\bgcp\b/i, /\bgoogle cloud\b/i, /\bcloud\b/i]],
  ["Docker / Kubernetes", [/\bdocker\b/i, /\bkubernetes\b/i, /\bk8s\b/i, /\bcontainers?\b/i]],
  ["CI/CD", [/\bci\/cd\b/i, /\bjenkins\b/i, /\bgithub actions\b/i]],
  // Security
  ["Penetration testing", [/\bpen(etration)?[ -]?test(ing|er)?\b/i, /\bethical hack/i, /\bred team/i]],
  ["Vulnerability assessment", [/\bvulnerabilit(y|ies)\b/i, /\bvapt\b/i, /\bnessus\b/i, /\bqualys\b/i]],
  ["Web app security (OWASP)", [/\bowasp\b/i, /\bweb (application )?security\b/i, /\bxss\b/i, /\bsql injection\b/i, /\bappsec\b/i]],
  ["Burp Suite", [/\bburp\b/i]],
  ["Nmap", [/\bnmap\b/i]],
  ["Wireshark", [/\bwireshark\b/i, /\bpacket (capture|analysis)\b/i, /\btcpdump\b/i]],
  ["Metasploit", [/\bmetasploit\b/i]],
  ["SIEM / log analysis", [/\bsiem\b/i, /\bsplunk\b/i, /\bqradar\b/i, /\belastic\b/i, /\bwazuh\b/i, /\blog (analysis|monitoring)\b/i]],
  ["SOC / monitoring", [/\bsoc\b/i, /\bsecurity operations\b/i, /\bsecurity monitoring\b/i]],
  ["Incident response", [/\bincident (response|handling)\b/i, /\bdfir\b/i]],
  ["Threat intelligence", [/\bthreat (intel(ligence)?|hunting)\b/i, /\bmitre att&?ck\b/i]],
  ["Digital forensics", [/\bforensics?\b/i]],
  ["Malware analysis", [/\bmalware\b/i, /\breverse engineering\b/i]],
  ["Cryptography", [/\bcryptograph(y|ic)\b/i, /\bencryption\b/i, /\bpki\b/i, /\btls\b/i]],
  ["Authentication & IAM (MFA/TOTP/OAuth)", [/\bauthenticat(ion|e)\b/i, /\biam\b/i, /\bidentity and access\b/i, /\bsso\b/i, /\boauth\b/i, /\bsaml\b/i, /\bmfa\b/i, /\b2fa\b/i, /\btotp\b/i, /\bokta\b/i]],
  ["IDS/IPS & EDR", [/\bids\b/i, /\bips\b/, /\bedr\b/i, /\bcrowdstrike\b/i, /\bintrusion detection\b/i]],
  ["Security standards (ISO 27001/NIST)", [/\biso ?27001\b/i, /\bnist\b/i, /\bpci[ -]?dss\b/i, /\bsoc ?2\b/i, /\bcis controls?\b/i]],
  ["GRC / risk & audit", [/\bgrc\b/i, /\brisk (assessment|management)\b/i, /\bit audit\b/i, /\bcompliance\b/i]],
  ["CTF", [/\bctfs?\b/i, /\bcapture the flag\b/i, /\bhack ?the ?box\b/i, /\btryhackme\b/i]],
  ["Bug bounty", [/\bbug bount(y|ies)\b/i, /\bresponsible disclosure\b/i]],
  ["Security certifications", [/\bsecurity\+/i, /\bceh\b/i, /\boscp\b/i, /\bcissp\b/i, /\bisc2\b/i, /\bcomptia\b/i]],
  // Data
  ["Excel", [/\bexcel\b/i, /\bspreadsheets?\b/i, /\bgoogle sheets\b/i]],
  ["Data analysis", [/\bdata analy(sis|tics|st)\b/i, /\bpandas\b/i]],
  ["BI tools (Power BI/Tableau)", [/\bpower ?bi\b/i, /\btableau\b/i, /\blooker\b/i]],
  ["Machine learning", [/\bmachine learning\b/i, /\bml\b/i, /\bdeep learning\b/i]],
  // People & languages
  ["Communication", [/\bcommunicat(ion|e)\b/i, /\bpresentation\b/i]],
  ["Teamwork", [/\bteam ?work\b/i, /\bcollaborat(e|ion|ive)\b/i, /\bteam player\b/i]],
  ["Customer service", [/\bcustomer (service|support|enquir|inquir)/i, /\bhelp ?desk\b/i]],
  ["Problem solving", [/\bproblem[ -]solving\b/i, /\banalytical\b/i]],
  ["English", [/\benglish\b/i]],
  ["Bahasa Indonesia", [/\bbahasa( indonesia)?\b/i, /\bindonesian\b/i]],
  ["Mandarin", [/\bmandarin\b/i, /\bchinese\b/i]],
];

// Map whatever the student typed ("python3", "unix shell commands") to a canonical skill.
window.canonicalSkill = function (raw) {
  const s = String(raw || "").trim();
  if (!s) return null;
  for (const [name, pats] of window.SKILLS) {
    if (name.toLowerCase() === s.toLowerCase()) return name;
  }
  for (const [name, pats] of window.SKILLS) {
    if (pats.some((p) => p.test(s))) return name;
  }
  return s; // custom skill: matched literally
};

// Which dictionary skills does this job ask for?
window.requestedSkills = function (text) {
  const t = String(text || "");
  const out = [];
  for (const [name, pats] of window.SKILLS) {
    if (pats.some((p) => p.test(t))) out.push(name);
  }
  return out;
};

// {matched, missing, pct} for one job given the student's skills.
window.matchSkills = function (text, userSkills) {
  const have = new Set((userSkills || []).map(window.canonicalSkill).filter(Boolean));
  const custom = [...have].filter((s) => !window.SKILLS.some(([n]) => n === s));
  const req = window.requestedSkills(text);
  const lower = String(text || "").toLowerCase();
  const customHits = custom.filter((c) => lower.includes(c.toLowerCase()));
  const matched = req.filter((r) => have.has(r)).concat(customHits);
  const missing = req.filter((r) => !have.has(r));
  const denom = req.length + customHits.length;
  return { matched, missing, pct: denom ? Math.round((100 * matched.length) / denom) : null };
};
