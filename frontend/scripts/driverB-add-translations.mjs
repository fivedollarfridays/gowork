/**
 * Driver B (sprint/gowork-facelift) — append home.ch1..ch8 translations
 * to en.json and es.json without disturbing existing keys.
 *
 * Idempotent: re-running just overwrites the ch* subtrees in `home`.
 *
 * Spanish copy is native-fluent (not machine-translated). Where the English
 * uses an idiom ("brick by brick"), the Spanish uses an equivalent gesture
 * ("ladrillo por ladrillo") rather than a calque.
 */
import fs from "node:fs";
import path from "node:path";
import url from "node:url";

const __dirname = path.dirname(url.fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, "..");
const enPath = path.join(root, "src/lib/translations/en.json");
const esPath = path.join(root, "src/lib/translations/es.json");

const en = JSON.parse(fs.readFileSync(enPath, "utf8"));
const es = JSON.parse(fs.readFileSync(esPath, "utf8"));

en.home = en.home || {};
es.home = es.home || {};

en.home.ch1 = {
  eyebrow: "HackFW 2026 · Fort Worth, TX · live in production",
  morphLine1Aria: "wall",
  line2: "There is a {{wall}} between you and {{job}}.",
  line2Wall: "wall",
  line2Job: "a job.",
  line3: "We tear it {{down}} — brick by brick.",
  line3Down: "down",
  ariaLabel:
    "There is a wall between you and a job. We tear it down, brick by brick.",
  subhead:
    "A Fort Worth worker hits {{seven}} before payroll: a suspended license, a court date, a childcare gap, a 47-minute bus headway, a record someone won't read past, a $2 raise that costs $400, and nobody to call. {{system}}",
  subheadSeven: "seven invisible barriers",
  subheadSystem: "GoWork is the first system that sees all seven at once.",
  ctaPrimary: "Get your plan",
  ctaGhost: "See how it works",
  scrollCue: "scroll",
  marquee: {
    license: "Suspended license",
    court: "Open court date",
    pickup: "Childcare pickup gap",
    bus: "47-minute bus headway",
    background: "Background-check stigma",
    cliff: "Wage-cliff math",
    nobody: "No human to call",
  },
  morphWords: [
    "wall",
    "license",
    "court date",
    "pickup",
    "47-min bus",
    "background",
    "wage cliff",
  ],
};

es.home.ch1 = {
  eyebrow: "HackFW 2026 · Fort Worth, TX · en producción",
  morphLine1Aria: "muro",
  line2: "Hay un {{wall}} entre tú y {{job}}",
  line2Wall: "muro",
  line2Job: "un trabajo.",
  line3: "Lo derribamos {{down}} — ladrillo por ladrillo.",
  line3Down: "ahora",
  ariaLabel:
    "Hay un muro entre tú y un trabajo. Lo derribamos, ladrillo por ladrillo.",
  subhead:
    "Un trabajador de Fort Worth choca contra {{seven}} antes del primer cheque: licencia suspendida, una cita en corte, recoger a los hijos, un autobús cada 47 minutos, antecedentes que nadie quiere leer, un aumento de $2 que cuesta $400 y nadie a quién llamar. {{system}}",
  subheadSeven: "siete barreras invisibles",
  subheadSystem: "GoWork es el primer sistema que las ve todas a la vez.",
  ctaPrimary: "Obtén tu plan",
  ctaGhost: "Mira cómo funciona",
  scrollCue: "desliza",
  marquee: {
    license: "Licencia suspendida",
    court: "Cita en corte",
    pickup: "Recoger a los niños",
    bus: "Autobús cada 47 minutos",
    background: "Antecedentes",
    cliff: "Acantilado de salario",
    nobody: "Nadie a quién llamar",
  },
  morphWords: [
    "muro",
    "licencia",
    "cita en corte",
    "los niños",
    "autobús 47-min",
    "antecedentes",
    "acantilado",
  ],
};

