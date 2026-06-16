# 📊 Truss Bridge Structural Analysis - Method of Nodes

![Language](https://img.shields.io/badge/Language-Python-blue)
![Library](https://img.shields.io/badge/Library-NumPy-green)
![Category](https://img.shields.io/badge/Category-Solid%20Mechanics-lightgrey)
![Status](https://img.shields.io/badge/Status-Completed-success)

---

## 📄 Overview

This repository contains the Python implementation for the **structural analysis and validation of a wooden truss bridge**, developed as a practical project for the **Solid Mechanics** (Mecânica dos Sólidos) course. 

The project involves the optimization, mathematical modeling, and structural assessment of a Warren-type parallel-chord truss bridge built using wooden tongue depressors and screw-nut connections. The core objective is to maximize the bridge's load capacity while minimizing its overall weight and financial cost, respecting the strict design constraints provided by the university.

---

## 🧠 Structural & Computational Modeling

In the context of civil and mechanical engineering, a truss is analyzed by assuming all members are connected via ideal frictionless joints (pins) and that external loads act exclusively on the nodes.

### This project automates:
- **Topology & Geometry Definition:** Mapping the coordinates of the multi-nodal 2D truss framework.
- **Incidence Matrix Assembly:** Building the structural connectivity layout linking members (bars) to their respective joints.
- **Linear System Generation ($[A]\{F\} = \{B\}$):** Formulating a deterministic system of joint equilibrium equations derived from static equilibrium ($\Sigma F_x = 0$ and $\Sigma F_y = 0$).
- **Vectorized Internal Force Solving:** Processing the system using numerical libraries to compute support reactions and internal axial forces (tension and compression) instantaneously.

---

## 🚀 Key Skills Demonstrated

- **Mathematical Modeling:** Implementation of the traditional **Method of Nodes** into a generalized matrix framework for arbitrary structural configurations.
- **Computational Engineering & Validation:** Design of a Python script to cross-validate analytical manual hand-calculations, eliminating algebraic errors and ensuring exact static closure.
- **Engineering Optimization:** Iterative design refinement by shifting from an unstable prototype to a reinforced double/triple-layered final structure, mitigating buckling failures in compressed members.

---

## 🛠️ Technologies & Tools

| Category | Detail |
| :--- | :--- |
| **Language** | Python 3.x |
| **Numerical Library** | NumPy |
| **CAD Software** | NanoCAD (Geometry Extraction & Drafting) |
| **Methodology** | Matrix Method of Joints / Analytical / Prototyping |

---

## 📐 Structural Specifications & Design Constraints

The model strictly adheres to the project guidelines set by the institution:
- **Span Distance (Vão):** Exactly $600 \text{ mm}$ between the support nodes.
- **Maximum Length:** $800 \text{ mm}$.
- **Maximum Heights:** Up to $280 \text{ mm}$ above the supports and $140 \text{ mm}$ below.
- **Width Range:** Between $65 \text{ mm}$ and $140 \text{ mm}$.
- **Load Application:** Mid-span central lower node via a dedicated hanging loading mechanism until structural collapse occurs.

---

## 🎓 Course Information

| Detail | Value |
| :--- | :--- |
| **Course** | Mechanics of Solids (Mecânica dos Sólidos) |
| **Institution** | Pontifical Catholic University of Campinas (PUC-Campinas) |
| **Program** | Computer Engineering |
| **Professor** | Prof. Dr. Fábio Menegatti de Melo |
| **Academic Term** | 1st Semester 2026 |
| **Project Team** | • João Paulo Nunes Andrade <br>• Eduardo Domingues Blanco <br>• Ulisses Miguel Dotta da Silva <br>• Gabriel Oliveira Batista  |

---

