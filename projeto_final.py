# Motor de Cálculo de Treliça: Resolução estática de 13 nós com output fracionário.

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
from fractions import Fraction
import datetime

# Geometria e precisão: Ângulos de 60° (equiláteros) e limite de truncamento.
C60 = math.cos(math.radians(60))
S60 = math.sin(math.radians(60))
TOLERANCIA_ZERO = 1e-6

def format_fraction(value: float, tol: float = TOLERANCIA_ZERO) -> str:
    """Simplifica resultados numéricos para frações de engenharia legíveis."""
    if abs(value) < tol:
        return "0"
    
    # Limita o denominador para manter as frações limpas (ex: evita 142857/1000000 para 1/7)
    frac = Fraction(value).limit_denominator(10000)
    
    # Adiciona o sinal explícito para tração/compressão
    sign = "+" if frac > 0 else ""
    return f"{sign}{frac.numerator}/{frac.denominator}"

def get_force_names():
    """Mapeamento das 23 incógnitas axiais da estrutura."""
    return [
        "FAB", "FAC", "FBC", "FBD", "FCD", "FCE", "FDE", "FDF",
        "FEF", "FEG", "FFG", "FFH", "FGH", "FGI", "FHI", "FHJ",
        "FIJ", "FIK", "FJK", "FJL", "FKL", "FKM", "FLM"
    ]

def get_node_equations_text():
    """Definições literais das equações de equilíbrio para exibição no relatório/UI."""
    return {
        "A": [
            "FAC + FAB·cos(60°) = 0",
            "FAB·sin(60°) + 5 = 0"
        ],
        "B": [
            "-FAB·cos(60°) + FBC·cos(60°) + FBD = 0",
            "-FAB·sin(60°) - FBC·sin(60°) = 0"
        ],
        "C": [
            "-FAC + FCE - FBC·cos(60°) + FCD·cos(60°) = 0",
            "FBC·sin(60°) + FCD·sin(60°) = 0"
        ],
        "D": [
            "-FBD - FCD·cos(60°) + FDE·cos(60°) + FDF = 0",
            "-FCD·sin(60°) - FDE·sin(60°) = 0"
        ],
        "E": [
            "-FCE - FDE·cos(60°) + FEF·cos(60°) + FEG = 0",
            "FDE·sin(60°) + FEF·sin(60°) = 0"
        ],
        "F": [
            "-FDF - FEF·cos(60°) + FFG·cos(60°) + FFH = 0",
            "-FEF·sin(60°) - FFG·sin(60°) = 0"
        ],
        "G": [
            "-FEG - FFG·cos(60°) + FGH·cos(60°) + FGI = 0",
            "FFG·sin(60°) + FGH·sin(60°) - 10 = 0"
        ],
        "H": [
            "-FFH - FGH·cos(60°) + FHI·cos(60°) + FHJ = 0",
            "-FGH·sin(60°) - FHI·sin(60°) = 0"
        ],
        "I": [
            "-FGI - FHI·cos(60°) + FIJ·cos(60°) + FIK = 0",
            "FHI·sin(60°) + FIJ·sin(60°) = 0"
        ],
        "J": [
            "-FHJ - FIJ·cos(60°) + FJK·cos(60°) + FJL = 0",
            "-FIJ·sin(60°) - FJK·sin(60°) = 0"
        ],
        "K": [
            "-FIK - FJK·cos(60°) + FKL·cos(60°) + FKM = 0",
            "FJK·sin(60°) + FKL·sin(60°) = 0"
        ],
        "L": [
            "-FJL - FKL·cos(60°) + FLM·cos(60°) = 0",
            "-FKL·sin(60°) - FLM·sin(60°) = 0"
        ],
        "M": [
            "-FKM - FLM·cos(60°) = 0",
            "FLM·sin(60°) + 5 = 0"
        ],
    }

