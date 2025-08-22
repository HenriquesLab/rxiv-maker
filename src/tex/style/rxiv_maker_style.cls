%%
%% This is file `rxiv_maker_style.cls',
%%
%% Unified version combining regular and arXiv-compatible features
%% Uses listings instead of minted for maximum compatibility
%% Watermark functionality disabled for arXiv compatibility
%%
%% Class files for pre-print servers such as Rxiv
%%
%% Copyright (C) Jacquemet and Henriques Labs <ricardo@henriqueslab.org>
%%
\typeout{Document Class `rxiv_maker_style' <20-June-2025>.}
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{rxiv_maker_style}
  [2025/06/20 unified arXiv compatible revision by Jacquemet and Henriques Labs]

%% Load base class
\LoadClass[a4paper]{article}

%% define new needed boolean variables
\newif\if@tmptwocolumn  \@tmptwocolumnfalse
\newif\if@times         \@timesfalse

%% Options
\newif\ifbfabstract     \bfabstracttrue
\DeclareOption{rmabstract}{\bfabstractfalse}
\newif\ifbibskip        \bibskipfalse
\DeclareOption{bibskip}{\bibskiptrue}
\newif\ifwatermark        \watermarkfalse
\DeclareOption{watermark}{\watermarktrue}

\DeclareOption{draft}{\PassOptionsToClass{draft}{article}}
\DeclareOption{times}{\@timestrue}
\DeclareOption{twoside}{\@twosidetrue}
\DeclareOption{twocolumn}{\@tmptwocolumntrue}
\DeclareOption{onecolumn}{\@tmptwocolumnfalse}
%\DeclareOption{watermark}{\@displaywatermark}

\ExecuteOptions{times,twoside,twocolumn}
\ProcessOptions

%% and math support and fonts
\RequirePackage{amsmath,amsfonts,amssymb}
\RequirePackage{mathptmx}

%% Make sections unnumbered by default
\setcounter{secnumdepth}{0}

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Jacquemet and Henriques lab dependencies - Start %%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
\RequirePackage{xcolor}
\RequirePackage{authblk}
\RequirePackage[latin1,utf8]{inputenc}
\RequirePackage[english]{babel}
%\RequirePackage{lmodern}
\RequirePackage{siunitx}
\RequirePackage{textgreek}
\RequirePackage[colorlinks=true, allcolors=blue]{hyperref}
\RequirePackage{cleveref}
\RequirePackage{gensymb}
\RequirePackage{textcomp}
\RequirePackage[version=4]{mhchem}
\RequirePackage{placeins}
\RequirePackage{afterpage}
\RequirePackage{needspace}
\RequirePackage{tabularx}
\RequirePackage{longtable}
\RequirePackage[scaled]{helvet}
\RequirePackage[T1]{fontenc}
\RequirePackage{lettrine} % For dropped capitals
\RequirePackage[rightcaption]{sidecap} % For sidecaptions
\RequirePackage[misc]{ifsym} % For the \Letter symbol
\RequirePackage{bbding} % For the \Envelope symbol
\RequirePackage[twoside,%
			letterpaper,includeheadfoot,%
			layoutsize={8.125in,10.875in},%
                layouthoffset=0.1875in,%
                layoutvoffset=0.0625in,%
                left=38.5pt,%
                right=43pt,%
                top=43pt,% 10pt provided by headsep
                bottom=32pt,%
                headheight=0pt,% No Header
                headsep=10pt,%
                footskip=25pt]{geometry}
\RequirePackage[labelfont={bf,sf},%
                labelsep=period,%
                figurename=Fig.]{caption}
\RequirePackage{scalerel} % for ORCID Icon
\RequirePackage{tikz} % for ORCID Icon
\usetikzlibrary{svg.path} % for ORCID Icon
\usepackage{fontawesome} % for Twitter Icon
\DeclareUnicodeCharacter{00B0}{\degree}

%% Hyperlinking (already loaded above at line 52)

