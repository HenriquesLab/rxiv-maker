# LaTeX Injection Examples

This document provides comprehensive examples of correct LaTeX injection syntax in Rxiv-Maker. All examples use packages that are already pre-loaded in the system template and demonstrate proper usage within document body context.

## Mathematical Expressions and Equations

### Units and SI Notation (siunitx already loaded)

Instead of incorrectly using `{{tex: \usepackage{siunitx}}}`, use the commands directly:

{{tex:
The sample was heated to \SI{373.15}{\kelvin} at a rate of \SI{5}{\kelvin\per\minute}.
The pressure was maintained at \SI{0.1}{\mega\pascal} throughout the experiment.
}}

### Chemical Formulas (mhchem already loaded)

Chemical reactions and formulas work directly:

{{tex:
The oxidation reaction can be written as:
\begin{equation}
\ce{2 Fe + 3/2 O2 -> Fe2O3}
\end{equation}
}}

### Complex Mathematical Expressions (amsmath already loaded)

Advanced mathematical notation using pre-loaded packages:

{{tex:
\begin{align}
\frac{\partial \mathbf{u}}{\partial t} + (\mathbf{u} \cdot \nabla)\mathbf{u} &= -\frac{1}{\rho}\nabla p + \nu \nabla^2 \mathbf{u} + \mathbf{f} \\
\nabla \cdot \mathbf{u} &= 0
\end{align}
}}

### Quantum Mechanics Notation

Instead of using `{{tex: \usepackage{physics}}}` followed by `\braket`, use standard LaTeX:

{{tex:
The quantum state can be written as $\langle \psi | \hat{H} | \psi \rangle$, where the expectation value of the Hamiltonian is:
\begin{equation}
\langle E \rangle = \int_{-\infty}^{\infty} \psi^*(\mathbf{r}) \hat{H} \psi(\mathbf{r}) d^3\mathbf{r}
\end{equation}
}}

## Advanced Tables and Data Presentation

### Professional Data Tables

{{tex:
\begin{table}[h!]
\centering
\begin{tabular}{@{}lcccc@{}}
\toprule
\textbf{Sample} & \textbf{Temperature (°C)} & \textbf{Pressure (bar)} & \textbf{Yield (\%)} & \textbf{Purity (\%)} \\
\midrule
Control & $25.0 \pm 0.1$ & $1.013 \pm 0.001$ & $82.3 \pm 1.5$ & $98.2 \pm 0.3$ \\
Exp-1 & $50.0 \pm 0.2$ & $2.000 \pm 0.005$ & $89.7 \pm 1.2$ & $97.8 \pm 0.4$ \\
Exp-2 & $75.0 \pm 0.3$ & $5.000 \pm 0.010$ & $94.1 \pm 0.8$ & $96.9 \pm 0.5$ \\
Exp-3 & $100.0 \pm 0.5$ & $10.000 \pm 0.020$ & $91.5 \pm 1.1$ & $95.7 \pm 0.6$ \\
\bottomrule
\end{tabular}
\caption{\textbf{Experimental Results Summary.} Temperature, pressure, yield, and purity measurements for control and experimental conditions. All values represent mean $\pm$ standard deviation from triplicate measurements.}
\label{table:experimental-results}
\end{table}
}}

### Statistical Analysis Table

{{tex:
\begin{table}[h!]
\centering
\begin{tabular}{lccc}
\hline
\textbf{Parameter} & \textbf{Value} & \textbf{95\% CI} & \textbf{p-value} \\
\hline
Intercept ($\beta_0$) & 2.47 & [1.85, 3.09] & $< 0.001$ \\
Slope ($\beta_1$) & 0.73 & [0.45, 1.01] & $< 0.001$ \\
$R^2$ & 0.847 & --- & --- \\
RMSE & 0.234 & --- & --- \\
\hline
\end{tabular}
\caption{\textbf{Linear Regression Analysis Results.} Statistical parameters from fitting the relationship between temperature and reaction rate. CI: Confidence Interval; RMSE: Root Mean Square Error.}
\label{table:regression-stats}
\end{table}
}}

## Graphics and Diagrams

### TikZ Diagrams (tikz already loaded)

Instead of `{{tex: \usepackage{tikz}}}`, use TikZ commands directly:

{{tex:
\begin{figure}[h!]
\centering
\begin{tikzpicture}[scale=1.0]
  % Draw reaction pathway
  \draw[thick, ->] (0,0) -- (8,0) node[right] {Reaction Coordinate};
  \draw[thick, ->] (0,0) -- (0,4) node[above] {Energy};

  % Draw energy profile
  \draw[thick, blue] (0,1) .. controls (2,1.2) and (3,2.8) .. (4,3)
                     .. controls (5,3.2) and (6,2.5) .. (8,1.5);

  % Add labels
  \node at (0.5,0.7) {Reactants};
  \node at (4,3.3) {Transition State};
  \node at (7.5,1.2) {Products};

  % Add activation energy arrow
  \draw[<->, red] (0.2,1) -- (0.2,2.9);
  \node[red] at (-0.8,1.95) {$E_a$};
\end{tikzpicture}
\caption{\textbf{Reaction Energy Profile.} Schematic representation of the energy changes during the catalytic reaction, showing activation energy ($E_a$) and overall energy change.}
\label{fig:energy-profile}
\end{figure}
}}

### Process Flow Diagram

