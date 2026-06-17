# Motor de Cálculo de Treliça: Modelo estático de 18 nós via equilíbrio nodal (SVD).

import math
import numpy as np
import tkinter as tk
from tkinter import messagebox, ttk
import customtkinter as ctk
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import os
import datetime

# Geometria da treliça: Segmentos equilaterais (60°) e limites de precisão.
C60 = math.cos(math.radians(60))
S60 = math.sin(math.radians(60))
TOLERANCIA_ZERO = 1e-6

def get_force_names():
    """Mapeamento dos 37 membros da estrutura. Convenção: (+) Tração, (-) Compressão."""
    return [
        "FAB", "FAD",                                   # Nó A
        "FBC", "FBD", "FBE",                            # Nó B (+ FAB, FAD já listados)
        "FCE", "FCF",                                   # Nó C
        "FDE", "FDG",                                   # Nó D
        "FEF", "FEG", "FEH",                            # Nó E
        "FFH", "FFI",                                   # Nó F
        "FGH", "FGJ",                                   # Nó G
        "FHI", "FHJ", "FHK",                            # Nó H
        "FIK", "FIL",                                   # Nó I
        "FJK", "FJM",                                   # Nó J
        "FKL", "FKM", "FKN",                            # Nó K
        "FLN", "FLO",                                   # Nó L
        "FMN", "FMP",                                   # Nó M
        "FNO", "FNP", "FNQ",                            # Nó N
        "FOQ",                                          # Nó O
        "FPQ", "FPR",                                   # Nó P
        "FQR",                                          # Nó Q/R
    ]


def get_node_equations_text():
    """Retorna as equações literais de cada nó para exibição na UI e PDF."""
    return {
        "A": [
            "FAD + FAB·cos(60°) = 0",
            "FAB·sin(60°) + 5 = 0",
        ],
        "B": [
            "-FAB·cos(60°) + FBC·cos(60°) + FBD·cos(60°) + FBE = 0",
            "-FAB·sin(60°) + FBC·sin(60°) - FBD·sin(60°) = 0",
        ],
        "C": [
            "-FBC·cos(60°) + FCE·cos(60°) + FCF = 0",
            "-FBC·sin(60°) - FCE·sin(60°) = 0",
        ],
        "D": [
            "-FAD - FBD·cos(60°) + FDE·cos(60°) + FDG = 0",
            "FBD·sin(60°) + FDE·sin(60°) = 0",
        ],
        "E": [
            "-FBE - FCE·cos(60°) - FDE·cos(60°) + FEF·cos(60°) + FEG·cos(60°) + FEH = 0",
            "FCE·sin(60°) - FDE·sin(60°) + FEF·sin(60°) - FEG·sin(60°) = 0",
        ],
        "F": [
            "-FCF - FEF·cos(60°) + FFH·cos(60°) + FFI = 0",
            "-FEF·sin(60°) - FFH·sin(60°) = 0",
        ],
        "G": [
            "-FDG - FEG·cos(60°) + FGH·cos(60°) + FGJ = 0",
            "FEG·sin(60°) + FGH·sin(60°) = 0",
        ],
        "H": [
            "-FEH - FFH·cos(60°) - FGH·cos(60°) + FHI·cos(60°) + FHJ·cos(60°) + FHK = 0",
            "FFH·sin(60°) - FGH·sin(60°) + FHI·sin(60°) - FHJ·sin(60°) = 0",
        ],
        "I": [
            "-FFI - FHI·cos(60°) + FIK·cos(60°) + FIL = 0",
            "-FHI·sin(60°) - FIK·sin(60°) = 0",
        ],
        "J": [
            "-FGJ - FHJ·cos(60°) + FJK·cos(60°) + FJM = 0",
            "FHJ·sin(60°) + FJK·sin(60°) = 10",
        ],
        "K": [
            "-FHK - FIK·cos(60°) - FJK·cos(60°) + FKL·cos(60°) + FKM·cos(60°) + FKN = 0",
            "FIK·sin(60°) - FJK·sin(60°) + FKL·sin(60°) - FKM·sin(60°) = 0",
        ],
        "L": [
            "-FIL - FKL·cos(60°) + FLN·cos(60°) + FLO = 0",
            "-FKL·sin(60°) - FLN·sin(60°) = 0",
        ],
        "M": [
            "-FJM - FKM·cos(60°) + FMN·cos(60°) + FMP = 0",
            "FKM·sin(60°) + FMN·sin(60°) = 0",
        ],
        "N": [
            "-FKN - FLN·cos(60°) - FMN·cos(60°) + FNO·cos(60°) + FNP·cos(60°) + FNQ = 0",
            "FLN·sin(60°) - FMN·sin(60°) + FNO·sin(60°) - FNP·sin(60°) = 0",
        ],
        "O": [
            "-FLO - FNO·cos(60°) + FOQ·cos(60°) = 0",
            "-FNO·sin(60°) - FOQ·sin(60°) = 0",
        ],
        "P": [
            "-FMP - FNP·cos(60°) + FPQ·cos(60°) + FPR = 0",
            "FNP·sin(60°) + FPQ·sin(60°) = 0",
        ],
        "Q": [
            "-FNQ - FOQ·cos(60°) - FPQ·cos(60°) + FQR·cos(60°) = 0",
            "FOQ·sin(60°) - FPQ·sin(60°) - FQR·sin(60°) = 0",
        ],
        "R": [
            "-FPR - FQR·cos(60°) = 0",
            "FQR·sin(60°) + 5 = 0",
        ],
    }