en.home.ch2 = {
  eyebrow: "The numbers",
  stat1Number: "600,000+",
  stat1Cap:
    "Texans hit a barrier this year that costs them a job they could have held.",
  stat2Number: "87 min",
  stat2Cap:
    "Average commute Carlos faces between his shift and his daughter's 2 p.m. dismissal — until we sequence the day.",
  stat3Number: "7",
  stat3Cap:
    "Distinct barriers in a single working week. None of them his work ethic. All of them connected.",
  stat4Number: "$22.50/hr",
  stat4Cap:
    "Wage of the fair-chance job 4.2 miles away — the destination the whole map orbits around.",
  pull: "These aren't talking points. They're {{tuesday}}.",
  pullTuesday: "Tuesday",
  ariaLabel: "The numbers behind the wall",
};

es.home.ch2 = {
  eyebrow: "Los números",
  stat1Number: "600,000+",
  stat1Cap:
    "tejanos chocan este año contra una barrera que les cuesta un empleo que podrían haber mantenido.",
  stat2Number: "87 min",
  stat2Cap:
    "Trayecto promedio que Carlos enfrenta entre su turno y la salida de su hija a las 2 p.m., hasta que ordenamos el día.",
  stat3Number: "7",
  stat3Cap:
    "Barreras distintas en una sola semana de trabajo. Ninguna es su ética laboral. Todas están conectadas.",
  stat4Number: "$22.50/hr",
  stat4Cap:
    "Salario del empleo de segunda oportunidad a 4.2 millas, el destino alrededor del cual gira el mapa entero.",
  pull: "No son frases. Son {{tuesday}}.",
  pullTuesday: "el martes",
  ariaLabel: "Los números detrás del muro",
};

en.home.ch3 = {
  eyebrow: "Meet Carlos",
  portraitAlt: "Stylized portrait of Carlos, a Fort Worth welder",
  captionEyebrow: "CARLOS R. · 34 · ZIP 76104",
  captionQuote:
    "I work nights at a warehouse. School pickup at 2. The bus runs every 47 minutes. You do the math.",
  h2Words: [
    "A",
    "father.",
    "A",
    "welder.",
    "Not",
    "a",
    "case",
    "number.",
  ],
  italicFromIndex: 4,
  p1:
    "Carlos lives in {{zip}} — a Fort Worth ZIP where one in three adults has an open record from a warrant they didn't know about, a license they couldn't afford to clear, or a court date they couldn't take off work to attend.",
  p1Zip: "76104",
  p2:
    "He has work history. He has references. He has a daughter who needs to be picked up from Como Elementary at 2:00. {{bold}} — until now.",
  p2Bold:
    "What he doesn't have is a system that can hold all of those things in its head at once",
  fact1Num: "2:30",
  fact1Cap: "clock-out",
  fact2Num: "2:00",
  fact2Cap: "school dismissal",
  fact3Num: "47",
  fact3Cap: "bus headway · min",
  fact4Num: "4:00",
  fact4Cap: "court date",
  ariaLabel: "Meet Carlos — a father, a welder, not a case number",
};

es.home.ch3 = {
  eyebrow: "Conoce a Carlos",
  portraitAlt: "Retrato estilizado de Carlos, soldador de Fort Worth",
  captionEyebrow: "CARLOS R. · 34 · ZIP 76104",
  captionQuote:
    "Trabajo de noche en una bodega. Recojo a mi hija de la escuela a las 2. El autobús pasa cada 47 minutos. Saca la cuenta.",
  h2Words: [
    "Un",
    "papá.",
    "Un",
    "soldador.",
    "No",
    "un",
    "número",
    "de caso.",
  ],
  italicFromIndex: 4,
  p1:
    "Carlos vive en {{zip}}, un código postal de Fort Worth donde uno de cada tres adultos tiene un expediente abierto: una orden que no sabía que existía, una licencia que no pudo pagar para arreglar, o una cita en corte a la que no pudo faltar al trabajo para asistir.",
  p1Zip: "76104",
  p2:
    "Tiene historial laboral. Tiene referencias. Tiene una hija a la que hay que recoger en la escuela primaria Como a las 2:00. {{bold}}, hasta ahora.",
  p2Bold:
    "Lo que no tiene es un sistema que pueda sostener todo eso en la cabeza al mismo tiempo",
  fact1Num: "2:30",
  fact1Cap: "fin de turno",
  fact2Num: "2:00",
  fact2Cap: "salida de escuela",
  fact3Num: "47",
  fact3Cap: "autobús · min",
  fact4Num: "4:00",
  fact4Cap: "cita en corte",
  ariaLabel: "Conoce a Carlos: un papá, un soldador, no un número de caso",
};

