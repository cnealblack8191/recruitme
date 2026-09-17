from pdfkit import *

TALKS = [
    ("Lock out and tag out before you touch it", "Bloqueo y etiquetado antes de tocar", "29 CFR 1926.417"),
    ("Verify zero energy: test before touch", "Verifique cero energía: pruebe antes de tocar", "NFPA 70E 120.5"),
    ("Arc-flash PPE categories and approach boundaries", "Categorías de EPP contra arco eléctrico y límites de aproximación", "NFPA 70E 130"),
    ("GFCI protection and assured equipment grounding", "Protección GFCI y programa de puesta a tierra", "29 CFR 1926.404(b)(1)"),
    ("Extension cords and temporary power", "Extensiones eléctricas y energía temporal", "29 CFR 1926.405(a)(2)"),
    ("Ladder inspection and setup", "Inspección y colocación de escaleras", "29 CFR 1926.1053"),
    ("Aerial and scissor lifts: harness, tie-off, ground conditions", "Plataformas elevadoras: arnés, anclaje y condiciones del terreno", "29 CFR 1926.453"),
    ("Fall protection above six feet", "Protección contra caídas a más de seis pies", "29 CFR 1926.501"),
    ("Working near overhead power lines", "Trabajo cerca de líneas eléctricas aéreas", "29 CFR 1926.416, 1926.1408"),
    ("Trenching and excavation for underground feeders", "Zanjas y excavaciones para alimentadores subterráneos", "29 CFR 1926.651, 1926.652"),
    ("Hazard communication and safety data sheets", "Comunicación de riesgos y hojas de datos de seguridad", "29 CFR 1926.59"),
    ("Heat illness: water, rest, shade, acclimatization", "Enfermedades por calor: agua, descanso, sombra y aclimatación", "OSHA Heat NEP; proposed rule"),
    ("Hand and power tool inspection", "Inspección de herramientas manuales y eléctricas", "29 CFR 1926.300"),
    ("Eye and face protection when cutting and drilling", "Protección de ojos y cara al cortar y perforar", "29 CFR 1926.102"),
    ("Hearing protection around demolition and generators", "Protección auditiva cerca de demolición y generadores", "29 CFR 1926.52, 1926.101"),
    ("Housekeeping, walkways and material storage", "Orden y limpieza, pasillos y almacenamiento de materiales", "29 CFR 1926.25"),
    ("Struck-by hazards: cranes, forklifts, deliveries", "Golpes por objetos: grúas, montacargas y entregas", "29 CFR 1926.600, 1926.1400"),
    ("Confined spaces: vaults, manholes, crawl spaces", "Espacios confinados: bóvedas, pozos de registro y entretechos", "29 CFR 1926 Subpart AA"),
    ("Silica dust when drilling concrete and block", "Polvo de sílice al perforar concreto y bloque", "29 CFR 1926.1153"),
    ("Fire prevention and hot-work permits", "Prevención de incendios y permisos de trabajo en caliente", "29 CFR 1926.150, 1926.352"),
    ("Emergency action: exits, first aid, who to call", "Plan de emergencia: salidas, primeros auxilios y a quién llamar", "29 CFR 1926.35, 1926.50"),
    ("Near-miss reporting: speak up", "Reporte de casi accidentes: hable", "OSHA Recommended Practices"),
    ("Driving and trailer safety between jobs", "Seguridad al conducir y con remolques entre trabajos", "Company policy; FMCSA where applicable"),
    ("Cold, wet and windy conditions", "Frío, humedad y viento", "General duty; company policy"),
    ("Stop-work authority: anyone can call it", "Autoridad para detener el trabajo: cualquiera puede pedirla", "OSHA Recommended Practices"),
    ("Job hazard analysis: plan the task before the task", "Análisis de riesgos del trabajo: planee la tarea antes de la tarea", "OSHA Publication 3071"),
]

def build():
    s = [Kicker("Appendix B"), H1("Appendix B. Twenty-six toolbox talks to publish first")]
    s += [Lead("The database holds 54 talk records and none is published. This list is a six-month weekly programme for an electrical contractor, ordered so the highest-risk topics come first. Write each to the same shape: about 150 words, three pre-task questions, one 'check this today' line, and the sign-in. Have your qualified person approve the English and a fluent Spanish speaker approve the Spanish before anything is marked published. Standard references are starting points to verify, not legal citations.")]
    rows = [[str(i), en, es, ref] for i, (en, es, ref) in enumerate(TALKS, 1)]
    s += Tbl(["#", "Title (English)", "Título (Español)", "Rests on"], rows, widths=[0.42 * inch, 2.3 * inch, 2.5 * inch, CONTENT_W - 5.22 * inch])
    s += [H2("The shape of a talk that crews will actually sit through")]
    s += Bullets([
        "**Open with the job, not the rule.** 'Today we are pulling feeders in the mechanical room. Here is what can hurt you in there.'",
        "**One hazard, one habit.** A talk that covers three things teaches none.",
        "**Three pre-task questions** the foreman asks out loud, and records the answers to: what is energized, who has the lock, where is the nearest exit.",
        "**One check this today**: a single physical inspection the crew does before starting.",
        "**Sign-in on the phone**, in the language the worker chooses, tied to the report snapshot your system already makes immutable.",
        "**Rotate the speaker.** Letting a journeyman lead the talk once a month is the cheapest culture programme there is, and it makes for a good Wednesday post.",
    ])
    return s