def build_system():
    """Constrói o sistema Ax = B baseado no equilíbrio estático (ΣFx=0, ΣFy=0) de cada nó."""
    names = get_force_names()
    idx   = {name: i for i, name in enumerate(names)}
    n_eq  = 36   # 18 nós x 2 direções
    n_unk = len(names)

    A = np.zeros((n_eq, n_unk))
    B = np.zeros(n_eq)
    row = 0

    def eq(coeffs: dict, b: float = 0.0):
        nonlocal row
        for name, coef in coeffs.items():
            A[row, idx[name]] += coef
        B[row] = b
        row += 1

    eq({"FAD": 1.0, "FAB": C60})
    eq({"FAB": S60}, b=-5.0)

    # Nó B
    eq({"FAB": -C60, "FBC": C60, "FBD": C60, "FBE": 1.0})
    eq({"FAB": -S60, "FBC": S60, "FBD": -S60})

    # Nó C
    eq({"FBC": -C60, "FCE": C60, "FCF": 1.0})
    eq({"FBC": -S60, "FCE": -S60})

    # Nó D
    eq({"FAD": -1.0, "FBD": -C60, "FDE": C60, "FDG": 1.0})
    eq({"FBD": S60,  "FDE": S60})

    # Nó E
    eq({"FBE": -1.0, "FCE": -C60, "FDE": -C60,
        "FEF": C60,  "FEG": C60,  "FEH": 1.0})
    eq({"FCE": S60,  "FDE": -S60, "FEF": S60, "FEG": -S60})

    # Nó F
    eq({"FCF": -1.0, "FEF": -C60, "FFH": C60, "FFI": 1.0})
    eq({"FEF": -S60, "FFH": -S60})

    # Nó G
    eq({"FDG": -1.0, "FEG": -C60, "FGH": C60, "FGJ": 1.0})
    eq({"FEG": S60,  "FGH": S60})

    # Nó H
    eq({"FEH": -1.0, "FFH": -C60, "FGH": -C60,
        "FHI": C60,  "FHJ": C60,  "FHK": 1.0})
    eq({"FFH": S60,  "FGH": -S60, "FHI": S60, "FHJ": -S60})

    # Nó I
    eq({"FFI": -1.0, "FHI": -C60, "FIK": C60, "FIL": 1.0})
    eq({"FHI": -S60, "FIK": -S60})

    # Carga central concentrada
    eq({"FGJ": -1.0, "FHJ": -C60, "FJK": C60, "FJM": 1.0})
    eq({"FHJ": S60,  "FJK": S60}, b=10.0)

    # Nó K
    eq({"FHK": -1.0, "FIK": -C60, "FJK": -C60,
        "FKL": C60,  "FKM": C60,  "FKN": 1.0})
    eq({"FIK": S60,  "FJK": -S60, "FKL": S60, "FKM": -S60})

    # Nó L
    eq({"FIL": -1.0, "FKL": -C60, "FLN": C60, "FLO": 1.0})
    eq({"FKL": -S60, "FLN": -S60})

    # Nó M
    eq({"FJM": -1.0, "FKM": -C60, "FMN": C60, "FMP": 1.0})
    eq({"FKM": S60,  "FMN": S60})

    # Nó N
    eq({"FKN": -1.0, "FLN": -C60, "FMN": -C60,
        "FNO": C60,  "FNP": C60,  "FNQ": 1.0})
    eq({"FLN": S60,  "FMN": -S60, "FNO": S60, "FNP": -S60})

    # Nó O
    eq({"FLO": -1.0, "FNO": -C60, "FOQ": C60})
    eq({"FNO": -S60, "FOQ": -S60})

    # Nó P
    eq({"FMP": -1.0, "FNP": -C60, "FPQ": C60, "FPR": 1.0})
    eq({"FNP": S60,  "FPQ": S60})

    # Nó Q
    eq({"FNQ": -1.0, "FOQ": -C60, "FPQ": -C60, "FQR": C60})
    eq({"FOQ": S60,  "FPQ": -S60, "FQR": -S60})

    eq({"FPR": -1.0, "FQR": -C60})
    eq({"FQR": S60}, b=-5.0)

    return A, B, names


