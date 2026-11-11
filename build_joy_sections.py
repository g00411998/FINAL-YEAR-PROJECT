from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


ROOT = "/Users/joyhowlader/Documents/ChatGPT/final year project"
OUT = f"{ROOT}/Parcel Panic - Joy Proposal Sections.docx"
UNITY_IMG = f"{ROOT}/mockups/parcel-panic-unity-simple-pencil-sketch-new-4x3.png"
START_IMG = f"{ROOT}/mockups/parcel-panic-start-screen-sketch.png"
DELIVERY_IMG = f"{ROOT}/mockups/parcel-panic-delivery-complete-sketch.png"
WEB_IMG = f"{ROOT}/mockups/parcel-panic-dispatch-dashboard-sketch.png"
LOGO_IMG = f"{ROOT}/mockups/parcel-panic-logo-preview.png"

doc = Document()
section = doc.sections[0]
section.page_width = Inches(8.27)
section.page_height = Inches(11.69)
section.top_margin = Inches(0.82)
section.bottom_margin = Inches(0.72)
section.left_margin = Inches(0.8)
section.right_margin = Inches(0.8)
section.footer_distance = Inches(0.35)

styles = doc.styles
normal = styles["Normal"]
normal.font.name = "Arial"
normal.font.size = Pt(11)
normal.font.color.rgb = RGBColor(25, 25, 25)
normal.paragraph_format.space_after = Pt(9)
normal.paragraph_format.line_spacing = 1.12

for name, size in [("Title", 23), ("Heading 1", 19), ("Heading 2", 12)]:
    style = styles[name]
    style.font.name = "Arial"
    style.font.size = Pt(size)
    style.font.bold = True
    style.font.color.rgb = RGBColor(0, 0, 0)
    style.paragraph_format.space_before = Pt(0 if name == "Heading 1" else 8)
    style.paragraph_format.space_after = Pt(6)

# Remove the built-in title underline/border, if present.
title_ppr = styles["Title"]._element.get_or_add_pPr()
title_border = title_ppr.find(qn("w:pBdr"))
if title_border is not None:
    title_ppr.remove(title_border)


def shade(cell, colour):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), colour)
    tc_pr.append(shd)


def borders(cell):
    tc_pr = cell._tc.get_or_add_tcPr()
    bdrs = tc_pr.first_child_found_in("w:tcBorders")
    if bdrs is None:
        bdrs = OxmlElement("w:tcBorders")
        tc_pr.append(bdrs)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        node = bdrs.find(qn(f"w:{edge}"))
        if node is None:
            node = OxmlElement(f"w:{edge}")
            bdrs.append(node)
        node.set(qn("w:val"), "single")
        node.set(qn("w:sz"), "5")
        node.set(qn("w:color"), "D9DDE5")


def cell_padding(cell, top=90, start=110, bottom=90, end=110):
    tc_pr = cell._tc.get_or_add_tcPr()
    margins = OxmlElement("w:tcMar")
    for side, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        item = OxmlElement(f"w:{side}")
        item.set(qn("w:w"), str(value))
        item.set(qn("w:type"), "dxa")
        margins.append(item)
    tc_pr.append(margins)


def heading(text):
    table = doc.add_table(rows=1, cols=1)
    table.autofit = False
    cell = table.cell(0, 0)
    cell.width = Inches(6.67)
    shade(cell, "F5A623")
    cell_padding(cell, top=110, start=135, bottom=105, end=135)
    tc_pr = cell._tc.get_or_add_tcPr()
    bdrs = OxmlElement("w:tcBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        edge_node = OxmlElement(f"w:{edge}")
        edge_node.set(qn("w:val"), "nil")
        bdrs.append(edge_node)
    tc_pr.append(bdrs)
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text.upper())
    run.bold = True
    run.font.name = "Arial"
    run.font.size = Pt(13)
    run.font.color.rgb = RGBColor(105, 61, 21)
    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_after = Pt(1)
    spacer.paragraph_format.line_spacing = 0.55
    return p


def subheading(text):
    p = doc.add_paragraph(style="Heading 2")
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.space_before = Pt(11)
    p.paragraph_format.space_after = Pt(5)
    p.add_run(text)
    return p


