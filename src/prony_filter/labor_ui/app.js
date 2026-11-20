"use strict";

const el = id => document.getElementById(id);
const generatorDefaults = { f1:3, f2:7, a1:4, a2:0, d1:0.4, d2:0.2, noise:0 };
const learningTasks = {
  single: {
    parameters: {},
    task: "Ändere die Frequenz der ersten Schwingung von 3 auf 4 Hz. Wie verändern sich der Abstand der Wellenberge und die geschätzte Frequenz?",
  },
  pair: {
    parameters: {a2:2, order:4},
    task: "Die Eingabe enthält 3 und 7 Hz. Setze die Modellordnung zuerst auf 2, dann wieder auf 4. Welche Frequenzen erkennt das Modell? Verschiebe danach die Zielfrequenz auf 7 Hz.",
  },
  noisy: {
    parameters: {a2:2, order:4, noise:0.05},
    task: "Erhöhe das Rauschen von 0,05 auf 0,2. Vergleiche die geschätzten Frequenzen und den Modellfehler. Ab wann hält der Filter den Abzug zurück?",
  },
};
const analysisInputs = ["order", "target", "tolerance"];
const experiments = new Map();
const curves = {
  signal:   {name:"Eingangssignal", color:"#5346c7", dash:[], shown:true},
  filtered: {name:"Gefiltertes Signal", color:"#107d70", dash:[], shown:true},
  model:    {name:"Modell", color:"#b36b16", dash:[7,4], shown:false},
  removed:  {name:"Entfernter Anteil", color:"#a64c76", dash:[2,3], shown:false}
};
const formatters = new Map();
function fmt(value, precision=2) {
  if (!formatters.has(precision)) formatters.set(precision,new Intl.NumberFormat("de-DE",{maximumFractionDigits:precision}));
  return formatters.get(precision).format(value);
}
const significant = new Intl.NumberFormat("de-DE", {maximumSignificantDigits: 5});
function quantity(value) {
  if (!value) return "0";
  return Math.abs(value) < 1e-4 ? value.toExponential(3).replace(".", ",") : significant.format(value);
}
function node(tag, text, className) {
  const item = document.createElement(tag);
  if (text !== undefined) item.textContent = text;
  if (className) item.className = className;
  return item;
}
function showMessage(id, message) {
  el(id).textContent = message;
  el(id).hidden = !message;
}
function setStatus(text, state="") {
  el("run-status").textContent = text;
  el("run-status").className = "status " + state;
}

// Zahlenfeld und Schieberegler bedienen denselben Parameter.
function slider(parent, id, labelText, unit, min, max, step) {
  const row = node("div",undefined,"slider-row");
  const head = node("div",undefined,"slider-head");
  const label = node("label",labelText);
  label.htmlFor = id;
  const box = node("div",undefined,"value-box");
  const number = node("input");
  Object.assign(number,{type:"number",id,min,max,step,value:generatorDefaults[id],required:true});
  const range = node("input");
  Object.assign(range,{type:"range",id:id+"-range",min,max,step,value:generatorDefaults[id]});
  const osc = id === "noise" ? "" : ", Schwingung " + id.slice(-1);
  for (const input of [number,range]) input.setAttribute("aria-label",labelText + osc + " (" + unit + ")");
  box.append(number,node("span",unit));
  head.append(label,box);
  row.append(head,range);
  parent.append(row);
  range.addEventListener("input",()=>{
    number.value = range.value;
    paintRange(range);
    schedule();
  });
  number.addEventListener("input",()=>{
    if (number.validity.valid) {
      range.value = number.value;
      paintRange(range);
    }
    schedule();
  });
  paintRange(range);
}
function paintRange(input) {
  const fraction = (Number(input.value)-Number(input.min))/(Number(input.max)-Number(input.min));
  input.style.setProperty("--fill",(100*fraction)+"%");
}
for (const i of [1,2]) {
  const panel=el("osc-panel-"+i);
  slider(panel,"f"+i,"Frequenz","Hz",0.25,40,0.01);
  slider(panel,"a"+i,"Amplitude","a. E.",0,12,0.01);
  slider(panel,"d"+i,"Abklingrate","1/s",0,2,0.01);
  el("osc-"+i).addEventListener("click",()=>selectOscillator(i));
}
slider(el("noise-panel"),"noise","Rauschen (σ)","a. E.",0,2,0.01);
function selectOscillator(index) {
  for (const i of [1,2]) {
    el("osc-"+i).setAttribute("aria-pressed",String(i===index));
    el("osc-panel-"+i).hidden = i!==index;
  }
}

