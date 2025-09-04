# latex_generator.py

import logging
from models import StructuredCV, CVEntry, Section

logger = logging.getLogger(__name__)

# --- Helper Functions ---

def _escape_latex(text: str) -> str:
    """Escapes special LaTeX characters in a string."""
    if not text:
        return ""
    replacements = {
        '&': '\\&', '%': '\\%', '$': '\\$', '#': '\\#', '_': '\\_',
        '{': '\\{', '}': '\\}', '~': '\\textasciitilde{}',
        '^': '\\textasciicircum{}', '\\': '\\textbackslash{}'
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def _generate_preamble() -> str:
    """Returns the complete LaTeX preamble as a string."""
    return "\n".join([
        "\\documentclass[9pt, a4paper]{extarticle}",
        "\\usepackage[a4paper, top=5mm, bottom=5mm, left=9mm, right=9mm]{geometry}",
        "\\usepackage{xcolor}",
        "\\usepackage{paracol}",
        "\\usepackage{hyperref}",
        "\\usepackage{ragged2e}",
        "\\usepackage{enumitem}",
        "\\usepackage{etoolbox}",
        "\\usepackage{amsmath}",
        "\\usepackage{graphicx}",
        "\\usepackage{tikz}",
        "\\usepackage[T1]{fontenc}",
        "\\usepackage[utf8]{inputenc}",
        "\\usepackage{avant}",
        "\\renewcommand{\\familydefault}{\\sfdefault}",
        "\\definecolor{headerblue}{HTML}{2C5F7C}",
        "\\definecolor{sectionheadercolor}{HTML}{555555}",
        "\\definecolor{jobrolecolor}{HTML}{444444}",
        "\\definecolor{metadatacolor}{HTML}{666666}",
        "\\definecolor{bodycolor}{HTML}{444444}",
        "\\definecolor{lightgray}{HTML}{F5F5F5}",
        "\\hypersetup{hidelinks, colorlinks=true, urlcolor=bodycolor, linkcolor=bodycolor, citecolor=bodycolor, breaklinks=true}",
        "\\setlength{\\parindent}{0pt}",
        "\\setlength{\\parskip}{0.2ex}",
        "\\linespread{1.0}",
        "\\setlist[itemize]{label=\\textbullet, leftmargin=*, topsep=1ex, itemsep=0.9ex, parsep=0ex, partopsep=0ex, before=\\RaggedRight}",
        "\\newcommand{\\sectionheader}[1]{\\par\\addvspace{1.2mm}\\noindent{\\normalsize\\bfseries\\color{sectionheadercolor}\\MakeUppercase{#1}}\\par\\addvspace{.4mm}}",
        # The updated command for your preamble generator
        "\\newcommand{\\cvitemrole}[5]{\\par\\addvspace{1mm}\\noindent{\\small\\bfseries\\color{sectionheadercolor}#1\\ifstrempty{#2}{}{ - #2}\\ifstrempty{#3}{}{ - #3}}\\par\\vspace{0.8mm}\\noindent{\\footnotesize\\color{metadatacolor}#4}\\par\\begin{itemize}\\small\\mdseries\\color{bodycolor}#5\\end{itemize}\\addvspace{0.5mm}}",
        "\\newcommand{\\cvsidebaritem}[3]{\\par\\addvspace{2mm}\\noindent{\\mdseries\\textbullet}~{\\small\\bfseries\\color{sectionheadercolor}#1}\\par\\ifstrempty{#2}{}{\\noindent\\hspace{1.5em}{\\small\\itshape\\color{jobrolecolor}#2}\\par}\\ifstrempty{#3}{}{\\vspace{0.3mm}\\noindent\\hspace{1.5em}{\\footnotesize\\color{metadatacolor}#3}\\par}\\addvspace{.4mm}}",
    ])

def _generate_header(info: dict, summary_text: str) -> str:
    """Generates the formatted header section."""
    header = ["\\noindent\\colorbox{lightgray}{\\begin{minipage}[c]{\\dimexpr\\textwidth-2\\fboxsep\\relax}\\vspace{2mm}"]

    # Use the photo from the CV data, or default to the placeholder.
    photo_path = info.get('photo', 'latex_templates/placeholder.png')

    # Ensure the path uses forward slashes for LaTeX, but do NOT escape it.
    photo_path_for_latex = photo_path.replace('\\', '/')

    header.append("\\begin{minipage}[c]{0.17\\textwidth}\\centering\\begin{tikzpicture}\\clip (0,0) circle (1.5cm);")
    # Pass the clean, unescaped path to includegraphics
    header.append(f"\\node at (0,0) {{\\includegraphics[width=3.05cm]{{{photo_path_for_latex}}}}};")
    header.append("\\draw[headerblue, line width=4.5pt] (0,0) circle (1.5cm);\\end{tikzpicture}\\end{minipage}%")


    header.append("\\hspace{0.05\\textwidth}\\begin{minipage}[c]{0.75\\textwidth}\\centering\\vspace*{\\fill}")
    header.append(f"{{\\Huge\\bfseries\\color{{headerblue}}{_escape_latex(info.get('name', ''))}}}")
    if info.get('subtitle'):
        header.append(f"\\\\[0.5em]\n{{\\large\\color{{headerblue}}{_escape_latex(info.get('subtitle'))}}}")
    header.append("\\\\[1em]\\textcolor{headerblue}{\\rule{10cm}{2pt}}\\\\[1em]")
    header.append("\\begin{minipage}{14.5cm}\\centering")
    header.append(f"{{\\small\\color{{bodycolor}}{_escape_latex(summary_text)}}}")
    header.append("\\end{minipage}\\vspace*{\\fill}\\end{minipage}\\vspace{2mm}\\end{minipage}}%\\vspace{5mm}")
    return "\n".join(header)

def _generate_main_column(sections: list[Section]) -> str:
    """Generates the LaTeX for the main (left) column."""
    content = []
    for section in sections:
        if section.name.lower() in ["experience", "projects"]:
            content.append(f"\\sectionheader{{{_escape_latex(section.name)}}}")

            if section.name.lower() == "experience":
                for entry in section.entries:
                    # The JSON subtitle "Company | Location" is split for processing
                    company, location = (entry.subtitle.split('|', 1) + [None])[:2] if entry.subtitle else (None, None)
                    company = company.strip() if company else ''
                    location = location.strip() if location else ''

                    # Metadata line is constructed as "Location • Date"
                    date_str = _escape_latex(entry.date_range or '')
                    loc_str = _escape_latex(location)
                    metadata = f"{loc_str} \\textperiodcentered\\ {date_str}" if loc_str and date_str else (loc_str or date_str)

                    arg1 = _escape_latex(company)
                    arg2 = _escape_latex(entry.title or '') # Job title is now argument #2
                    arg3 = ""
                    arg4 = metadata.strip()
                    arg5 = "".join([f"\\item {_escape_latex(d)}\n" for d in entry.details])
                    content.append(f"\\cvitemrole{{{arg1}}}{{{arg2}}}{{{arg3}}}{{{arg4}}}{{{arg5}}}")

            elif section.name.lower() == "projects":
                for entry in section.entries:
                    tech = f"Technologies: {_escape_latex(', '.join(entry.tags))}" if entry.tags else ""
                    arg1 = _escape_latex(entry.title or '') # Project title is argument #1
                    arg2 = ""
                    arg3 = ""
                    arg4 = tech # Technologies string is now argument #4
                    arg5 = "".join([f"\\item {_escape_latex(d)}\n" for d in entry.details])
                    content.append(f"\\cvitemrole{{{arg1}}}{{{arg2}}}{{{arg3}}}{{{arg4}}}{{{arg5}}}")

    return "\n".join(content)

def _generate_sidebar(sections: list[Section], info: dict) -> str:
    """Generates the LaTeX for the sidebar (right) column."""
    content = []

    # --- Contact Section ---
    content.append("\\sectionheader{Contact}")
    email = info.get('email', '')
    phone = info.get('phone', '')
    email_escaped = _escape_latex(email)
    phone_escaped = _escape_latex(phone)
    content.append(r"{\small\color{bodycolor}\bfseries E:~}\href{mailto:" + email + r"}{" + r"{\small\color{bodycolor}" + email_escaped + r"}}\par\vspace{0.3ex}")
    content.append(r"{\small\color{bodycolor}\bfseries P:~}{\small\color{bodycolor}" + phone_escaped + r"}\par")

    # --- Skills Section (from Key Qualifications) ---
    quals_section = next((s for s in sections if 'qualifications' in s.name.lower()), None)
    if quals_section:
        content.append("\\sectionheader{Skills}")
        content.append("\\begin{itemize}[nosep, itemsep=0.4ex]\\small\\mdseries\\color{bodycolor}")
        for entry in quals_section.entries:
            content.append(f"\\item {_escape_latex(entry.title)}")
        content.append("\\end{itemize}")

    # --- Education, Certifications, and Languages ---
    for section in sections:
        if section.name.lower() == "education":
            content.append(f"\\sectionheader{{{_escape_latex(section.name)}}}")
            for entry in section.entries:
                detail_text = entry.details[0] if entry.details else ''
                content.append(f"\\cvsidebaritem{{{_escape_latex(entry.title or '')}}}{{{_escape_latex(entry.subtitle or '')}}}{{{_escape_latex(detail_text)}}}")

        elif section.name.lower() == "certifications":
            content.append(f"\\sectionheader{{{_escape_latex(section.name)}}}")
            if section.entries and section.entries[0].details:
                for cert_string in section.entries[0].details:
                    # Safely parse "Certification Name (Provider, Year)"
                    parts = cert_string.split('(', 1)
                    title = parts[0].strip()
                    # Check if subtitle exists before accessing it
                    subtitle = ''
                    if len(parts) > 1:
                        subtitle = parts[1].replace(')', '').strip()

                    content.append(f"\\cvsidebaritem{{{_escape_latex(title)}}}{{{_escape_latex(subtitle)}}}{{}}")

        elif section.name.lower() == "languages":
            content.append(f"\\sectionheader{{{_escape_latex(section.name)}}}")
            # The actual language items are in the 'details' array of the first entry
            if section.entries and section.entries[0].details:
                content.append("\\begin{itemize}[nosep, itemsep=0.4ex]\\small\\mdseries\\color{bodycolor}")
                for lang_string in section.entries[0].details:
                    # Reformat "Language (Proficiency)" to "Language: Proficiency"
                    formatted_lang = lang_string.replace(" (", ": ").replace(")", "")
                    content.append(f"\\item {_escape_latex(formatted_lang)}")
                content.append("\\end{itemize}")

    return "\n".join(content)


# --- Main Orchestrator Function ---

def generate_latex_string(cv_data: StructuredCV) -> str:
    """
    Builds a complete LaTeX CV document from a StructuredCV object by assembling its parts.
    """
    logger.info("Building LaTeX string from scratch using modular functions.")

    doc_parts = []

    # 1. Preamble
    doc_parts.append(_generate_preamble())

    # 2. Document Start
    doc_parts.append("\\begin{document}")

    # 3. Header
    summary_section = next((s for s in cv_data.sections if 'summary' in s.name.lower()), None)
    summary_text = ". ".join(summary_section.entries[0].details) if (summary_section and summary_section.entries) else ""
    doc_parts.append(_generate_header(cv_data.personal_info, summary_text))

    # 4. Main Body (two columns using paracol with \columnratio)
    # Set the ratio of columns: 67% for left column, 33% for right column
    doc_parts.append("\\columnratio{0.67}")
    doc_parts.append("\\begin{paracol}{2}")
    doc_parts.append(_generate_main_column(cv_data.sections))
    doc_parts.append("\\switchcolumn")
    doc_parts.append(_generate_sidebar(cv_data.sections, cv_data.personal_info))
    doc_parts.append("\\end{paracol}")

    # 5. Document End
    doc_parts.append("\\end{document}")

    logger.info("LaTeX string generation successful.")
    return "\n".join(doc_parts)