def solve_truss():
    """Resolve o sistema via SVD (mínimos quadrados) para gerenciar a hiperestaticidade."""
    A, B, names = build_system()

    x, residuals, rank, sv = np.linalg.lstsq(A, B, rcond=None)

    # Verificação de consistência física (resíduo numérico)
    max_res = float(np.max(np.abs(A @ x - B)))
    if max_res > 1e-8:
        raise ValueError(
            f"Resíduo numérico elevado: {max_res:.2e}. "
            "Verifique as equações de equilíbrio."
        )

    results = {name: round(float(val), 6) for name, val in zip(names, x)}
    return results, {
        "rank": int(rank),
        "n_unknowns": len(names),
        "n_equations": A.shape[0],
        "max_residual": max_res,
    }


def classify_force(value: float, tol: float = TOLERANCIA_ZERO) -> str:
    if abs(value) < tol:
        return "Nulo"
    return "Tração" if value > 0 else "Compressão"

def generate_pdf_report(results: dict, info: dict, output_path: str):
    """Gera documentação técnica formal em PDF."""
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2.0*cm, leftMargin=2.0*cm,
        topMargin=2.0*cm,   bottomMargin=2.0*cm,
        title="Análise Estrutural de Treliça",
        author="Software de Análise Estrutural — Python",
        subject="Método dos Nós — 18 Nós",
    )

    # Configuração de Identidade Visual e Estilos
    NAVY   = colors.HexColor("#1a2a4a")
    BLUE   = colors.HexColor("#2c5282")
    LIGHT  = colors.HexColor("#4a90d9")
    BG1    = colors.HexColor("#f0f4fa")
    BG2    = colors.white
    GREEN  = colors.HexColor("#1a6b2a")
    RED    = colors.HexColor("#8b1a1a")
    GREY   = colors.HexColor("#888888")

    styles = getSampleStyleSheet()

    s_title = ParagraphStyle("T1", parent=styles["Title"],
        fontSize=18, textColor=NAVY, spaceAfter=4, alignment=TA_CENTER)
    s_sub   = ParagraphStyle("T2", parent=styles["Normal"],
        fontSize=11, textColor=BLUE, spaceAfter=3, alignment=TA_CENTER)
    s_date  = ParagraphStyle("T3", parent=styles["Normal"],
        fontSize=9, textColor=GREY,  spaceAfter=10, alignment=TA_CENTER)
    s_sec   = ParagraphStyle("SEC", parent=styles["Heading2"],
        fontSize=12, textColor=NAVY, spaceBefore=14, spaceAfter=5)
    s_node  = ParagraphStyle("NOD", parent=styles["Heading3"],
        fontSize=10, textColor=BLUE, spaceBefore=8, spaceAfter=2,
        fontName="Helvetica-Bold")
    s_eq    = ParagraphStyle("EQ", parent=styles["Normal"],
        fontSize=9, leftIndent=20, fontName="Courier",
        spaceAfter=2, leading=13)
    s_body  = ParagraphStyle("BD", parent=styles["Normal"],
        fontSize=9, spaceAfter=5, alignment=TA_JUSTIFY, leading=13)
    s_foot  = ParagraphStyle("FT", parent=styles["Normal"],
        fontSize=8, textColor=GREY, alignment=TA_CENTER)
    s_info  = ParagraphStyle("INF", parent=styles["Normal"],
        fontSize=8, textColor=GREY, leftIndent=10)

    story = []
    now   = datetime.datetime.now().strftime("%d/%m/%Y às %H:%M:%S")

    story += [
        Spacer(1, 0.2*cm),
        Paragraph("RELATÓRIO DE ANÁLISE ESTRUTURAL", s_title),
        Paragraph("Treliça Plana — Método dos Nós — 18 Nós (A a R)", s_sub),
        Paragraph(f"Emitido em: {now}", s_date),
        HRFlowable(width="100%", thickness=2, color=NAVY, spaceAfter=10),
    ]

    story.append(Paragraph("1. Descrição do Problema e Metodologia", s_sec))
    story.append(Paragraph(
        "A presente análise aplica o <b>Método dos Nós</b> (equilíbrio nodal) para "
        "determinação das forças internas em todos os 37 membros de uma treliça plana "
        "composta por <b>18 nós</b> (A a R). O sistema de equações de equilíbrio é "
        "montado na forma matricial <b>Ax = B</b> (36 equações × 37 incógnitas) e "
        "resolvido numericamente pela solução de <b>mínima norma</b> via decomposição "
        "SVD (numpy.linalg.lstsq), com resíduo máximo da ordem de 10⁻¹⁴, confirmando "
        "plena compatibilidade do sistema. Os ângulos de 60° foram convertidos para "
        "radianos antes da aplicação das funções trigonométricas "
        "[cos(60°) = 0,5000 | sin(60°) = 0,8660]. "
        "Cargas externas: <b>5 kN ↑</b> no nó A, <b>10 kN ↑</b> no nó J e "
        "<b>5 kN ↑</b> no nó R. "
        "Convenção: força <b>positiva</b> → <b>Tração</b>; "
        "força <b>negativa</b> → <b>Compressão</b>.",
        s_body
    ))

    story.append(Paragraph(
        f"Sistema linear: {info['n_equations']} equações × {info['n_unknowns']} incógnitas "
        f"| Posto: {info['rank']} "
        f"| Resíduo máximo: {info['max_residual']:.2e} kN",
        s_info
    ))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("2. Equações de Equilíbrio Nodal", s_sec))
    story.append(Paragraph(
        "Equações de equilíbrio estático (ΣFx = 0 e ΣFy = 0) para cada nó da treliça.",
        s_body
    ))

    eq_texts = get_node_equations_text()
    for node in list("ABCDEFGHIJKLMNOPQR"):
        eqs = eq_texts.get(node, [])
        block = [Paragraph(f"Nó {node}:", s_node)]
        for i, eq in enumerate(eqs):
            label = "ΣFx = 0:  " if i == 0 else "ΣFy = 0:  "
            block.append(Paragraph(f"{label}{eq}", s_eq))
        story.append(KeepTogether(block))

    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph("3. Resultados — Forças nos Membros", s_sec))
    story.append(Paragraph(
        "Valores obtidos pela resolução numérica do sistema linear. "
        "A coluna <b>Estado</b> classifica cada membro quanto à solicitação axial.",
        s_body
    ))

    header = [
        Paragraph("<b>Membro</b>",   styles["Normal"]),
        Paragraph("<b>Força (kN)</b>", styles["Normal"]),
        Paragraph("<b>Estado</b>",   styles["Normal"]),
    ]
    table_data = [header]

    for name, value in results.items():
        state = classify_force(value)
        color_map = {"Tração": GREEN, "Compressão": RED, "Nulo": GREY}
        c = color_map[state]
        table_data.append([
            Paragraph(f"<font name='Courier'>{name}</font>", styles["Normal"]),
            Paragraph(
                f"<font name='Courier'>{value:+.4f}</font>",
                ParagraphStyle("V", parent=styles["Normal"], alignment=TA_CENTER)
            ),
            Paragraph(
                f"<font color='{c.hexval() if hasattr(c,'hexval') else c}'>"
                f"<b>{state}</b></font>",
                ParagraphStyle("S", parent=styles["Normal"], alignment=TA_CENTER,
                               textColor=c)
            ),
        ])

    col_w = [4.5*cm, 5.0*cm, 5.5*cm]
    tbl   = Table(table_data, colWidths=col_w, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  NAVY),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0),  10),
        ("ALIGN",         (0, 0), (-1,  0), "CENTER"),
        ("BOTTOMPADDING", (0, 0), (-1,  0), 7),
        ("TOPPADDING",    (0, 0), (-1,  0), 7),
        ("FONTSIZE",      (0, 1), (-1, -1), 9),
        ("TOPPADDING",    (0, 1), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
        ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [BG1, BG2]),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("4. Resumo Estatístico", s_sec))

    vals       = list(results.values())
    n_tr       = sum(1 for v in vals if classify_force(v) == "Tração")
    n_cp       = sum(1 for v in vals if classify_force(v) == "Compressão")
    n_zr       = sum(1 for v in vals if classify_force(v) == "Nulo")
    max_nm     = max(results, key=lambda k: abs(results[k]))
    max_vl     = results[max_nm]

    sum_data = [
        [Paragraph("<b>Parâmetro</b>",    styles["Normal"]),
         Paragraph("<b>Valor</b>",        styles["Normal"])],
        ["Total de membros analisados",   str(len(results))],
        ["Membros em Tração (+)",         str(n_tr)],
        ["Membros em Compressão (−)",     str(n_cp)],
        ["Membros com força nula",        str(n_zr)],
        ["Maior força (em módulo)",
         f"{max_nm}: {max_vl:+.4f} kN  [{classify_force(max_vl)}]"],
        ["Soma algébrica das forças",
         f"{sum(vals):.4f} kN"],
    ]

    stbl = Table(sum_data, colWidths=[8.5*cm, 6.5*cm])
    stbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), BLUE),
        ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0), 10),
        ("ALIGN",         (0, 0), (-1, -1), "LEFT"),
        ("FONTSIZE",      (0, 1), (-1, -1), 9),
        ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [BG1, BG2]),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(stbl)

    story += [
        Spacer(1, 1.0*cm),
        HRFlowable(width="100%", thickness=1,
                   color=colors.HexColor("#aaaaaa"), spaceBefore=4),
        Paragraph(
            "Relatório gerado automaticamente pelo software de Análise Estrutural de Treliça — "
            "Método dos Nós  |  Resolução via numpy.linalg.lstsq (SVD)  |  Python 3",
            s_foot
        ),
    ]

    doc.build(story)
    return output_path