{{tex:
\begin{figure}[h!]
\centering
\begin{tikzpicture}[node distance=2cm, auto]
  % Define styles
  \tikzstyle{process} = [rectangle, draw, fill=blue!20, text width=3em, text centered, minimum height=2em]
  \tikzstyle{decision} = [diamond, draw, fill=red!20, text width=4em, text centered, minimum height=2em]
  \tikzstyle{line} = [draw, -latex']

  % Place nodes
  \node [process] (start) {Sample Prep};
  \node [decision, right of=start] (decide) {Quality OK?};
  \node [process, right of=decide, node distance=3cm] (analyze) {Analysis};
  \node [process, below of=decide] (reject) {Reject};
  \node [process, right of=analyze] (report) {Report};

  % Draw edges
  \path [line] (start) -- (decide);
  \path [line] (decide) -- node {Yes} (analyze);
  \path [line] (decide) -- node {No} (reject);
  \path [line] (analyze) -- (report);
\end{tikzpicture}
\caption{\textbf{Sample Processing Workflow.} Flowchart showing the decision points and processes in the experimental protocol.}
\label{fig:workflow}
\end{figure}
}}

## Colored Elements and Highlighting

### Color Boxes and Highlights (xcolor already loaded)

{{tex:
\begin{tcolorbox}[colback=yellow!10, colframe=orange!50, title=Important Note]
The reaction conditions must be maintained within $\pm 2°C$ of the target temperature to ensure reproducible results. Deviation beyond this range may lead to side reactions or incomplete conversion.
\end{tcolorbox}
}}

### Colored Text for Emphasis

{{tex:
The key findings of this study are:
\begin{itemize}
\item \textcolor{blue}{Catalyst activity} increased by 45\% under optimized conditions
\item \textcolor{red}{Side product formation} was reduced to less than 2\%
\item \textcolor{green}{Energy efficiency} improved by 23\% compared to the baseline process
\end{itemize}
}}

## Advanced Mathematical Formatting

### Matrix Operations

{{tex:
The transformation matrix for the coordinate system rotation is given by:
\begin{equation}
\mathbf{R} = \begin{pmatrix}
\cos\theta & -\sin\theta & 0 \\
\sin\theta & \cos\theta & 0 \\
0 & 0 & 1
\end{pmatrix}
\end{equation}
where $\theta$ is the rotation angle about the z-axis.
}}

### Statistical Distributions

{{tex:
The probability density function of the normal distribution is:
\begin{equation}
f(x|\mu,\sigma^2) = \frac{1}{\sqrt{2\pi\sigma^2}} \exp\left(-\frac{(x-\mu)^2}{2\sigma^2}\right)
\end{equation}
with parameters $\mu$ (mean) and $\sigma^2$ (variance).
}}

### Thermodynamic Equations

{{tex:
The Gibbs free energy change for the reaction is calculated using:
\begin{align}
\Delta G &= \Delta H - T\Delta S \\
\Delta G^{\circ} &= -RT \ln K_{eq} \\
K_{eq} &= \frac{[\text{Products}]}{[\text{Reactants}]}
\end{align}
where $R$ is the gas constant and $K_{eq}$ is the equilibrium constant.
}}

## Multi-column Layouts and Complex Formatting

### Two-column Comparison

{{tex:
\begin{table}[h!]
\centering
\begin{tabular}{|p{6cm}|p{6cm}|}
\hline
\textbf{Traditional Method} & \textbf{Optimized Method} \\
\hline
Temperature: 150°C & Temperature: 120°C \\
Pressure: 10 bar & Pressure: 5 bar \\
Time: 8 hours & Time: 4 hours \\
Yield: 65\% & Yield: 89\% \\
Energy consumption: High & Energy consumption: Medium \\
Catalyst requirement: 5\% & Catalyst requirement: 2\% \\
\hline
\end{tabular}
\caption{\textbf{Method Comparison.} Side-by-side comparison of process parameters and outcomes for traditional versus optimized synthetic routes.}
\label{table:method-comparison}
\end{table}
}}

### Multi-step Procedure

{{tex:
\begin{enumerate}
\item \textbf{Preparation Phase:}
  \begin{enumerate}
    \item Weigh reactants to $\pm 0.001$ g precision
    \item Pre-heat reactor to \SI{100}{\celsius}
    \item Purge system with nitrogen for 10 minutes
  \end{enumerate}

\item \textbf{Reaction Phase:}
  \begin{enumerate}
    \item Add reactants in the following order: A, then B, then catalyst
    \item Increase temperature to \SI{150}{\celsius} at \SI{5}{\celsius\per\minute}
    \item Maintain conditions for 4 hours with continuous stirring
  \end{enumerate}

\item \textbf{Workup Phase:}
  \begin{enumerate}
    \item Cool to room temperature
    \item Filter and wash precipitate with cold ethanol
    \item Dry under vacuum at \SI{60}{\celsius} overnight
  \end{enumerate}
\end{enumerate}
}}

## Notes on Package Usage

**Important:** All the examples above use packages that are already pre-loaded in the Rxiv-Maker template:

- `amsmath` and `amssymb` for advanced mathematics
- `siunitx` for units and scientific notation
- `mhchem` for chemical formulas
- `tikz` for diagrams and graphics
- `xcolor` for colored elements
- `booktabs` for professional tables
- `tcolorbox` for colored boxes and highlights

**Do not include `\usepackage{...}` commands in `{{tex: ...}}` blocks** as these belong in the document preamble and will cause compilation errors when placed in the document body.

If you need functionality from packages not already loaded, please consult the Rxiv-Maker documentation for adding packages to the template preamble, or find alternative approaches using the already-available packages.