let timer, controller, generation=0, result, activeSettings, view="time", hoverIndex=null, geometry=null;
const canvas=el("chart"), ctx=canvas.getContext("2d");
function clearData(message) {
  result=null; hoverIndex=null; geometry=null;
  for (const id of ["sample-rate","analysis-rate","fit-error","mode-count"]) el(id).textContent="–";
  el("mode-rows").replaceChildren();
  el("steps").replaceChildren();
  el("comparison").textContent="";
  el("calculation").hidden=true;
  el("open-calculation").disabled=true;
  showMessage("analysis-note","");
  showMessage("plot-message",message);
  draw();
}
function readInputs() {
  const settings={source:el("source").value};
  const keys = settings.source === "synthetic" ? [...Object.keys(generatorDefaults), ...analysisInputs] : analysisInputs;
  for (const key of keys) {
    const input = el(key);
    if (!input.validity.valid) {
      const name = input.getAttribute("aria-label") || input.labels[0].firstChild.textContent;
      const range = input.min && input.max ? " Zulässig sind " + quantity(+input.min) + " bis " + quantity(+input.max) + "." : "";
      throw new Error("Prüfe die Eingabe für „" + name + "“." + range);
    }
    settings[key] = Number(input.value);
  }
  return settings;
}
function schedule(delay=250) {
  clearTimeout(timer);
  if(controller) controller.abort();
  const requestId=++generation;
  let settings;
  try {
    settings=readInputs();
    el("band").textContent=quantity(Math.max(0,settings.target-settings.tolerance))+" – "+quantity(settings.target+settings.tolerance)+" Hz";
  } catch (error) {
    el("band").textContent="–";
    setStatus("Eingabe prüfen","error");
    clearData(error.message);
    return;
  }
  setStatus("Berechnung läuft","busy");
  clearData("Signal wird berechnet …");
  timer=setTimeout(()=>analyze(settings,requestId),delay);
}
async function analyze(settings,requestId) {
  const current = new AbortController();
  controller=current;
  try {
    const response=await fetch("/api/analyze",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(settings),signal:current.signal});
    const data=await response.json();
    if(requestId!==generation) return;
    if(!response.ok || data.error) throw new Error(data.error || "Die Analyse ist fehlgeschlagen.");
    result=data; activeSettings=settings;
    renderResult();
    setStatus("Bereit");
  } catch(error) {
    if(requestId!==generation || error.name==="AbortError") return;
    clearData(error instanceof TypeError ? "Der lokale Analyseserver ist nicht erreichbar." : error.message);
    setStatus("Fehler bei der Analyse","error");
  } finally {
    if(controller===current) controller=null;
  }
}
function creditLink(name, url) {
  if (!name) return null;
  if (!url || !/^https?:\/\//i.test(url)) return document.createTextNode(name);
  const link = node("a", name);
  link.href = url;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  return link;
}
function unitDescription(unit) {
  return unit === "Dateieinheit" ? "Einheit nicht angegeben" : unit;
}
function showExperiment(experiment) {
  el("experiment-info").hidden = false;
  el("experiment-description").textContent = experiment.description;
  const list = el("source-facts");
  list.replaceChildren();
  for (const [label, value] of [
    ["Signal und Einheit", [experiment.signalLabel, unitDescription(experiment.unit)].filter(Boolean).join(" · ")],
    ["Quelle", creditLink(experiment.sourceName, experiment.sourceUrl)],
    ["Lizenz", creditLink(experiment.license, experiment.licenseUrl)],
    ["Urheber / Nachweis", experiment.attribution],
    ["Datenaufbereitung", experiment.processing],
  ]) {
    if (!value) continue;
    const text = node("dd");
    text.append(value);
    list.append(node("dt", label), text);
  }
  if (experiment.csvUrl) {
    const link = node("a", "Messwerte als CSV");
    link.href = experiment.csvUrl;
    link.download = "";
    const download = node("dd");
    download.append(link);
    list.append(node("dt", "Download"), download);
  }
  el("provenance").hidden = list.childElementCount === 0;
}
function restoreParameters(experiment, taskId="single") {
  for (const [key, lower, upper] of [
    ["target", experiment.minTarget, experiment.maxTarget],
    ["tolerance", experiment.minTolerance, experiment.maxTolerance],
  ]) {
    const input = el(key);
    input.min = String(lower);
    input.max = String(upper);
    input.value = experiment[key];
  }
  el("order").value = experiment.order;
  if (experiment.id !== "synthetic") return;
  const task = learningTasks[taskId];
  const settings = {...generatorDefaults, ...task.parameters};
  for (const [id, value] of Object.entries(settings)) {
    el(id).value = value;
    const range = el(id + "-range");
    if (range) {range.value = value; paintRange(range);}
  }
  for (const id of Object.keys(learningTasks)) el("preset-" + id).setAttribute("aria-pressed", String(id === taskId));
  el("learning-task").textContent = task.task;
  selectOscillator(1);
}
function sourceChanged() {
  const select = el("source");
  const experiment = experiments.get(select.value);
  if (!experiment) return;
  el("synthesis").hidden = experiment.id !== "synthetic";
  el("learning").hidden = experiment.id !== "synthetic";
  el("previous-source").disabled = select.selectedIndex === 0;
  el("next-source").disabled = select.selectedIndex === select.length - 1;
  showExperiment(experiment);
  restoreParameters(experiment);
  el("time-zoom").value = "all";
  el("time-pan").value = 0;
  updateTimeControls();
  schedule(0);
}
function moveSource(offset) {
  el("source").selectedIndex += offset;
  sourceChanged();
}
async function loadCatalog() {
  el("retry-catalog").hidden = true;
  setStatus("Versuche laden …", "busy");
  try {
    const response = await fetch("/api/catalog");
    if (!response.ok) throw new Error();
    const {experiments: entries} = await response.json();
    if (!Array.isArray(entries) || !entries.length) throw new Error();
    const groups = new Map();
    experiments.clear();
    for (const entry of entries) {
      experiments.set(entry.id, entry);
      const group = entry.group;
      if (!groups.has(group)) {
        const options = document.createElement("optgroup");
        options.label = group;
        groups.set(group, options);
      }
      groups.get(group).append(new Option(entry.title, entry.id));
    }
    const select = el("source");
    select.replaceChildren(...groups.values());
    select.value = experiments.has("synthetic") ? "synthetic" : entries[0].id;
    select.disabled = false;
    el("catalog-count").textContent = "· " + fmt(entries.length) + (entries.length === 1 ? " Versuch" : " Versuche");
    document.querySelector(".parameters").inert = false;
    sourceChanged();
  } catch {
    clearData("Der Versuchskatalog ist nicht erreichbar. Prüfe, ob das Labor läuft, und lade die Versuche erneut.");
    setStatus("Katalog nicht verfügbar", "error");
    el("retry-catalog").hidden = false;
  }
}
el("source").addEventListener("change", sourceChanged);
el("previous-source").addEventListener("click", () => moveSource(-1));
el("next-source").addEventListener("click", () => moveSource(1));
el("retry-catalog").addEventListener("click", loadCatalog);
for (const id of analysisInputs) el(id).addEventListener(id==="order"?"change":"input",()=>schedule());
el("reset").addEventListener("click", sourceChanged);
el("open-calculation").addEventListener("click", () => {
  const detail = el("calculation");
  detail.open = true;
  detail.querySelector("summary").focus({preventScroll:true});
  detail.scrollIntoView({block:"start"});
});
for (const taskId of Object.keys(learningTasks)) {
  el("preset-" + taskId).addEventListener("click", () => {
    restoreParameters(experiments.get("synthetic"), taskId);
    schedule(0);
  });
}

function hankelExample(samples) {
  const example = node("div", undefined, "hankel-example");
  example.id = "hankel-example";
  for (const [offset, name] of [[0, "H₀"], [1, "H₁"]]) {
    const block = node("div", undefined, "matrix-block");
    block.append(node("strong", name + " ="));
    const matrix = node("div", undefined, "matrix");
    matrix.setAttribute("role", "img");
    const entries = [samples[offset], samples[offset+1], samples[offset+1], samples[offset+2]].map(quantity);
    matrix.setAttribute("aria-label", name + ", erste Zeile " + entries.slice(0,2).join(" und ") + ", zweite Zeile " + entries.slice(2).join(" und "));
    for (const value of entries) matrix.append(node("span", value, "matrix-entry"));
    block.append(matrix);
    example.append(block);
  }
  return example;
}

function renderResult() {
  showMessage("plot-message","");
  showMessage("analysis-note",result.status || "");
  el("sample-rate").textContent=quantity(result.sampleRate)+" Hz";
  el("analysis-rate").textContent=quantity(result.analysisRate)+" Hz";
  const percent=result.fitError*100;
  el("fit-error").textContent=percent>0 && percent<0.001 ? "< 0,001 %" : fmt(percent,3)+" %";
  el("mode-count").textContent=result.modes.length;
  el("amplitude-label").textContent = result.unit === "Dateieinheit" ? "Amplitude" : "Amplitude (" + result.unit + ")";
  const windowText = "Zeitfenster " + quantity(result.time[0]) + " bis " + quantity(result.time.at(-1)) + " s";
  if (activeSettings.source === "synthetic") {
    const frequencies = [1,2].filter(i => activeSettings["a"+i] > 0).map(i => fmt(activeSettings["f"+i]) + " Hz");
    el("comparison").textContent = frequencies.length ? "Im Generator eingestellt: " + frequencies.join(" und ") + "." : "Beide Schwingungen sind ausgeschaltet. Die Eingabe besteht aus Rauschen.";
  } else {
    el("comparison").textContent = windowText + " · " + fmt(result.sampleCount, 0) + " Messwerte" + (result.unit === "Dateieinheit" ? " · Einheit nicht angegeben" : "");
  }
  const body=el("mode-rows");
  body.replaceChildren();
  for (const mode of result.modes) {
    const row=node("tr");
    const state=node("td");
    state.append(node("span",mode.selected?"Entfernt":"Erhalten","mode-tag"+(mode.selected?" selected":"")));
    row.append(node("td",quantity(mode.frequency)+" Hz"),node("td",quantity(mode.decay)+" 1/s"),node("td",quantity(mode.amplitude)),state);
    body.append(row);
  }
  if (!result.modes.length) {
    const cell=node("td","Keine Moden gefunden.");
    cell.colSpan=4;
    const row=node("tr");row.append(cell);body.append(row);
  }
  const steps=el("steps");
  el("calculation").hidden=!result.pencil;
  el("open-calculation").disabled=!result.pencil;
  if(result.pencil) {
    const {rows,columns,rank,samples}=result.pencil;
    const buildStep = node("li","Die Hankelmatrizen H₀ und H₁ haben je "+fmt(rows)+" Zeilen und "+fmt(columns)+" Spalten. H₁ beginnt einen Abtastwert später.");
    if (samples?.length >= 4) {
      buildStep.append(node("p","Die ersten vier Werte des Schätzsignals sind " + samples.slice(0,4).map(quantity).join(" · ") + ". Links oben beginnen die Matrizen so:"));
      buildStep.append(hankelExample(samples));
    }
    steps.replaceChildren(node("li","Die Polschätzung nutzt "+quantity(result.analysisRate)+" Werte pro Sekunde. Der Zeitschritt Δt beträgt "+quantity(1/result.analysisRate)+" s."),
      buildStep,
      node("li","Die Singulärwertzerlegung liefert den Teilraum mit Rang "+rank+". Aus dem reduzierten Matrizenpaar ergeben sich die diskreten Pole z."));
    const pole=result.modes.find(mode=>mode.frequency>0.000001 && Number.isFinite(mode.poleImag));
    if(pole) {
      const poleStep = node("li","Ein Pol ist z ≈ "+quantity(pole.poleReal)+(pole.poleImag<0?" − ":" + ")+quantity(Math.abs(pole.poleImag))+"i. Sein Winkel liefert f = |arg(z)| / (2π Δt) ≈ "+quantity(pole.frequency)+" Hz. Sein Betrag liefert die Abklingrate −ln|z| / Δt ≈ "+quantity(pole.decay)+" 1/s.");
      poleStep.append(node("p","Bei gleichem Zeitschritt bedeutet ein größerer Winkelbetrag eine höhere Frequenz. Ein Polbetrag unter 1 lässt die Amplitude mit jedem Abtastschritt sinken."));
      steps.append(poleStep);
    }
    const removed = result.modes.filter(mode => mode.selected).map(mode => quantity(mode.frequency) + " Hz");
    const decision = removed.length ? "Vom Eingangssignal werden die rekonstruierten Anteile bei " + removed.join(" und ") + " abgezogen." : "Bei dieser Einstellung bleibt das Eingangssignal vollständig erhalten.";
    steps.append(node("li", "Das Labor passt Amplituden und Phasen gemeinsam mit der Methode der kleinsten Quadrate an. " + decision));
  }
  draw();
}
for (const button of document.querySelectorAll("[data-curve]")) {
  button.addEventListener("click",()=>{
    const line=curves[button.dataset.curve];line.shown=!line.shown;
    button.setAttribute("aria-pressed",String(line.shown));draw();
  });
}
function changeView(next) {
  view=next;hoverIndex=null;
  const isTime=view==="time";
  el("time-view").setAttribute("aria-pressed",String(isTime));el("mode-view").setAttribute("aria-pressed",String(!isTime));
  el("chart-heading").textContent=isTime ? "Signalverlauf" : "Modenspektrum";
  canvas.setAttribute("aria-label",el("chart-heading").textContent+". Mit den Pfeiltasten Werte ablesen.");
  el("curve-controls").hidden=!isTime;el("spectral-key").hidden=isTime;draw();
  el("time-controls").hidden=!isTime;
}
el("time-view").addEventListener("click",()=>changeView("time"));
el("mode-view").addEventListener("click",()=>changeView("frequency"));

function updateTimeControls() {
  const full = el("time-zoom").value === "all";
  el("time-pan").hidden = full;
  el("pan-label").hidden = full;
  paintRange(el("time-pan"));
}
el("time-zoom").addEventListener("change", () => {
  updateTimeControls();
  clearHover();
});
el("time-pan").addEventListener("input", () => {
  paintRange(el("time-pan"));
  clearHover();
});
function timeSlice() {
  const times = result.time;
  const duration = times.at(-1) - times[0];
  const zoom = el("time-zoom").value;
  if (zoom === "all") return [0, times.length - 1];
  const span = zoom === "half" ? duration / 2 : Math.min(duration, 10 / activeSettings.target);
  const start = times[0] + (duration - span) * Number(el("time-pan").value) / 1000;
  let first = times.findIndex(t => t >= start);
  first = Math.min(Math.max(first, 0), times.length - 2);
  let last = times.findIndex(t => t >= start + span);
  if (last === -1) last = times.length - 1;
  return [first, Math.max(first + 1, last)];
}

// Die Achsenskalierung folgt den gerade sichtbaren Kurven.
function tickStep(span,count) {
  const nominal=span/Math.max(2,count);
  const magnitude=10**Math.floor(Math.log10(nominal));
  const step=[1,2,2.5,5,10].find(value=>value>=nominal/magnitude);
  return (step || 10)*magnitude;
}
function tickText(value,step) {
  if (Math.abs(value) < step * 1e-6) return "0";
  const precision = Math.max(0, 1 - Math.floor(Math.log10(step)));
  return fmt(value, Math.min(12, precision));
}
function line(x1,y1,x2,y2,color,width=1) {
  ctx.beginPath();ctx.strokeStyle=color;ctx.lineWidth=width;ctx.moveTo(x1,y1);ctx.lineTo(x2,y2);ctx.stroke();
}
function draw() {
  showMessage("plot-tooltip","");
  const width=canvas.clientWidth, height=canvas.clientHeight;
  if(!width || !height) return;
  const ratio=window.devicePixelRatio || 1;
  if(canvas.width!==Math.round(width*ratio) || canvas.height!==Math.round(height*ratio)) {
    canvas.width=Math.round(width*ratio);canvas.height=Math.round(height*ratio);
  }
  ctx.setTransform(ratio,0,0,ratio,0,0);ctx.clearRect(0,0,width,height);
  if(!result) return;
  const timeView=view==="time";
  const shown=Object.entries(curves).filter(([,curve])=>curve.shown);
  const right=width-24, top=36, bottom=height-52;
  let yLow=Infinity,yHigh=-Infinity,xMin,xMax,first=0,last=result.time.length-1;
  if(timeView) {
    [first,last]=timeSlice();
    xMin=result.time[first];xMax=result.time[last];
    for(const [key] of shown) {
      for(let i=first;i<=last;i++) {
        yLow=Math.min(yLow,result[key][i]);
        yHigh=Math.max(yHigh,result[key][i]);
      }
    }
  } else {
    xMin=0;
    xMax=Math.max(activeSettings.target+activeSettings.tolerance,...result.modes.map(m=>m.frequency))*1.08;
    yLow=0;yHigh=Math.max(0,...result.modes.map(m=>m.amplitude));
  }
  if(!Number.isFinite(yLow)) {yLow=-1;yHigh=1;}
  if(yHigh===yLow) {const pad=Math.abs(yLow)*0.03 || 1;yHigh+=pad;if(timeView)yLow-=pad;}
  const margin=(yHigh-yLow)*0.065;
  yHigh+=margin;if(timeView)yLow-=margin;
  const dy=tickStep(yHigh-yLow,5);
  const yMin=Math.floor(yLow/dy)*dy,yMax=Math.ceil(yHigh/dy)*dy;
  const magnitude = Math.max(Math.abs(yMin), Math.abs(yMax));
  const exponent = magnitude ? 3 * Math.floor(Math.log10(magnitude)/3) : 0;
  const yScale = exponent >= 6 || exponent <= -3 ? 10**exponent : 1;
  const xlabel = j => tickText(j*dy/yScale, dy/yScale);
  ctx.font = '13px "Segoe UI", Arial, sans-serif';
  let labelWidth = 24;
  for (let j=Math.ceil(yMin/dy-1e-8);j<=Math.floor(yMax/dy+1e-8);j++) {
    labelWidth = Math.max(labelWidth, ctx.measureText(xlabel(j)).width);
  }
  const left = Math.ceil(labelWidth)+13;
  const dx=tickStep(xMax-xMin,Math.min(9,Math.floor((right-left)/72)));
  const x=t=>left+(t-xMin)/(xMax-xMin)*(right-left);
  const y=v=>bottom-(v-yMin)/(yMax-yMin)*(bottom-top);
  geometry={xMin,xMax,left,right,top,bottom,first,last};
  ctx.textBaseline="middle";ctx.fillStyle="#405068";ctx.textAlign="left";
  const experiment=experiments.get(activeSettings.source);
  const signalName=timeView ? experiment.signalLabel || "Signalwert" : "Anfangsamplitude";
  const superscript = String(exponent).replace(/[-0-9]/g, char => ({"-":"⁻","0":"⁰","1":"¹","2":"²","3":"³","4":"⁴","5":"⁵","6":"⁶","7":"⁷","8":"⁸","9":"⁹"})[char]);
  ctx.fillText(signalName+" ("+(yScale===1 ? "" : "×10"+superscript+" ")+unitDescription(result.unit)+")",left,15,right-left);
  ctx.textAlign="right";
  for(let j=Math.ceil(yMin/dy-1e-8);j<=Math.floor(yMax/dy+1e-8);j++) {
    const v=j*dy;line(left,y(v),right,y(v),j===0?"#bfc9d8":"#e5e9f0");
    ctx.fillText(xlabel(j),left-8,y(v));
  }
  ctx.textAlign="center";ctx.textBaseline="top";
  for(let j=Math.ceil(xMin/dx-1e-8);j<=Math.floor(xMax/dx+1e-8);j++) {
    const v=j*dx;line(x(v),top,x(v),bottom,"#e8ecf2");ctx.fillText(tickText(v,dx),x(v),bottom+5);
  }
  ctx.fillText(timeView?"Zeit (s)":"Frequenz (Hz)",(left+right)/2,height-19);
  ctx.save();ctx.beginPath();ctx.rect(left-1,top,right-left+2,bottom-top+1);ctx.clip();
  if(timeView) {
    for(const [key,curve] of shown) {
      ctx.beginPath();ctx.strokeStyle=curve.color;ctx.lineWidth=key==="signal"?2.15:1.8;ctx.setLineDash(curve.dash);
      for(let i=first;i<=last;i++) {
        const tx=x(result.time[i]),vy=y(result[key][i]);if(i===first)ctx.moveTo(tx,vy);else ctx.lineTo(tx,vy);
      }
      ctx.stroke();
    }
    ctx.setLineDash([]);
  } else {
    const lower=x(Math.max(0,activeSettings.target-activeSettings.tolerance)),upper=x(activeSettings.target+activeSettings.tolerance);
    ctx.fillStyle="#78bea943";ctx.fillRect(lower,top,upper-lower,bottom-top);
    for(const mode of result.modes) {
      const px=x(mode.frequency),py=y(mode.amplitude);
      line(px,y(0),px,py,"#5346c7",3);
      ctx.beginPath();ctx.arc(px,py,4,0,Math.PI*2);ctx.fillStyle="#5346c7";ctx.fill();
    }
  }
  if(hoverIndex!==null) {
    let tip,px;
    if(timeView) {
      px=x(result.time[hoverIndex]);
      tip=quantity(result.time[hoverIndex])+" s";
      for(const [key,curve] of shown) tip+="\n"+curve.name+"  "+quantity(result[key][hoverIndex])+" "+result.unit;
    } else if(result.modes.length) {
      const mode=result.modes[hoverIndex];px=x(mode.frequency);tip=quantity(mode.frequency)+" Hz\nAmplitude  "+quantity(mode.amplitude)+" "+result.unit;
    }
    if(tip) {
      ctx.setLineDash([3,3]);line(px,top,px,bottom,"#728099");ctx.setLineDash([]);
      showMessage("plot-tooltip",tip);
    }
  }
  ctx.restore();
  if(timeView && !shown.length) {
    ctx.fillStyle="#46546c";ctx.textAlign="center";ctx.fillText("Wähle eine Kurve in der Legende.",(left+right)/2,(top+bottom)/2);
  }
}
canvas.addEventListener("pointermove",event=>{
  if(!result || !geometry) return;
  const {left,right,xMin,xMax,top,bottom}=geometry;
  const pos=canvas.getBoundingClientRect(), x=event.clientX-pos.left,y=event.clientY-pos.top;
  if(x<left || x>right || y<top || y>bottom) {hoverIndex=null;draw();return;}
  const value=xMin+(x-left)/(right-left)*(xMax-xMin);
  const values=view==="time"?result.time:result.modes.map(m=>m.frequency);
  if(!values.length)return;
  let best=0;
  for(let i=1;i<values.length;i++) if(Math.abs(values[i]-value)<Math.abs(values[best]-value)) best=i;
  if(best!==hoverIndex) {hoverIndex=best;draw();}
});
function clearHover() {hoverIndex=null;draw();}
canvas.addEventListener("pointerleave",clearHover);
canvas.addEventListener("blur",clearHover);
canvas.addEventListener("keydown",event=>{
  if(!result || !["ArrowLeft","ArrowRight","Home","End","Escape"].includes(event.key)) return;
  event.preventDefault();
  if(!geometry || event.key==="Escape") {clearHover();return;}
  const first=view==="time"?geometry.first:0, last=view==="time"?geometry.last:result.modes.length-1;
  if(last < first) return;
  if(event.key==="Home") hoverIndex=first;
  else if(event.key==="End") hoverIndex=last;
  else if(hoverIndex===null) hoverIndex=first;
  else hoverIndex=Math.max(first,Math.min(last,hoverIndex+(event.key==="ArrowRight"?1:-1)));
  draw();
});
new ResizeObserver(draw).observe(el("chart-wrap"));
loadCatalog();