def build_system():
    """Monta a matriz de rigidez estática A e o vetor de forças externas B (Ax = B)."""
    names = get_force_names()
    idx   = {name: i for i, name in enumerate(names)}
    n_eq  = 26   # 13 nós x 2 direções (x, y)
    n_unk = len(names)

    A = np.zeros((n_eq, n_unk))
    B = np.zeros(n_eq)
    row = 0

    def eq(coeffs: dict, b: float = 0.0):  # Helper para popular as linhas da matriz
        nonlocal row
        for name, coef in coeffs.items():
            A[row, idx[name]] += coef
        B[row] = b
        row += 1

    eq({"FAC": 1.0, "FAB": C60})
    eq({"FAB": S60}, b=-5.0)

    eq({"FAB": -C60, "FBC": C60, "FBD": 1.0})
    eq({"FAB": -S60, "FBC": -S60})

    eq({"FAC": -1.0, "FCE": 1.0, "FBC": -C60, "FCD": C60})
    eq({"FBC": S60, "FCD": S60})

    eq({"FBD": -1.0, "FCD": -C60, "FDE": C60, "FDF": 1.0})
    eq({"FCD": -S60, "FDE": -S60})

    eq({"FCE": -1.0, "FDE": -C60, "FEF": C60, "FEG": 1.0})
    eq({"FDE": S60, "FEF": S60})

    eq({"FDF": -1.0, "FEF": -C60, "FFG": C60, "FFH": 1.0})
    eq({"FEF": -S60, "FFG": -S60})

    eq({"FEG": -1.0, "FFG": -C60, "FGH": C60, "FGI": 1.0})
    eq({"FFG": S60, "FGH": S60}, b=10.0)

    eq({"FFH": -1.0, "FGH": -C60, "FHI": C60, "FHJ": 1.0})
    eq({"FGH": -S60, "FHI": -S60})

    eq({"FGI": -1.0, "FHI": -C60, "FIJ": C60, "FIK": 1.0})
    eq({"FHI": S60, "FIJ": S60})

    eq({"FHJ": -1.0, "FIJ": -C60, "FJK": C60, "FJL": 1.0})
    eq({"FIJ": -S60, "FJK": -S60})

    eq({"FIK": -1.0, "FJK": -C60, "FKL": C60, "FKM": 1.0})
    eq({"FJK": S60, "FKL": S60})

    eq({"FJL": -1.0, "FKL": -C60, "FLM": C60})
    eq({"FKL": -S60, "FLM": -S60})

    eq({"FKM": -1.0, "FLM": -C60})
    eq({"FLM": S60}, b=-5.0)

    return A, B, names

def solve_truss():
    """Resolve via Mínimos Quadrados (SVD) para gerenciar hiperestaticidade/estabilidade."""
    A, B, names = build_system()

    x, residuals, rank, sv = np.linalg.lstsq(A, B, rcond=None)

    max_res = float(np.max(np.abs(A @ x - B))) # Check de consistência física
    if max_res > 1e-8:
        raise ValueError(
            f"Resíduo numérico elevado: {max_res:.2e}. "
            "A estrutura está geometricamente instável ou as cargas são inconsistentes."
        )

    results = {name: round(float(val), 6) for name, val in zip(names, x)}
    return results, {
        "rank": int(rank),
        "n_unknowns": len(names),
        "n_equations": A.shape[0],
        "max_residual": max_res,
    }

def classify_force(value: float, tol: float = TOLERANCIA_ZERO) -> str:
    """Define se a força é Tração, Compressão ou Nula."""
    if abs(value) < tol:
        return "Nulo"
    return "Tração" if value > 0 else "Compressão"

