let events=[];
let cur=new Date();
let filter="all";
cur=new Date(Date.UTC(cur.getFullYear(),cur.getMonth(),1));

const names=["January","February","March","April","May","June","July","August","September","October","November","December"];
const days=["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"];

async function load(){
  const response=await fetch("data/events.json?t="+Date.now());
  events=await response.json();
  events.sort((a,b)=>(a.date||"").localeCompare(b.date||"") || (a.start||"").localeCompare(b.start||""));
  render();
}

function abbreviatePracticeTitle(title){
  if(!title) return "";
  return title
    .replace(/\bCubs\b/gi,"Cb")
    .replace(/\bJuniors?\b/gi,"Jr")
    .replace(/\bCougs?\b/gi,"Cg")
    .replace(/\bSeniors?\b/gi,"Sr")
    .replace(/\bNational\b/gi,"Nat");
}

function displayTitle(e){
  return e.type==="practice" ? abbreviatePracticeTitle(e.title) : (e.title||"");
}

function formatClock(date){
  return new Intl.DateTimeFormat("en-US",{
    timeZone:"America/Los_Angeles",
    hour:"numeric",
    minute:"2-digit",
    hour12:true
  }).format(date).replace(/\s/g," ");
}

function compactEventTime(e){
  if(e.allDay) return "";

  if(e.start){
    const s=new Date(e.start);
    const en=e.end ? new Date(e.end) : null;

    if(!Number.isNaN(s.getTime())){
      const a=formatClock(s);

      if(!en || Number.isNaN(en.getTime()) || en.getTime()===s.getTime()){
        return a;
      }

      const b=formatClock(en);

      const ma=a.match(/^(.+?)\s(AM|PM)$/);
      const mb=b.match(/^(.+?)\s(AM|PM)$/);

      if(ma && mb){
        if(ma[2]===mb[2]) return `${ma[1]}–${mb[1]} ${mb[2]}`;
        return `${ma[1]} ${ma[2]}–${mb[1]} ${mb[2]}`;
      }

      return `${a}–${b}`;
    }
  }

  const detail=e.detail||"";
  if(/^All day\b/i.test(detail)) return "";

  let t=detail.split("•")[0].trim().replace(/\s*[–—-]\s*/g," – ");
  let m=t.match(/^(.+?)\s+–\s+(.+)$/);

  if(m && m[1].trim()===m[2].trim()){
    return m[1].trim();
  }

  m=t.match(/^(\d{1,2}:\d{2})\s*(AM|PM)\s+–\s+(\d{1,2}:\d{2})\s*(AM|PM)$/i);
  if(m){
    const [,a,ap,b,bp]=m;
    if(a===b && ap.toUpperCase()===bp.toUpperCase()) return `${a} ${ap.toUpperCase()}`;
    if(ap.toUpperCase()===bp.toUpperCase()) return `${a}–${b} ${bp.toUpperCase()}`;
    return `${a} ${ap.toUpperCase()}–${b} ${bp.toUpperCase()}`;
  }

  return t.replace(/\s+–\s+/g,"–");
}

function deadlineParts(title){
  const t=(title||"").trim();

  // Entries Due — COUG Fall Fury
  let m=t.match(/^Entries\s+Due\s*[-–—:]\s*(.+)$/i);
  if(m) return {subject:m[1].trim(), action:"Entries due"};

  // Deadline for Entries for COUG Fall Fury
  m=t.match(/^Deadline\s+for\s+Entries\s+for\s+(.+)$/i);
  if(m) return {subject:m[1].trim(), action:"Entries due"};

  // Entry Deadline — Meet Name
  m=t.match(/^(?:Entry|Entries)\s+Deadline\s*[-–—:]\s*(.+)$/i);
  if(m) return {subject:m[1].trim(), action:"Entries due"};

  return null;
}

function filtered(){
  return filter==="all" ? events : events.filter(e=>e.type===filter);
}

function render(){
  renderDesktop();
  renderImportant("#important");
  renderImportant("#mobile-important-list");
  renderAgenda();
}

function renderDesktop(){
  let y=cur.getUTCFullYear(),m=cur.getUTCMonth();
  document.querySelector("#month").textContent=names[m]+" "+y;

  let first=new Date(Date.UTC(y,m,1)).getUTCDay();
  let count=new Date(Date.UTC(y,m+1,0)).getUTCDate();
  let prev=new Date(Date.UTC(y,m,0)).getUTCDate();
  let g=document.querySelector("#grid");
  g.innerHTML="";

  for(let i=0;i<42;i++){
    let d,mm=m,yy=y,mut=false;
    if(i<first){
      d=prev-first+i+1; mm--;
      if(mm<0){mm=11;yy--}
      mut=true;
    }else if(i>=first+count){
      d=i-first-count+1; mm++;
      if(mm>11){mm=0;yy++}
      mut=true;
    }else{
      d=i-first+1;
    }

    let ds=`${yy}-${String(mm+1).padStart(2,"0")}-${String(d).padStart(2,"0")}`;
    let c=document.createElement("div");
    c.className="day"+(mut?" muted":"");
    c.innerHTML="<b>"+d+"</b>";

    filtered().filter(e=>e.date===ds).forEach(e=>{
      let x=document.createElement("div");
      x.className="ev "+e.type;

      const t=compactEventTime(e);
      const title=displayTitle(e);

      if(e.color) x.style.borderLeftColor=e.color;

      x.innerHTML=
        (t?`<span class="ev-time">${escapeHtml(t)}</span>`:"")+
        `<span class="ev-title">${escapeHtml(title)}</span>`;

      c.appendChild(x);
    });

    g.appendChild(c);
  }
}