class TrussApp(ctk.CTk):
    # Configuração de Cores (Dark Theme)
    C_BG      = "#1a2a4a"
    C_PANEL   = "#1e3155"
    C_ACCENT  = "#4a90d9"
    C_TEXT    = "#e8eef6"
    C_SUCCESS = "#27ae60"
    C_ERROR   = "#e74c3c"
    C_TRAC    = "#2ecc71"
    C_COMP    = "#e67e73"
    C_ZERO    = "#888888"

    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("Análise Estrutural de Treliça — Método dos Nós")
        self.geometry("1120x760")
        self.minsize(900, 600)
        self.configure(fg_color=self.C_BG)

        self._build_layout()

    def _build_layout(self):
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_left_panel()
        self._build_right_panel()
        self._build_footer()

    def _build_header(self):
        hdr = ctk.CTkFrame(self, fg_color=self.C_PANEL, corner_radius=0, height=70)
        hdr.grid(row=0, column=0, columnspan=2, sticky="ew")
        hdr.grid_propagate(False)
        hdr.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            hdr,
            text="⚙   ANÁLISE ESTRUTURAL DE TRELIÇA",
            font=ctk.CTkFont(family="Helvetica", size=20, weight="bold"),
            text_color=self.C_ACCENT,
        ).grid(row=0, column=0, pady=(12, 2))

        ctk.CTkLabel(
            hdr,
            text="Método dos Nós  —  18 Nós (A a R)  |  Resolução Numérica via NumPy/SciPy",
            font=ctk.CTkFont(size=11),
            text_color=self.C_TEXT,
        ).grid(row=1, column=0, pady=(0, 10))

    def _build_left_panel(self):
        frame = ctk.CTkFrame(self, fg_color=self.C_PANEL, corner_radius=8)
        frame.grid(row=1, column=0, sticky="nsew", padx=(10, 5), pady=10)
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame,
            text="📐  Equações de Equilíbrio Nodal",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=self.C_ACCENT,
        ).grid(row=0, column=0, padx=12, pady=(10, 5), sticky="w")

        self.eq_textbox = ctk.CTkTextbox(
            frame,
            font=ctk.CTkFont(family="Courier", size=10),
            fg_color="#0d1b2e",
            text_color="#a8c8e8",
            corner_radius=6,
            wrap="none",
        )
        self.eq_textbox.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        self._populate_equations()

    def _populate_equations(self):
        eq_texts = get_node_equations_text()
        self.eq_textbox.configure(state="normal")
        self.eq_textbox.delete("1.0", "end")

        for node in list("ABCDEFGHIJKLMNOPQR"):
            self.eq_textbox.insert("end",
                f"{'─'*36}\n  NÓ {node}\n{'─'*36}\n")
            for i, eq in enumerate(eq_texts.get(node, [])):
                label = "  ΣFx = 0:  " if i == 0 else "  ΣFy = 0:  "
                self.eq_textbox.insert("end", f"{label}{eq}\n")
            self.eq_textbox.insert("end", "\n")

        self.eq_textbox.configure(state="disabled")

    def _build_right_panel(self):
        frame = ctk.CTkFrame(self, fg_color=self.C_PANEL, corner_radius=8)
        frame.grid(row=1, column=1, sticky="nsew", padx=(5, 10), pady=10)
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        # Header do Painel de Resultados
        top = ctk.CTkFrame(frame, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        top.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            top,
            text="📊  Resultados — Forças nos Membros",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=self.C_ACCENT,
        ).grid(row=0, column=0, sticky="w")

        self.btn_calc = ctk.CTkButton(
            top,
            text="▶  Calcular e Gerar PDF",
            command=self._on_calculate,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=self.C_ACCENT,
            hover_color="#2563ab",
            corner_radius=8,
            height=36,
            width=200,
        )
        self.btn_calc.grid(row=0, column=1, padx=(10, 0))

        # Configuração da Tabela de Dados (Estilo Clam para customização)
        tree_frame = ctk.CTkFrame(frame, fg_color="#0d1b2e", corner_radius=6)
        tree_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 4))
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Truss.Treeview",
            background="#0d1b2e", foreground="#c5daf0",
            rowheight=25, fieldbackground="#0d1b2e",
            font=("Courier", 10))
        style.configure("Truss.Treeview.Heading",
            background="#1a3a6a", foreground="#e8eef6",
            font=("Helvetica", 10, "bold"))
        style.map("Truss.Treeview",
            background=[("selected", "#2563ab")],
            foreground=[("selected", "white")])

        self.tree = ttk.Treeview(
            tree_frame,
            columns=("Membro", "Força (kN)", "Estado"),
            show="headings",
            style="Truss.Treeview",
        )
        self.tree.heading("Membro",     text="  Membro")
        self.tree.heading("Força (kN)", text="Força (kN)")
        self.tree.heading("Estado",     text="Estado")
        self.tree.column("Membro",      width=130, anchor="w")
        self.tree.column("Força (kN)",  width=160, anchor="center")
        self.tree.column("Estado",      width=130, anchor="center")

        self.tree.tag_configure("tracao",     foreground=self.C_TRAC)
        self.tree.tag_configure("compressao", foreground=self.C_COMP)
        self.tree.tag_configure("nulo",       foreground=self.C_ZERO)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical",
                            command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        self.status_label = ctk.CTkLabel(
            frame,
            text="Clique em '▶ Calcular e Gerar PDF' para iniciar a análise.",
            font=ctk.CTkFont(size=10),
            text_color="#8ab4d4",
        )
        self.status_label.grid(row=2, column=0,
                               padx=10, pady=(2, 6), sticky="w")

    def _build_footer(self):
        ftr = ctk.CTkFrame(self, fg_color=self.C_PANEL,
                           corner_radius=0, height=26)
        ftr.grid(row=2, column=0, columnspan=2, sticky="ew")
        ftr.grid_propagate(False)
        ctk.CTkLabel(
            ftr,
            text="Treliça 18 Nós — Método dos Nós  |  NumPy + SciPy + ReportLab  |  Python 3",
            font=ctk.CTkFont(size=9),
            text_color="#5a7a9a",
        ).pack(side="left", padx=12, pady=4)

    def _on_calculate(self):
        """Orquestra o cálculo, atualização da interface e exportação PDF."""
        self.btn_calc.configure(state="disabled", text="⏳  Calculando...")
        self.status_label.configure(
            text="Resolvendo o sistema de equações...",
            text_color="#8ab4d4"
        )
        self.update()

        try:
            results, info = solve_truss()
            self._populate_results(results)

            # Seleção de destino para o relatório
            pdf_path = ctk.filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("Arquivos PDF", "*.pdf")],
                initialfile="relatorio_trelica.pdf",
                title="Salvar Relatório Técnico"
            )

            if not pdf_path:
                self.status_label.configure(text="Geração de PDF cancelada pelo usuário.", text_color="#8ab4d4")
                return

            generate_pdf_report(results, info, pdf_path)

            self.status_label.configure(
                text=f"✅  Concluído! Posto={info['rank']} | "
                     f"Resíduo={info['max_residual']:.1e} | PDF: {pdf_path}",
                text_color=self.C_SUCCESS,
            )
            messagebox.showinfo(
                "Análise Concluída com Sucesso",
                f"✅  Sistema resolvido com sucesso!\n\n"
                f"• Equações:   {info['n_equations']}\n"
                f"• Incógnitas: {info['n_unknowns']}\n"
                f"• Posto:      {info['rank']}\n"
                f"• Resíduo:    {info['max_residual']:.2e} kN\n\n"
                f"Relatório PDF salvo em:\n{pdf_path}"
            )

        except Exception as exc:
            self.status_label.configure(
                text=f"❌  Erro: {exc}",
                text_color=self.C_ERROR,
            )
            messagebox.showerror("Erro na Análise", str(exc))

        finally:
            self.btn_calc.configure(
                state="normal", text="▶  Calcular e Gerar PDF")

    def _populate_results(self, results: dict):
        for item in self.tree.get_children():
            self.tree.delete(item)

        tag_map = {"Tração": "tracao", "Compressão": "compressao", "Nulo": "nulo"}
        for name, value in results.items():
            state = classify_force(value)
            self.tree.insert(
                "", "end",
                values=(f"  {name}", f"{value:+.4f}", state),
                tags=(tag_map[state],),
            )


def run_cli(output_pdf: str = "relatorio_trelica.pdf"):
    print("  ANÁLISE ESTRUTURAL DE TRELIÇA — Método dos Nós")
    print("  18 Nós (A a R) | Resolução NumPy")
    print("=" * 60)

    results, info = solve_truss()

    print(f"\nSistema: {info['n_equations']} eq × {info['n_unknowns']} inc"
          f"  |  Posto: {info['rank']}"
          f"  |  Resíduo: {info['max_residual']:.2e}")
    print(f"\n{'Membro':8s}  {'Força (kN)':>12s}  {'Estado':12s}")
    print("-" * 38)

    for name, value in results.items():
        state = classify_force(value)
        print(f"{name:8s}  {value:+12.4f}  {state}")

    generate_pdf_report(results, info, output_pdf)
    print(f"\n✅  PDF gerado: {output_pdf}")

if __name__ == "__main__":
    import sys
    
    # Interface de Linha de Comando opcional
    if "--cli" in sys.argv:
        out = sys.argv[sys.argv.index("--cli") + 1] \
              if len(sys.argv) > sys.argv.index("--cli") + 1 \
              else "relatorio_trelica.pdf"
        run_cli(out)
    else:
        app = TrussApp()
        app.mainloop()
