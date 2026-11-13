"""
CORRER TODO · NAT (integradora) — corre los 5 pasos en orden y arma salidas/reporte.html

  python correr_todo.py              # todo
  python correr_todo.py --desde 3    # desde el paso 3 (si ya corrieron 1 y 2)
  python correr_todo.py --solo-reporte
  python correr_todo.py --config config_otro.py   # otra configuración (ej. dos personas probando dos targets)

Si un paso falla, se detiene y dice cuál: arreglen ese paso (o config.py) y sigan con --desde N.
El reporte junta, en orden, la pregunta de cada rol, sus números, sus alertas y sus gráficos.
Es lo primero que abre el equipo después de cada corrida, y sirve de base para la presentación.
"""
import base64
import html
import subprocess
import sys
import time

from comun import C, GRAF, RAIZ, SAL, leer_resumen

PASOS = [("1", "1_limpiar.py", "1_limpiar"), ("2", "2_revisar_caso.py", "2_revisar_caso"),
         ("3", "3_variables.py", "3_variables"), ("4", "4_modelo.py", "4_modelo"),
         ("5", "5_priorizar_entregar.py", "5_priorizar")]


def correr(desde):
    for n, script, _ in PASOS:
        if int(n) < desde:
            continue
        t = time.time()
        extra = sys.argv[sys.argv.index("--config"):sys.argv.index("--config") + 2] if "--config" in sys.argv else []
        r = subprocess.run([sys.executable, str(RAIZ / script), *extra], cwd=RAIZ)
        if r.returncode != 0:
            sys.exit(f"\n  FALLÓ el paso {n} ({script}). Lean el mensaje de arriba, corrijan y sigan con:"
                     f"  python correr_todo.py --desde {n}\n")
        print(f"  -> paso {n} OK en {time.time() - t:.0f} s")


DIAGRAMA = """<svg viewBox="0 0 980 120" role="img" aria-label="Flujo de la plantilla" style="width:100%;max-width:980px">
<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
<path d="M0 0L10 5L0 10z" fill="#9a9993"/></marker></defs>
{cajas}
</svg>"""


def diagrama():
    pasos = [("datos/", "archivos del caso", ""), ("1 · Hellen", "limpiar", ""), ("2 · Nat", "revisar el caso", ""),
             ("3 · Kath", "variables", ""), ("4 · Sophia", "modelo", ""), ("5 · Liz", "priorizar", ""),
             ("submission", "la entrega", "main")]
    w, g, out = 120, 20, []
    for i, (a, b, k) in enumerate(pasos):
        x = 10 + i * (w + g)
        fill = "#2a78d61f" if k else "none"
        stroke = "#2a78d6" if k else "#9a9993"
        out.append(f'<rect x="{x}" y="30" width="{w}" height="56" rx="8" fill="{fill}" stroke="{stroke}" '
                   f'stroke-width="{2 if k else 1.2}"/><text x="{x + w / 2}" y="54" text-anchor="middle" '
                   f'font-weight="600" font-size="13">{a}</text><text x="{x + w / 2}" y="73" text-anchor="middle" '
                   f'font-size="11.5" fill="#52514e">{b}</text>')
        if i:
            out.append(f'<path d="M{x - g + 2} 58H{x - 2}" stroke="#9a9993" stroke-width="1.2" marker-end="url(#a)"/>')
    return DIAGRAMA.format(cajas="".join(out))


def reporte():
    partes = []
    for n, script, clave in PASOS:
        r = leer_resumen(clave)
        if not r:
            partes.append(f"<section><h2>Paso {n}</h2><p class='q'>Aún no se corrió <code>{script}</code>.</p></section>")
            continue
        nums = "".join(f"<div class='kpi'><b>{html.escape(str(v))}</b><span>{html.escape(k)}</span></div>"
                       for k, v in r["numeros"].items())
        expl = "".join(f"<li>{html.escape(x)}</li>" for x in r.get("explicacion", []))
        alert = "".join(f"<li>{html.escape(x)}</li>" for x in r.get("alertas", []))
        imgs = ""
        for gname in r.get("graficos", []):
            p = GRAF / gname
            if p.exists():
                b64 = base64.b64encode(p.read_bytes()).decode()
                imgs += f"<img src='data:image/png;base64,{b64}' alt='{html.escape(gname)}'>"
        partes.append(f"""<section><h2>{html.escape(r['titulo'])} <small>· {html.escape(r['rol'])}</small></h2>
            <p class='q'>{html.escape(r['pregunta'])}</p><div class='kpis'>{nums}</div>
            {'<ul>' + expl + '</ul>' if expl else ''}
            {'<div class="al"><b>Para revisar</b><ul>' + alert + '</ul></div>' if alert else
             '<p class="ok">Sin alertas.</p>'}<div class='imgs'>{imgs}</div></section>""")
    doc = f"""<!DOCTYPE html><html lang="es"><head><meta charset="utf-8"><title>Reporte · plantilla simple</title>
<style>body{{font-family:system-ui,-apple-system,Segoe UI,sans-serif;max-width:1040px;margin:24px auto;padding:0 16px;
color:#0b0b0b;background:#fcfcfb}} h1{{font-size:22px;margin-bottom:4px}} h2{{font-size:18px;margin:0 0 4px}}
h2 small{{color:#52514e;font-weight:400}} section{{border-top:1px solid #e6e5e0;padding:20px 0}}
.q{{color:#52514e;margin:0 0 12px}} .kpis{{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:10px}}
.kpi{{border:1px solid #e6e5e0;border-radius:8px;padding:8px 12px;min-width:120px}}
.kpi b{{display:block;font-size:18px}} .kpi span{{font-size:12px;color:#52514e}}
.al{{background:#e349481a;border-left:3px solid #e34948;padding:8px 12px;border-radius:4px;margin:8px 0}}
.ok{{color:#008300}} .imgs img{{max-width:100%;border:1px solid #e6e5e0;border-radius:8px;margin:8px 0}}
code{{background:#f0efec;padding:1px 4px;border-radius:4px}}</style></head><body>
<h1>Reporte de la plantilla simple</h1><p class="q">Corte {C.FECHA_CORTE} · horizonte {C.HORIZONTE_MESES} meses ·
entrena con el corte {C.CORTE_ANTERIOR} · generado {time.strftime('%Y-%m-%d %H:%M')}</p>{diagrama()}
{''.join(partes)}</body></html>"""
    destino = SAL / "reporte.html"
    destino.write_text(doc, encoding="utf-8")
    print(f"\n  Reporte: {destino}  (ábranlo en el navegador)")


if __name__ == "__main__":
    if "--solo-reporte" not in sys.argv:
        desde = int(sys.argv[sys.argv.index("--desde") + 1]) if "--desde" in sys.argv else 1
        correr(desde)
    reporte()