%% Ref to Sup
\RequirePackage{nameref}
\RequirePackage{cleveref}
\crefname{equation}{Eq. S}{equations}
\crefname{figure}{Fig.}{figures}
\crefname{section}{Sup. Note}{notes}
\crefname{sfigure}{SFig.}{sfigures}

%% Float parameters to eliminate white space and improve text flow
\renewcommand{\floatpagefraction}{0.7}   % Fill 70% of dedicated float pages (default: 0.2) - conservative improvement
\renewcommand{\topfraction}{0.8}         % Allow 80% of page top for floats (default: 0.7) - moderate increase
\renewcommand{\bottomfraction}{0.7}      % Allow 70% of page bottom for floats (default: 0.3) - reasonable increase
\renewcommand{\textfraction}{0.1}        % Require 10% text per page (default: 0.2) - safe permissive setting
\setcounter{totalnumber}{10}             % Allow reasonable floats per page (default: 3) - prevents memory issues
\setcounter{topnumber}{5}                % Allow moderate floats at top (default: 2) - balanced approach
\setcounter{bottomnumber}{5}             % Allow moderate floats at bottom (default: 1) - balanced approach

%% Custom command for supplementary notes that properly increments counter and displays number
\newcommand{\suppnotesection}[1]{%
  \refstepcounter{subsection}%
  \subsection*{\thesubsection: #1}%
}

%% Unified supplementary float environments
% Supplementary figures counter and environments
\newcounter{sfigure}
\renewcommand{\thesfigure}{S\arabic{sfigure}}
\newenvironment{sfigure}[1][htbp]{%
  \begin{figure}[#1]%
  \renewcommand{\thefigure}{\thesfigure}%
  \stepcounter{sfigure}%
}{%
  \end{figure}%
}

% Supplementary tables counter and environments
\newcounter{stable}
\renewcommand{\thestable}{S\arabic{stable}}
\newenvironment{stable}[1][htbp]{%
  \begin{table}[#1]%
  \renewcommand{\thetable}{\thestable}%
  \stepcounter{stable}%
}{%
  \end{table}%
}

% Double-column supplementary table environment
\newenvironment{stable*}[1][htbp]{%
  \begin{table*}[#1]%
  \renewcommand{\thetable}{\thestable}%
  \stepcounter{stable}%
}{%
  \end{table*}%
}

% Rotated supplementary table environment using sidewaystable
\RequirePackage{rotating}
\newenvironment{ssidewaystable}{%
  \begin{sidewaystable}%
  \renewcommand{\thetable}{\thestable}%
  \stepcounter{stable}%
}{%
  \end{sidewaystable}%
}

%% Core document functionality packages
\RequirePackage{listings}   % Code formatting (arXiv compatible replacement for minted)
\RequirePackage{pdfpages}   % Document assembly
\RequirePackage{url}        % URL formatting and line breaks
\RequirePackage{seqsplit}   % Better long text breaking

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Jacquemet and Henriques lab dependencies - End %%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%% Code block formatting (listings configuration - arXiv compatible)
%% Configure listings to mimic minted appearance
\definecolor{codebg}{RGB}{248,248,248}
\definecolor{codeframe}{RGB}{204,204,204}

\lstdefinestyle{arxivstyle}{
    backgroundcolor=\color{codebg},
    commentstyle=\color{green!60!black},
    keywordstyle=\color{blue},
    numberstyle=\tiny\color{gray},
    stringstyle=\color{red},
    basicstyle=\fontsize{10}{12}\ttfamily,
    breakatwhitespace=false,
    breaklines=true,
    captionpos=b,
    keepspaces=true,
    numbers=none,
    numbersep=5pt,
    showspaces=false,
    showstringspaces=false,
    showtabs=false,
    tabsize=2,
    frame=none,
    aboveskip=6pt,
    belowskip=6pt,
    xleftmargin=0pt,
    xrightmargin=0pt
}

%% Set default style
\lstset{style=arxivstyle}

%% Define languages for syntax highlighting
\lstdefinelanguage{latex}{
    keywords={begin,end,documentclass,usepackage,newcommand,renewcommand,section,subsection,subsubsection,
              textbf,textit,emph,cite,ref,label,caption,includegraphics,
              nabla,times,mathbf,frac,partial,sum,int,alpha,beta,gamma,delta,epsilon,mu,sigma,rho,
              align,equation,gather,multiline},
    keywordstyle=\color{blue},
    sensitive=true,
    comment=[l]{\%},
    commentstyle=\color{green!60!black},
    string=[b]{"},
    stringstyle=\color{red},
    morestring=[b]',
    moredelim=*[s][\color{purple}]{\$}{\$},
    moredelim=*[s][\color{purple}]{\$\$}{\$\$}
}

%% Command to mimic minted font size setting
\newcommand{\mintedconsize}{\fontsize{10}{12}\selectfont}

%% Fonts

\if@times\RequirePackage{times}\fi



%% sizes and margins
\topmargin      -16.0mm
%\oddsidemargin  -11.0mm
%\evensidemargin -11.0mm
%\textwidth        175mm
\textheight       243mm
\columnsep          7mm
\headsep          6.3mm
\headheight        12pt
\lineskip           1pt
\normallineskip     1pt
\def\baselinestretch{1}

\marginparsep      10pt
\marginparwidth    20pt
\marginparpush     25pt

\partopsep          \z@
\topsep           1.3ex
\parsep             \z@
\itemsep            \z@

%%
\abovedisplayskip       0pt plus2pt minus5pt%
\belowdisplayskip       \abovedisplayskip
\abovedisplayshortskip  0pt plus3pt%
\belowdisplayshortskip  0pt plus3pt minus3pt%

\arraycolsep     5pt
\tabcolsep       6pt
\arrayrulewidth .4pt
\doublerulesep   2pt
\tabbingsep\labelsep

%% footnotes
\skip\footins 10pt plus 4pt minus 2pt
\footnotesep 7pt
\footskip 10mm
\skip\@mpfootins = \skip\footins
\fboxsep = 3pt \fboxrule = .4pt
\long\def\@makefntext#1{\parindent .8em\indent$^{\@thefnmark}$#1}
\def\footnoterule{}


\newdimen\@maxsep
\newdimen\@dblmaxsep
%% Definitions for floats
%%
%% Normal Floats                      %% Double Column Floats
\floatsep 12pt plus 2pt minus 2pt     \dblfloatsep 12pt plus 2pt minus 2pt
\textfloatsep 20pt plus 2pt minus 4pt \dbltextfloatsep 20pt plus 2pt minus 4pt
\@maxsep 20pt                         \@dblmaxsep 20pt
\@fptop 0pt plus 1fil                 \@dblfptop 0pt plus 1fil
\@fpsep 8pt plus 2fil                 \@dblfpsep 8pt plus 2fil
\@fpbot 0pt plus 1fil                 \@dblfpbot 0pt plus 1fil
\def\topfraction{1.0}                 \def\dbltopfraction{1.0}
\def\floatpagefraction{0.8}           \def\dblfloatpagefraction{0.8}
\setcounter{topnumber}{2}             \setcounter{dbltopnumber}{4}
\intextsep 12pt plus 2pt minus 2pt
\setcounter{bottomnumber}{2}
\def\bottomfraction{.1}
\setcounter{totalnumber}{4}
\def\textfraction{.1}
\setlength{\belowcaptionskip}{-10pt} % reduces spacing between figure legend and text

\renewcommand{\topfraction}{0.99}
\renewcommand{\floatpagefraction}{0.5}
\renewcommand{\bottomfraction}{0.99}
\renewcommand{\textfraction}{0.01}

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% %%
%% Jacquemet and Henriques lab parts adapted from PNAS %%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\newcommand{\shorttitle}[1]{\def\@shorttitle{#1}}
\newcommand{\leadauthor}[1]{\def\@leadauthor{#1}}
%\newcommand{\headerfont}{\normalfont\sffamily\fontsize{7}{9} \selectfont}
\newcommand{\footerfont}{\normalfont\sffamily\fontsize{7}{9} \selectfont}
\newcommand{\titlefont}{\fontfamily{lmss}\bfseries\fontsize{22pt}{24pt}\selectfont}
\newcommand{\dropcapfont}{\fontfamily{lmss}\bfseries\fontsize{26pt}{28pt}\selectfont}
\newcommand{\datesfont}{\normalfont\sffamily\fontsize{7}{8}\selectfont}
\newcommand{\absfont}{\normalfont\sffamily\bfseries\fontsize{8}{11}\selectfont}
\newcommand{\keywordsfont}{\normalfont\rmfamily\fontsize{7}{10}\selectfont}
\newcommand{\copyrightfont}{\normalfont\rmfamily\fontsize{6}{8}\selectfont}

%% Set document color scheme
\definecolor{black50}{gray}{0.5} % 50% black for hrules
\definecolor{color0}{RGB}{0,0,0} % Base
\definecolor{color1}{RGB}{59,90,198} % author email, doi
\definecolor{color2}{RGB}{16,131,16} %

%% Author and affiliation
\setlength{\affilsep}{8.5pt} % 16.5pts between base of author line and base of affil line
\renewcommand\Authfont{\color{color0}\normalfont\sffamily\bfseries\fontsize{9}{11}\selectfont}
\renewcommand\Affilfont{\color{color0}\normalfont\sffamily\fontsize{7}{8}\selectfont}
\makeatletter
\renewcommand\Authands{, and }

%% Section/subsection/paragraph set-up
\RequirePackage[explicit]{titlesec}
\renewcommand{\thesubsection}{\Alph{subsection}}

%\usepackage[explicit]{titlesec}
% \titleformat{<command>}[<shape>]{<format>}{<label>}{<sep>}{<before>}[<after>]
% \titleformat{\section}[hang]{\normalfont\Large\bfseries}%
%     {\thechapter.}{4pt}%
%     {#1 \arabic{section}.}
% \makeatletter
% \renewcommand\thesection{}
% \renewcommand\thesubsection{\@arabic\c@section.\@arabic\c@subsection}
% \makeatother
% \titleformat{\section}[hang]
%   {\large\sffamily\bfseries}
%   {\thesection.}
%   {0.5em}
%   {#1.}
%   []

\titleformat{\section}
  {\large\sffamily\bfseries}
  {}
  {0em}
  {Note \thesection: #1}
  []
\titleformat{name=\section,numberless}
  {\large\sffamily\bfseries}
  {}
  {0em}
  {#1}
  []
\titleformat{\subsection}[runin]
  {\sffamily\bfseries}
  {\thesubsection.}
  {0.5em}
  {#1. }
  []
\titleformat{\subsubsection}[runin]
  {\sffamily\small\bfseries\itshape}
  {\thesubsubsection.}
  {0.5em}
  {#1. }
  []
\titleformat{\paragraph}[runin]
  {\sffamily\small\bfseries}
  {}
  {0em}
  {#1}
\titlespacing*{\section}{0pc}{3ex \@plus4pt \@minus3pt}{5pt}
\titlespacing*{\subsection}{0pc}{2.5ex \@plus3pt \@minus2pt}{2pt}
\titlespacing*{\subsubsection}{0pc}{2ex \@plus2.5pt \@minus1.5pt}{2pt}
\titlespacing*{\paragraph}{0pc}{1.5ex \@plus2pt \@minus1pt}{12pt}

%% Figure caption style
\DeclareCaptionFormat{smallformat}{\normalfont\sffamily\fontsize{7}{9}\selectfont#1#2#3}
\DeclareCaptionFormat{largeformat}{\normalfont\sffamily\fontsize{9}{12}\selectfont#1#2#3}
\captionsetup*{format=smallformat}

% %% Watermark - Disabled for arXiv compatibility
% arXiv doesn't support xwatermark package due to grouping issues
% \usepackage[printwatermark]{xwatermark}
% \AtBeginDocument{%
%   \ifwatermark%
%   \newwatermark[allpages,color=gray!20,angle=45,scale=3,xpos=0,ypos=0]{DRAFT}
%   \fi
% }

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Jacquemet and Henriques lab parts adapted from PNAS - END %%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Jacquemet and Henriques lab parts to count words - Start %%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\RequirePackage{verbatim}

%% You can pass in your own texcount params, e.g. -chinese to turn on Chinese mode, or -char to do a character count instead (which does NOT include spaces!)
%%% http://app.uio.no/ifi/texcount/documentation.html
\newcommand{\detailtexcount}{%
  \immediate\write18{texcount -merge -sum -incbib -dir \jobname.tex > \jobname.wcdetail }%
  \verbatiminput{\jobname.wcdetail}%
}

\newcommand{\quickwordcount}{%
  \immediate\write18{texcount -1 -sum -merge \jobname.tex > \jobname-words.sum }%
  \input{\jobname-words.sum} words%
}

\newcommand{\quickcharcount}{%
  \immediate\write18{texcount -1 -sum -merge -char \jobname.tex > \jobname-chars.sum }%
  \input{\jobname-chars.sum} characters (not including spaces)%
}

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Jacquemet and Henriques lab parts to count words - End %%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%% marks
\def\markboth#1#2{\def\leftmark{#1}\def\rightmark{#2}}
\def\footernote#1{\markboth{#1}{#1}}

% %% bibliography
\RequirePackage{chapterbib}
\RequirePackage[sectionbib,numbers,sort&compress,merge,round]{natbib}
\setlength{\bibsep}{0.0pt}
\bibliographystyle{rxiv_maker_style}
\renewcommand{\bibsection}{} % Remove header
\renewcommand\bibfont{\normalfont\sffamily\fontsize{6}{8}\selectfont} % set font to be sans serif

\makeatletter
\renewcommand\@biblabel[1]{ #1.} % Remove brackets from label
\def\tagform@#1{\maketag@@@{\bfseries(\ignorespaces#1\unskip\@@italiccorr)}}
\renewcommand{\eqref}[1]{\textup{{\normalfont Eq.~(\ref{#1}}\normalfont)}}
% \makeatother

%% Title
\def\maketitle{\par
  \begingroup
  \def\thefootnote{} % the \thanks{} mark type is empty
\if@tmptwocolumn
  \twocolumn[\@maketitle]
\else
  \@maketitle
\fi
  \thispagestyle{plain}\@thanks
  \endgroup
  \setcounter{footnote}{0}\let\maketitle\relax\let\@maketitle\relax
  \gdef\@thanks{}\gdef\@author{}\gdef\@title{}\let\thanks\relax
}

\def\@maketitle{\newpage
  \begin{center}
    \vskip0.2em{\Huge\bfseries\@title\par}\vskip1.0em%
    {\lineskip.5em\large\@author\par}
  \end{center}\par\vskip 1.4em}

%% Abstract and keywords
\def\abstract{%\vspace{-.3em}
  \ifbfabstract\small\bfseries\else\footnotesize\fi}

\def\endabstract{\vspace{1.0em}\par\normalsize}

% \def\keywords{%\vspace{-.3em}
% \noindent\ifbfabstract\Affilfont\bfseries\itshape\else\footnotesize\fi  Keywords --- }
% \def\endkeywords{\vspace{0.3em}\par\normalsize}

% \newcommand{\at}{\makeatletter @\makeatother}
% \def\corrauthor{%\vspace{-.3em}
% \noindent\ifbfabstract\Affilfont\bfseries\itshape\else\footnotesize\fi  Correspondence --- }
% \def\endcorrauthor{\vspace{0.3em}\par\normalsize}

\def\keywords{%\vspace{-.3em}
\ifbfabstract\Affilfont\bfseries\else\footnotesize\fi}
\def\endkeywords{\vspace{0.3em}\par\normalsize}

\newcommand{\at}{\makeatletter @\makeatother}
\def\corrauthor{%\vspace{-.3em}
\noindent\ifbfabstract\Affilfont\bfseries\else\footnotesize\fi  Correspondence:\itshape}
\def\endcorrauthor{\vspace{0.3em}\par\normalsize}

\def\acknowledgements{\vspace{.3em}
\Affilfont\bfseries ACKNOWLEDGEMENTS\par\mdseries}
\def\endacknowledgements{\vspace{0.3em}\par\normalsize}

\def\manuscriptinfo{\vspace{.3em}
\Affilfont\bfseries ABOUT THIS MANUSCRIPT\par\mdseries}
\def\endmanuscriptinfo{\vspace{0.3em}\par\normalsize}

\def\contributions{\vspace{.3em}
\Affilfont\bfseries AUTHOR CONTRIBUTIONS\par\mdseries}
\def\endcontributions{\vspace{0.3em}\par\normalsize}

\def\data{\vspace{.3em}
\Affilfont\bfseries DATA AVAILABILITY\par\mdseries}
\def\enddata{\vspace{0.3em}\par\normalsize}

\def\code{\vspace{.3em}
\Affilfont\bfseries CODE AVAILABILITY\par\mdseries}
\def\endcode{\vspace{0.3em}\par\normalsize}

\def\funding{\vspace{.3em}
\Affilfont\bfseries FUNDING\par\mdseries}
\def\endfunding{\vspace{0.3em}\par\normalsize}

\def\interests{\vspace{.3em}
\Affilfont\bfseries COMPETING FINANCIAL INTERESTS\par\mdseries}
\def\endinterests{\vspace{0.3em}\par\normalsize}

\def\exauthor{\vspace{.3em}
\Affilfont\bfseries EXTENDED AUTHOR INFORMATION \par\mdseries}
\def\endexauthor{\vspace{0.3em}\par\normalsize}

%% Custom environment for extended author info with reduced indentation
\newenvironment{extendedauthorlist}{%
  \begin{list}{\textbullet}{%
    \setlength{\leftmargin}{1em}%         % Reduce left margin
    \setlength{\itemindent}{0em}%         % No extra indentation for items
    \setlength{\labelsep}{0.5em}%         % Space between bullet and text
    \setlength{\labelwidth}{0.5em}%       % Width of label area
    \setlength{\itemsep}{0.5em}%          % Space between items
    \setlength{\parsep}{0em}%             % No extra paragraph spacing
    \setlength{\topsep}{0.3em}%           % Space before list
    \setlength{\partopsep}{0em}%          % No extra space when list starts paragraph
  }%
}{%
  \end{list}%
}

%% Command for formatting individual extended author entries
\newcommand{\extendedauthor}[2]{%
  \item \textbf{#1:}\\[0.2em]%
  #2%
}

%% ORCID

\definecolor{orcidlogocol}{HTML}{A6CE39}
\tikzset{
  orcidlogo/.pic={
    \fill[orcidlogocol] svg{M256,128c0,70.7-57.3,128-128,128C57.3,256,0,198.7,0,128C0,57.3,57.3,0,128,0C198.7,0,256,57.3,256,128z};
    \fill[white] svg{M86.3,186.2H70.9V79.1h15.4v48.4V186.2z}
                 svg{M108.9,79.1h41.6c39.6,0,57,28.3,57,53.6c0,27.5-21.5,53.6-56.8,53.6h-41.8V79.1z M124.3,172.4h24.5c34.9,0,42.9-26.5,42.9-39.7c0-21.5-13.7-39.7-43.7-39.7h-23.7V172.4z}
                 svg{M88.7,56.8c0,5.5-4.5,10.1-10.1,10.1c-5.6,0-10.1-4.6-10.1-10.1c0-5.6,4.5-10.1,10.1-10.1C84.2,46.7,88.7,51.3,88.7,56.8z};
  }
}
\newcommand\orcidicon[1]{\href{https://orcid.org/#1}{\mbox{\scalerel*{
\begin{tikzpicture}[yscale=-1,transform shape]
\pic{orcidlogo};
\end{tikzpicture}
}{|}}}~\href{https://orcid.org/#1}{#1}}

\newcommand\twittericon[1]{\href{https://twitter.com/#1}{\faTwitter}~\href{https://twitter.com/#1}{#1}}
\newcommand\xicon[1]{\href{https://x.com/#1}{\faTwitter}~\href{https://x.com/#1}{#1}}
\newcommand\blueskyicon[1]{\href{https://bsky.app/profile/#1}{\textcolor{blue}{\faStar}}~\href{https://bsky.app/profile/#1}{#1}}
\newcommand\linkedinicon[1]{\href{https://linkedin.com/in/#1}{\faLinkedin}~\href{https://linkedin.com/in/#1}{#1}}

%% environments
\newdimen\tmpitemindent
\def\QED{\mbox{\rule[0pt]{1.5ex}{1.5ex}}}
\def\proof{\noindent\hspace{2em}{\it Proof: }}
\def\endproof{\hspace*{\fill}~\QED\par\endtrivlist\unskip}
\def\@begintheorem#1#2{\tmpitemindent\itemindent\topsep 0pt\rm\trivlist
    \item[\hskip \labelsep{\indent\it #1\ #2:}]\itemindent\tmpitemindent}
\def\@opargbegintheorem#1#2#3{\tmpitemindent\itemindent\topsep 0pt\rm \trivlist
    \item[\hskip\labelsep{\indent\it #1\ #2\ \rm(#3)}]\itemindent\tmpitemindent}
\def\@endtheorem{\endtrivlist\unskip}

\newtheorem{theorem}{Theorem}
\newtheorem{definition}{Definition}
\newtheorem{corollary}{Corollary}

\twocolumn \sloppy \flushbottom

%% Units
\DeclareSIUnit\molar{\mole\per\cubic\deci\metre}
\DeclareSIUnit\Molar{\textsc{m}}


%% Allows to enter BIOGRAPHY leaving place for picture
%%
\newenvironment{biography}[1]{%
\footnotesize\unitlength 1mm\bigskip\bigskip\bigskip\parskip=0pt\par%
\rule{0pt}{39mm}\vspace{-39mm}\par%   guarantees correct page breaking
\noindent\setbox0\hbox{\framebox(25,32){}}%   box containing the frame
\ht0=37mm\count10=\ht0\divide\count10 by\baselineskip%  calculates lines
\global\hangindent29mm\global\hangafter-\count10%
\hskip-28.5mm\setbox0\hbox to 28.5mm {\raise-30.5mm\box0\hss}%
\dp0=0mm\ht0=0mm\box0\noindent\bf#1\rm}{
\par\rm\normalsize}

%% Default rules for including pictures
\RequirePackage{graphicx}
\RequirePackage{color}
\DeclareGraphicsRule{*}{eps}{*}{}

%% Page headers and footers
%%
\RequirePackage{fancyhdr} % Custom headers/footers
\RequirePackage{lastpage} % Number of pages in the document
\pagestyle{fancy}		  % Enables the custom headers/footers


\def\aRxiv{{\footnotesize
    \footerfont {\color{white}rxiv-maker\hspace{2pt}|\hspace{7pt}}\@leadauthor\ifnum \value{authors} > 1\hspace{2pt}\textit{et al.}\fi\hspace{7pt}|\hspace{7pt}\today\hspace{7pt}|\hspace{7pt}\thepage\textendash\pageref{LastPage}
  }}

\def\bRxiv{{\footnotesize
    \footerfont \thepage
  }}

\def\cRxiv{{\footnotesize
    \footerfont \thepage
  }}

\def\dRxiv{{\footnotesize
    \footerfont \@leadauthor\ifnum \value{authors} > 1\hspace{2pt}\textit{et al.}\fi\hspace{7pt}|\hspace{7pt}\@shorttitle
  }}


\lfoot[\bRxiv]{\dRxiv}
\rfoot[\dRxiv]{\cRxiv}

\rhead[]{\footnotesize\rightmark}
\lhead[\footnotesize\leftmark]{}
\cfoot{}
\renewcommand{\headrulewidth}{0pt}

\fancypagestyle{plain}{
\fancyhf{}
\fancyfoot[RE]{}
\fancyfoot[LO]{}
\fancyfoot[LE]{}
\fancyfoot[RO]{\aRxiv}}

\def\sectionmark#1{\relax}

\parindent=0pt
\endinput