def generate_pdf_report(results: dict, info: dict, output_path: str):
    """Gera o relatório técnico em PDF via ReportLab."""
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2.0*cm, leftMargin=2.0*cm,
        topMargin=2.0*cm,   bottomMargin=2.0*cm,
        title="Análise Estrutural de Treliça",
        author="Software de Análise Estrutural — Python",
        subject="Método dos Nós — 13 Nós",
    )

    # Identidade visual do relatório
    NAVY   = colors.HexColor("#1a2a4a")
    BLUE   = colors.HexColor("#2c5282")
    BG1    = colors.HexColor("#f0f4fa")
    BG2    = colors.white
    GREEN  = colors.HexColor("#1a6b2a")
    RED    = colors.HexColor("#8b1a1a")
    GREY   = colors.HexColor("#888888")

    styles = getSampleStyleSheet()

    s_title = ParagraphStyle("T1", parent=styles["Title"], fontSize=18, textColor=NAVY, spaceAfter=4, alignment=TA_CENTER)
    s_sub   = ParagraphStyle("T2", parent=styles["Normal"], fontSize=11, textColor=BLUE, spaceAfter=3, alignment=TA_CENTER)
    s_date  = ParagraphStyle("T3", parent=styles["Normal"], fontSize=9, textColor=GREY, spaceAfter=10, alignment=TA_CENTER)
    s_sec   = ParagraphStyle("SEC", parent=styles["Heading2"], fontSize=12, textColor=NAVY, spaceBefore=14, spaceAfter=5)
    s_node  = ParagraphStyle("NOD", parent=styles["Heading3"], fontSize=10, textColor=BLUE, spaceBefore=8, spaceAfter=2, fontName="Helvetica-Bold")
    s_eq    = ParagraphStyle("EQ", parent=styles["Normal"], fontSize=9, leftIndent=20, fontName="Courier", spaceAfter=2, leading=13)
    s_body  = ParagraphStyle("BD", parent=styles["Normal"], fontSize=9, spaceAfter=5, alignment=TA_JUSTIFY, leading=13)
    s_foot  = ParagraphStyle("FT", parent=styles["Normal"], fontSize=8, textColor=GREY, alignment=TA_CENTER)
    s_info  = ParagraphStyle("INF", parent=styles["Normal"], fontSize=8, textColor=GREY, leftIndent=10)

    story = []
    now   = datetime.datetime.now().strftime("%d/%m/%Y às %H:%M:%S")

    story += [
        Spacer(1, 0.2*cm),
        Paragraph("RELATÓRIO DE ANÁLISE ESTRUTURAL", s_title),
        Paragraph("Treliça Plana — Método dos Nós — 13 Nós (A a M)", s_sub),
        Paragraph(f"Emitido em: {now}", s_date),
        HRFlowable(width="100%", thickness=2, color=NAVY, spaceAfter=10),
    ]

    story.append(Paragraph("1. Descrição do Problema e Metodologia", s_sec))
    story.append(Paragraph(
        "A presente análise aplica o <b>Método dos Nós</b> (equilíbrio nodal) para "
        "determinação das forças internas em todos os 23 membros de uma treliça plana "
        "composta por <b>13 nós</b> (A a M). O sistema de equações de equilíbrio é "
        "montado na forma matricial <b>Ax = B</b> (26 equações × 23 incógnitas) e "
        "resolvido numericamente, apresentando resultados perfeitamente fracionários. "
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
    eq_texts = get_node_equations_text() # Renderização das equações de equilíbrio
    for node in list("ABCDEFGHIJKLM"):
        eqs = eq_texts.get(node, [])
        block = [Paragraph(f"Nó {node}:", s_node)]
        for i, eq in enumerate(eqs):
            label = "ΣFx = 0:  " if i == 0 else "ΣFy = 0:  "
            block.append(Paragraph(f"{label}{eq}", s_eq))
        story.append(KeepTogether(block))

    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph("3. Resultados — Forças nos Membros", s_sec))
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
                f"<font name='Courier'>{format_fraction(value)}</font>",
                ParagraphStyle("V", parent=styles["Normal"], alignment=TA_CENTER)
            ),
            Paragraph(
                f"<font color='{c.hexval() if hasattr(c,'hexval') else c}'>"
                f"<b>{state}</b></font>",
                ParagraphStyle("S", parent=styles["Normal"], alignment=TA_CENTER, textColor=c)
            ),
        ])

    col_w = [4.5*cm, 5.0*cm, 5.5*cm]
    tbl   = Table(table_data, colWidths=col_w, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  NAVY),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("ALIGN",         (0, 0), (-1,  0), "CENTER"),
        ("BOTTOMPADDING", (0, 0), (-1,  0), 7),
        ("TOPPADDING",    (0, 0), (-1,  0), 7),
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

    sum_data = [ # Tabela de resumo executivo
        [Paragraph("<b>Parâmetro</b>",    styles["Normal"]), Paragraph("<b>Valor</b>",        styles["Normal"])],
        ["Total de membros analisados",   str(len(results))],
        ["Membros em Tração (+)",         str(n_tr)],
        ["Membros em Compressão (−)",     str(n_cp)],
        ["Membros com força nula",        str(n_zr)],
        ["Maior força (em módulo)",       f"{max_nm}: {format_fraction(max_vl)} kN  [{classify_force(max_vl)}]"],
    ]

    stbl = Table(sum_data, colWidths=[8.5*cm, 6.5*cm])
    stbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), BLUE),
        ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [BG1, BG2]),
    ]))
    story.append(stbl)

    story += [
        Spacer(1, 1.0*cm),
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#aaaaaa"), spaceBefore=4),
        Paragraph("Relatório gerado automaticamente | Resolução via numpy | Formato Fracionário", s_foot),
    ]

    doc.build(story)
    return output_path


