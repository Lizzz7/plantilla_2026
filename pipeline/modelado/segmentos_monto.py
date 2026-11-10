"""
¿UNO O VARIOS MODELOS? y EL MONTO.

Por qué un equipo termina con "6 modelos": casi nunca es un ensamble de 6 algoritmos por gusto.
Es la DESCOMPOSICIÓN de la decisión en preguntas distintas, cada una con su modelo:
    caso 2025 (canal óptimo):  P(acepta | llamada), P(acepta | SMS), P(acepta | correo),
                               P(acepta | app), monto esperado, momento -> ~6 modelos
    caso factoring:            P(convierte | con lead), P(convierte | sin lead) (habilitar),
                               E[monto | convierte] -> 2 a 4 modelos
La data "se presta" cuando: (a) hay sub-poblaciones que se comportan distinto, (b) cada una
tiene suficientes positivos (≥200 aprox.), y (c) la decisión necesita varias cantidades
(probabilidad Y monto, o una probabilidad por canal).
Este módulo NO asume que separar es mejor: entrena global y separado, y gana el que mide más
en cada segmento. Si el global gana, se usa 1 modelo y se explica por qué.
"""
import numpy as np
import pandas as pd

import config as C
from pipeline.modelado import metricas as M
from pipeline.modelado.candidatos import fit_lgbm, oof
from pipeline.modelado.datos import pliegues


def comparar_segmentos(D, p_global, params=None):
    seg = C.SEGMENTO
    tr = D["train"]
    if not seg or seg not in tr:
        return None, p_global
    vs = [v for v in D["vars"] if v != seg]
    y = tr["target"].astype(int)
    s = tr[seg].astype("string").fillna("NA")
    filas, p_final = [], p_global.copy()
    for g in s.unique():
        m = (s == g).to_numpy(dtype=bool)
        yg = y[m]
        fila = dict(segmento=g, n=int(m.sum()), positivos=int(yg.sum()), tasa=float(yg.mean()),
                    gini_global=M.gini(yg, p_global[m]))
        if yg.sum() >= 30 and (len(yg) - yg.sum()) >= 30:
            Xg = tr.loc[m, vs].reset_index(drop=True)
            pg = oof(fit_lgbm, Xg, yg.reset_index(drop=True), pliegues(yg.reset_index(drop=True)), params=params)
            fila["gini_separado"] = M.gini(yg, pg)
            if fila["gini_separado"] > fila["gini_global"] + 0.005:
                fila["gana"] = "separado"
                p_final[m] = pg
            else:
                fila["gana"] = "global"
        else:
            fila.update(gini_separado=np.nan, gana="global (pocos positivos)")
        filas.append(fila)
        print(f"  segmento {g}: n={fila['n']:,} tasa={fila['tasa']:.2%}  global {fila['gini_global']:.4f} vs "
              f"separado {fila.get('gini_separado', float('nan')):.4f} -> {fila['gana']}")
    t = pd.DataFrame(filas)
    t["n_modelos_recomendado"] = 1 + int((t.gana == "separado").sum()) - int((t.gana == "separado").all())
    return t, p_final


def dos_partes(D, p_conv, params=None):
    """E[monto] = P(convierte) × E[monto | convierte].
    Parte 2: LightGBM sobre log1p(monto) SOLO en quienes convirtieron (OOF).
    Al volver de log se multiplica por el factor de Duan (smearing): exp(log) subestima la media.
    Se compara con una regresión directa sobre todos (Tweedie, que tolera muchos ceros)."""
    tr = D["train"]
    if "target_monto" not in tr:
        return None, None
    vs, y, m = D["vars"], tr["target"].astype(int), tr["target_monto"].astype(float)
    pos = (m > 0).values
    Xp = tr.loc[pos, vs].reset_index(drop=True)
    lp = np.log1p(m[pos].reset_index(drop=True))
    folds = list(pliegues((lp > lp.median()).astype(int)))
    pred_log = np.zeros(pos.sum())
    for a, b in folds:
        pred_log[b] = fit_lgbm(Xp.iloc[a], lp.iloc[a], Xp.iloc[b], params=params, monto=True)
    duan = float(np.mean(np.exp(lp - pred_log)))
    cond = np.full(len(tr), np.nan)
    cond[pos] = np.expm1(pred_log) * duan
    # para TODOS (incluidos no convertidos) se necesita E[monto|convierte]: modelo final sobre positivos
    _, mod = fit_lgbm(Xp, lp, tr[vs].iloc[:5], params=params, monto=True, devolver=True)
    cond_todos = np.expm1(mod.predict(tr[vs])) * duan
    cond_todos[pos] = cond[pos]          # para positivos usar la OOF (honesta)
    esperado = p_conv * cond_todos

    params_tw = {**(params or {}), "objective": "tweedie", "tweedie_variance_power": 1.5}
    directo = oof(fit_lgbm, tr[vs], m, pliegues(y), params=params_tw, monto=True)
    from scipy.stats import spearmanr
    r = dict(r2_dos_partes=M.r2(m, esperado), r2_directo_tweedie=M.r2(m, directo),
             spearman_dos_partes=float(spearmanr(m, esperado).statistic),
             spearman_directo=float(spearmanr(m, directo).statistic),
             r2_condicional_log=M.r2(lp, pred_log), factor_duan=duan,
             monto_real_total=float(m.sum()), monto_esperado_total=float(esperado.sum()))
    # R² en soles sobre TODOS: es lo que pediría un "R²" oficial. Spearman: ¿ordena bien los montos?
    # R² condicional (log, solo convertidos): ¿hay señal en el TAMAÑO? Si ~0, el monto solo aporta su promedio.
    r["gana"] = "dos_partes" if r["r2_dos_partes"] >= r["r2_directo_tweedie"] else "directo_tweedie"
    print(f"  monto: R² soles dos partes {r['r2_dos_partes']:.3f} vs directo {r['r2_directo_tweedie']:.3f} · "
          f"Spearman {r['spearman_dos_partes']:.3f} vs {r['spearman_directo']:.3f} · "
          f"R² condicional (log, convertidos) {r['r2_condicional_log']:.3f}")
    return r, mod