en.home.ch7 = {
  eyebrow: "The cliff",
  h2: "A {{raise}} that costs {{cost}} is not a raise.",
  h2Raise: "$2 raise",
  h2Cost: "$400",
  p1:
    "At {{wage}}, Carlos crosses a benefits cliff. SNAP drops $312. Childcare subsidy phases out. Medicaid lapses. The raise nets a $400/month {{loss}} — and he can't see it until the first paycheck after the offer.",
  p1Wage: "$18.50/hr",
  p1Loss: "loss",
  p2:
    "We do this math for every offer. Honestly. Before the signature. So the next move is a {{real}}.",
  p2Real: "real one",
  controlsLabel: "Hourly wage",
  rowGross: "Gross / mo",
  rowSnap: "SNAP change",
  rowCc: "Childcare",
  rowMed: "Medicaid",
  rowTotal: "Real Δ / mo",
  medSafe: "safe",
  medAtRisk: "at risk",
  medLapses: "lapses",
  chartAria: "Wage cliff chart — real take-home by hourly wage",
  cliffZone: "cliff zone",
  ariaLabel: "The benefits cliff — a $2 raise that costs $400",
};

es.home.ch7 = {
  eyebrow: "El acantilado",
  h2: "Un {{raise}} que cuesta {{cost}} no es un aumento.",
  h2Raise: "aumento de $2",
  h2Cost: "$400",
  p1:
    "A {{wage}}, Carlos cruza un acantilado de beneficios. SNAP baja $312. El subsidio de cuidado infantil se acaba. Medicaid se cae. El aumento le deja una {{loss}} de $400 al mes, y no la ve hasta el primer cheque después de aceptar la oferta.",
  p1Wage: "$18.50/hr",
  p1Loss: "pérdida",
  p2:
    "Hacemos esta cuenta para cada oferta. Sin trampas. Antes de la firma. Para que el siguiente paso sea uno {{real}}.",
  p2Real: "de verdad",
  controlsLabel: "Salario por hora",
  rowGross: "Bruto / mes",
  rowSnap: "Cambio en SNAP",
  rowCc: "Cuidado infantil",
  rowMed: "Medicaid",
  rowTotal: "Δ real / mes",
  medSafe: "seguro",
  medAtRisk: "en riesgo",
  medLapses: "se cae",
  chartAria:
    "Gráfica del acantilado salarial: ingreso real por salario por hora",
  cliffZone: "zona de acantilado",
  ariaLabel: "El acantilado de beneficios: un aumento de $2 que cuesta $400",
};

en.home.ch8 = {
  eyebrow: "Find your path",
  line1: "We won't fix the wall.",
  line2: "We'll just keep tearing it down,",
  line3: "brick by brick by brick,",
  line4: "until you have somewhere to {{tuesday}}",
  line4Tuesday: "be on Tuesday.",
  ctaPrimary: "Get your plan",
  ctaMeta: "~3 min · web or text · in English or Spanish",
  wordmarkRow1: "GO",
  wordmarkRow2: "WORK",
  ariaLabel: "Find your path — get your plan",
};

es.home.ch8 = {
  eyebrow: "Encuentra tu camino",
  line1: "No vamos a arreglar el muro.",
  line2: "Lo seguiremos derribando,",
  line3: "ladrillo por ladrillo por ladrillo,",
  line4: "hasta que tengas a dónde {{tuesday}}",
  line4Tuesday: "ir el martes.",
  ctaPrimary: "Obtén tu plan",
  ctaMeta: "~3 min · web o texto · en inglés o español",
  wordmarkRow1: "GO",
  wordmarkRow2: "WORK",
  ariaLabel: "Encuentra tu camino: obtén tu plan",
};

fs.writeFileSync(enPath, JSON.stringify(en, null, 2) + "\n");
fs.writeFileSync(esPath, JSON.stringify(es, null, 2) + "\n");

console.log("Driver B translations merged into en.json + es.json");