class TrussApp(ctk.CTk):
    # Paleta de cores da interface (Dark Theme)
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
            hdr, text="⚙  ANÁLISE ESTRUTURAL DE TRELIÇA",
            font=ctk.CTkFont(family="Helvetica", size=20, weight="bold"),
            text_color=self.C_ACCENT,
        ).grid(row=0, column=0, pady=(12, 2))

        ctk.CTkLabel(
            hdr, text="Método dos Nós  —  13 Nós (A a M)  |  Resultados em Fração",
            font=ctk.CTkFont(size=11), text_color=self.C_TEXT,
        ).grid(row=1, column=0, pady=(0, 10))

    def _build_left_panel(self):
        frame = ctk.CTkFrame(self, fg_color=self.C_PANEL, corner_radius=8)
        frame.grid(row=1, column=0, sticky="nsew", padx=(10, 5), pady=10)
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame, text="📐  Equações de Equilíbrio Nodal",
            font=ctk.CTkFont(size=13, weight="bold"), text_color=self.C_ACCENT,
        ).grid(row=0, column=0, padx=12, pady=(10, 5), sticky="w")

        self.eq_textbox = ctk.CTkTextbox( # Área de visualização das equações literais
            frame, font=ctk.CTkFont(family="Courier", size=10),
            fg_color="#0d1b2e", text_color="#a8c8e8", corner_radius=6, wrap="none",
        )
        self.eq_textbox.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        self._populate_equations()

    def _populate_equations(self):
        eq_texts = get_node_equations_text()
        self.eq_textbox.configure(state="normal")
        self.eq_textbox.delete("1.0", "end")

        for node in list("ABCDEFGHIJKLM"):
            self.eq_textbox.insert("end", f"{'─'*36}\n  NÓ {node}\n{'─'*36}\n")
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

        top = ctk.CTkFrame(frame, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        top.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            top, text="📊  Resultados — Forças nos Membros",
            font=ctk.CTkFont(size=13, weight="bold"), text_color=self.C_ACCENT,
        ).grid(row=0, column=0, sticky="w")

        self.btn_calc = ctk.CTkButton(
            top, text="▶  Calcular e Gerar PDF", command=self._on_calculate,
            font=ctk.CTkFont(size=12, weight="bold"), fg_color=self.C_ACCENT,
            hover_color="#2563ab", corner_radius=8, height=36, width=200,
        )
        self.btn_calc.grid(row=0, column=1, padx=(10, 0))

        tree_frame = ctk.CTkFrame(frame, fg_color="#0d1b2e", corner_radius=6) # Frame da tabela
        tree_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 4))
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Truss.Treeview", background="#0d1b2e", foreground="#c5daf0", rowheight=25, fieldbackground="#0d1b2e", font=("Courier", 10))
        style.configure("Truss.Treeview.Heading", background="#1a3a6a", foreground="#e8eef6", font=("Helvetica", 10, "bold"))
        style.map("Truss.Treeview", background=[("selected", "#2563ab")], foreground=[("selected", "white")])

        self.tree = ttk.Treeview(tree_frame, columns=("Membro", "Força (kN)", "Estado"), show="headings", style="Truss.Treeview")
        self.tree.heading("Membro",     text="  Membro")
        self.tree.heading("Força (kN)", text="Força (kN) Fracionária")
        self.tree.heading("Estado",     text="Estado")
        self.tree.column("Membro",      width=130, anchor="w")
        self.tree.column("Força (kN)",  width=160, anchor="center")
        self.tree.column("Estado",      width=130, anchor="center")

        self.tree.tag_configure("tracao",     foreground=self.C_TRAC)
        self.tree.tag_configure("compressao", foreground=self.C_COMP)
        self.tree.tag_configure("nulo",       foreground=self.C_ZERO)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        self.status_label = ctk.CTkLabel(frame, text="Clique em '▶ Calcular e Gerar PDF' para iniciar.", font=ctk.CTkFont(size=10), text_color="#8ab4d4")
        self.status_label.grid(row=2, column=0, padx=10, pady=(2, 6), sticky="w")

    def _build_footer(self):
        ftr = ctk.CTkFrame(self, fg_color=self.C_PANEL, corner_radius=0, height=26)
        ftr.grid(row=2, column=0, columnspan=2, sticky="ew")
        ftr.grid_propagate(False)
        ctk.CTkLabel(ftr, text="Treliça 13 Nós  |  Resultados em Fração  |  Python 3", font=ctk.CTkFont(size=9), text_color="#5a7a9a").pack(side="left", padx=12, pady=4)

    def _on_calculate(self):
        """Fluxo de execução: Cálculo -> UI -> Exportação PDF."""
        self.btn_calc.configure(state="disabled", text="⏳  Calculando...")
        self.status_label.configure(text="Resolvendo o sistema de equações...", text_color="#8ab4d4")
        self.update()

        try:
            results, info = solve_truss()
            pdf_path = ctk.filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("Arquivos PDF", "*.pdf")],
                initialfile="relatorio_trelica.pdf",
                title="Salvar Relatório Técnico"
            )

            if not pdf_path:
                self.status_label.configure(text="Geração de PDF cancelada.", text_color="#8ab4d4")
                return

            generate_pdf_report(results, info, pdf_path)
            self._populate_results(results)

            self.status_label.configure(
                text=f"✅  Concluído! PDF gerado em: {pdf_path}",
                text_color=self.C_SUCCESS,
            )
            messagebox.showinfo(
                "Análise Concluída",
                f"✅  Sistema resolvido!\n\n"
                f"• Equações:   {info['n_equations']}\n"
                f"• Incógnitas: {info['n_unknowns']}\n\n"
                f"Relatório PDF salvo com resultados fracionários."
            )

        except Exception as exc:
            self.status_label.configure(text=f"❌  Erro: {exc}", text_color=self.C_ERROR)
            messagebox.showerror("Erro na Análise", str(exc))
        finally:
            self.btn_calc.configure(state="normal", text="▶  Calcular e Gerar PDF")

    def _populate_results(self, results: dict):
        for item in self.tree.get_children():
            self.tree.delete(item)

        tag_map = {"Tração": "tracao", "Compressão": "compressao", "Nulo": "nulo"}
        for name, value in results.items():
            state = classify_force(value)
            self.tree.insert(
                "", "end",
                values=(f"  {name}", f"{format_fraction(value)}", state),
                tags=(tag_map[state],),
            )

if __name__ == "__main__":
    app = TrussApp()
    app.mainloop()