def caption(text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after = Pt(4)
    run = p.add_run(text)
    run.italic = True
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor(85, 92, 104)
    return p


# Centered page numbers, matching the supplied proposal.
footer = section.footer.paragraphs[0]
footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
page_run = footer.add_run()
page_run.font.name = "Arial"
page_run.font.size = Pt(9)
field = OxmlElement("w:fldSimple")
field.set(qn("w:instr"), "PAGE")
page_run._r.addnext(field)


# Page 1: Branding
heading("Branding")
doc.add_paragraph(
    "Parcel Panic is a timed delivery game set in a small city. The word Parcel explains the delivery theme, while Panic suggests the pressure of racing against the clock. We want the branding to feel playful and easy to recognise."
)
logo_p = doc.add_paragraph()
logo_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
logo_p.paragraph_format.space_after = Pt(0)
logo_p.add_run().add_picture(LOGO_IMG, width=Inches(1.65))
caption("Current Parcel Panic logo concept")
subheading("Why the logo suits the game")
doc.add_paragraph(
    "The courier wears a cap and carries a delivery bag and parcel. The running pose and speed lines show movement. The large game name makes the logo suitable for the start menu, website, and presentation. A simpler courier or parcel icon could be used where the full logo is too small to read."
)
subheading("Colour palette")
doc.add_paragraph(
    "This palette follows the current logo. Purple will be the main brand colour, with pink, cyan, and lime used for highlights. Dark text and a pale background will help keep information readable."
)

palette = [
    ("Purple", "#7C3AED", "Main brand colour and menus"),
    ("Pink", "#EC4899", "Selected orders and highlights"),
    ("Cyan", "#06B6D4", "Routes and map details"),
    ("Lime green", "#84CC16", "Success and available actions"),
    ("Dark purple", "#312E81", "Text and outlines"),
    ("Light background", "#F5F3FF", "Website and menu backgrounds"),
]
table = doc.add_table(rows=1, cols=3)
table.alignment = WD_TABLE_ALIGNMENT.CENTER
table.autofit = False
widths = [Inches(1.55), Inches(1.2), Inches(3.92)]
for col, width in zip(table.columns, widths):
    col.width = width
for cell, text, width in zip(table.rows[0].cells, ["Colour", "Code", "Use"], widths):
    cell.width = width
    cell.text = text
    shade(cell, "FCE4BE")
    borders(cell)
    cell_padding(cell)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    for run in cell.paragraphs[0].runs:
        run.bold = True
        run.font.size = Pt(9.5)
for row_idx, values in enumerate(palette):
    cells = table.add_row().cells
    for idx, (cell, value, width) in enumerate(zip(cells, values, widths)):
        cell.width = width
        cell.text = value
        cell_padding(cell)
        borders(cell)
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        if idx == 0:
            fills = ["7C3AED", "EC4899", "06B6D4", "84CC16", "312E81", "F5F3FF"]
            shade(cell, fills[row_idx])
        elif row_idx % 2:
            shade(cell, "FFF8EE")
        for run in cell.paragraphs[0].runs:
            run.font.size = Pt(9.25)
            run.font.name = "Arial"
            if idx == 0:
                run.bold = True
                run.font.color.rgb = RGBColor(255, 255, 255) if row_idx in (0, 1, 4) else RGBColor(35, 42, 56)

doc.add_paragraph(
    "The group will confirm the final palette before development. Buttons and status messages will also use words and icons, so players do not have to rely on colour alone."
)

# Page 2: Design
doc.add_page_break()
heading("Design")
doc.add_paragraph(
    "The design will help players follow one clear loop: collect a parcel, find the delivery address, deliver it, and choose the next order. A round will last about two minutes, so the player needs to understand the screen quickly."
)
subheading("Game screen")
doc.add_paragraph(
    "The third-person camera will show the courier and the road ahead. This should help the player judge jumps, avoid traffic, and see nearby parcels. A small city block with clear shop fronts and delivery markers will make addresses easier to recognise."
)
subheading("Where the information goes")
doc.add_paragraph(
    "The timer, score, and combo will sit across the top of the screen. Keeping them together will make progress easy to check without covering the courier. The route map will sit in the bottom-right corner, and a marker will point to the current delivery. Short messages will explain events such as picking up a parcel or completing an order."
)
subheading("Companion website")
doc.add_paragraph(
    "On a laptop, the dispatcher will see orders on the left, the city map in the centre, and gadget controls on the right. This places the route beside the actions that can change it. Each gadget button will show whether it is ready and how long its cooldown has left. On a phone, the panels will stack vertically with large, clearly labelled buttons."
)
subheading("Simple and easy to read")
doc.add_paragraph(
    "Both screens will use the same logo, colours, and simple wording. Icons will have text labels, and important messages will stand out against their background. Delivery success will show a points message and a check mark, rather than using colour alone."
)
subheading("How we will check the design")
doc.add_paragraph(
    "We will ask classmates to find the next delivery, check the time, and use a dispatcher gadget. We will note where they hesitate or press the wrong button. Their feedback will help us decide which labels, messages, and controls need changing."
)

# Page 3: Mockups
doc.add_page_break()
heading("Mockups")
doc.add_paragraph(
    "These four sketches show the main screens we plan to make. They are early ideas, not finished designs."
)
mockups = [
    (UNITY_IMG, "Unity gameplay", "The player follows the route, collects a parcel, and avoids traffic while checking time and score."),
    (START_IMG, "Start menu", "Start Game begins a round. How to Play explains the controls and delivery goal before the player starts."),
    (DELIVERY_IMG, "Delivery complete", "A points message confirms a successful delivery. Next Order guides the player back to the delivery loop."),
    (WEB_IMG, "Dispatcher website", "The dispatcher selects an order, checks the courier route, and uses shortcut, boost, or traffic controls."),
]
grid = doc.add_table(rows=2, cols=2)
grid.alignment = WD_TABLE_ALIGNMENT.CENTER
grid.autofit = False
for row in grid.rows:
    for cell in row.cells:
        cell.width = Inches(3.335)
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
        cell_padding(cell, top=100, start=100, bottom=90, end=100)
        borders(cell)
for col in grid.columns:
    col.width = Inches(3.335)
for idx, (image_path, label, explanation) in enumerate(mockups):
    cell = grid.cell(idx // 2, idx % 2)
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(2)
    p.add_run().add_picture(image_path, width=Inches(3.13))
    cap = cell.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_after = Pt(1)
    run = cap.add_run(label)
    run.bold = True
    run.font.size = Pt(10)
    description = cell.add_paragraph(explanation)
    description.paragraph_format.space_after = Pt(5)
    description.paragraph_format.line_spacing = 1.05
    for run in description.runs:
        run.font.size = Pt(10)
doc.add_paragraph(
    "These are AI-assisted concept visuals. We can use them to discuss the layouts, then make editable versions in Figma and improve them with feedback."
)

# Page 4: Final thoughts
doc.add_page_break()
heading("Final Thoughts")
doc.add_paragraph(
    "Parcel Panic will give the courier and dispatcher different jobs in the same round. The courier will focus on movement and deliveries. The dispatcher will help choose routes and use limited gadgets. The design needs to make both roles clear, while keeping the courier's view easy to follow."
)
subheading("What we will build first")
doc.add_paragraph(
    "Our first target will be a solo round in one small city block, with parcel pickup, one delivery address, a timer, and a score. The first website connection will be one simple action, such as placing a delivery marker or opening a shortcut. We can add more parcel types and gadgets once this works reliably."
)
subheading("Main challenges")
doc.add_paragraph(
    "Courier movement needs to feel responsive, and information shared with the website must stay clear and up to date. A delayed action could confuse the dispatcher. The website should show a connection warning if updates stop. Gadget buttons should also show a cooldown so the dispatcher knows why an action is unavailable."
)
subheading("My next steps")
for item in [
    "Confirm the logo and colour palette with the group, then prepare versions for the game and website.",
    "Turn the sketches into editable Figma screens, including a phone layout for the dispatcher.",
    "Test the layouts with classmates and record confusing labels, missed messages, and wrong button presses.",
    "Update the designs and prepare matching images for the proposal and presentation.",
]:
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(6)
    p.add_run(item)

subheading("Final design goal")
doc.add_paragraph(
    "We will judge the design by whether a new player can find the next delivery, read the remaining time, and understand the dispatcher controls. We will use feedback to improve the screens before adding more features. The sketches will guide the first version and will be updated as the project develops."
)

doc.core_properties.title = "Parcel Panic Branding Design Mockups and Final Thoughts"
doc.core_properties.subject = "Joy's proposal section"
doc.core_properties.author = "Joy Howlader"
doc.save(OUT)
print(OUT)