function renderImportant(selector){
  const box=document.querySelector(selector);
  if(!box) return;

  const today=localDateString(new Date());
  const list=events
    .filter(e=>e.type==="important" && e.date>=today)
    .slice(0,8);

  box.innerHTML="";

  if(!list.length){
    box.innerHTML='<p class="agenda-empty">No upcoming important dates.</p>';
    return;
  }

  list.forEach(e=>{
    let d=parseDate(e.date);
    let x=document.createElement("div");
    x.className="imp";

    const t=compactEventTime(e);
    const deadline=deadlineParts(e.title);

    let copy;

    if(deadline){
      copy=
        `<b>${escapeHtml(deadline.subject)}</b>`+
        `<span class="imp-action">${escapeHtml(deadline.action)}${t ? ` · <strong>${escapeHtml(t)}</strong>` : ""}</span>`+
        (e.location?`<p>${escapeHtml(e.location)}</p>`:"");
    }else{
      copy=
        `<b>${escapeHtml(displayTitle(e))}</b>`+
        (t?`<span class="imp-time">${escapeHtml(t)}</span>`:"")+
        (e.location?`<p>${escapeHtml(e.location)}</p>`:"");
    }

    x.innerHTML=
      `<div class="date"><em>${names[d.getMonth()].slice(0,3).toUpperCase()}</em><strong>${d.getDate()}</strong></div>`+
      `<div>${copy}</div>`;

    box.appendChild(x);
  });
}

function renderAgenda(){
  let y=cur.getUTCFullYear(),m=cur.getUTCMonth();
  const list=filtered().filter(e=>{
    const d=parseDate(e.date);
    return d.getFullYear()===y && d.getMonth()===m;
  });

  const box=document.querySelector("#agenda");
  box.innerHTML="";

  if(!list.length){
    box.innerHTML='<div class="agenda-empty">No events this month.</div>';
    return;
  }

  const grouped={};
  list.forEach(e=>{
    (grouped[e.date] ||= []).push(e);
  });

  Object.keys(grouped).sort().forEach(date=>{
    const d=parseDate(date);
    const day=document.createElement("section");
    day.className="agenda-day";

    const dateHead=document.createElement("div");
    dateHead.className="agenda-date";
    dateHead.innerHTML=
      `<span class="dow">${days[d.getDay()].slice(0,3)}</span>`+
      `<span class="full-date">${names[d.getMonth()]} ${d.getDate()}</span>`;
    day.appendChild(dateHead);

    grouped[date].forEach(e=>{
      const row=document.createElement("div");
      row.className="agenda-event";
      const t=compactEventTime(e);
      const timeLabel=t || "All day";

      row.innerHTML=
        `<div class="agenda-time${t?"":" all-day"}">${escapeHtml(timeLabel)}</div>`+
        `<div class="agenda-copy ${e.type}">`+
          `<div class="agenda-title">${escapeHtml(displayTitle(e))}</div>`+
          (e.location?`<div class="agenda-location">${escapeHtml(e.location)}</div>`:"")+
        `</div>`;

      if(e.color){
        const copy=row.querySelector(".agenda-copy");
        if(copy) copy.style.borderLeftColor=e.color;
      }

      day.appendChild(row);
    });

    box.appendChild(day);
  });
}

function parseDate(s){
  const [y,m,d]=s.split("-").map(Number);
  return new Date(y,m-1,d,12,0,0);
}

function localDateString(d){
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}-${String(d.getDate()).padStart(2,"0")}`;
}

function escapeHtml(s){
  return String(s??"")
    .replaceAll("&","&amp;")
    .replaceAll("<","&lt;")
    .replaceAll(">","&gt;")
    .replaceAll('"',"&quot;")
    .replaceAll("'","&#039;");
}

document.querySelector("#prev").onclick=()=>{
  cur=new Date(Date.UTC(cur.getUTCFullYear(),cur.getUTCMonth()-1,1));
  render();
};

document.querySelector("#next").onclick=()=>{
  cur=new Date(Date.UTC(cur.getUTCFullYear(),cur.getUTCMonth()+1,1));
  render();
};

document.querySelectorAll("[data-f]").forEach(b=>b.onclick=()=>{
  document.querySelectorAll("[data-f]").forEach(x=>x.classList.remove("active"));
  b.classList.add("active");
  filter=b.dataset.f;
  render();
});

load().catch(err=>{
  console.error(err);
  alert("Calendar data could not be loaded.");
});